"""Build L_Hero v6: one real Venemask product (Casanova Bauta) on a canal-side loggia parapet, Venice at night.

Run headless:  UnrealEditor-Cmd <uproject> -ExecutePythonScript=Scripts/ue_build_hero.py
Everything is (re)created idempotently under /Game/Venemask.

World (cm), camera looks roughly +X across the canal, slightly toward +Y.
  * Parapet along Y at X~6, cap top Z=CAP_TOP; the mask sits on it at the origin, leaning on a loggia pier.
  * Loggia columns + round arches on the parapet line, receding to -Y (frame left) and +Y (behind the pier).
  * Canal from X=30 to the far bank at X=FAR; palazzi with rusticated arcades, plaster floors, gothic windows.
  * Side canal + bridge at Y~+1500 on the far bank; dome + campanile ~200 m away; moon low left.
Env overrides: VM_EV, VM_FOCAL, VM_FSTOP, VM_KEY, VM_RIM, VM_LEDGE, VM_MASK_YAW, VM_SHIFT, VM_CAM_H, VM_AIM_H, VM_MOON
"""
import json
import math
import os
import random
import unreal

ROOT = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
SRC = os.path.join(ROOT, "SourceAssets")
G = "/Game/Venemask"
MAP = G + "/Maps/L_Hero"
REPORT = []

mel = unreal.MaterialEditingLibrary
at = unreal.AssetToolsHelpers.get_asset_tools()
eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
sms = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)

with open(os.path.join(SRC, "casanova_bauta", "casanova_bauta_prep.json")) as f:
    PREP = json.load(f)

E = os.environ.get
CAP_TOP = 104.0
WATER_Z = -140.0
FAR = 11000.0                      # far bank distance: the Giudecca-like wide water, buildings read above the parapet
SIDE_Y0, SIDE_Y1 = 1250.0, 1750.0  # side canal gap in the far bank (the bridge spans it)
MASK_YAW = float(E("VM_MASK_YAW", "55"))
MASK_FIX_YAW = 90.0                # the OBJ front imports as +Y; 90 turns it to face -X
MOON_POS = (39300.0, 3400.0, 6100.0)


def log(*a):
    s = " ".join(str(x) for x in a)
    REPORT.append(s)
    unreal.log("[VENEMASK] " + s)


# ---------------------------------------------------------------- import
def import_file(path, dest, name):
    t = unreal.AssetImportTask()
    t.filename = path
    t.destination_path = dest
    t.destination_name = name
    t.automated = True
    t.replace_existing = True
    t.save = True
    at.import_asset_tasks([t])
    return unreal.load_asset(dest + "/" + name)


def import_mesh(path, dest, name):
    """Nanite OFF: the Path Tracer traces Nanite's fallback mesh, which faceted the mask."""
    m = import_file(path, dest, name)
    ns = m.get_editor_property("nanite_settings")
    if ns.enabled:
        ns.enabled = False
        try:
            sms.set_nanite_settings(m, ns, apply_changes=True)
        except Exception:
            m.set_editor_property("nanite_settings", ns)
    eas.save_loaded_asset(m)
    log(name, "verts lod0", sms.get_number_verts(m, 0))
    return m


def import_tex(fname, kind):
    tex = import_file(os.path.join(SRC, "textures", fname), G + "/Textures", os.path.splitext(fname)[0])
    tex.set_editor_property("srgb", False)
    tex.set_editor_property("compression_settings",
                            unreal.TextureCompressionSettings.TC_NORMALMAP if kind == "normal" else unreal.TextureCompressionSettings.TC_GRAYSCALE)
    eas.save_loaded_asset(tex)
    return tex


# ---------------------------------------------------------------- material graph helpers
P = unreal.MaterialProperty
CLEAR = unreal.MaterialShadingModel.MSM_CLEAR_COAT


