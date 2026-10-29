"""Procedural, tileable source textures for the hero set (pure Python).

T_Crackle_M   : craquelure crack mask for the white glaze (two Voronoi layers)
T_Crackle_N   : tangent-space normal from the crack mask (grooves)
T_Stone_H     : stone height / grain (fBm + pitting)
T_Stone_N     : normal map from T_Stone_H
T_Stone_W     : wetness mask (low frequency, 1 = wet / glossy)
T_Water_N     : gentle canal ripple normal
"""
import math
import os
import random
import struct
import sys
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "SourceAssets", "textures")
os.makedirs(OUT, exist_ok=True)


def write_png(path, w, h, chans, data):
    raw = bytearray()
    row = w * chans
    for y in range(h):
        raw.append(0)
        raw += data[y * row:(y + 1) * row]

    def chunk(tag, body):
        c = struct.pack(">I", len(body)) + tag + body
        return c + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF)

    ctype = {1: 0, 3: 2}[chans]
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, ctype, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 6)) + chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


# ---------- tileable value noise ----------
def make_noise(period, seed):
    rnd = random.Random(seed)
    lat = [rnd.random() for _ in range(period * period)]

    def n(x, y):
        xi, yi = int(math.floor(x)), int(math.floor(y))
        fx, fy = x - xi, y - yi
        fx = fx * fx * (3 - 2 * fx)
        fy = fy * fy * (3 - 2 * fy)
        x0, x1 = xi % period, (xi + 1) % period
        y0, y1 = yi % period, (yi + 1) % period
        a = lat[y0 * period + x0]
        b = lat[y0 * period + x1]
        c = lat[y1 * period + x0]
        d = lat[y1 * period + x1]
        return (a + (b - a) * fx) + ((c + (d - c) * fx) - (a + (b - a) * fx)) * fy

    return n


def fbm_image(size, base_period, octaves, seed, gain=0.5, warp=0.0, stretch=(1.0, 1.0)):
    layers = [make_noise(base_period * (2 ** o), seed + o) for o in range(octaves)]
    wn = make_noise(base_period, seed + 99)
    img = [0.0] * (size * size)
    for y in range(size):
        for x in range(size):
            u, v = x / size, y / size
            if warp:
                u += warp * (wn(u * base_period, v * base_period) - 0.5) / base_period
                v += warp * (wn(u * base_period + 17.3, v * base_period + 5.1) - 0.5) / base_period
            s, amp, tot = 0.0, 1.0, 0.0
            for o, L in enumerate(layers):
                p = base_period * (2 ** o)
                s += amp * L(u * p * stretch[0], v * p * stretch[1])
                tot += amp
                amp *= gain
            img[y * size + x] = s / tot
    return normalize(img)


def normalize(img):
    lo, hi = min(img), max(img)
    return [(v - lo) / (hi - lo or 1) for v in img]


# ---------- tileable Voronoi crack lines (F2 - F1) ----------
def voronoi_edges(size, cells, seed, width):
    rnd = random.Random(seed)
    g = cells
    pts = [[(rnd.random(), rnd.random()) for _ in range(1)] for _ in range(g * g)]
    img = [0.0] * (size * size)
    for y in range(size):
        for x in range(size):
            u, v = x / size * g, y / size * g
            cx, cy = int(u), int(v)
            d1 = d2 = 1e9
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    gx, gy = cx + dx, cy + dy
                    for px, py in pts[(gy % g) * g + (gx % g)]:
                        d = math.hypot(gx + px - u, gy + py - v)
                        if d < d1:
                            d1, d2 = d, d1
                        elif d < d2:
                            d2 = d
            e = (d2 - d1) * size / g  # distance to edge in px (approx x2)
            img[y * size + x] = max(0.0, 1.0 - e / width)
    return img


def blur(img, size, r):
    out = img[:]
    for _ in range(r):
        tmp = [0.0] * len(out)
        for y in range(size):
            for x in range(size):
                tmp[y * size + x] = (out[y * size + (x - 1) % size] + 2 * out[y * size + x] + out[y * size + (x + 1) % size]) / 4
        out = [0.0] * len(tmp)
        for y in range(size):
            for x in range(size):
                out[y * size + x] = (tmp[((y - 1) % size) * size + x] + 2 * tmp[y * size + x] + tmp[((y + 1) % size) * size + x]) / 4
    return out


def to_gray(img):
    return bytearray(int(max(0, min(1, v)) * 255) for v in img)


def normal_from_height(h, size, strength):
    data = bytearray(size * size * 3)
    for y in range(size):
        for x in range(size):
            dx = h[y * size + (x + 1) % size] - h[y * size + (x - 1) % size]
            dy = h[((y + 1) % size) * size + x] - h[((y - 1) % size) * size + x]
            nx, ny, nz = -dx * strength, -dy * strength, 1.0
            l = math.sqrt(nx * nx + ny * ny + nz * nz)
            k = (y * size + x) * 3
            data[k] = int((nx / l * 0.5 + 0.5) * 255)
            data[k + 1] = int((ny / l * 0.5 + 0.5) * 255)
            data[k + 2] = int((nz / l * 0.5 + 0.5) * 255)
    return data


def main(which):
    S = 1024
    if "crackle" in which:
        big = voronoi_edges(S, 34, 11, 1.6)
        fine = voronoi_edges(S, 90, 23, 1.1)
        m = [min(1.0, a + 0.55 * b) for a, b in zip(big, fine)]
        write_png(os.path.join(OUT, "T_Crackle_M.png"), S, S, 1, to_gray(m))
        h = blur([1 - v for v in m], S, 1)
        write_png(os.path.join(OUT, "T_Crackle_N.png"), S, S, 3, normal_from_height(h, S, 3.0))
        print("crackle done")
    if "stone" in which:
        grain = fbm_image(S, 4, 8, 5, gain=0.5, warp=0.25)
        fine = fbm_image(S, 64, 3, 9, gain=0.6)
        rnd = random.Random(3)
        pores = [1.0] * (S * S)
        for _ in range(1200):  # sparse weathering pores, 1-3 px
            cx, cy, r = rnd.randrange(S), rnd.randrange(S), rnd.choice((1, 1, 1, 2, 2, 3))
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    if dx * dx + dy * dy <= r * r:
                        pores[((cy + dy) % S) * S + (cx + dx) % S] = 0.82
        h = [(0.7 * g + 0.3 * f) * p for g, f, p in zip(grain, fine, pores)]
        write_png(os.path.join(OUT, "T_Stone_H.png"), S, S, 1, to_gray(h))
        write_png(os.path.join(OUT, "T_Stone_N.png"), S, S, 3, normal_from_height(h, S, 6.0))
        wet = fbm_image(S, 2, 4, 77, gain=0.5, warp=2.0)
        write_png(os.path.join(OUT, "T_Stone_W.png"), S, S, 1, to_gray(wet))
        print("stone done")
    if "water" in which:
        h = fbm_image(S, 3, 6, 131, gain=0.5, warp=0.8, stretch=(1.0, 3.0))
        write_png(os.path.join(OUT, "T_Water_N.png"), S, S, 3, normal_from_height(h, S, 2.0))
        print("water done")


if __name__ == "__main__":
    main(sys.argv[1:] or ["crackle", "stone", "water"])
