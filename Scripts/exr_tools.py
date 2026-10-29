"""Colour-managed PNG <-> EXR transfer for the AI environment plate (pure Python, no numpy/PIL).

Run with Unreal's Python:  "C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/ThirdParty/Python3/Win64/python.exe"

  exr_tools.py info     plate.exr
  exr_tools.py stats    image.png|image.exr [--linear]           mean linear RGB / luminance
  exr_tools.py fitlut   pass.exr pass.png lut.json [--step N]
        fit the inverse of the project's display transform (exposure + ACES tonemap + sRGB) from a
        pixel-aligned MRQ FinalImage EXR (compression NONE) and its PNG; used by png2exr --lut
  exr_tools.py png2exr  in.png out.exr [--linear | --lut lut.json] [--exposure S] [--match ref.png]
        sRGB PNG (8/16 bit) -> linear half-float EXR (channels B,G,R, no compression, Unreal-importable).
        --lut       decode through the fitted inverse display transform instead of the plain sRGB curve
                    (the plain curve leaves the tonemapper's toe/shoulder in the data, which the hybrid
                    render would then tonemap a second time)
        --linear    the PNG already holds linear values (skip the sRGB decode)
        --exposure  extra gain in stops (x 2**S) applied after the decode
        --match     scale so the mean luminance equals that of ref.png (sRGB decoded the same way); the
                    chosen gain is printed, so the exposure of a generated plate is anchored to the
                    render it was made from instead of guessed
  exr_tools.py exr2png  in.exr out.png [--layer NAME] [--gray] [--bits 8|16] [--srgb] [--exposure S]
        one layer of an uncompressed (MRQ, compression NONE) EXR to PNG. Data layers (depth, normal)
        are written linear; --srgb encodes a beauty layer for viewing.

Why: an image tool returns display-referred sRGB. Unreal's projection material wants scene-linear
radiance in the same space as the Path Tracer plate EXR, so the PNG is decoded with the exact sRGB
curve (not a gamma-2.2 approximation), gained to the reference exposure and stored as half floats.
"""
import math
import struct
import sys
import zlib

HALF_MAX = 65504.0


# ----------------------------------------------------------------------------- colour
def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def linear_to_srgb(v):
    v = min(max(v, 0.0), 1.0)
    return v * 12.92 if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055


def decode_lut(bits, linear):
    n = (1 << bits) - 1
    return [(i / n) if linear else srgb_to_linear(i / n) for i in range(n + 1)]