class MB:
    """Tiny material builder over MaterialEditingLibrary."""

    def __init__(self, name, shading=None, two_sided=False, unlit=False, domain=None):
        path = G + "/Materials/" + name
        if eas.does_asset_exist(path):
            eas.delete_asset(path)
        self.m = at.create_asset(name, G + "/Materials", unreal.Material, unreal.MaterialFactoryNew())
        if unlit:
            self.m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
        elif shading:
            self.m.set_editor_property("shading_model", shading)
        if domain:
            self.m.set_editor_property("material_domain", domain)
        self.m.set_editor_property("two_sided", two_sided)
        self.y = 0

    def e(self, cls, **props):
        self.y += 120
        x = mel.create_material_expression(self.m, cls, -600, self.y)
        for k, v in props.items():
            x.set_editor_property(k, v)
        return x

    def c(self, v): return self.e(unreal.MaterialExpressionConstant, r=v)
    def c3(self, r, g, b): return self.e(unreal.MaterialExpressionConstant3Vector, constant=unreal.LinearColor(r, g, b, 1))
    def sp(self, name, v): return self.e(unreal.MaterialExpressionScalarParameter, parameter_name=name, default_value=v)
    def vp(self, name, r, g, b): return self.e(unreal.MaterialExpressionVectorParameter, parameter_name=name, default_value=unreal.LinearColor(r, g, b, 1))

    def tex(self, t, uv=None, kind="gray"):
        st = {"normal": unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL, "gray": unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE}[kind]
        x = self.e(unreal.MaterialExpressionTextureSample, texture=t, sampler_type=st)
        if uv is not None:
            self.link(uv, "", x, "UVs")
        return x

    def uv(self, tiling): return self.e(unreal.MaterialExpressionTextureCoordinate, u_tiling=tiling, v_tiling=tiling)
    def link(self, a, aout, b, bin_): mel.connect_material_expressions(a, aout, b, bin_)

    def op(self, cls, a, b, aout="", bout=""):
        x = self.e(cls)
        self.link(a, aout, x, "A")
        self.link(b, bout, x, "B")
        return x

    def mul(self, a, b, aout="", bout=""): return self.op(unreal.MaterialExpressionMultiply, a, b, aout, bout)
    def add(self, a, b, aout="", bout=""): return self.op(unreal.MaterialExpressionAdd, a, b, aout, bout)
    def sub(self, a, b, aout="", bout=""): return self.op(unreal.MaterialExpressionSubtract, a, b, aout, bout)
    def div(self, a, b, aout="", bout=""): return self.op(unreal.MaterialExpressionDivide, a, b, aout, bout)
    def mn(self, a, b, aout="", bout=""): return self.op(unreal.MaterialExpressionMin, a, b, aout, bout)

    def un(self, cls, a, aout=""):
        x = self.e(cls)
        self.link(a, aout, x, "")
        return x

    def sat(self, a, aout=""): return self.un(unreal.MaterialExpressionSaturate, a, aout)
    def frac(self, a, aout=""): return self.un(unreal.MaterialExpressionFrac, a, aout)
    def floor(self, a, aout=""): return self.un(unreal.MaterialExpressionFloor, a, aout)
    def oneminus(self, a, aout=""): return self.un(unreal.MaterialExpressionOneMinus, a, aout)

    def mask(self, a, r=False, g=False, b=False, aout=""):
        x = self.e(unreal.MaterialExpressionComponentMask, r=r, g=g, b=b, a=False)
        self.link(a, aout, x, "")
        return x

    def lerp(self, a, b, alpha, aout="", bout="", alphaout=""):
        x = self.e(unreal.MaterialExpressionLinearInterpolate)
        self.link(a, aout, x, "A")
        self.link(b, bout, x, "B")
        self.link(alpha, alphaout, x, "Alpha")
        return x

    def world_z(self):
        return self.mask(self.e(unreal.MaterialExpressionWorldPosition), b=True)

    def zgrad(self, z0, z1):
        """saturate((worldZ - z0) / (z1 - z0))"""
        return self.sat(self.div(self.sub(self.world_z(), self.c(z0)), self.c(z1 - z0)))

    def ashlar(self, uv, bw, bh, jw):
        """Joint mask for staggered blocks: UV in metres, block bw x bh m, joint half-width jw m."""
        u = self.div(self.mask(uv, r=True), self.c(bw))
        v = self.div(self.mask(uv, g=True), self.c(bh))
        row = self.floor(v)
        fu = self.frac(self.add(u, self.mul(row, self.c(0.5))))
        fv = self.frac(v)
        du = self.mul(self.mn(fu, self.oneminus(fu)), self.c(bw))
        dv = self.mul(self.mn(fv, self.oneminus(fv)), self.c(bh))
        d = self.mn(du, dv)
        return self.sat(self.oneminus(self.div(d, self.c(jw))))

    def out(self, x, prop, xout=""): mel.connect_material_property(x, xout, prop)

    def attrs(self, **inputs):
        self.m.set_editor_property("use_material_attributes", True)
        ma = self.e(unreal.MaterialExpressionMakeMaterialAttributes)
        for name, src in inputs.items():
            x, xout = src if isinstance(src, tuple) else (src, "")
            self.link(x, xout, ma, name)
        mel.connect_material_property(ma, "", P.MP_MATERIAL_ATTRIBUTES)

    def done(self):
        mel.layout_material_expressions(self.m)
        mel.recompile_material(self.m)
        eas.save_loaded_asset(self.m)
        return self.m


