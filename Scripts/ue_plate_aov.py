"""Data passes for the K0 plate camera (hand-off to an external image-generation tool).

  1. M_PP_DepthNorm : post-process material, log-normalised scene depth, near = white, far = black.
                      v = 1 - saturate(log2(depth_m / NEAR_M) / log2(FAR_M / NEAR_M))
                      inverse: depth_m = NEAR_M * (FAR_M / NEAR_M) ** (1 - v)
  2. L_Hero_Plate_Seg : copy of L_Hero_Plate (near layer already removed, no mask, no text) with every
                      mesh swapped to a flat unlit colour by category of its original material
                      (segmentation plate), exposure bias 0, bloom/vignette off, same CAM_Plate.

Run:   UnrealEditor-Cmd <uproject> -ExecutePythonScript=Scripts/ue_plate_aov.py
then   ue_make_configs.py (VM_CONFIGS with MRQ_AOV_Plate / MRQ_Seg_Plate) and
       render.ps1 -Config MRQ_AOV_Plate -Map L_Hero_Plate -Sequence LS_Plate -WarmUp
       render.ps1 -Config MRQ_Seg_Plate -Map L_Hero_Plate_Seg -Sequence LS_Plate_Seg -WarmUp
"""
import math
import os
import sys
import unreal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["VM_STAGE"] = "none"          # import the helpers without running a stage
import ue_hybrid as H                    # noqa: E402

G = H.G
mel, at, eas, actors, les = H.mel, H.at, H.eas, H.actors, H.les
NEAR_M, FAR_M = 4.0, 800.0               # plate level: nearest geometry are the mid proxies (~16 m), sky dome far

# segmentation colours (linear emissive, rendered unlit at exposure bias 0)
CATEGORIES = [   # (material-name prefixes, category, colour)
    (("M_Canal",), "water", (0.0, 0.25, 1.0)),
    (("M_NightSky",), "sky", (0.45, 0.0, 0.9)),
    (("M_Moon",), "moon", (1.0, 1.0, 0.1)),
    (("M_WindowGlow", "MI_WindowGlow", "MI_Window", "MI_Lantern"), "lit_window_lamp", (1.0, 0.45, 0.0)),
    (("M_Stone_Istrian", "MI_Stone"), "stone", (0.6, 0.6, 0.6)),
    (("M_Facade_Plaster", "MI_Facade", "MI_Plaster"), "plaster_facade", (1.0, 0.0, 0.0)),
    (("M_Wood", "MI_Wood", "M_PoleA", "M_PoleB", "MI_Pole"), "wood_pole", (0.5, 0.22, 0.0)),
    (("M_Interior",), "interior", (0.0, 0.55, 0.0)),
    (("M_CB_", "M_Braid"), "product", (1.0, 1.0, 1.0)),
]
OTHER = ("other", (0.0, 1.0, 1.0))


def build_depth_material():
    name = "M_PP_DepthNorm"
    path = G + "/Materials/" + name
    if eas.does_asset_exist(path):
        eas.delete_asset(path)
    m = at.create_asset(name, G + "/Materials", unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property("material_domain", unreal.MaterialDomain.MD_POST_PROCESS)
    y = [0]

    def e(cls, **props):
        y[0] += 110
        x = mel.create_material_expression(m, cls, -700, y[0])
        for k, v in props.items():
            x.set_editor_property(k, v)
        return x

    def op(cls, a, b, ao="", bo=""):
        x = e(cls)
        mel.connect_material_expressions(a, ao, x, "A")
        mel.connect_material_expressions(b, bo, x, "B")
        return x

    def un(cls, a, ao=""):
        x = e(cls)
        mel.connect_material_expressions(a, ao, x, "")
        return x

    def const(v): return e(unreal.MaterialExpressionConstant, r=v)

    st = e(unreal.MaterialExpressionSceneTexture, scene_texture_id=unreal.SceneTextureId.PPI_SCENE_DEPTH)
    depth = e(unreal.MaterialExpressionComponentMask, r=True, g=False, b=False, a=False)
    mel.connect_material_expressions(st, "Color", depth, "")
    ratio = op(unreal.MaterialExpressionDivide, depth, const(100.0 * NEAR_M))          # depth / NEAR in metres
    t = op(unreal.MaterialExpressionDivide, un(unreal.MaterialExpressionLogarithm2, ratio), const(math.log2(FAR_M / NEAR_M)))
    v = un(unreal.MaterialExpressionOneMinus, un(unreal.MaterialExpressionSaturate, t))
    mel.connect_material_property(v, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.layout_material_expressions(m)
    mel.recompile_material(m)
    eas.save_loaded_asset(m)
    H.log("depth material", path, "near_m", NEAR_M, "far_m", FAR_M)


def category_of(mat):
    n = mat.get_name() if mat else ""
    for prefixes, cat, col in CATEGORIES:
        if n.startswith(prefixes):
            return cat, col
    return OTHER


def build_seg_level():
    H.duplicate_level(G + "/Maps/L_Hero_Plate", G + "/Maps/L_Hero_Plate_Seg")
    flats = {}
    counts = {}
    unmapped = set()
    for a in actors.get_all_level_actors():
        cls = a.get_class().get_name()
        if cls in ("ExponentialHeightFog", "SkyAtmosphere", "VolumetricCloud", "SkyLight"):
            actors.destroy_actor(a)
            continue
        if isinstance(a, unreal.PostProcessVolume):
            s = a.get_editor_property("settings")
            s.override_auto_exposure_bias = True
            s.auto_exposure_bias = 0.0
            s.override_bloom_intensity = True
            s.bloom_intensity = 0.0
            s.override_vignette_intensity = True
            s.vignette_intensity = 0.0
            a.set_editor_property("settings", s)
            continue
        if not hasattr(a, "static_mesh_component"):
            continue
        c = a.static_mesh_component
        for i in range(c.get_num_materials()):
            cat, col = category_of(c.get_material(i))
            if cat == "other":
                unmapped.add(c.get_material(i).get_name() if c.get_material(i) else "None")
            if cat not in flats:
                flats[cat] = H.flat_material("M_Seg_" + cat, col)
            c.set_material(i, flats[cat])
            counts[cat] = counts.get(cat, 0) + 1
    cam = H.find_actor("CAM_Plate")
    assert cam, "CAM_Plate missing in L_Hero_Plate_Seg"
    H.make_sequence("LS_Plate_Seg", cam)
    les.save_current_level()
    H.log("segmentation level built; material slots per category:", sorted(counts.items()))
    if unmapped:
        H.log("unmapped materials (cyan 'other'):", sorted(unmapped))
    for prefixes, cat, col in CATEGORIES:
        H.log("colour", cat, col)
    H.log("colour", *OTHER)


build_depth_material()
build_seg_level()
with open(os.path.join(H.ROOT, "reports", "ue_plate_aov.txt"), "w") as f:
    f.write("\n".join(H.REPORT))
