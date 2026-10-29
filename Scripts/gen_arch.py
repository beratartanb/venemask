"""Venetian architecture pieces as OBJ meshes (cm, Z up, pivot at bottom centre).

  SM_ArchRound   semicircular arch (loggia / bridge), profile extruded along Y
  SM_ArchGothic  pointed arch (palazzo windows), thin
  SM_Column      lathe: plinth, torus base, shaft with entasis, capital, abacus
  SM_Cornice     stepped moulding profile extruded along Y
  SM_Paline      mooring pole, tapered, with band sections as separate material groups
  SM_Bridge      wide segmental arch with parapet (one piece)

Same OBJ convention as gen_stone.py (UE Interchange maps (x,y,z) -> (x,-y,z)).
"""
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "SourceAssets", "arch")
os.makedirs(OUT, exist_ok=True)


class Mesh:
    def __init__(self):
        self.v, self.vt, self.groups = [], [], {}

    def add(self, p, uv=(0.0, 0.0)):
        self.v.append(p)
        self.vt.append(uv)
        return len(self.v)

    def tri(self, g, a, b, c):
        self.groups.setdefault(g, []).append((a, b, c))

    def quad(self, g, a, b, c, d):
        self.tri(g, a, b, c)
        self.tri(g, a, c, d)

    def write(self, name):
        path = os.path.join(OUT, name + ".obj")
        with open(path, "w") as f:
            f.write("# %s (gen_arch.py), cm, Z up\n" % name)
            for x, y, z in self.v:
                f.write("v %.4f %.4f %.4f\n" % (x, y, z))
            for u, w in self.vt:
                f.write("vt %.5f %.5f\n" % (u, w))
            f.write("o %s\n" % name)
            for g, faces in self.groups.items():
                f.write("usemtl %s\n" % g)
                for a, b, c in faces:
                    f.write("f %d/%d %d/%d %d/%d\n" % (a, a, b, b, c, c))
        print(name, len(self.v), "verts", sum(len(v) for v in self.groups.values()), "tris")


def extrude_profile_y(m, g, loops, y0, y1):
    """Extrude closed 2D loops (x, z) along Y between y0 and y1; loops[0] outer CCW, others holes CW.

    Caps are built per loop as fans from the loop centroid: fine for convex-ish rings we use
    (arches are built as ring strips instead, see arch()).
    """
    for loop in loops:
        n = len(loop)
        front = [m.add((x, y0, z), (x / 100, z / 100)) for x, z in loop]
        back = [m.add((x, y1, z), (x / 100, z / 100)) for x, z in loop]
        for i in range(n):
            j = (i + 1) % n
            m.quad(g, front[i], back[i], back[j], front[j])


def arch(name, r_in, r_out, depth, pointed=False, segs=36, spring=0.0, group="M_Stone"):
    """Ring strip between inner and outer curves, plus vertical legs down to z=0 when spring>0."""
    m = Mesh()
    y0, y1 = -depth / 2, depth / 2

    def curve(r):
        pts = []
        if pointed:
            # equilateral pointed arch: two arcs of radius 2r centred at the opposite springers
            for k in range(segs + 1):
                t = k / segs
                if t <= 0.5:
                    a = math.radians(180 - 60 * (t / 0.5))  # from left springer up to the apex
                    cx = r
                    pts.append((cx + 2 * r * math.cos(a), spring + 2 * r * math.sin(a)))
                else:
                    a = math.radians(60 - 60 * ((t - 0.5) / 0.5))
                    cx = -r
                    pts.append((cx + 2 * r * math.cos(a), spring + 2 * r * math.sin(a)))
            return pts
        return [(r * math.cos(math.radians(180 - 180 * k / segs)), spring + r * math.sin(math.radians(180 - 180 * k / segs))) for k in range(segs + 1)]

    inner, outer = curve(r_in), curve(r_out)
    # legs
    if spring > 0:
        inner = [(-r_in, 0.0)] + inner + [(r_in, 0.0)]
        outer = [(-r_out, 0.0)] + outer + [(r_out, 0.0)]
    n = len(inner)
    fi = [m.add((x, y0, z), (x / 100, z / 100)) for x, z in inner]
    fo = [m.add((x, y0, z), (x / 100, z / 100)) for x, z in outer]
    bi = [m.add((x, y1, z), (x / 100, z / 100)) for x, z in inner]
    bo = [m.add((x, y1, z), (x / 100, z / 100)) for x, z in outer]
    for i in range(n - 1):
        m.quad(group, fo[i], fi[i], fi[i + 1], fo[i + 1])       # front face
        m.quad(group, bi[i], bo[i], bo[i + 1], bi[i + 1])       # back face
        m.quad(group, fi[i], bi[i], bi[i + 1], fi[i + 1])       # intrados
        m.quad(group, bo[i], fo[i], fo[i + 1], bo[i + 1])       # extrados
    m.quad(group, fi[0], fo[0], bo[0], bi[0])                   # end caps
    m.quad(group, fo[-1], fi[-1], bi[-1], bo[-1])
    m.write(name)