def mic(name, parent, scalars=None, vectors=None):
    path = G + "/Materials/" + name
    if eas.does_asset_exist(path):
        eas.delete_asset(path)
    mi = at.create_asset(name, G + "/Materials", unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mi.set_editor_property("parent", parent)
    for k, v in (scalars or {}).items():
        mel.set_material_instance_scalar_parameter_value(mi, k, v)
    for k, v in (vectors or {}).items():
        mel.set_material_instance_vector_parameter_value(mi, k, unreal.LinearColor(*v))
    eas.save_loaded_asset(mi)
    return mi


def flat_normal(b, n_expr, strength):
    return b.lerp(b.c3(0, 0, 1), n_expr, b.c(strength), bout="RGB")


def build_materials(T):
    M = {}
    # ---- product: white crackle glaze (photo01_crackle_cheek: 1-3 mm cells, warm grey-brown cracks, gloss glaze, faint stains)
    b = MB("M_CB_Face", shading=CLEAR)
    uv = b.uv(2.6)
    crack = b.tex(T["crk"], uv)
    stain = b.tex(T["stw"], b.uv(0.7))
    ivory = b.lerp(b.c3(0.84, 0.80, 0.72), b.c3(0.70, 0.62, 0.50), b.mul(stain, b.c(0.35), "R"))
    col = b.lerp(ivory, b.c3(0.36, 0.29, 0.21), b.mul(crack, b.c(0.75), "R"))
    b.attrs(BaseColor=col,
            Roughness=b.lerp(b.c(0.30), b.c(0.7), crack, alphaout="R"),
            Normal=flat_normal(b, b.tex(T["crkn"], uv, "normal"), 1.0),
            ClearCoat=b.c(0.95), ClearCoatRoughness=b.lerp(b.c(0.07), b.c(0.18), stain, alphaout="R"))
    M["face"] = b.done()

    # ---- product: black lacquer tricorn (photo: high gloss, faint brush texture)
    b = MB("M_CB_Hat", shading=CLEAR)
    h = b.tex(T["sth"], b.uv(12.0))
    b.attrs(BaseColor=b.c3(0.012, 0.011, 0.012),
            Roughness=b.lerp(b.c(0.25), b.c(0.45), h, alphaout="R"),
            Normal=flat_normal(b, b.tex(T["stn"], b.uv(12.0), "normal"), 0.12),
            ClearCoat=b.c(1.0), ClearCoatRoughness=b.lerp(b.c(0.03), b.c(0.10), h, alphaout="R"))
    M["hat"] = b.done()

    # ---- product: gold leaf curls (photo03_curls: matte leaf, umber base showing in creases)
    b = MB("M_CB_Gold")
    h = b.tex(T["sth"], b.uv(6.0))
    leaf = b.tex(T["crk"], b.uv(5.0))
    col = b.lerp(b.c3(0.86, 0.64, 0.28), b.c3(1.0, 0.82, 0.45), h, alphaout="R")
    col = b.lerp(col, b.c3(0.30, 0.17, 0.06), b.mul(leaf, b.c(0.6), "R"))
    b.out(col, P.MP_BASE_COLOR)
    b.out(b.c(0.8), P.MP_METALLIC)
    b.out(b.lerp(b.c(0.5), b.c(0.7), h, alphaout="R"), P.MP_ROUGHNESS)
    b.out(flat_normal(b, b.tex(T["crkn"], b.uv(5.0), "normal"), 0.6), P.MP_NORMAL)
    M["gold"] = b.done()

    # ---- product: gold thread braids (photo01_braid_brim / photo03_braid_side)
    for name, tiling in (("M_BraidWave", 40.0), ("M_BraidRope", 60.0)):
        b = MB(name)
        h = b.tex(T["sth"], b.uv(tiling))
        b.out(b.lerp(b.c3(0.70, 0.50, 0.20), b.c3(0.98, 0.78, 0.40), h, alphaout="R"), P.MP_BASE_COLOR)
        b.out(b.c(0.85), P.MP_METALLIC)
        b.out(b.lerp(b.c(0.45), b.c(0.62), h, alphaout="R"), P.MP_ROUGHNESS)
        b.out(flat_normal(b, b.tex(T["stn"], b.uv(tiling), "normal"), 0.9), P.MP_NORMAL)
        M[name] = b.done()

    # ---- Istrian limestone, wet, with ashlar joints (UVs are metres from gen_* meshes)
    b = MB("M_Stone_Istrian")
    uv = b.uv(1.0)
    uvt = b.uv(1.6)
    h = b.tex(T["sth"], uvt)
    pores = b.tex(T["crk"], b.uv(3.0))
    joint = b.ashlar(uv, 0.95, 0.42, 0.012)
    grime = b.oneminus(b.zgrad(WATER_Z + 10, WATER_Z + 190))        # dark near the water line
    damp = b.oneminus(b.zgrad(WATER_Z + 60, CAP_TOP + 40))           # wetter lower down
    wetmask = b.sat(b.mul(b.add(b.tex(T["stw"], b.uv(0.5)), b.c(-0.35), "R"), b.c(3.0)))
    up = b.mask(b.e(unreal.MaterialExpressionVertexNormalWS), b=True)
    topmask = b.sat(b.add(b.mul(up, b.c(2.0)), b.c(-0.9)))
    wet = b.sat(b.mul(b.add(b.mul(wetmask, topmask), b.mul(damp, b.c(0.55))), b.sp("WetMul", 1.0)))
    light = b.lerp(b.c3(0.26, 0.245, 0.21), b.c3(0.46, 0.43, 0.37), h, alphaout="R")
    light = b.lerp(light, b.c3(0.14, 0.13, 0.115), b.mul(pores, b.c(0.5), "R"))
    light = b.mul(light, b.sp("Brightness", 1.0))
    light = b.lerp(light, b.c3(0.06, 0.07, 0.05), b.mul(grime, b.c(0.85)))
    light = b.lerp(light, b.c3(0.08, 0.075, 0.07), joint)
    col = b.lerp(light, b.mul(light, b.c(0.45)), wet)
    rough = b.lerp(b.lerp(b.c(0.78), b.c(0.6), h, alphaout="R"), b.c(0.95), joint)
    rough = b.lerp(rough, b.c(0.10), wet)
    n = flat_normal(b, b.tex(T["stn"], uvt, "normal"), 0.5)
    b.out(col, P.MP_BASE_COLOR)
    b.out(rough, P.MP_ROUGHNESS)
    b.out(b.lerp(n, b.c3(0, 0, 1), b.mul(wet, b.c(0.8))), P.MP_NORMAL)
    M["stone"] = b.done()
    M["stone_dark"] = mic("MI_Stone_Dark", M["stone"], scalars={"Brightness": 0.45, "WetMul": 0.5})
    M["stone_cap"] = mic("MI_Stone_Cap", M["stone"], scalars={"Brightness": 0.9, "WetMul": 1.7})

    # ---- Venetian plaster facades (tint parameter), peeled to brick, grimy and damp at the bottom
    b = MB("M_Facade_Plaster")
    uv = b.uv(1.0)
    h = b.tex(T["sth"], b.uv(0.8))
    peel = b.sat(b.mul(b.add(b.tex(T["stw"], b.uv(0.35)), b.c(-0.55), "R"), b.c(4.0)))
    brick_j = b.ashlar(uv, 0.26, 0.07, 0.008)
    tint = b.vp("Tint", 0.42, 0.26, 0.16)
    plaster = b.lerp(b.mul(tint, b.c(0.7)), tint, h, alphaout="R")
    brick = b.lerp(b.c3(0.30, 0.13, 0.08), b.c3(0.10, 0.08, 0.07), brick_j)
    col = b.lerp(plaster, brick, peel)
    grime = b.oneminus(b.zgrad(WATER_Z + 20, WATER_Z + 320))
    col = b.lerp(col, b.c3(0.05, 0.06, 0.045), b.mul(grime, b.c(0.8)))
    b.out(col, P.MP_BASE_COLOR)
    b.out(b.lerp(b.lerp(b.c(0.85), b.c(0.7), h, alphaout="R"), b.c(0.35), b.mul(grime, b.c(0.6))), P.MP_ROUGHNESS)
    b.out(flat_normal(b, b.tex(T["stn"], b.uv(0.8), "normal"), 0.35), P.MP_NORMAL)
    M["plaster"] = b.done()
    M["plaster_ochre"] = mic("MI_Plaster_Ochre", M["plaster"], vectors={"Tint": (0.48, 0.30, 0.15, 1)})
    M["plaster_rose"] = mic("MI_Plaster_Rose", M["plaster"], vectors={"Tint": (0.40, 0.20, 0.16, 1)})
    M["plaster_cream"] = mic("MI_Plaster_Cream", M["plaster"], vectors={"Tint": (0.46, 0.40, 0.30, 1)})
    M["plaster_grey"] = mic("MI_Plaster_Grey", M["plaster"], vectors={"Tint": (0.26, 0.25, 0.23, 1)})

    # ---- canal: dark, near-still, two ripple scales
    b = MB("M_Canal")
    n1 = b.tex(T["wtn"], b.uv(24.0), "normal")
    n2 = b.tex(T["wtn"], b.uv(90.0), "normal")
    n = b.lerp(n1, n2, b.c(0.35), "RGB", "RGB")
    b.out(b.c3(0.004, 0.006, 0.008), P.MP_BASE_COLOR)
    b.out(b.c(0.03), P.MP_ROUGHNESS)
    b.out(b.c(0.28), P.MP_SPECULAR)
    b.out(flat_normal(b, n, 0.22), P.MP_NORMAL)
    M["water"] = b.done()

    # ---- weathered wood for mooring poles
    b = MB("M_Wood")
    h = b.tex(T["sth"], b.uv(3.0))
    tint = b.vp("Tint", 0.09, 0.065, 0.045)
    b.out(b.lerp(b.mul(tint, b.c(0.5)), tint, h, alphaout="R"), P.MP_BASE_COLOR)
    b.out(b.c(0.75), P.MP_ROUGHNESS)
    b.out(flat_normal(b, b.tex(T["stn"], b.uv(3.0), "normal"), 0.5), P.MP_NORMAL)
    M["wood"] = b.done()
    M["wood_b"] = mic("MI_Wood_Pale", M["wood"], vectors={"Tint": (0.16, 0.12, 0.08, 1)})

    # ---- lit windows: warm emissive pane, "curtain" falloff, intensity parameter
    b = MB("M_WindowGlow", unlit=True)
    p = b.sp("Intensity", 6.0)
    curtain = b.tex(T["stw"], b.uv(1.5))
    k = b.lerp(b.c3(1.0, 0.45, 0.16), b.c3(1.0, 0.70, 0.38), curtain, alphaout="R")
    b.out(b.mul(k, p), P.MP_EMISSIVE_COLOR)
    M["window"] = b.done()
    M["window_dim"] = mic("MI_Window_Dim", M["window"], scalars={"Intensity": 1.6})
    M["window_mid"] = mic("MI_Window_Mid", M["window"], scalars={"Intensity": 4.0})
    M["window_bright"] = mic("MI_Window_Bright", M["window"], scalars={"Intensity": 9.0})
    M["lantern_glass"] = mic("MI_Lantern", M["window"], scalars={"Intensity": 40.0})

    # ---- night sky: horizon glow -> deep blue zenith; moon disc
    b = MB("M_NightSky", unlit=True, two_sided=True)
    z = b.mask(b.e(unreal.MaterialExpressionVertexNormalWS), b=True)
    t = b.sat(b.mul(z, b.c(2.2)))
    b.out(b.lerp(b.c3(0.17, 0.21, 0.33), b.c3(0.014, 0.020, 0.042), t), P.MP_EMISSIVE_COLOR)
    M["sky"] = b.done()
    b = MB("M_Moon", unlit=True)
    b.out(b.mul(b.c3(1.0, 0.96, 0.88), b.c(60.0)), P.MP_EMISSIVE_COLOR)
    M["moon"] = b.done()

    # ---- dark reveal inside windows / arcade depth
    b = MB("M_Interior")
    b.out(b.c3(0.02, 0.015, 0.012), P.MP_BASE_COLOR)
    b.out(b.c(0.9), P.MP_ROUGHNESS)
    M["interior"] = b.done()

    # ---- QA post-process passes
    b = MB("M_PP_WorldNormal", domain=unreal.MaterialDomain.MD_POST_PROCESS)
    st = b.e(unreal.MaterialExpressionSceneTexture, scene_texture_id=unreal.SceneTextureId.PPI_WORLD_NORMAL)
    b.out(b.add(b.mul(st, b.c(0.5), "Color"), b.c(0.5)), P.MP_EMISSIVE_COLOR)
    M["pp_normal"] = b.done()
    b = MB("M_PP_ProductMatte", domain=unreal.MaterialDomain.MD_POST_PROCESS)
    st = b.e(unreal.MaterialExpressionSceneTexture, scene_texture_id=unreal.SceneTextureId.PPI_CUSTOM_STENCIL)
    b.out(b.sat(b.mul(st, b.c(10.0), "Color")), P.MP_EMISSIVE_COLOR)
    M["pp_matte"] = b.done()
    return M


# ---------------------------------------------------------------- level helpers
CUBE = "/Engine/BasicShapes/Cube.Cube"
SPHERE = "/Engine/BasicShapes/Sphere.Sphere"
CYL = "/Engine/BasicShapes/Cylinder.Cylinder"
PLANE = "/Engine/BasicShapes/Plane.Plane"


def spawn_mesh(mesh, loc, rot=None, scale=None, mat=None, label=None, mats=None):
    if isinstance(mesh, str):
        mesh = unreal.load_asset(mesh)
    a = actors.spawn_actor_from_object(mesh, unreal.Vector(*loc), rot or unreal.Rotator(0, 0, 0))
    if scale:
        a.set_actor_scale3d(unreal.Vector(*scale))
    c = a.static_mesh_component
    if mat:
        for i in range(c.get_num_materials()):
            c.set_material(i, mat)
    if mats:
        for i, m in enumerate(mats):
            c.set_material(i, m)
    if label:
        a.set_actor_label(label)
    return a


def spawn(cls, loc, rot=None, label=None):
    a = actors.spawn_actor_from_class(cls, unreal.Vector(*loc), rot or unreal.Rotator(0, 0, 0))
    if label:
        a.set_actor_label(label)
    return a


def look_at(src, dst):
    return unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*src), unreal.Vector(*dst))


