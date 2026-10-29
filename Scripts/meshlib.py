"""Pure-Python mesh helpers (UE's bundled Python has no numpy/PIL).

Binary STL reading, vertex welding, orthographic z-buffer previews written as PNG.
"""
import math
import struct
import zlib


def read_stl(path):
    """Return (verts, tris) with vertices welded on exact float equality."""
    with open(path, "rb") as f:
        data = f.read()
    n = struct.unpack_from("<I", data, 80)[0]
    index = {}
    verts = []
    tris = []
    off = 84
    rec = struct.Struct("<12fH")
    for _ in range(n):
        vals = rec.unpack_from(data, off)
        off += 50
        tri = []
        for k in range(3):
            p = (vals[3 + 3 * k], vals[4 + 3 * k], vals[5 + 3 * k])
            i = index.get(p)
            if i is None:
                i = len(verts)
                index[p] = i
                verts.append(p)
            tri.append(i)
        if tri[0] != tri[1] and tri[1] != tri[2] and tri[0] != tri[2]:
            tris.append(tri)
    return verts, tris


def bounds(verts):
    xs, ys, zs = zip(*verts)
    return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


def face_normal(a, b, c):
    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    l = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    return nx / l, ny / l, nz / l


def vertex_normals(verts, tris):
    acc = [[0.0, 0.0, 0.0] for _ in verts]
    for t in tris:
        a, b, c = (verts[i] for i in t)
        ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
        vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
        n = (uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx)  # area weighted
        for i in t:
            acc[i][0] += n[0]
            acc[i][1] += n[1]
            acc[i][2] += n[2]
    out = []
    for n in acc:
        l = math.sqrt(n[0] ** 2 + n[1] ** 2 + n[2] ** 2) or 1.0
        out.append((n[0] / l, n[1] / l, n[2] / l))
    return out


def write_png(path, w, h, rgb):
    """rgb: bytearray of w*h*3."""
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw += rgb[y * w * 3:(y + 1) * w * 3]

    def chunk(tag, body):
        c = struct.pack(">I", len(body)) + tag + body
        return c + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 6)) + chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


def front_depth(verts, tris, px_per_mm):
    """Min Y per pixel seen from -Y (vertex splat, dense mesh). Returns (lookup(x,z)->depth)."""
    (x0, _, z0), (x1, _, z1) = bounds(verts)
    w, h = int((x1 - x0) * px_per_mm) + 1, int((z1 - z0) * px_per_mm) + 1
    buf = [1e30] * (w * h)
    for x, y, z in verts:
        k = int((z1 - z) * px_per_mm) * w + int((x - x0) * px_per_mm)
        if y < buf[k]:
            buf[k] = y

    def lookup(x, z):
        u, v = int((x - x0) * px_per_mm), int((z1 - z) * px_per_mm)
        best = 1e30
        for dv in (-1, 0, 1):
            for du in (-1, 0, 1):
                uu, vv = u + du, v + dv
                if 0 <= uu < w and 0 <= vv < h:
                    best = min(best, buf[vv * w + uu])
        return best

    return lookup


def render_ortho(verts, tris, colors, view, px_per_mm, path, grid_mm=10):
    """Flat-shaded orthographic z-buffer render.

    view: 'front' looks along +Y (viewer at -Y), image x = +X, image up = +Z.
          'side' looks along -X (viewer at +X), image x = -Y (front to the left)... kept simple.
    colors: per-triangle (r,g,b) base colour 0..1.
    """
    (x0, y0, z0), (x1, y1, z1) = bounds(verts)
    if view == "front":
        proj = lambda p: (p[0] - x0, z1 - p[2], p[1])  # u, v, depth (smaller = nearer)
        W, H = x1 - x0, z1 - z0
        light = (0.35, -0.8, 0.5)
    else:
        proj = lambda p: (p[1] - y0, z1 - p[2], -p[0])
        W, H = y1 - y0, z1 - z0
        light = (0.6, -0.5, 0.6)
    ll = math.sqrt(sum(c * c for c in light))
    light = tuple(c / ll for c in light)
    w, h = int(W * px_per_mm) + 1, int(H * px_per_mm) + 1
    zbuf = [1e30] * (w * h)
    img = bytearray([60] * (w * h * 3))
    for ti, t in enumerate(tris):
        a, b, c = (verts[i] for i in t)
        n = face_normal(a, b, c)
        shade = max(0.0, n[0] * light[0] + n[1] * light[1] + n[2] * light[2]) * 0.8 + 0.2
        col = colors[ti]
        pa, pb, pc = proj(a), proj(b), proj(c)
        P = [(q[0] * px_per_mm, q[1] * px_per_mm, q[2]) for q in (pa, pb, pc)]
        minx = max(0, int(min(q[0] for q in P)))
        maxx = min(w - 1, int(max(q[0] for q in P)) + 1)
        miny = max(0, int(min(q[1] for q in P)))
        maxy = min(h - 1, int(max(q[1] for q in P)) + 1)
        (ax, ay, az), (bx, by, bz), (cx, cy, cz) = P
        den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(den) < 1e-12:
            continue
        for yy in range(miny, maxy + 1):
            for xx in range(minx, maxx + 1):
                px, py = xx + 0.5, yy + 0.5
                l1 = ((by - cy) * (px - cx) + (cx - bx) * (py - cy)) / den
                l2 = ((cy - ay) * (px - cx) + (ax - cx) * (py - cy)) / den
                l3 = 1 - l1 - l2
                if l1 < 0 or l2 < 0 or l3 < 0:
                    continue
                d = l1 * az + l2 * bz + l3 * cz
                k = yy * w + xx
                if d < zbuf[k]:
                    zbuf[k] = d
                    img[k * 3] = int(255 * min(1, col[0] * shade))
                    img[k * 3 + 1] = int(255 * min(1, col[1] * shade))
                    img[k * 3 + 2] = int(255 * min(1, col[2] * shade))
    if grid_mm:
        step = grid_mm * px_per_mm
        for gx in range(0, w, max(1, int(step))):
            for yy in range(h):
                k = (yy * w + gx) * 3
                img[k] = min(255, img[k] + 40)
        for gy in range(0, h, max(1, int(step))):
            for xx in range(w):
                k = (gy * w + xx) * 3
                img[k] = min(255, img[k] + 40)
    write_png(path, w, h, img)
    return w, h