def lathe(name, profile, segs=32, group="M_Stone", square_top=None, square_base=None):
    """profile: list of (radius, z) from bottom to top."""
    m = Mesh()
    rings = []
    for r, z in profile:
        rings.append([m.add((r * math.cos(2 * math.pi * k / segs), r * math.sin(2 * math.pi * k / segs), z), (k / segs, z / 100)) for k in range(segs)])
    for a, b in zip(rings, rings[1:]):
        for k in range(segs):
            m.quad(group, a[k], b[k], b[(k + 1) % segs], a[(k + 1) % segs])
    for box, z0 in ((square_base, 0.0), (square_top, profile[-1][1])):
        if box:
            s, h = box
            pts = [(-s, -s), (s, -s), (s, s), (-s, s)]
            lo = [m.add((x, y, z0), (x / 100, y / 100)) for x, y in pts]
            hi = [m.add((x, y, z0 + h), (x / 100, y / 100)) for x, y in pts]
            for i in range(4):
                j = (i + 1) % 4
                m.quad(group, lo[i], lo[j], hi[j], hi[i])
            m.quad(group, hi[0], hi[1], hi[2], hi[3])
            m.quad(group, lo[3], lo[2], lo[1], lo[0])
    m.write(name)


def column(name, h=300.0, r=18.0):
    prof = [(r * 1.35, 0), (r * 1.35, 6), (r * 1.15, 9), (r * 1.05, 14),      # torus base
            (r, 18), (r * 1.02, h * 0.35), (r * 0.92, h * 0.8), (r * 0.86, h - 30),  # shaft, entasis
            (r * 0.95, h - 26), (r * 1.25, h - 12), (r * 1.4, h - 6)]           # capital flare
    lathe(name, prof, square_base=(r * 1.5, 4.0), square_top=(r * 1.55, 6.0))


def cornice(name, length=400.0, steps=((0, 0), (10, 0), (10, 6), (16, 10), (16, 14), (24, 18), (24, 26), (0, 26))):
    """Stepped moulding: profile (x out, z up) extruded along Y; x=0 is the wall plane."""
    m = Mesh()
    extrude_profile_y(m, "M_Stone", [list(steps)], -length / 2, length / 2)
    # end caps
    for y in (-length / 2, length / 2):
        ids = [m.add((x, y, z), (x / 100, z / 100)) for x, z in steps]
        c = m.add((sum(p[0] for p in steps) / len(steps), y, sum(p[1] for p in steps) / len(steps)))
        for i in range(len(ids)):
            j = (i + 1) % len(ids)
            if y < 0:
                m.tri("M_Stone", c, ids[j], ids[i])
            else:
                m.tri("M_Stone", c, ids[i], ids[j])
    m.write(name)