def box(loc, size, mat, label, rot=None):
    """CUBE is 100 cm; size in cm; pivot at the box centre."""
    return spawn_mesh(CUBE, loc, rot, scale=(size[0] / 100, size[1] / 100, size[2] / 100), mat=mat, label=label)


def rect_light(loc, target, kelvin, cd, w, h, label, barn=60.0):
    a = spawn(unreal.RectLight, loc, look_at(loc, target), label)
    c = a.get_component_by_class(unreal.RectLightComponent)
    c.set_editor_property("intensity_units", unreal.LightUnits.CANDELAS)
    c.set_intensity(cd)
    c.set_editor_property("use_temperature", True)
    c.set_editor_property("temperature", kelvin)
    c.set_editor_property("source_width", w)
    c.set_editor_property("source_height", h)
    c.set_editor_property("barn_door_angle", barn)
    c.set_editor_property("barn_door_length", 35.0)
    return a


def spot_light(loc, target, kelvin, cd, inner, outer, label, radius=6.0, att=None):
    a = spawn(unreal.SpotLight, loc, look_at(loc, target), label)
    c = a.get_component_by_class(unreal.SpotLightComponent)
    c.set_editor_property("attenuation_radius", att or 2.5 * unreal.MathLibrary.vector_distance(unreal.Vector(*loc), unreal.Vector(*target)))
    c.set_editor_property("intensity_units", unreal.LightUnits.CANDELAS)
    c.set_intensity(cd)
    c.set_editor_property("use_temperature", True)
    c.set_editor_property("temperature", kelvin)
    c.set_editor_property("source_radius", radius)
    c.set_editor_property("inner_cone_angle", inner)
    c.set_editor_property("outer_cone_angle", outer)
    return a


