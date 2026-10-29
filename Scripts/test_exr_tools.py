"""Round-trip test for exr_tools.py: synthetic sRGB PNGs (8 and 16 bit, all PNG filter types)
-> png2exr -> read_exr -> compare with the exact sRGB decode; then exr2png --srgb back and compare.
Run: python Scripts/test_exr_tools.py   (Unreal's python.exe)"""
import os
import struct
import sys
import tempfile
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exr_tools as T   # noqa: E402

W, H = 64, 17
tmp = tempfile.mkdtemp()


def png_with_filters(path, bits, filters):
    """Write a gradient PNG using the given filter type per row (exercises the de-filter code)."""
    top = (1 << bits) - 1
    bpp = 3 * bits // 8
    rows = []
    for y in range(H):
        r = []
        for x in range(W):
            r += [int(x / (W - 1) * top), int(y / (H - 1) * top), int(((x * 7 + y * 13) % 97) / 96 * top)]
        rows.append(r)
    raw = bytearray()
    prev = bytes(W * bpp)
    for y, r in enumerate(rows):
        cur = bytes(r) if bits == 8 else struct.pack(">%dH" % (W * 3), *r)
        ft = filters[y % len(filters)]
        out = bytearray(len(cur))
        for i in range(len(cur)):
            a = cur[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            if ft == 0: pred = 0
            elif ft == 1: pred = a
            elif ft == 2: pred = b
            elif ft == 3: pred = (a + b) >> 1
            else:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pred = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
            out[i] = (cur[i] - pred) & 255
        raw.append(ft)
        raw += out
        prev = cur

    def chunk(tag, body):
        c = struct.pack(">I", len(body)) + tag + body
        return c + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, bits, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw))) + chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return rows


ok = True
for bits in (8, 16):
    src = os.path.join(tmp, "g%d.png" % bits)
    rows = png_with_filters(src, bits, [0, 1, 2, 3, 4])
    w, h, ch, b, got = T.read_png(src)
    assert (w, h, ch, b) == (W, H, 3, bits) and got == rows, "PNG de-filter mismatch at %d bit" % bits
    exr = os.path.join(tmp, "g%d.exr" % bits)
    T.cmd_png2exr([src, exr, "--exposure", "1.0"])
    ew, eh, planes, hdr = T.read_exr(exr)
    assert (ew, eh) == (W, H) and [n for n, _ in hdr["channel_list"]] == ["B", "G", "R"]
    top = (1 << bits) - 1
    worst = 0.0
    for y in range(H):
        for x in range(W):
            for ci, cn in enumerate("RGB"):
                expect = T.srgb_to_linear(rows[y][x * 3 + ci] / top) * 2.0
                worst = max(worst, abs(planes[cn][y][x] - expect) / max(expect, 1e-3))
    print("%2d-bit: max relative error vs exact sRGB decode (half precision): %.5f" % (bits, worst))
    ok &= worst < 2e-3
    back = os.path.join(tmp, "back%d.png" % bits)
    T.cmd_exr2png([exr, back, "--srgb", "--bits", str(bits), "--exposure", "-1.0"])
    _, _, _, _, rows2 = T.read_png(back)
    diff = max(abs(a - b) for r1, r2 in zip(rows, rows2) for a, b in zip(r1, r2))
    print("%2d-bit: round trip PNG -> EXR -> PNG max code difference: %d / %d" % (bits, diff, top))
    ok &= diff <= (1 if bits == 8 else 40)
T.cmd_stats([src])
print("ALL OK" if ok else "FAILED")