def paline(name, h=380.0, r=9.0, bands=7):
    """Mooring pole with alternating material bands (painted stripes)."""
    m = Mesh()
    segs = 20
    rings = []
    zs = [h * k / bands for k in range(bands + 1)]
    for z in zs:
        rr = r * (1.0 - 0.25 * z / h)
        rings.append([m.add((rr * math.cos(2 * math.pi * k / segs), rr * math.sin(2 * math.pi * k / segs), z), (k / segs, z / 100)) for k in range(segs)])
    for b, (a, c) in enumerate(zip(rings, rings[1:])):
        g = "M_PoleA" if b % 2 == 0 else "M_PoleB"
        for k in range(segs):
            m.quad(g, a[k], c[k], c[(k + 1) % segs], a[(k + 1) % segs])
    # tapered cap
    top = m.add((0, 0, h + 14), (0.5, (h + 14) / 100))
    for k in range(segs):
        m.tri("M_PoleA", rings[-1][k], rings[-1][(k + 1) % segs], top)
    m.write(name)


def bridge(name, span=900.0, rise=260.0, width=320.0, thick=70.0):
    """Segmental stone bridge: arch ring + solid spandrel/deck + parapets."""
    m = Mesh()
    segs = 40
    R = (span * span / 4 + rise * rise) / (2 * rise)   # circle through the springers and crown
    zc = rise - R
    a0 = math.atan2(0 - zc, -span / 2)
    a1 = math.atan2(0 - zc, span / 2)
    inner = [(R * math.cos(a0 + (a1 - a0) * k / segs), zc + R * math.sin(a0 + (a1 - a0) * k / segs)) for k in range(segs + 1)]
    deck_z = rise + thick
    outer = [(-span / 2 - 60, 0), (-span / 2 - 60, deck_z), (span / 2 + 60, deck_z), (span / 2 + 60, 0)]
    # face polygon: outer rectangle minus arch (built as a strip between inner arc and deck line)
    y0, y1 = -width / 2, width / 2
    for y, sgn in ((y0, 1), (y1, -1)):
        top = [m.add((x, y, deck_z), (x / 100, deck_z / 100)) for x, _ in inner]
        arc = [m.add((x, y, z), (x / 100, z / 100)) for x, z in inner]
        for i in range(segs):
            if sgn > 0:
                m.quad("M_Stone", arc[i], top[i], top[i + 1], arc[i + 1])
            else:
                m.quad("M_Stone", top[i], arc[i], arc[i + 1], top[i + 1])
    # intrados
    fa = [m.add((x, y0, z), (x / 100, z / 100)) for x, z in inner]
    ba = [m.add((x, y1, z), (x / 100, z / 100)) for x, z in inner]
    for i in range(segs):
        m.quad("M_Stone", fa[i], fa[i + 1], ba[i + 1], ba[i])
    # deck + parapets as boxes
    def box(x0, x1, yy0, yy1, z0, z1, g="M_Stone"):
        c = [(x0, yy0, z0), (x1, yy0, z0), (x1, yy1, z0), (x0, yy1, z0), (x0, yy0, z1), (x1, yy0, z1), (x1, yy1, z1), (x0, yy1, z1)]
        ids = [m.add(p, (p[0] / 100, p[2] / 100)) for p in c]
        m.quad(g, ids[4], ids[5], ids[6], ids[7]); m.quad(g, ids[3], ids[2], ids[1], ids[0])
        m.quad(g, ids[0], ids[1], ids[5], ids[4]); m.quad(g, ids[2], ids[3], ids[7], ids[6])
        m.quad(g, ids[1], ids[2], ids[6], ids[5]); m.quad(g, ids[3], ids[0], ids[4], ids[7])
    box(-span / 2 - 60, span / 2 + 60, y0, y1, deck_z, deck_z + 12)
    box(-span / 2 - 60, span / 2 + 60, y0, y0 + 22, deck_z + 12, deck_z + 110)
    box(-span / 2 - 60, span / 2 + 60, y1 - 22, y1, deck_z + 12, deck_z + 110)
    m.write(name)


if __name__ == "__main__":
    arch("SM_ArchRound", 125, 150, 44, spring=0.0)
    arch("SM_ArchGothic", 52, 62, 14, pointed=True, spring=0.0)
    arch("SM_ArchGothicBig", 110, 128, 30, pointed=True, spring=0.0)
    column("SM_Column", h=310, r=18)
    column("SM_ColumnSlim", h=250, r=11)
    cornice("SM_Cornice", length=400)
    paline("SM_Paline")
    bridge("SM_Bridge")