def point_light(loc, kelvin, cd, radius, label, att=3000.0):
    a = spawn(unreal.PointLight, loc, None, label)
    c = a.get_component_by_class(unreal.PointLightComponent)
    c.set_editor_property("intensity_units", unreal.LightUnits.CANDELAS)
    c.set_intensity(cd)
    c.set_editor_property("use_temperature", True)
    c.set_editor_property("temperature", kelvin)
    c.set_editor_property("source_radius", radius)
    c.set_editor_property("attenuation_radius", att)
    return a


# ---------------------------------------------------------------- set pieces
def loggia(M, S, back):
    """Columns and round arches along the parapet; the pier behind the mask is part of it."""
    yaw = unreal.Rotator(0, 0, 0)
    # pier behind the mask: 6 ashlar courses, face plane touching the mask's rearmost point
    d = PREP["rear_contact_cm"][1] + 18.0
    px, py = back[0] * d, back[1] * d
    pier_yaw = math.degrees(math.atan2(back[1], back[0]))
    for i in range(6):
        spawn_mesh(S["pier" if i % 2 == 0 else "pier2"], (px, py, CAP_TOP + i * 36), unreal.Rotator(0, 0, pier_yaw + (3.0 if i % 2 else 0.0)), mat=M["stone_dark"], label="PierCourse_%d" % i)
    spawn_mesh(S["cornice"], (px - 18, py, CAP_TOP + 216), unreal.Rotator(0, 0, pier_yaw), scale=(1, 0.2, 1), mat=M["stone_dark"], label="PierCap")
    # columns on the parapet, receding to frame-left (-Y) and one behind (+Y), arches between them
    xs = 8.0
    spawn_mesh(S["column"], (xs, -96.0, CAP_TOP), yaw, mat=M["stone_dark"], label="Column_Near")
    for i, y in enumerate((-230.0, -520.0, -810.0, 240.0)):
        spawn_mesh(S["column"], (xs, y, CAP_TOP), yaw, mat=M["stone"], label="Column_%d" % i)
    for i, y in enumerate((-375.0, -665.0)):
        spawn_mesh(S["arch"], (xs, y, CAP_TOP + 310), unreal.Rotator(0, 0, 90), scale=(1.16, 1, 1.0), mat=M["stone"], label="Arch_%d" % i)
    # arch from the pier to the column behind it
    spawn_mesh(S["arch"], (xs + 4, 120.0, CAP_TOP + 310), unreal.Rotator(0, 0, 90), scale=(0.96, 1, 1.0), mat=M["stone"], label="Arch_Pier")
    # entablature over the arches and a dark loggia ceiling/wall behind (reads as the building)
    box((xs - 60, -300, CAP_TOP + 470), (160, 1400, 30), M["stone"], "Entablature")
    box((xs - 200, -300, CAP_TOP + 250), (12, 1400, 500), M["plaster_grey"], "LoggiaBackWall")
    box((xs - 110, -300, CAP_TOP + 486), (220, 1400, 4), M["interior"], "LoggiaCeiling")


def parapet(M, S):
    """Ashlar cap blocks (geometric joints) on a parapet body, terrace slabs behind."""
    y = 60.0
    for i, key in enumerate(("cap", "cap2", "cap3", "cap", "cap2", "cap3", "cap")):
        L = {"cap": 104, "cap2": 118, "cap3": 96}[key]
        spawn_mesh(S[key], (6, y - L / 2, CAP_TOP - 16), unreal.Rotator(0, 0, random.uniform(-0.3, 0.3)), mat=M["stone_cap"], label="Cap_%d" % i)
        y -= L + 0.6
    spawn_mesh(S["body"], (6, -40, CAP_TOP - 108), mat=M["stone"], label="ParapetBody_A")
    spawn_mesh(S["body"], (6, -362, CAP_TOP - 108), mat=M["stone"], label="ParapetBody_B")
    spawn_mesh(S["body"], (6, 276, CAP_TOP - 108), mat=M["stone"], label="ParapetBody_C")
    for i in range(-6, 4):
        for j in range(-3, 0):
            spawn_mesh(S["slab"], (j * 121 - 30, i * 121, -8), mat=M["stone"], label="Floor")
    # embankment wall down to the water, mossy at the water line (material grime)
    box((34, 300, WATER_Z + 60), (14, 2600, 120 + (CAP_TOP - 108 - WATER_Z)), M["stone"], "Embankment")