# ----------------------------------------------------------------------------- PNG
def read_png(path):
    """Return (w, h, channels, bits, rows) with rows = list of lists of ints (already de-filtered)."""
    with open(path, "rb") as f:
        data = f.read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG: " + path
    pos, idat, hdr = 8, [], None
    while pos < len(data):
        ln, tag = struct.unpack_from(">I4s", data, pos)
        body = data[pos + 8:pos + 8 + ln]
        pos += 12 + ln
        if tag == b"IHDR":
            hdr = struct.unpack(">IIBBBBB", body)
        elif tag == b"IDAT":
            idat.append(body)
        elif tag == b"IEND":
            break
    w, h, bits, ctype, _, _, interlace = hdr
    assert interlace == 0, "interlaced PNG not supported"
    assert bits in (8, 16), "bit depth %d not supported" % bits
    channels = {0: 1, 2: 3, 4: 2, 6: 4}[ctype]
    bpp = channels * bits // 8
    stride = w * bpp
    raw = zlib.decompress(b"".join(idat))
    rows, prev, off = [], bytes(stride), 0
    for _ in range(h):
        ft = raw[off]
        cur = bytearray(raw[off + 1:off + 1 + stride])
        off += 1 + stride
        if ft == 1:
            for i in range(bpp, stride):
                cur[i] = (cur[i] + cur[i - bpp]) & 255
        elif ft == 2:
            cur = bytearray((a + b) & 255 for a, b in zip(cur, prev))
        elif ft == 3:
            for i in range(stride):
                left = cur[i - bpp] if i >= bpp else 0
                cur[i] = (cur[i] + ((left + prev[i]) >> 1)) & 255
        elif ft == 4:
            for i in range(stride):
                a = cur[i - bpp] if i >= bpp else 0
                b = prev[i]
                c = prev[i - bpp] if i >= bpp else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pred = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                cur[i] = (cur[i] + pred) & 255
        prev = bytes(cur)
        if bits == 8:
            rows.append(list(cur))
        else:
            rows.append(list(struct.unpack(">%dH" % (stride // 2), bytes(cur))))
    return w, h, channels, bits, rows


def write_png(path, w, h, rows, channels, bits):
    """rows: list of lists of ints (0..255 or 0..65535), channels 1 or 3."""
    ctype = {1: 0, 3: 2}[channels]
    fmt = ">%dH" % (w * channels)
    raw = bytearray()
    for r in rows:
        raw.append(0)
        raw += bytes(r) if bits == 8 else struct.pack(fmt, *r)

    def chunk(tag, body):
        c = struct.pack(">I", len(body)) + tag + body
        return c + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, bits, ctype, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 6)) + chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


# ----------------------------------------------------------------------------- EXR
def _attr(name, typ, value):
    return name.encode() + b"\0" + typ.encode() + b"\0" + struct.pack("<i", len(value)) + value


def write_exr(path, w, h, planes):
    """planes: dict channel name -> list of h rows, each a bytes object of w packed little-endian halves.
    Single-part scanline file, NO_COMPRESSION, channels sorted as OpenEXR requires."""
    names = sorted(planes)
    chlist = b""
    for n in names:
        chlist += n.encode() + b"\0" + struct.pack("<iB3xii", 1, 0, 1, 1)   # HALF, not pLinear, sampling 1,1
    chlist += b"\0"
    box = struct.pack("<iiii", 0, 0, w - 1, h - 1)
    hdr = struct.pack("<ii", 20000630, 2)
    hdr += _attr("channels", "chlist", chlist)
    hdr += _attr("compression", "compression", b"\0")
    hdr += _attr("dataWindow", "box2i", box)
    hdr += _attr("displayWindow", "box2i", box)
    hdr += _attr("lineOrder", "lineOrder", b"\0")
    hdr += _attr("pixelAspectRatio", "float", struct.pack("<f", 1.0))
    hdr += _attr("screenWindowCenter", "v2f", struct.pack("<ff", 0.0, 0.0))
    hdr += _attr("screenWindowWidth", "float", struct.pack("<f", 1.0))
    hdr += b"\0"
    line_bytes = w * 2 * len(names)
    base = len(hdr) + 8 * h
    offsets = struct.pack("<%dQ" % h, *[base + y * (8 + line_bytes) for y in range(h)])
    with open(path, "wb") as f:
        f.write(hdr)
        f.write(offsets)
        for y in range(h):
            f.write(struct.pack("<ii", y, line_bytes))
            for n in names:
                f.write(planes[n][y])


def read_exr(path, want=None, step=1):
    """Uncompressed scanline EXR -> (w, h, {channel: list of rows (tuples of floats)}, header dict).
    want: optional set of channel names to decode (others skipped). step > 1: decode every step-th
    row and column only (rows in between are None) for statistics on large frames."""
    with open(path, "rb") as f:
        data = f.read()
    magic, version = struct.unpack_from("<ii", data, 0)
    assert magic == 20000630, "not an EXR: " + path
    assert version & 0x1000 == 0 and version & 0x200 == 0, "multipart / deep EXR not supported"
    pos = 8
    header = {}

    def cstr(p):
        e = data.index(b"\0", p)
        return data[p:e].decode("latin-1"), e + 1

    while True:
        if data[pos] == 0:
            pos += 1
            break
        name, pos = cstr(pos)
        typ, pos = cstr(pos)
        size = struct.unpack_from("<i", data, pos)[0]
        pos += 4
        header[name] = (typ, data[pos:pos + size])
        pos += size
    comp = header["compression"][1][0]
    assert comp == 0, "EXR compression %d not supported (render with MRQ EXR compression NONE)" % comp
    x0, y0, x1, y1 = struct.unpack("<iiii", header["dataWindow"][1])
    w, h = x1 - x0 + 1, y1 - y0 + 1
    chans, p, raw = [], 0, header["channels"][1]
    while raw[p] != 0:
        e = raw.index(b"\0", p)
        n = raw[p:e].decode("latin-1")
        ptype = struct.unpack_from("<i", raw, e + 1)[0]
        chans.append((n, ptype))
        p = e + 1 + 16
    header["channel_list"] = chans
    sizes = {0: 4, 1: 2, 2: 4}
    fmts = {0: "<%dI", 1: "<%de", 2: "<%df"}
    offsets = struct.unpack_from("<%dQ" % h, data, pos)
    out = {n: [None] * h for n, t in chans if want is None or n in want}
    for off in offsets:
        y, size = struct.unpack_from("<ii", data, off)
        if (y - y0) % step:
            continue
        q = off + 8
        for n, t in chans:
            nb = w * sizes[t]
            if n in out:
                row = struct.unpack_from(fmts[t] % w, data, q)
                out[n][y - y0] = row if step == 1 else row[::step]
            q += nb
    return w, h, out, header


# ----------------------------------------------------------------------------- commands
def luminance_stats(w, h, rgb_rows):
    """rgb_rows: rows of (r,g,b,...) floats; returns mean r,g,b, mean luminance over a 4x4 subsample."""
    sr = sg = sb = 0.0
    n = 0
    for y in range(0, h, 4):
        row = rgb_rows[y]
        for x in range(0, w * 3, 12):
            sr += row[x]; sg += row[x + 1]; sb += row[x + 2]
            n += 1
    mr, mg, mb = sr / n, sg / n, sb / n
    return mr, mg, mb, 0.2126 * mr + 0.7152 * mg + 0.0722 * mb


def png_linear_rows(path, linear=False):
    w, h, ch, bits, rows = read_png(path)
    lut = decode_lut(bits, linear)
    out = []
    for r in rows:
        if ch == 1 or ch == 2:
            vals = [lut[v] for v in r[::ch]]
            out.append([v for v in vals for _ in range(3)])
        else:
            if ch == 4:
                r = [v for i, v in enumerate(r) if i % 4 != 3]
            out.append([lut[v] for v in r])
    return w, h, out


def cmd_stats(args):
    path = args[0]
    linear = "--linear" in args
    if path.lower().endswith(".exr"):
        w, h, ch, hdr = read_exr(path)
        names = [n for n, _ in hdr["channel_list"]]
        for layer in sorted({n.rsplit(".", 1)[0] if "." in n else "" for n in names}):
            pre = layer + "." if layer else ""
            if pre + "R" in ch and pre + "G" in ch and pre + "B" in ch:
                rows = [[v for trip in zip(ch[pre + "R"][y], ch[pre + "G"][y], ch[pre + "B"][y]) for v in trip] for y in range(h)]
                mr, mg, mb, lum = luminance_stats(w, h, rows)
                print("%s  %dx%d  layer %-40s mean RGB %.5f %.5f %.5f  luminance %.5f" % (path, w, h, layer or "(root)", mr, mg, mb, lum))
        return
    w, h, rows = png_linear_rows(path, linear)
    mr, mg, mb, lum = luminance_stats(w, h, rows)
    print("%s  %dx%d  %s mean linear RGB %.5f %.5f %.5f  luminance %.5f" % (path, w, h, "(linear)" if linear else "(sRGB decoded)", mr, mg, mb, lum))


def cmd_fitlut(args):
    """fitlut pass.exr pass.png lut.json [--step N]
    Empirical inverse of the project's display transform (exposure + ACES filmic tonemapper + sRGB):
    the EXR root R,G,B (scene-linear, exposure applied) and the PNG of the same MRQ FinalImage pass are
    pixel-aligned, so for every 8-bit code the mean linear value of the pixels carrying that code is the
    inverse mapping. Codes never seen are interpolated in log space, codes above the brightest seen are
    extrapolated with the last decade's slope. The fit error is reported (apply LUT to the PNG, compare
    with the EXR)."""
    exr, png, out = args[0], args[1], args[2]
    step = int(args[args.index("--step") + 1]) if "--step" in args else 4
    w, h, ch, hdr = read_exr(exr, {"R", "G", "B"}, step=step)
    pw, ph, pch, pbits, prow = read_png(png)
    assert (pw, ph) == (w, h) and pbits == 8 and pch >= 3, "PNG must be the 8-bit image of the same pass"
    top = 255
    sums = [[0.0] * 256 for _ in range(3)]
    cnts = [[0] * 256 for _ in range(3)]
    for y in range(0, h, step):
        er, eg, eb = ch["R"][y], ch["G"][y], ch["B"][y]
        pr = prow[y]
        for i, x in enumerate(range(0, w, step)):
            px = x * pch
            for c, e in ((0, er), (1, eg), (2, eb)):
                code = pr[px + c]
                sums[c][code] += max(e[i], 0.0)
                cnts[c][code] += 1
    lut = []
    for c in range(3):
        known = [(k, sums[c][k] / cnts[c][k]) for k in range(256) if cnts[c][k] >= 8 and sums[c][k] > 0]
        assert len(known) > 8, "too few samples for channel %d" % c
        table = [0.0] * 256
        ks = [k for k, _ in known]
        for k in range(256):
            if k <= ks[0]:
                table[k] = known[0][1] * (k / ks[0]) if ks[0] else known[0][1]
            elif k >= ks[-1]:
                # extrapolate in log space with the slope over the last ~16 codes
                j = max(0, len(ks) - 1)
                i0 = j
                while i0 > 0 and ks[j] - ks[i0] < 16:
                    i0 -= 1
                slope = (math.log(known[j][1]) - math.log(known[i0][1])) / max(1, ks[j] - ks[i0])
                table[k] = min(HALF_MAX, math.exp(math.log(known[j][1]) + slope * (k - ks[j])))
            else:
                for i in range(len(ks) - 1):
                    if ks[i] <= k <= ks[i + 1]:
                        t = (k - ks[i]) / (ks[i + 1] - ks[i])
                        table[k] = math.exp(math.log(known[i][1]) * (1 - t) + math.log(known[i + 1][1]) * t)
                        break
        # enforce monotonic
        for k in range(1, 256):
            table[k] = max(table[k], table[k - 1])
        lut.append(table)
        print("channel %s: codes seen %d..%d (%d distinct), linear %.6f..%.5f, extrapolated above %d" % ("RGB"[c], ks[0], ks[-1], len(ks), known[0][1], known[-1][1], ks[-1]))
    # fit error
    err = n = 0.0
    for y in range(0, h, step):
        e3 = (ch["R"][y], ch["G"][y], ch["B"][y])
        pr = prow[y]
        for i, x in enumerate(range(0, w, step)):
            for c in range(3):
                ev = e3[c][i]
                if ev > 1e-4:
                    err += abs(lut[c][pr[x * pch + c]] - ev) / ev
                    n += 1
    print("mean relative error of LUT(png) vs exr over %d samples (> 1e-4): %.4f" % (int(n), err / max(n, 1)))
    import json
    with open(out, "w") as f:
        json.dump({"source_exr": exr, "source_png": png, "step": step, "lut": lut}, f)
    print("wrote", out)


def cmd_png2exr(args):
    src, dst = args[0], args[1]
    linear = "--linear" in args
    gain = 1.0
    if "--exposure" in args:
        gain *= 2.0 ** float(args[args.index("--exposure") + 1])
    w, h, ch, bits, rows = read_png(src)
    lut = decode_lut(bits, linear)
    lut3 = None
    if "--lut" in args:   # empirical inverse display transform (cmd_fitlut), 8-bit input only
        import json
        assert bits == 8, "--lut expects an 8-bit PNG"
        with open(args[args.index("--lut") + 1]) as f:
            lut3 = json.load(f)["lut"]
    if "--match" in args:
        ref = args[args.index("--match") + 1]
        rw, rh, rrows = png_linear_rows(ref, linear)
        _, _, _, lref = luminance_stats(rw, rh, rrows)
        _, _, _, lsrc = luminance_stats(w, h, [[lut[v] for i, v in enumerate(r) if ch != 4 or i % 4 != 3] for r in rows] if ch >= 3 else [[lut[v] for v in r[::ch] for _ in range(3)] for r in rows])
        m = lref / max(lsrc, 1e-9)
        print("match: source luminance %.5f, reference %.5f -> gain x%.4f (%+.2f stops)" % (lsrc, lref, m, math.log2(m)))
        gain *= m
    # value -> packed half, one table lookup per sample (per channel when an inverse-display LUT is used)
    halfs = [[struct.pack("<e", min(v * gain, HALF_MAX)) for v in (lut3[c] if lut3 else lut)] for c in range(3)]
    planes = {"R": [], "G": [], "B": []}
    for r in rows:
        if ch >= 3:
            planes["R"].append(b"".join([halfs[0][v] for v in r[0::ch]]))
            planes["G"].append(b"".join([halfs[1][v] for v in r[1::ch]]))
            planes["B"].append(b"".join([halfs[2][v] for v in r[2::ch]]))
        else:
            g = b"".join([halfs[0][v] for v in r[0::ch]])
            planes["R"].append(g); planes["G"].append(g); planes["B"].append(g)
    write_exr(dst, w, h, planes)
    print("wrote %s  %dx%d  half RGB linear, gain x%.4f (%+.2f stops), decode %s" % (dst, w, h, gain, math.log2(gain), "linear" if linear else ("inverse display LUT" if lut3 else "sRGB")))


def cmd_exr2png(args):
    src, dst = args[0], args[1]
    layer = args[args.index("--layer") + 1] if "--layer" in args else ""
    gray = "--gray" in args
    bits = int(args[args.index("--bits") + 1]) if "--bits" in args else 16
    srgb = "--srgb" in args
    gain = 2.0 ** float(args[args.index("--exposure") + 1]) if "--exposure" in args else 1.0
    pre = layer + "." if layer else ""
    want = {pre + "R"} if gray else {pre + "R", pre + "G", pre + "B"}
    w, h, ch, hdr = read_exr(src, want)
    missing = [n for n in want if n not in ch]
    assert not missing, "channels %s not in %s; layers: %s" % (missing, src, sorted({n.rsplit('.', 1)[0] for n, _ in hdr['channel_list']}))
    top = (1 << bits) - 1
    enc = (lambda v: linear_to_srgb(v * gain)) if srgb else (lambda v: min(max(v * gain, 0.0), 1.0))
    rows = []
    for y in range(h):
        if gray:
            rows.append([int(round(enc(v) * top)) for v in ch[pre + "R"][y]])
        else:
            rows.append([int(round(enc(v) * top)) for trip in zip(ch[pre + "R"][y], ch[pre + "G"][y], ch[pre + "B"][y]) for v in trip])
    write_png(dst, w, h, rows, 1 if gray else 3, bits)
    print("wrote %s  %dx%d  %s %d-bit %s from layer %s" % (dst, w, h, "gray" if gray else "RGB", bits, "sRGB" if srgb else "linear", layer or "(root)"))


def cmd_info(args):
    w, h, ch, hdr = read_exr(args[0], want=set())
    print("%s  %dx%d  compression %d" % (args[0], w, h, hdr["compression"][1][0]))
    for n, t in hdr["channel_list"]:
        print("  %-48s %s" % (n, {0: "uint", 1: "half", 2: "float"}[t]))


if __name__ == "__main__":
    cmds = {"info": cmd_info, "stats": cmd_stats, "png2exr": cmd_png2exr, "exr2png": cmd_exr2png, "fitlut": cmd_fitlut}
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        print(__doc__)
        sys.exit(1)
    cmds[sys.argv[1]](sys.argv[2:])
