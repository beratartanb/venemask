"""Gold braid trims for the Casanova Bauta, built on the real STL edges.

Evidence (SourceAssets/casanova_bauta/inspect/photo01_braid_brim.png, photo03_braid_side.png):
  * brim lip  : flat scroll braid ~6.5 mm wide with a raised serpentine cord (period ~5.5 mm)
  * band edge : thinner twisted gimp ~3.5 mm, from the left curl to the right curl under the hat
Both are gold metallic thread. Nothing else is added (no feathers, stones or ornaments).

Curves come from the mesh itself: the brim lip is the rolled edge where up- and down-facing
faces meet; the band edge is the painted hat/face boundary measured in prep_mask.py.
Output: casanova_braid.obj in the same placed frame (cm) as casanova_bauta_segmented.obj.
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import meshlib
import prep_mask as pm

D = pm.D
OUT = os.path.join(D, "casanova_braid.obj")

RIBBON_W, RIBBON_T = 6.5, 0.9      # mm
CORD_R, CORD_AMP, CORD_PERIOD = 0.85, 1.9, 5.5
ROPE_R, ROPE_STRANDS, ROPE_PITCH = 1.7, 3, 4.0


def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def mul(a, s): return (a[0] * s, a[1] * s, a[2] * s)
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def norm(a):
    l = math.sqrt(dot(a, a)) or 1.0
    return (a[0] / l, a[1] / l, a[2] / l)


class NearestNormal:
    """Hash-grid lookup of the nearest STL vertex normal."""

    def __init__(self, verts, normals, cell=4.0):
        self.cell = cell
        self.grid = {}
        self.verts, self.normals = verts, normals
        for i, v in enumerate(verts):
            self.grid.setdefault(self.key(v), []).append(i)

    def key(self, p):
        return (int(math.floor(p[0] / self.cell)), int(math.floor(p[1] / self.cell)), int(math.floor(p[2] / self.cell)))

    def __call__(self, p, radius=4.0, min_z=-2.0):
        """Average normal of the vertices within `radius` (optionally only those facing up)."""
        kx, ky, kz = self.key(p)
        acc = (0.0, 0.0, 0.0)
        r2 = radius * radius
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for i in self.grid.get((kx + dx, ky + dy, kz + dz), ()):
                        d = sub(self.verts[i], p)
                        if dot(d, d) <= r2 and self.normals[i][2] > min_z:
                            acc = add(acc, self.normals[i])
        return norm(acc) if dot(acc, acc) > 0 else (0.0, 0.0, 1.0)


def brim_lip_loop(verts, tris, vlab):
    """Ordered loop of brim-lip points (rolled edge of the brim, all the way round)."""
    up = [False] * len(verts)
    down = [False] * len(verts)
    for t in tris:
        n = meshlib.face_normal(*(verts[i] for i in t))
        for i in t:
            if n[2] > 0.3:
                up[i] = True
            elif n[2] < -0.3:
                down[i] = True
    hat = [verts[i] for i in range(len(verts)) if vlab[i] == pm.HAT]
    cx = sum(v[0] for v in hat) / len(hat)
    cy = sum(v[1] for v in hat) / len(hat)
    lip = [verts[i] for i in range(len(verts))
           if vlab[i] == pm.HAT and up[i] and down[i] and verts[i][2] > pm.band_z(verts[i][0]) + 14]
    bins = {}
    for p in lip:
        a = int(math.degrees(math.atan2(p[1] - cy, p[0] - cx))) % 360
        bins.setdefault(a, []).append(p)
    pts = []
    for a in range(360):
        if a in bins:
            ps = bins[a]
            # outermost point in the bin = the actual lip
            pts.append(max(ps, key=lambda p: (p[0] - cx) ** 2 + (p[1] - cy) ** 2))
    pts = smooth(resample(pts, 1.0, closed=True), 6, closed=True)
    return pts, (cx, cy)


def smooth(pts, half, closed):
    n = len(pts)
    out = []
    for i in range(n):
        if closed:
            win = [pts[(i + k) % n] for k in range(-half, half + 1)]
        else:
            win = pts[max(0, i - half):i + half + 1]
        out.append(tuple(sum(p[j] for p in win) / len(win) for j in range(3)))
    return out


def band_curve(depth):
    pts = []
    x = -63.0
    while x <= 63.0:
        z = pm.band_z(x) + 1.6
        y = depth(x, z)
        if y < 1e29:
            pts.append((x, y - 0.3, z))
        x += 2.0
    return smooth(resample(pts, 0.8, closed=False), 3, closed=False)


def resample(pts, step, closed):
    if closed:
        pts = pts + [pts[0]]
    out = [pts[0]]
    carry = 0.0
    for a, b in zip(pts, pts[1:]):
        seg = math.sqrt(dot(sub(b, a), sub(b, a)))
        if seg == 0:
            continue
        t = step - carry
        while t <= seg:
            out.append(add(a, mul(sub(b, a), t / seg)))
            t += step
        carry = seg - (t - step)
    return out


class OBJ:
    def __init__(self):
        self.v, self.vt, self.f = [], [], {}

    def quad(self, group, a, b, c, d):
        self.f.setdefault(group, []).extend([(a, b, c), (a, c, d)])

    def add_v(self, p, uv):
        self.v.append(p)
        self.vt.append(uv)
        return len(self.v)


def frames(pts, nn, closed, inward=None, min_z=-2.0):
    """(point, tangent, normal, binormal) per sample.

    normal = averaged mesh surface normal (top faces only when min_z is set);
    binormal points toward `inward` (a 2D centre) when given, so insets are consistent."""
    out = []
    n = len(pts)
    for i in range(n):
        if closed:
            T = norm(sub(pts[(i + 1) % n], pts[(i - 1) % n]))
        else:
            T = norm(sub(pts[min(i + 1, n - 1)], pts[max(i - 1, 0)]))
        N = nn(pts[i], min_z=min_z)
        N = norm(sub(N, mul(T, dot(N, T))))
        B = norm(cross(T, N))
        if inward is not None:
            to_c = (inward[0] - pts[i][0], inward[1] - pts[i][1], 0.0)
            if dot(B, to_c) > 0:   # we inset along -B, so B must point outward
                B = mul(B, -1.0)
                N = mul(N, -1.0) if N[2] < 0 else N
        out.append((pts[i], T, N, B))
    return out


def sweep_tube(obj, group, fr, radius_fn, segs, closed):
    rings = []
    s = 0.0
    prev = None
    for i, (p, T, N, B) in enumerate(fr):
        if prev is not None:
            s += math.sqrt(dot(sub(p, prev), sub(p, prev)))
        prev = p
        ring = []
        for k in range(segs):
            th = 2 * math.pi * k / segs
            r = radius_fn(s, th)
            q = add(p, add(mul(N, r * math.cos(th)), mul(B, r * math.sin(th))))
            ring.append(obj.add_v(q, (s / 10.0, k / segs)))
        rings.append(ring)
    n = len(rings)
    for i in range(n if closed else n - 1):
        r0, r1 = rings[i], rings[(i + 1) % n]
        for k in range(segs):
            obj.quad(group, r0[k], r1[k], r1[(k + 1) % segs], r0[(k + 1) % segs])


def sweep_ribbon(obj, group, fr, width, thick, inset, closed):
    """Flat box strip lying on the surface, centred `inset` mm inward (along -B) from the curve."""
    rings = []
    s = 0.0
    prev = None
    corners = [(-width / 2, 0.0), (width / 2, 0.0), (width / 2, thick), (-width / 2, thick)]
    for p, T, N, B in fr:
        if prev is not None:
            s += math.sqrt(dot(sub(p, prev), sub(p, prev)))
        prev = p
        c = add(p, mul(B, -inset))
        ring = [obj.add_v(add(c, add(mul(B, u), mul(N, w))), (s / 10.0, j / 4.0)) for j, (u, w) in enumerate(corners)]
        rings.append(ring)
    n = len(rings)
    for i in range(n if closed else n - 1):
        r0, r1 = rings[i], rings[(i + 1) % n]
        for k in range(4):
            obj.quad(group, r0[k], r1[k], r1[(k + 1) % 4], r0[(k + 1) % 4])


def sweep_wave_cord(obj, group, fr, inset, closed):
    """Serpentine cord on top of the ribbon: path offset across the ribbon by a sine."""
    pts = []
    s = 0.0
    prev = None
    for p, T, N, B in fr:
        if prev is not None:
            s += math.sqrt(dot(sub(p, prev), sub(p, prev)))
        prev = p
        off = CORD_AMP * math.sin(2 * math.pi * s / CORD_PERIOD)
        # cord rides on the band's outer surface: up (N) in the middle, outward (B) at the swings
        pts.append(add(p, add(mul(B, -inset + off), mul(N, RIBBON_W / 2 * 0.9 + CORD_R * 0.5 - abs(off) * 0.35))))
    fr2 = [(q, T, N, B) for q, (p, T, N, B) in zip(pts, fr)]
    sweep_tube(obj, group, fr2, lambda s, th: CORD_R, 8, closed)


def main():
    verts, tris = meshlib.read_stl(pm.SRC)
    vlab = [pm.label(v) for v in verts]
    normals = meshlib.vertex_normals(verts, tris)
    nn = NearestNormal(verts, normals)
    depth = meshlib.front_depth(verts, tris, 1.0)

    lip, centre = brim_lip_loop(verts, tris, vlab)
    band = band_curve(depth)
    print("lip samples", len(lip), "band samples", len(band))

    obj = OBJ()
    fr_lip = frames(lip, nn, closed=True, inward=centre, min_z=0.15)
    # the scroll braid wraps the rolled lip (photo 01: visible from every angle), so it is built as a
    # half-round band straddling the edge, with the serpentine cord on its outer face
    sweep_tube(obj, "M_BraidWave", fr_lip, lambda s, th: RIBBON_W / 2 * (0.55 + 0.45 * abs(math.cos(th))), 12, closed=True)
    sweep_ribbon(obj, "M_BraidWave", fr_lip, RIBBON_W, RIBBON_T, RIBBON_W / 2 - 0.8, closed=True)
    sweep_wave_cord(obj, "M_BraidWave", fr_lip, 0.0, closed=True)
    fr_band = frames(band, nn, closed=False)
    sweep_tube(obj, "M_BraidRope", fr_band,
               lambda s, th: ROPE_R + 0.45 * math.cos(ROPE_STRANDS * th - 2 * math.pi * s / ROPE_PITCH), 10, closed=False)

    with open(os.path.join(D, "casanova_bauta_prep.json")) as f:
        T = json.load(f)["transform"]
    with open(OUT, "w") as f:
        f.write("# gold braid trims, Casanova Bauta (product 7591523549267); placed frame, cm\n")
        for p in obj.v:
            x, y, z = pm.rot_x(p, T["tilt_rad"])
            f.write("v %.5f %.5f %.5f\n" % ((x - T["cx_mm"]) / 10, (y - T["cy_mm"]) / 10, (z - T["zmin_mm"]) / 10))
        for u, v in obj.vt:
            f.write("vt %.5f %.5f\n" % (u, v))
        f.write("o SM_CasanovaBraid\n")
        for g, faces in obj.f.items():
            f.write("usemtl %s\n" % g)
            for a, b, c in faces:
                f.write("f %d/%d %d/%d %d/%d\n" % (a, a, b, b, c, c))
    print("verts", len(obj.v), "tris", sum(len(v) for v in obj.f.values()), "->", OUT)

    # preview: braid over the grey mask (front)
    cols = [(0.75, 0.75, 0.75)] * len(tris)
    allv = list(verts) + obj.v
    alltris = list(tris)
    for g, faces in obj.f.items():
        for a, b, c in faces:
            alltris.append((a - 1 + len(verts), b - 1 + len(verts), c - 1 + len(verts)))
            cols.append((0.95, 0.72, 0.25))
    meshlib.render_ortho(allv, alltris, cols, "front", 2.5, os.path.join(pm.INSPECT, "braid_front.png"), grid_mm=0)
    meshlib.render_ortho(allv, alltris, cols, "side", 2.5, os.path.join(pm.INSPECT, "braid_side.png"), grid_mm=0)


if __name__ == "__main__":
    main()