def far_bank(M, S, rnd):
    """Palazzi facing the canal: rusticated arcade ground floor, plaster upper floors, gothic windows, cornices."""
    y = -3000.0
    tints = [M["plaster_ochre"], M["plaster_rose"], M["plaster_cream"], M["plaster_grey"]]
    while y < 11000:
        w = rnd.uniform(1400, 2600)
        floors = rnd.choice((2, 2, 3))
        fh = rnd.uniform(380, 440)
        if y < SIDE_Y1 and y + w > SIDE_Y0:          # leave the side canal open
            y = SIDE_Y1 + 20
            continue
        x = FAR + rnd.uniform(-120, 160)
        gf = 420.0                                           # ground floor height
        H = gf + floors * fh
        mat = rnd.choice(tints)
        box((x + 300, y + w / 2, WATER_Z + H / 2), (600, w, H), mat, "Palazzo")
        # rusticated ground floor skin
        box((x - 6, y + w / 2, WATER_Z + gf / 2), (12, w, gf), M["stone"], "Rustic")
        # water gate / arcade: round arches with columns, dark interior behind
        n_arch = max(1, int(w / 420))
        for k in range(n_arch):
            ay = y + w * (k + 0.5) / n_arch
            if rnd.random() < 0.7:
                spawn_mesh(S["arch"], (x - 14, ay, WATER_Z + 150), unreal.Rotator(0, 0, 90), scale=(1.0, 1, 0.9), mat=M["stone"], label="Arcade")
                box((x + 40, ay, WATER_Z + 140), (90, 240, 280), M["interior"], "ArcadeDepth")
                if rnd.random() < 0.45:
                    point_light((x - 30, ay, WATER_Z + 230), 2300, 90.0, 10.0, "ArcadeLamp", att=1400.0)
        # string courses / cornices between floors and at the roofline
        for fl in range(floors + 1):
            z = WATER_Z + gf + fl * fh
            spawn_mesh(S["cornice"], (x - 2, y + w / 2, z - 26), unreal.Rotator(0, 0, 0), scale=(1, w / 400, 1), mat=M["stone"], label="Cornice")
        # gothic windows per floor, lit at random
        n_win = max(2, int(w / 330))
        for fl in range(floors):
            zb = WATER_Z + gf + fl * fh + 70
            for k in range(n_win):
                wy = y + w * (k + 0.5) / n_win
                lit = rnd.random()
                pane = M["window_bright"] if lit < 0.12 else M["window_mid"] if lit < 0.32 else M["window_dim"] if lit < 0.5 else M["interior"]
                box((x - 4, wy, zb + 110), (14, 100, 220), M["interior"], "Reveal")
                box((x + 2, wy, zb + 105), (4, 86, 200), pane, "Pane")
                spawn_mesh(S["gothic"], (x - 14, wy, zb + 150), unreal.Rotator(0, 0, 90), mat=M["stone"], label="WinArch")
                box((x - 12, wy, zb + 150), (10, 8, 150), M["stone"], "Mullion")
                box((x - 14, wy, zb - 4), (22, 128, 10), M["stone"], "Sill")
                if lit < 0.32:
                    point_light((x - 40, wy, zb + 120), 2400, 60.0 if lit < 0.12 else 25.0, 20.0, "WinLamp", att=1200.0)
        y += w + rnd.uniform(0, 30)
    # side canal + bridge at Y ~ 1500: gap in the row is implied by the bridge in front of it
    spawn_mesh(S["bridge"], (FAR + 420, (SIDE_Y0 + SIDE_Y1) / 2, WATER_Z), unreal.Rotator(0, 0, 90), scale=(0.72, 1, 0.9), mat=M["stone"], label="Bridge")
    side_canal(M, S, rnd)
    for i, by in enumerate((SIDE_Y0 - 120, SIDE_Y1 + 120)):
        point_light((FAR + 420, by, WATER_Z + 480), 2200, 300.0, 12.0, "BridgeLantern_%d" % i, att=3000.0)
        spawn_mesh(SPHERE, (FAR + 420, by, WATER_Z + 480), scale=(0.3, 0.3, 0.42), mat=M["lantern_glass"], label="BridgeLanternGlass")
    for i, (bx, by) in enumerate(((FAR - 250, 900), (FAR - 240, 1300), (FAR - 260, 1850), (FAR - 230, 2900), (FAR - 250, 4200))):
        spawn_mesh(S["paline"], (bx, by, WATER_Z - 40), unreal.Rotator(0, 0, rnd.uniform(0, 360)), mats=[M["wood"], M["wood_b"]], label="PalineFar_%d" % i)
    # lanterns along the far quay
    for i, ly in enumerate(range(-2200, 10000, 900)):
        point_light((FAR - 80, ly, WATER_Z + 330), 2200, 260.0, 12.0, "QuayLantern_%d" % i, att=3000.0)
        spawn_mesh(SPHERE, (FAR - 80, ly, WATER_Z + 330), scale=(0.3, 0.3, 0.42), mat=M["lantern_glass"], label="LanternGlass")
        box((FAR - 80, ly, WATER_Z + 150), (10, 10, 340), M["wood"], "LanternPost")


def side_canal(M, S, rnd):
    """Buildings along both banks of the side canal, receding to +X; the bridge crosses at its mouth."""
    tints = [M["plaster_ochre"], M["plaster_rose"], M["plaster_cream"], M["plaster_grey"]]
    for side, y_face in ((-1, SIDE_Y0), (1, SIDE_Y1)):
        x = FAR + 700.0
        while x < FAR + 6500:
            w = rnd.uniform(900, 1800)
            H = rnd.uniform(1000, 1500)
            mat = rnd.choice(tints)
            cy = y_face - side * 300
            box((x + w / 2, cy, WATER_Z + H / 2), (w, 600, H), mat, "SideCanalHouse")
            for k in range(int(w / 350)):
                wx = x + w * (k + 0.5) / max(1, int(w / 350))
                for fl in range(2):
                    zb = WATER_Z + 300 + fl * 380
                    lit = rnd.random()
                    pane = M["window_mid"] if lit < 0.25 else M["window_dim"] if lit < 0.45 else M["interior"]
                    box((wx, y_face - side * 2, zb + 100), (80, 6, 180), pane, "SidePane")
                    box((wx, y_face - side * 6, zb + 100), (96, 10, 200), M["interior"], "SideReveal")
            if rnd.random() < 0.6:
                point_light((x + w / 2, y_face + side * 60, WATER_Z + 320), 2200, 120.0, 10.0, "SideLantern", att=2200.0)
            x += w + rnd.uniform(0, 40)
    for i in range(4):
        spawn_mesh(S["paline"], (FAR + 900 + i * 1100, SIDE_Y0 + 70 + rnd.uniform(0, 30), WATER_Z - 40), unreal.Rotator(0, 0, rnd.uniform(0, 360)), mats=[M["wood"], M["wood_b"]], label="SidePaline_%d" % i)


