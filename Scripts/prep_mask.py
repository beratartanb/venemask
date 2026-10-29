"""Casanova Bauta: STL -> segmented OBJ (Hat / Face / Gold / Trim) for Unreal.

Geometry is untouched (no smoothing, decimation or reshaping). Only material regions are
assigned, by hand-measured boundaries read off the 10 mm grid previews and checked against
the finished-product photos (01/03_*.jpg):
  * Hat   - black lacquer tricorn incl. the band above the brows
  * Trim  - 3.5 mm strip along the band's lower edge, where the real gold braid sits
            (braid itself is NOT in the STL: painted approximation, flagged UNVERIFIED)
  * Gold  - sideburn curls
  * Face  - white crackle-glaze face (and unseen interior)
Rest pose: the tilt about X is solved so the chin tip and the rear rim both touch the plinth.
Output in centimetres, Z up (UE Interchange maps OBJ (x,y,z) to (x,-y,z)).
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import meshlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "SourceAssets", "casanova_bauta")
SRC = os.path.join(D, "casanova_bauta_3.stl")
OUT_OBJ = os.path.join(D, "casanova_bauta_segmented.obj")
INSPECT = os.path.join(D, "inspect")

X0, Z1, PPM = -150.47215270996094, 249.35162353515625, 2.5


def img_to_xz(u, v):
    return u / PPM + X0, Z1 - v / PPM


# Lower edge of the black hat band, measured in front_grid.png pixels (u, v).
BAND_EDGE_PX = [(0, 212), (150, 212), (185, 224), (240, 236), (300, 244), (376, 250),
                (450, 244), (510, 236), (565, 224), (600, 212), (753, 212)]
BAND_EDGE = [img_to_xz(u, v) for u, v in BAND_EDGE_PX]


def band_z(x):
    for (xa, za), (xb, zb) in zip(BAND_EDGE, BAND_EDGE[1:]):
        if xa <= x <= xb:
            t = (x - xa) / (xb - xa)
            return za + t * (zb - za)
    return BAND_EDGE[-1][1]


CURL_Z = (img_to_xz(0, 452)[1], img_to_xz(0, 214)[1])
# Curls sit 25-40 mm behind the face strip next to them (inspect/curl_depth.png, from
# Scripts/qa_curl_depth.py), so depth separates gold curls from white face cleanly.
CURL_MIN_Y = 19.5

# Brim lip seen from the front (left half, front_grid.png px); mirrored about the centre u=376.
_LIP_L = [(8, 58), (60, 60), (110, 72), (160, 95), (210, 125), (260, 160), (300, 190), (340, 222), (376, 240)]
LIP = [img_to_xz(u, v) for u, v in _LIP_L] + [img_to_xz(752 - u, v) for u, v in reversed(_LIP_L[:-1])]


def dist_to_lip(x, z):
    best = 1e30
    for (ax, az), (bx, bz) in zip(LIP, LIP[1:]):
        dx, dz = bx - ax, bz - az
        t = max(0.0, min(1.0, ((x - ax) * dx + (z - az) * dz) / (dx * dx + dz * dz)))
        best = min(best, math.hypot(x - ax - t * dx, z - az - t * dz))
    return best


LEAN_DEG = -12.0  # negative = top leans back (+Y)
REFINE_PASSES = 3  # boundary tessellation passes (each halves the paint-edge step)

HAT, TRIM, GOLD, FACE = 0, 1, 2, 3
NAMES = ["M_Hat", "M_Trim", "M_Gold", "M_Face"]
PREVIEW = [(0.12, 0.12, 0.14), (0.95, 0.75, 0.3), (0.85, 0.62, 0.2), (0.95, 0.95, 0.92)]


def label(p):
    x, y, z = p
    bz = band_z(x)
    if z >= bz + 3.5:
        return HAT
    if z >= bz:
        return TRIM
    if CURL_Z[0] <= z <= CURL_Z[1] and abs(x) > 62 and y > CURL_MIN_Y:
        return GOLD
    return FACE


def brim_rim(verts, tris, vlab, rings=3):
    """Hat vertices on the brim's rolled lip: their 1-ring holds both up- and down-facing faces.

    This is where the real gold braid runs along the brim. Dilated a few rings to braid width.
    """
    up = [False] * len(verts)
    down = [False] * len(verts)
    adj = [[] for _ in verts]
    for t in tris:
        n = meshlib.face_normal(*(verts[i] for i in t))
        for i in t:
            if n[2] > 0.25:
                up[i] = True
            elif n[2] < -0.25:
                down[i] = True
        a, b, c = t
        adj[a] += (b, c)
        adj[b] += (a, c)
        adj[c] += (a, b)
    depth = meshlib.front_depth(verts, tris, 1.0)
    rim = set(i for i, v in enumerate(verts)
              if vlab[i] == HAT and up[i] and down[i] and dist_to_lip(v[0], v[2]) < 6.0
              and v[1] < depth(v[0], v[2]) + 2.0)
    for _ in range(rings):
        rim |= set(j for i in rim for j in adj[i] if vlab[j] == HAT)
    return rim


def fit_lip(verts, rim, bin_mm=3.0):
    """Polyline (x, z) through the detected brim-lip vertices: median z per x bin, front side only."""
    bins = {}
    for i in rim:
        x, y, z = verts[i]
        if y < 10:
            bins.setdefault(int(math.floor(x / bin_mm)), []).append(z)
    pts = []
    for k in sorted(bins):
        zs = sorted(bins[k])
        pts.append(((k + 0.5) * bin_mm, zs[len(zs) // 2]))
    # light smoothing
    sm = []
    for i in range(len(pts)):
        win = pts[max(0, i - 2):i + 3]
        sm.append((pts[i][0], sum(p[1] for p in win) / len(win)))
    return sm


def dist_to_polyline(x, z, poly):
    best = 1e30
    for (ax, az), (bx, bz) in zip(poly, poly[1:]):
        dx, dz = bx - ax, bz - az
        L = dx * dx + dz * dz
        if L == 0:
            continue
        t = max(0.0, min(1.0, ((x - ax) * dx + (z - az) * dz) / L))
        best = min(best, math.hypot(x - ax - t * dx, z - az - t * dz))
    return best


def make_labeler(lip, depth, braid_half_mm=3.5):
    def lab(p):
        l = label(p)
        if l == HAT and p[1] < depth(p[0], p[2]) + 2.0 and dist_to_polyline(p[0], p[2], lip) < braid_half_mm:
            return TRIM
        return l
    return lab


def refine_boundaries(verts, tris, labeler, iterations):
    """Split triangles that straddle paint boundaries (edge midpoints, no T-junctions).

    Midpoints lie on the original flat triangles, so the surface shape is unchanged; only the
    tessellation along colour boundaries gets finer, which removes the jagged paint edges.
    """
    verts = list(verts)
    vlab = [labeler(v) for v in verts]
    for it in range(iterations):
        split = set()
        for a, b, c in tris:
            if not (vlab[a] == vlab[b] == vlab[c]):
                split.update(((min(a, b), max(a, b)), (min(b, c), max(b, c)), (min(c, a), max(c, a))))
        mids = {}

        def mid(a, b):
            k = (min(a, b), max(a, b))
            i = mids.get(k)
            if i is None:
                pa, pb = verts[a], verts[b]
                p = ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2, (pa[2] + pb[2]) / 2)
                i = len(verts)
                verts.append(p)
                vlab.append(labeler(p))
                mids[k] = i
            return i

        out = []
        for t in tris:
            a, b, c = t
            f = [(min(a, b), max(a, b)) in split, (min(b, c), max(b, c)) in split, (min(c, a), max(c, a)) in split]
            n = sum(f)
            if n == 0:
                out.append(t)
                continue
            # rotate so the pattern is canonical
            for _ in range(3):
                if (n == 1 and f[0]) or (n == 2 and not f[2]) or n == 3:
                    break
                a, b, c = b, c, a
                f = f[1:] + f[:1]
            if n == 1:
                m = mid(a, b)
                out += [(a, m, c), (m, b, c)]
            elif n == 2:
                m0, m1 = mid(a, b), mid(b, c)
                out += [(m0, b, m1), (a, m0, m1), (a, m1, c)]
            else:
                m0, m1, m2 = mid(a, b), mid(b, c), mid(c, a)
                out += [(a, m0, m2), (m0, b, m1), (m2, m1, c), (m0, m1, m2)]
        tris = out
        print("refine pass", it + 1, "split edges", len(split), "tris", len(tris))
    return verts, tris, vlab


def rot_x(p, a):
    c, s = math.cos(a), math.sin(a)
    x, y, z = p
    return x, y * c - z * s, y * s + z * c


def solve_rest_tilt(verts):
    """Tilt so the chin tip (front, y<0) and the rear rim (y>20) rest at the same height."""
    front = [v for v in verts if v[1] < -20 and v[2] < 60]
    back = [v for v in verts if v[1] > 20 and v[2] < 120]
    lo, hi = math.radians(-70), math.radians(70)

    def diff(a):
        return min(rot_x(v, a)[2] for v in front) - min(rot_x(v, a)[2] for v in back)

    print("tilt diff at bounds", diff(lo), diff(hi))
    for _ in range(50):
        mid = (lo + hi) / 2
        if diff(lo) * diff(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def volume_centroid(verts, tris):
    vol = cx = cy = cz = 0.0
    for t in tris:
        a, b, c = (verts[i] for i in t)
        v = (a[0] * (b[1] * c[2] - b[2] * c[1]) - a[1] * (b[0] * c[2] - b[2] * c[0])
             + a[2] * (b[0] * c[1] - b[1] * c[0])) / 6.0
        vol += v
        cx += v * (a[0] + b[0] + c[0]) / 4
        cy += v * (a[1] + b[1] + c[1]) / 4
        cz += v * (a[2] + b[2] + c[2]) / 4
    return cx / vol, cy / vol, cz / vol


def main():
    verts, tris = meshlib.read_stl(SRC)
    vlab0 = [label(v) for v in verts]
    lip = fit_lip(verts, brim_rim(verts, tris, vlab0, rings=0))
    depth = meshlib.front_depth(verts, tris, 1.0)
    verts, tris, vlab = refine_boundaries(verts, tris, make_labeler(lip, depth), REFINE_PASSES)
    flab = []
    for t in tris:
        ls = [vlab[i] for i in t]
        flab.append(max(set(ls), key=ls.count))
    counts = {NAMES[k]: flab.count(k) for k in range(4)}
    print("face labels", counts)

    os.makedirs(INSPECT, exist_ok=True)
    cols = [PREVIEW[l] for l in flab]
    meshlib.render_ortho(verts, tris, cols, "front", 2.5, os.path.join(INSPECT, "seg_front.png"), grid_mm=0)
    meshlib.render_ortho(verts, tris, cols, "side", 2.5, os.path.join(INSPECT, "seg_side.png"), grid_mm=0)

    # Free-standing on the chin is unstable (centre of mass falls behind the base: see
    # solve_rest_tilt / contacts printout), so the mask leans back against a stone riser.
    free_tilt = solve_rest_tilt(verts)
    print("free-standing tilt would be", math.degrees(free_tilt))
    tilt = math.radians(LEAN_DEG)
    rv = [rot_x(v, tilt) for v in verts]
    zmin = min(v[2] for v in rv)
    contacts = [v for v in rv if v[2] < zmin + 1.0]
    com = rot_x(volume_centroid(verts, tris), tilt)
    cys = [v[1] for v in contacts]
    cxs = [v[0] for v in contacts]
    print("contacts", len(contacts), "x range", min(cxs), max(cxs), "y range", min(cys), max(cys))
    print("centre of mass (rotated)", com)
    # centre in X/Y, put the lowest point on z=0, mm -> cm
    xs = [v[0] for v in rv]
    ys = [v[1] for v in rv]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    fv = [((v[0] - cx) / 10, (v[1] - cy) / 10, (v[2] - zmin) / 10) for v in rv]
    # front-projection UVs (crackle texture), 1 UV = 30 cm
    uvs = [(v[0] / 30 + 0.5, v[2] / 30) for v in fv]

    with open(OUT_OBJ, "w") as f:
        f.write("# Casanova Bauta Mask - Venemask product 7591523549267\n")
        f.write("# source casanova bauta_3.stl, geometry unmodified, units cm\n")
        for x, y, z in fv:
            # UE Interchange reads OBJ as Z-up and only negates Y. Mask front (-Y here) -> +Y in UE.
            f.write("v %.5f %.5f %.5f\n" % (x, y, z))
        for u, v in uvs:
            f.write("vt %.5f %.5f\n" % (u, v))
        # one object, four material sections (Interchange splits OBJ 'g' groups into separate meshes)
        f.write("o SM_CasanovaBauta\n")
        for m in range(4):
            f.write("usemtl %s\n" % NAMES[m])
            for t, l in zip(tris, flab):
                if l == m:
                    a, b, c = (i + 1 for i in t)
                    f.write("f %d/%d %d/%d %d/%d\n" % (a, a, b, b, c, c))

    bmin, bmax = meshlib.bounds(fv)
    rear = max(fv, key=lambda v: v[1])
    info = {
        "lean_deg": LEAN_DEG,
        "rear_contact_cm": rear,
        "floor_contact_cm": [list(v) for v in fv if v[2] < 0.1][:5],
        "product_id": 7591523549267,
        "handle": "casanova-mask-bauta-mask-venetian-mask",
        "title": "Casanova Bauta Mask - Eyes Wide Shut Inspired",
        "source_stl": SRC,
        "rest_tilt_deg": math.degrees(tilt),
        "bounds_cm": [bmin, bmax],
        "face_labels": counts,
        "verts": len(verts),
        "tris": len(tris),
    }
    with open(os.path.join(D, "casanova_bauta_prep.json"), "w") as f:
        json.dump(info, f, indent=2)
    print(json.dumps(info, indent=2))


if __name__ == "__main__":
    main()
