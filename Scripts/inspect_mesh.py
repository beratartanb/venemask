"""Load the Casanova STL, print stats and write grey front/side previews with a 10 mm grid."""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import meshlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "SourceAssets", "casanova_bauta", "casanova_bauta_3.stl")
OUT = os.path.join(ROOT, "SourceAssets", "casanova_bauta", "inspect")
os.makedirs(OUT, exist_ok=True)

t = time.time()
verts, tris = meshlib.read_stl(SRC)
print("verts", len(verts), "tris", len(tris), "load s", round(time.time() - t, 1))
print("bounds", meshlib.bounds(verts))
grey = [(0.8, 0.8, 0.8)] * len(tris)
print("front", meshlib.render_ortho(verts, tris, grey, "front", 2.5, os.path.join(OUT, "front_grid.png")))
print("side", meshlib.render_ortho(verts, tris, grey, "side", 2.5, os.path.join(OUT, "side_grid.png")))
print("total s", round(time.time() - t, 1))