def skyline(M, S):
    # dome + drum + campanile ~200 m away, left of the view axis; moon low left
    dx, dy = 26000.0, 6200.0
    box((dx, dy, WATER_Z + 900), (3200, 3200, 1800), M["plaster_cream"], "DomeBase")
    spawn_mesh(CYL, (dx, dy, WATER_Z + 2300), scale=(19, 19, 10), mat=M["plaster_cream"], label="DomeDrum")
    for k in range(12):   # drum windows
        a = 2 * math.pi * k / 12
        box((dx + 955 * math.cos(a), dy + 955 * math.sin(a), WATER_Z + 2300), (40, 110, 260), M["window_dim"], "DrumWindow", rot=unreal.Rotator(0, 0, math.degrees(a)))
    spawn_mesh(SPHERE, (dx, dy, WATER_Z + 3100), scale=(20, 20, 17), mat=M["plaster_cream"], label="Dome")
    spawn_mesh(CYL, (dx, dy, WATER_Z + 4150), scale=(3, 3, 6), mat=M["plaster_cream"], label="DomeLantern")
    spot_light((dx - 5000, dy - 1500, WATER_Z + 200), (dx, dy, WATER_Z + 3000), 2800, 40000.0, 14.0, 24.0, "DomeFlood", radius=60.0)
    cx, cy = 26500.0, 2700.0
    box((cx, cy, WATER_Z + 1800), (900, 900, 3600), M["plaster_rose"], "Campanile")
    spawn_mesh(S["gothic_big"], (cx - 460, cy, WATER_Z + 3300), unreal.Rotator(0, 0, 90), scale=(2.6, 1, 2.0), mat=M["stone"], label="BelfryArch")
    box((cx, cy, WATER_Z + 4050), (1100, 1100, 900), M["plaster_cream"], "Belfry")
    spot_light((cx - 4000, cy - 2500, WATER_Z + 200), (cx, cy, WATER_Z + 3300), 2800, 12000.0, 8.0, 14.0, "CampanileFlood", radius=40.0)
    # moon: low, left of the dome (reference 02)
    spawn_mesh(SPHERE, MOON_POS, scale=(6, 6, 6), mat=M["moon"], label="Moon")


def build_level(M, S):
    if eas.does_asset_exist(MAP):
        les.load_level(MAP)
        actors.destroy_actors(actors.get_all_level_actors())
    else:
        les.new_level(MAP)
    rnd = random.Random(11)

    # --- the product + its braids (same placed frame)
    rot = unreal.Rotator(0, 0, MASK_YAW + MASK_FIX_YAW)
    mask = spawn_mesh(S["mask"], (0, 0, CAP_TOP), rot, label="Product_CasanovaBauta")
    smc = mask.static_mesh_component
    slot_mat = {"M_Hat": "hat", "M_Trim": "hat", "M_Gold": "gold", "M_Face": "face"}
    for i, s in enumerate(S["mask"].static_materials):
        key = slot_mat.get(str(s.material_slot_name))
        if key:
            smc.set_material(i, M[key])
    smc.set_render_custom_depth(True)
    smc.set_custom_depth_stencil_value(1)
    braid = spawn_mesh(S["braid"], (0, 0, CAP_TOP), rot, label="Product_CasanovaBauta_Braid")
    bc = braid.static_mesh_component
    for i, s in enumerate(S["braid"].static_materials):
        bc.set_material(i, M.get(str(s.material_slot_name), M["M_BraidWave"]))
    bc.set_render_custom_depth(True)
    bc.set_custom_depth_stencil_value(1)

    t = math.radians(MASK_YAW + MASK_FIX_YAW)
    back = (math.sin(t), -math.cos(t))   # mask local back (-Y in UE) rotated by yaw
    log("mask yaw", MASK_YAW + MASK_FIX_YAW, "back dir", back)

    parapet(M, S)
    loggia(M, S, back)
    spawn_mesh(PLANE, (FAR / 2 + 100, 3000, WATER_Z), scale=(FAR / 100 + 4, 300, 1), mat=M["water"], label="Canal")
    far_bank(M, S, rnd)
    skyline(M, S)
    # mid-canal mooring poles for layered depth
    for i, (bx, by) in enumerate(((620, -70), (1600, 760))):
        spawn_mesh(S["paline"], (bx, by, WATER_Z - 40), unreal.Rotator(0, 0, rnd.uniform(0, 360)), mats=[M["wood"], M["wood_b"]], label="Paline_%d" % i)

    # --- sky + moonlight
    spawn_mesh(SPHERE, (0, 0, 0), scale=(4500, 4500, 4500), mat=M["sky"], label="SkyDome")
    sky = spawn(unreal.SkyLight, (0, 0, 500), label="SkyLight")
    slc = sky.get_component_by_class(unreal.SkyLightComponent)
    slc.set_editor_property("real_time_capture", True)
    slc.set_intensity(1.0)
    moon_dir = MOON_POS
    moon = spawn(unreal.DirectionalLight, (0, 0, 2000), look_at(moon_dir, (0, 0, 0)), "Moonlight")
    mc = moon.get_component_by_class(unreal.DirectionalLightComponent)
    mc.set_intensity(float(E("VM_MOON", "0.35")))
    mc.set_editor_property("use_temperature", True)
    mc.set_editor_property("temperature", 7200.0)
    mc.set_editor_property("light_source_angle", 0.6)

    # --- practical lights on the product
    mask_c = (0, 0, CAP_TOP + 12)
    spot_light((-85.0, -75.0, CAP_TOP + 70.0), (0, 0, CAP_TOP + 9), 2900, float(E("VM_KEY", "40")), 3.5, 7.5, "Key_Warm", radius=10.0)
    spot_light((75.0, -45.0, CAP_TOP + 55.0), (0, 0, CAP_TOP + 18), 2400, float(E("VM_RIM", "30")), 3.0, 8.0, "Rim_Warm", radius=4.0)
    rect_light((-170, 140, CAP_TOP + 150), mask_c, 8000, 9.0, 180, 120, "Fill_Cool")
    rect_light((-30.0, -330.0, CAP_TOP + 28.0), (0, -40, CAP_TOP), 2600, float(E("VM_LEDGE", "40")), 25, 25, "Ledge_Rake", barn=50.0)
    # small lantern in the near arch: a soft warm edge on the near column (frame left)
    point_light((-130.0, -210.0, CAP_TOP + 150.0), 2200, 9.0, 5.0, "NearArchLantern", att=600.0)
    # loggia lantern on the far column (frame left), warm pool on the colonnade
    point_light((-20.0, -520.0, CAP_TOP + 250.0), 2200, 180.0, 8.0, "LoggiaLantern", att=1500.0)
    spawn_mesh(SPHERE, (-20.0, -520.0, CAP_TOP + 250.0), scale=(0.22, 0.22, 0.3), mat=M["lantern_glass"], label="LoggiaLanternGlass")

    # --- camera (reference 02: level eye line, mask on the right third, canal and skyline to the left)
    focal = float(E("VM_FOCAL", "42"))
    cam_loc = (-150.0, -75.0, CAP_TOP + float(E("VM_CAM_H", "26")))
    vx, vy = -cam_loc[0], -cam_loc[1]
    vl = math.hypot(vx, vy)
    right = (-vy / vl, vx / vl)
    shift = float(E("VM_SHIFT", "26"))
    cam_target = (-right[0] * shift, -right[1] * shift, CAP_TOP + float(E("VM_AIM_H", "16")))
    cam = spawn(unreal.CineCameraActor, cam_loc, look_at(cam_loc, cam_target), "CAM_Hero")
    cc = cam.get_cine_camera_component()
    fb = cc.get_editor_property("filmback")
    fb.sensor_width = 36.0
    fb.sensor_height = 20.25
    cc.set_editor_property("filmback", fb)
    cc.set_editor_property("current_focal_length", focal)
    cc.set_editor_property("current_aperture", float(E("VM_FSTOP", "6.3")))
    fs = cc.get_editor_property("focus_settings")
    fs.focus_method = unreal.CameraFocusMethod.MANUAL
    face = (-back[0] * 7.0, -back[1] * 7.0, CAP_TOP + 15.0)
    fs.manual_focus_distance = unreal.MathLibrary.vector_distance(unreal.Vector(*cam_loc), unreal.Vector(*face))
    cc.set_editor_property("focus_settings", fs)
    lens = cc.get_editor_property("lens_settings")
    lens.diaphragm_blade_count = 9
    cc.set_editor_property("lens_settings", lens)
    log("camera", cam_loc, "focal", focal, "focus distance", fs.manual_focus_distance)

    ppv = spawn(unreal.PostProcessVolume, (0, 0, 0), label="PPV_Hero")
    ppv.set_editor_property("unbound", True)
    s = ppv.get_editor_property("settings")
    for k, v in {
        "override_auto_exposure_method": True, "auto_exposure_method": unreal.AutoExposureMethod.AEM_MANUAL,
        "override_auto_exposure_bias": True, "auto_exposure_bias": float(E("VM_EV", "-2.5")),
        "override_auto_exposure_apply_physical_camera_exposure": True, "auto_exposure_apply_physical_camera_exposure": False,
        "override_bloom_intensity": True, "bloom_intensity": 0.3,
        "override_vignette_intensity": True, "vignette_intensity": 0.4,
        "override_film_grain_intensity": True, "film_grain_intensity": 0.05,
        "override_white_temp": True, "white_temp": 5600.0,
    }.items():
        try:
            s.set_editor_property(k, v)
        except Exception as ex:
            log("pp skip", k, ex)
    ppv.set_editor_property("settings", s)
    les.save_current_level()
    return cam


