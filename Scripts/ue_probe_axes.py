"""Print the imported mask's per-axis extreme vertices (source mesh description) to map OBJ->UE axes."""
import os
import unreal

ROOT = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
mesh = unreal.load_asset("/Game/Venemask/Products/CasanovaBauta/SM_CasanovaBauta")
b = mesh.get_bounds()
out = ["bounds origin %s extent %s" % (b.origin, b.box_extent)]
desc = mesh.get_static_mesh_description(0)
n = desc.get_vertex_count()
out.append("vertex count %d" % n)
ext = {}
for i in range(n):
    p = desc.get_vertex_position(unreal.VertexID(i))
    for ax in ("x", "y", "z"):
        v = getattr(p, ax)
        lo = ext.get(ax + "-")
        hi = ext.get(ax + "+")
        if lo is None or v < getattr(lo, ax):
            ext[ax + "-"] = p
        if hi is None or v > getattr(hi, ax):
            ext[ax + "+"] = p
for k, p in sorted(ext.items()):
    out.append("%s (%.3f, %.3f, %.3f)" % (k, p.x, p.y, p.z))
ns = mesh.get_editor_property("nanite_settings")
out.append("nanite %s" % ns.enabled)
with open(os.path.join(ROOT, "reports", "ue_probe_axes.txt"), "w") as f:
    f.write("\n".join(out))
