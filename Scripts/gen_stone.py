"""Worn stone blocks as dense OBJ meshes (rounded edges + chipped, weathered displacement).

Units cm, Z up (UE Interchange maps OBJ (x,y,z) to (x,-y,z)).
Each block: size (X depth, Y length, Z height), edge radius, displacement amplitude.
"""
import math
import os
import random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "SourceAssets", "stone")
os.makedirs(OUT, exist_ok=True)


def hash3(ix, iy, iz, seed):
    h = (ix * 374761393 + iy * 668265263 + iz * 2147483647 + seed * 1442695041) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def noise3(x, y, z, seed):
    xi, yi, zi = math.floor(x), math.floor(y), math.floor(z)
    fx, fy, fz = x - xi, y - yi, z - zi
    fx, fy, fz = (f * f * (3 - 2 * f) for f in (fx, fy, fz))
    acc = 0.0
    for dz in (0, 1):
        for dy in (0, 1):
            for dx in (0, 1):
                w = (fx if dx else 1 - fx) * (fy if dy else 1 - fy) * (fz if dz else 1 - fz)
                acc += w * hash3(xi + dx, yi + dy, zi + dz, seed)
    return acc


def fbm3(x, y, z, seed, octaves=5):
    s, amp, tot, f = 0.0, 1.0, 0.0, 1.0
    for o in range(octaves):
        s += amp * noise3(x * f, y * f, z * f, seed + o)
        tot += amp
        amp *= 0.5
        f *= 2.0
    return s / tot


def block(name, size, radius, amp, step, seed):
    sx, sy, sz = size
    hx, hy, hz = sx / 2, sy / 2, sz / 2
    ix, iy, iz = hx - radius, hy - radius, hz - radius
    verts, uvs, faces = [], [], []
    index = {}

    def vid(p):
        key = (round(p[0], 4), round(p[1], 4), round(p[2], 4))
        i = index.get(key)
        if i is None:
            i = len(verts)
            index[key] = i
            # rounded-box projection
            cx = max(-ix, min(ix, p[0]))
            cy = max(-iy, min(iy, p[1]))
            cz = max(-iz, min(iz, p[2]))
            dx, dy, dz = p[0] - cx, p[1] - cy, p[2] - cz
            l = math.sqrt(dx * dx + dy * dy + dz * dz) or 1.0
            nx, ny, nz = dx / l, dy / l, dz / l
            q = (cx + nx * radius, cy + ny * radius, cz + nz * radius)
            # edge-ness: how far we are from a flat face (0 flat, 1 on rounded edge)
            edge = 1.0 - max(abs(nx), abs(ny), abs(nz))
            grain = fbm3(q[0] * 0.08, q[1] * 0.08, q[2] * 0.08, seed) - 0.5
            chips = fbm3(q[0] * 0.35, q[1] * 0.35, q[2] * 0.35, seed + 50)
            chip = max(0.0, chips - 0.55) * 6.0 * (0.25 + 2.5 * edge)
            d = amp * grain - amp * chip
            verts.append((q[0] + nx * d, q[1] + ny * d, q[2] + nz * d))
            # box-projected UV in metres
            if abs(nz) >= max(abs(nx), abs(ny)):
                uvs.append((q[0] / 100, q[1] / 100))
            elif abs(nx) >= abs(ny):
                uvs.append((q[1] / 100, q[2] / 100))
            else:
                uvs.append((q[0] / 100, q[2] / 100))
        return i

    def grid(origin, du, dv, nu, nv):
        rows = []
        for j in range(nv + 1):
            row = []
            for i in range(nu + 1):
                p = tuple(origin[k] + du[k] * i / nu + dv[k] * j / nv for k in range(3))
                row.append(vid(p))
            rows.append(row)
        for j in range(nv):
            for i in range(nu):
                a, b, c, d = rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]
                faces.append((a, b, c))
                faces.append((a, c, d))

    n = lambda L: max(2, int(round(L / step)))
    # six faces, counter-clockwise seen from outside (right-handed, Z up)
    grid((-hx, -hy, hz), (sx, 0, 0), (0, sy, 0), n(sx), n(sy))            # top
    grid((-hx, -hy, -hz), (0, sy, 0), (sx, 0, 0), n(sy), n(sx))           # bottom
    grid((-hx, -hy, -hz), (sx, 0, 0), (0, 0, sz), n(sx), n(sz))           # -Y
    grid((-hx, hy, -hz), (0, 0, sz), (sx, 0, 0), n(sz), n(sx))            # +Y
    grid((-hx, -hy, -hz), (0, 0, sz), (0, sy, 0), n(sz), n(sy))           # -X
    grid((hx, -hy, -hz), (0, sy, 0), (0, 0, sz), n(sy), n(sz))            # +X

    path = os.path.join(OUT, name + ".obj")
    with open(path, "w") as f:
        f.write("# %s size %s cm\n" % (name, size))
        for x, y, z in verts:
            f.write("v %.4f %.4f %.4f\n" % (x, y, z + hz))  # Z up, pivot at bottom centre
        for u, v in uvs:
            f.write("vt %.5f %.5f\n" % (u, v))
        f.write("g %s\nusemtl M_Stone\n" % name)
        for a, b, c in faces:
            f.write("f %d/%d %d/%d %d/%d\n" % (a + 1, a + 1, b + 1, b + 1, c + 1, c + 1))
    print(name, len(verts), "verts", len(faces), "tris")


if __name__ == "__main__":
    # parapet cap the mask sits on: real ashlar blocks (joints are geometry near the camera)
    block("SM_LedgeCap", (52, 104, 16), 1.6, 0.35, 0.8, 3)
    block("SM_LedgeCap2", (52, 118, 16), 1.6, 0.35, 0.8, 4)
    block("SM_LedgeCap3", (52, 96, 16), 1.6, 0.35, 0.8, 5)
    block("SM_ParapetBody", (44, 316, 92), 1.0, 0.6, 2.5, 7)
    block("SM_Riser", (24, 40, 26), 1.8, 0.3, 0.6, 13)
    # loggia pier rising from the parapet (ashlar courses, 36 cm high)
    block("SM_PierCourse", (36, 44, 36), 1.3, 0.4, 1.0, 17)
    block("SM_PierCourse2", (36, 44, 36), 1.3, 0.4, 1.0, 19)
    block("SM_FloorSlab", (120, 120, 8), 0.8, 0.25, 2.0, 21)
    # rusticated facade blocks for the far bank ground floor
    block("SM_Rustic", (40, 120, 55), 3.5, 0.9, 2.5, 23)