def build_sequence(cam):
    path = G + "/Cinematics/LS_Hero"
    if eas.does_asset_exist(path):
        eas.delete_asset(path)
    seq = at.create_asset("LS_Hero", G + "/Cinematics", unreal.LevelSequence, unreal.LevelSequenceFactoryNew())
    seq.set_display_rate(unreal.FrameRate(24, 1))
    seq.set_playback_start(0)
    seq.set_playback_end(1)
    binding = seq.add_possessable(cam)
    try:
        track = seq.add_track(unreal.MovieSceneCameraCutTrack)
    except Exception:
        track = seq.add_master_track(unreal.MovieSceneCameraCutTrack)
    sec = track.add_section()
    sec.set_range(0, 1)
    try:
        bid = unreal.MovieSceneSequenceExtensions.get_portable_binding_id(seq, seq, binding)
    except Exception:
        bid = seq.get_binding_id(binding)
    sec.set_camera_binding_id(bid)
    eas.save_loaded_asset(seq)
    log("sequence", seq.get_path_name())


def main():
    T = {k: import_tex(f, kind) for k, f, kind in (
        ("crk", "T_Crackle_M.png", "gray"), ("crkn", "T_Crackle_N.png", "normal"),
        ("sth", "T_Stone_H.png", "gray"), ("stn", "T_Stone_N.png", "normal"),
        ("stw", "T_Stone_W.png", "gray"), ("wtn", "T_Water_N.png", "normal"))}
    S = {
        "mask": import_mesh(os.path.join(SRC, "casanova_bauta", "casanova_bauta_segmented.obj"), G + "/Products/CasanovaBauta", "SM_CasanovaBauta"),
        "braid": import_mesh(os.path.join(SRC, "casanova_bauta", "casanova_braid.obj"), G + "/Products/CasanovaBauta", "SM_CasanovaBraid"),
    }
    for key, name in (("cap", "SM_LedgeCap"), ("cap2", "SM_LedgeCap2"), ("cap3", "SM_LedgeCap3"), ("body", "SM_ParapetBody"),
                      ("pier", "SM_PierCourse"), ("pier2", "SM_PierCourse2"), ("slab", "SM_FloorSlab"), ("rustic", "SM_Rustic")):
        S[key] = import_mesh(os.path.join(SRC, "stone", name + ".obj"), G + "/Set", name)
    for key, name in (("arch", "SM_ArchRound"), ("gothic", "SM_ArchGothic"), ("gothic_big", "SM_ArchGothicBig"), ("column", "SM_Column"),
                      ("column_slim", "SM_ColumnSlim"), ("cornice", "SM_Cornice"), ("paline", "SM_Paline"), ("bridge", "SM_Bridge")):
        S[key] = import_mesh(os.path.join(SRC, "arch", name + ".obj"), G + "/Set", name)
    M = build_materials(T)
    cam = build_level(M, S)
    build_sequence(cam)
    with open(os.path.join(ROOT, "reports", "ue_build_hero.txt"), "w") as f:
        f.write("\n".join(REPORT))


main()
