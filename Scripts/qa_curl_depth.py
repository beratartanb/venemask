"""Depth-coloured front view of the left curl column (blue = front, red = back)."""
import os
import sys

sys.path.insert(0, r"C:\Users\berat\Documents\Venemask_Cinematic_Showroom\Scripts")
import meshlib

verts, tris = meshlib.read_stl(r"C:\Users\berat\Documents\Venemask_Cinematic_Showroom\SourceAssets\casanova_bauta\casanova_bauta_3.stl")
keep, cols, used = [], [], set()
for t in tris:
    a, b, c = (verts[i] for i in t)
    cx, cy, cz = (a[0] + b[0] + c[0]) / 3, (a[1] + b[1] + c[1]) / 3, (a[2] + b[2] + c[2]) / 3
    if -95 < cx < -45 and 55 < cz < 175:
        keep.append(t)
        f = max(0.0, min(1.0, (cy + 20) / 70))
        cols.append((f, 0.25, 1 - f))
        used.update(t)
# re-index to the crop so the image is small
idx = {v: i for i, v in enumerate(sorted(used))}
vs = [verts[v] for v in sorted(used)]
ts = [tuple(idx[i] for i in t) for t in keep]
out = r"C:\Users\berat\Documents\Venemask_Cinematic_Showroom\SourceAssets\casanova_bauta\inspect\curl_depth.png"
print(meshlib.render_ortho(vs, ts, cols, "front", 6, out, grid_mm=5))
