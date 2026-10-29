"""Build L_Hero: one real Venemask product (Casanova Bauta) on a wet stone parapet by a night canal.

Run headless:  UnrealEditor-Cmd <uproject> -ExecutePythonScript=Scripts/ue_build_hero.py
Everything is (re)created idempotently under /Game/Venemask.

World layout (cm). Camera looks roughly +X across the canal.
  * Parapet runs along Y at X=0, cap top at Z=CAP_TOP. Mask sits on the cap at the origin.
  * Riser block behind the mask (+X) - the mask leans on it (it cannot stand free, see prep_mask.py).
  * Canal water at Z=-140 from X=30 to X=3600; far bank buildings at X~3600.
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

CAP_TOP = 104.0          # parapet cap top (cap 16 cm on a 88 cm body)
MASK_YAW = float(os.environ.get("VM_MASK_YAW", "55"))  # with the 90 fix: face ~30 deg off camera, toward frame-left
# Import correction: the mask front imports as +Y (ue_probe_axes); yaw 90 turns it to face -X.
MASK_FIX = unreal.Rotator(roll=0.0, pitch=0.0, yaw=float(os.environ.get("VM_MASK_FIX_YAW", "90")))


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
    """Import with Nanite OFF: the Path Tracer traces Nanite's reduced fallback mesh, which
    faceted the mask's nose and curls. ~1.3M triangles in total is fine as plain geometry."""
    m = import_file(path, dest, name)
    ns = m.get_editor_property("nanite_settings")
    if ns.enabled:
        ns.enabled = False
        try:
            sms.set_nanite_settings(m, ns, apply_changes=True)
        except Exception:
            m.set_editor_property("nanite_settings", ns)
    eas.save_loaded_asset(m)
    log(name, "triangles lod0", sms.get_number_verts(m, 0), "verts; nanite", m.get_editor_property("nanite_settings").enabled)
    return m


def import_tex(fname, kind):
    tex = import_file(os.path.join(SRC, "textures", fname), G + "/Textures", os.path.splitext(fname)[0])
    if kind == "normal":
        tex.set_editor_property("srgb", False)
        tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
    else:
        tex.set_editor_property("srgb", False)
        tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_GRAYSCALE)
    eas.save_loaded_asset(tex)
    return tex


# ---------------------------------------------------------------- material graph helpers
class MB:
    """Tiny material builder over MaterialEditingLibrary."""

    def __init__(self, name, shading=None, two_sided=False, unlit=False):
        path = G + "/Materials/" + name
        if eas.does_asset_exist(path):
            eas.delete_asset(path)
        self.m = at.create_asset(name, G + "/Materials", unreal.Material, unreal.MaterialFactoryNew())
        if unlit:
            self.m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
        elif shading:
            self.m.set_editor_property("shading_model", shading)
        self.m.set_editor_property("two_sided", two_sided)
        self.y = 0

    def e(self, cls, **props):
        self.y += 120
        x = mel.create_material_expression(self.m, cls, -600, self.y)
        for k, v in props.items():
            x.set_editor_property(k, v)
        return x

    def c(self, v):
        return self.e(unreal.MaterialExpressionConstant, r=v)

    def c3(self, r, g, b):
        return self.e(unreal.MaterialExpressionConstant3Vector, constant=unreal.LinearColor(r, g, b, 1))

    def tex(self, t, uv=None, kind="linear"):
        st = {"normal": unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL,
              "gray": unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE}[kind]
        x = self.e(unreal.MaterialExpressionTextureSample, texture=t, sampler_type=st)
        if uv is not None:
            self.link(uv, "", x, "UVs")
        return x

    def uv(self, tiling):
        return self.e(unreal.MaterialExpressionTextureCoordinate, u_tiling=tiling, v_tiling=tiling)

    def link(self, a, aout, b, bin_):
        mel.connect_material_expressions(a, aout, b, bin_)

    def op(self, cls, a, b, aout="", bout=""):
        x = self.e(cls)
        self.link(a, aout, x, "A")
        self.link(b, bout, x, "B")
        return x

    def mul(self, a, b, aout="", bout=""):
        return self.op(unreal.MaterialExpressionMultiply, a, b, aout, bout)

    def add(self, a, b, aout="", bout=""):
        return self.op(unreal.MaterialExpressionAdd, a, b, aout, bout)

    def lerp(self, a, b, alpha, aout="", bout="", alphaout=""):
        x = self.e(unreal.MaterialExpressionLinearInterpolate)
        self.link(a, aout, x, "A")
        self.link(b, bout, x, "B")
        self.link(alpha, alphaout, x, "Alpha")
        return x

    def sat(self, a, aout=""):
        x = self.e(unreal.MaterialExpressionSaturate)
        self.link(a, aout, x, "")
        return x

    def out(self, x, prop, xout=""):
        mel.connect_material_property(x, xout, prop)

    def attrs(self, **inputs):
        """Route through MakeMaterialAttributes (needed for ClearCoat, not exposed in MaterialProperty)."""
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


P = unreal.MaterialProperty
CLEAR = unreal.MaterialShadingModel.MSM_CLEAR_COAT


def flat_normal(b, n_expr, strength):
    """lerp((0,0,1), normal, strength)"""
    return b.lerp(b.c3(0, 0, 1), n_expr, b.c(strength), bout="RGB")


def build_materials(T):
    M = {}
    # White crackle-glaze face (photos: glossy ivory glaze with fine dark craquelure)
    b = MB("M_CB_Face", shading=CLEAR)
    uv = b.uv(2.6)  # cells ~3 mm like the finished product photos
    crack = b.tex(T["crk"], uv, "gray")
    crack_c = b.mul(crack, b.c(0.5), "R")
    b.attrs(BaseColor=b.lerp(b.c3(0.80, 0.775, 0.715), b.c3(0.36, 0.32, 0.27), crack_c),
            Roughness=b.lerp(b.c(0.24), b.c(0.6), crack, alphaout="R"),
            Normal=flat_normal(b, b.tex(T["crkn"], uv, "normal"), 0.45),
            ClearCoat=b.c(0.9),
            ClearCoatRoughness=b.c(0.06))
    M["face"] = b.done()

    # Black lacquered tricorn
    b = MB("M_CB_Hat", shading=CLEAR)
    h = b.tex(T["sth"], b.uv(9.0), "gray")
    b.attrs(BaseColor=b.c3(0.011, 0.010, 0.012),
            Roughness=b.lerp(b.c(0.22), b.c(0.42), h, alphaout="R"),
            ClearCoat=b.c(1.0),
            ClearCoatRoughness=b.lerp(b.c(0.03), b.c(0.12), h, alphaout="R"))
    M["hat"] = b.done()

    # Painted antique gold curls
    b = MB("M_CB_Gold")
    h = b.tex(T["sth"], b.uv(5.0), "gray")
    # acrylic gold paint: metallic flakes in a binder -> brighter, rougher than polished metal
    b.out(b.lerp(b.c3(0.72, 0.48, 0.16), b.c3(0.98, 0.74, 0.34), h, alphaout="R"), P.MP_BASE_COLOR)
    b.out(b.c(0.6), P.MP_METALLIC)
    b.out(b.lerp(b.c(0.48), b.c(0.36), h, alphaout="R"), P.MP_ROUGHNESS)
    M["gold"] = b.done()

    # Gold braid trim (painted approximation; real braid geometry not in STL)
    b = MB("M_CB_Trim")
    uvt = b.uv(60.0)
    b.out(b.c3(0.86, 0.64, 0.30), P.MP_BASE_COLOR)
    b.out(b.c(1.0), P.MP_METALLIC)
    b.out(b.c(0.38), P.MP_ROUGHNESS)
    b.out(flat_normal(b, b.tex(T["stn"], uvt, "normal"), 0.8), P.MP_NORMAL)
    M["trim"] = b.done()

    # Wet weathered stone (UVs are metres; one texture tile = 0.8 m)
    b = MB("M_Stone_Wet")
    uv = b.uv(1.25)
    h = b.tex(T["sth"], uv, "gray")
    wet_raw = b.tex(T["stw"], b.uv(0.45), "gray")
    up = b.e(unreal.MaterialExpressionVertexNormalWS)
    upz = b.e(unreal.MaterialExpressionComponentMask, r=False, g=False, b=True, a=False)
    b.link(up, "", upz, "")
    # wet = saturate((wetmask - 0.45) * 4) * saturate(up.z*2 - 1) ; vertical faces stay damp only
    wet = b.sat(b.mul(b.add(wet_raw, b.c(-0.42), "R"), b.c(4.0)))
    topmask = b.sat(b.add(b.mul(upz, b.c(2.0)), b.c(-1.0)))
    wet = b.add(b.mul(wet, topmask), b.c(0.04))
    wet = b.sat(wet)
    dry_col = b.lerp(b.c3(0.028, 0.026, 0.024), b.c3(0.105, 0.096, 0.086), h, alphaout="R")
    b.out(b.lerp(dry_col, b.mul(dry_col, b.c(0.5)), wet), P.MP_BASE_COLOR)
    rough_dry = b.lerp(b.c(0.85), b.c(0.62), h, alphaout="R")
    b.out(b.lerp(rough_dry, b.c(0.08), wet), P.MP_ROUGHNESS)
    n = flat_normal(b, b.tex(T["stn"], uv, "normal"), 0.45)
    b.out(b.lerp(n, b.c3(0, 0, 1), b.mul(wet, b.c(0.85))), P.MP_NORMAL)
    M["stone"] = b.done()

    # Darker, rougher stone for distant facades
    b = MB("M_Facade")
    h = b.tex(T["sth"], b.uv(0.6), "gray")
    b.out(b.lerp(b.c3(0.020, 0.018, 0.017), b.c3(0.060, 0.052, 0.046), h, alphaout="R"), P.MP_BASE_COLOR)
    b.out(b.c(0.9), P.MP_ROUGHNESS)
    M["facade"] = b.done()

    # Canal water: deep, dark, mirror-like with gentle ripples
    b = MB("M_Canal")
    n = b.tex(T["wtn"], b.uv(30.0), "normal")
    b.out(b.c3(0.004, 0.006, 0.007), P.MP_BASE_COLOR)
    b.out(b.c(0.035), P.MP_ROUGHNESS)
    b.out(b.c(0.25), P.MP_SPECULAR)
    b.out(flat_normal(b, n, 0.35), P.MP_NORMAL)
    M["water"] = b.done()

    # Warm lit windows / lantern glass (emissive, distant)
    b = MB("M_WindowGlow", unlit=True)
    p = b.e(unreal.MaterialExpressionScalarParameter, parameter_name="Intensity", default_value=5.0)
    b.out(b.mul(b.c3(1.0, 0.52, 0.20), p), P.MP_EMISSIVE_COLOR)
    M["window"] = b.done()

    # Night sky backdrop: horizon glow -> near-black zenith
    b = MB("M_NightSky", unlit=True, two_sided=True)
    vn = b.e(unreal.MaterialExpressionVertexNormalWS)
    z = b.e(unreal.MaterialExpressionComponentMask, r=False, g=False, b=True, a=False)
    b.link(vn, "", z, "")
    t = b.sat(b.mul(z, b.c(2.5)))
    b.out(b.lerp(b.c3(0.16, 0.21, 0.34), b.c3(0.016, 0.022, 0.045), t), P.MP_EMISSIVE_COLOR)
    M["sky"] = b.done()

    # Post-process passes for QA: world normal + matte (custom stencil 1 = product)
    b = MB("M_PP_WorldNormal")
    b.m.set_editor_property("material_domain", unreal.MaterialDomain.MD_POST_PROCESS)
    st = b.e(unreal.MaterialExpressionSceneTexture, scene_texture_id=unreal.SceneTextureId.PPI_WORLD_NORMAL)
    b.out(b.add(b.mul(st, b.c(0.5), "Color"), b.c(0.5)), P.MP_EMISSIVE_COLOR)
    M["pp_normal"] = b.done()

    b = MB("M_PP_ProductMatte")
    b.m.set_editor_property("material_domain", unreal.MaterialDomain.MD_POST_PROCESS)
    st = b.e(unreal.MaterialExpressionSceneTexture, scene_texture_id=unreal.SceneTextureId.PPI_CUSTOM_STENCIL)
    m1 = b.sat(b.mul(st, b.c(10.0), "Color"))
    b.out(m1, P.MP_EMISSIVE_COLOR)
    M["pp_matte"] = b.done()
    return M


# ---------------------------------------------------------------- level helpers
CUBE = "/Engine/BasicShapes/Cube.Cube"
SPHERE = "/Engine/BasicShapes/Sphere.Sphere"
CYL = "/Engine/BasicShapes/Cylinder.Cylinder"
PLANE = "/Engine/BasicShapes/Plane.Plane"


def spawn_mesh(mesh, loc, rot=None, scale=None, mat=None, label=None):
    if isinstance(mesh, str):
        mesh = unreal.load_asset(mesh)
    a = actors.spawn_actor_from_object(mesh, unreal.Vector(*loc), rot or unreal.Rotator(0, 0, 0))
    if scale:
        a.set_actor_scale3d(unreal.Vector(*scale))
    if mat:
        c = a.static_mesh_component
        for i in range(c.get_num_materials()):
            c.set_material(i, mat)
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


def build_level(M, meshes):
    # new_level() does not replace an existing map, so rebuilds would stack duplicate actors.
    if eas.does_asset_exist(MAP):
        les.load_level(MAP)
        actors.destroy_actors(actors.get_all_level_actors())
    else:
        les.new_level(MAP)

    # --- the product
    mask = spawn_mesh(meshes["mask"], (0, 0, CAP_TOP), unreal.Rotator(0, 0, MASK_YAW + MASK_FIX.yaw), label="Product_CasanovaBauta")
    smc = mask.static_mesh_component
    for i, s in enumerate(meshes["mask"].static_materials):
        key = {"M_Hat": "hat", "M_Trim": "trim", "M_Gold": "gold", "M_Face": "face"}.get(str(s.material_slot_name))
        if key:
            smc.set_material(i, M[key])
    smc.set_render_custom_depth(True)
    smc.set_custom_depth_stencil_value(1)

    # --- loggia pier the mask leans on: its face plane touches the mask's rearmost point.
    # Mask local back is -Y in UE (prep +Y, negated on import); rotated by yaw t it points (sin t, -cos t).
    t = math.radians(MASK_YAW + MASK_FIX.yaw)
    back = (math.sin(t), -math.cos(t))
    d = PREP["rear_contact_cm"][1] + 15.0  # pier half depth 15
    pier_yaw = math.degrees(math.atan2(back[1], back[0]))  # pier local +X (depth) along the mask's back
    spawn_mesh(meshes["pier"], (back[0] * d, back[1] * d, CAP_TOP), unreal.Rotator(0, 0, pier_yaw), mat=M["stone"], label="Pier")
    log("mask yaw", MASK_YAW + MASK_FIX.yaw, "back dir", back, "pier centre", (back[0] * d, back[1] * d))

    # --- parapet: cap + body, along Y, plus the next cap segment receding left
    spawn_mesh(meshes["cap"], (6, -40, CAP_TOP - 16), mat=M["stone"], label="ParapetCap_A")
    spawn_mesh(meshes["body"], (6, -40, CAP_TOP - 16 - 92), mat=M["stone"], label="ParapetBody_A")
    spawn_mesh(meshes["cap"], (6, -362, CAP_TOP - 16), unreal.Rotator(0, 0, 0.4), mat=M["stone"], label="ParapetCap_B")
    spawn_mesh(meshes["body"], (6, -362, CAP_TOP - 16 - 92), mat=M["stone"], label="ParapetBody_B")
    # terrace floor slabs in front of the parapet (mostly out of frame, bounce light)
    for i in range(-5, 3):
        for j in range(-3, 0):
            spawn_mesh(meshes["slab"], (j * 121 - 30, i * 121, -8), mat=M["stone"], label="Floor")

    # --- canal water, embankment wall below the parapet
    # The camera looks ~24 deg off +X, so the far bank must cover Y up to ~+0.45 * FAR.
    FAR = 9000.0
    spawn_mesh(PLANE, (FAR / 2, 3000, -140), scale=(FAR / 100, 260, 1), mat=M["water"], label="Canal")
    spawn_mesh(CUBE, (40, 3000, -70), scale=(0.4, 260, 1.6), mat=M["stone"], label="Embankment")

    # --- far bank (~90 m): low palazzo masses with sparse lit windows, read as silhouettes + bokeh
    rnd = random.Random(7)
    y = -6000.0
    while y < 14000:
        w = rnd.uniform(1100, 2000)
        h = rnd.uniform(500, 1100)
        x = FAR + rnd.uniform(-200, 300)
        spawn_mesh(CUBE, (x + 600, y + w / 2, -140), scale=(12, w / 100, h / 100), mat=M["facade"], label="Palazzo")
        for fl in range(1, min(3, int((h - 150) / 330) + 1)):  # lower floors only: high windows read as UI blocks
            for cl in range(int(w / 320)):
                if rnd.random() < 0.22:
                    spawn_mesh(CUBE, (x - 2, y + 160 + cl * 320, -140 + fl * 330), scale=(0.05, 0.7, 1.3),
                               mat=M["window"], label="Window")
        y += w + rnd.uniform(60, 400)
    # basilica dome silhouette ~160 m away, ~14 deg left of the view axis: rises above the
    # roofline in the negative space, small enough to stay a landmark, not a shape in front
    spawn_mesh(CYL, (21000, 4300, 100), scale=(19, 19, 8), mat=M["facade"], label="DomeDrum")
    spawn_mesh(SPHERE, (21000, 4300, 900), scale=(18, 18, 15), mat=M["facade"], label="Dome")
    spawn_mesh(CYL, (21000, 4300, 1700), scale=(2, 2, 3), mat=M["facade"], label="DomeLantern")

    # --- sky
    spawn_mesh(SPHERE, (0, 0, 0), scale=(4000, 4000, 4000), mat=M["sky"], label="SkyDome")
    sky = spawn(unreal.SkyLight, (0, 0, 500), label="SkyLight")
    slc = sky.get_component_by_class(unreal.SkyLightComponent)
    slc.set_editor_property("real_time_capture", True)
    slc.set_intensity(1.0)

    # --- lights
    def rect(loc, target, kelvin, cd, w, h, label, barn=60.0):
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

    def point(loc, kelvin, cd, radius, label, att=3000.0):
        a = spawn(unreal.PointLight, loc, None, label)
        c = a.get_component_by_class(unreal.PointLightComponent)
        c.set_editor_property("intensity_units", unreal.LightUnits.CANDELAS)
        c.set_intensity(cd)
        c.set_editor_property("use_temperature", True)
        c.set_editor_property("temperature", kelvin)
        c.set_editor_property("source_radius", radius)
        c.set_editor_property("attenuation_radius", att)
        return a

    mask_c = (0, 0, CAP_TOP + 12)
    # key in front of the face (face looks toward -X/-Y), above; rim from behind-left; cool sky fill
    # key: tight soft spot (a flagged lamp) so the mask is lit, not the whole ledge
    kl = (-85.0, -75.0, CAP_TOP + 70.0)
    key = spawn(unreal.SpotLight, kl, look_at(kl, mask_c), "Key_Warm")
    kc = key.get_component_by_class(unreal.SpotLightComponent)
    kc.set_editor_property("intensity_units", unreal.LightUnits.CANDELAS)
    kc.set_intensity(float(os.environ.get("VM_KEY", "40")))
    kc.set_editor_property("use_temperature", True)
    kc.set_editor_property("temperature", 2900.0)
    kc.set_editor_property("source_radius", 10.0)
    kc.set_editor_property("inner_cone_angle", 4.0)
    kc.set_editor_property("outer_cone_angle", 9.0)
    # rim: narrow soft spot from behind-left, aimed at the hat/cheek edge only
    rl = (75.0, -45.0, CAP_TOP + 55.0)
    rim = spawn(unreal.SpotLight, rl, look_at(rl, (0, 0, CAP_TOP + 18)), "Rim_Warm")
    rc = rim.get_component_by_class(unreal.SpotLightComponent)
    rc.set_editor_property("intensity_units", unreal.LightUnits.CANDELAS)
    rc.set_intensity(float(os.environ.get("VM_RIM", "30")))
    rc.set_editor_property("use_temperature", True)
    rc.set_editor_property("temperature", 2400.0)
    rc.set_editor_property("source_radius", 4.0)
    rc.set_editor_property("inner_cone_angle", 3.0)
    rc.set_editor_property("outer_cone_angle", 8.0)
    rect((-170, 140, CAP_TOP + 150), mask_c, 8000, 6.0, 180, 120, "Fill_Cool")
    # off-frame terrace lantern far left: low raking light along the wet ledge (leading line)
    rect((-30.0, -330.0, CAP_TOP + 28.0), (0, -40, CAP_TOP), 2600, float(os.environ.get("VM_LEDGE", "25")), 25, 25, "Ledge_Rake", barn=50.0)
    # distant lanterns on the far bank: reflections on water, bokeh
    for i, ly in enumerate(range(-1000, 12000, 1150)):
        lx = FAR - 350
        point((lx, ly, 160), 2200, 450.0, 15.0, "Lantern_%d" % i, att=4500.0)
        spawn_mesh(SPHERE, (lx, ly, 160), scale=(0.5, 0.5, 0.7), mat=M["window"], label="LanternGlass")
        spawn_mesh(CYL, (lx, ly, 0), scale=(0.15, 0.15, 3.0), mat=M["facade"], label="LanternPost")

    # --- camera
    # 50 mm at ~1.5 m, a little above the mask, aimed left of it so the mask lands on the right third
    focal = float(os.environ.get("VM_FOCAL", "60"))
    cam_loc = (-135.0, -60.0, CAP_TOP + float(os.environ.get("VM_CAM_H", "15")))
    vx, vy = -cam_loc[0], -cam_loc[1]
    vl = math.hypot(vx, vy)
    right = (-vy / vl, vx / vl)
    shift = float(os.environ.get("VM_SHIFT", "18"))
    cam_target = (-right[0] * shift, -right[1] * shift, CAP_TOP + float(os.environ.get("VM_AIM_H", "13")))  # ~level: horizon mid-frame (ref 02)
    cam = spawn(unreal.CineCameraActor, cam_loc, look_at(cam_loc, cam_target), "CAM_Hero")
    cc = cam.get_cine_camera_component()
    fb = cc.get_editor_property("filmback")
    fb.sensor_width = 36.0
    fb.sensor_height = 20.25
    cc.set_editor_property("filmback", fb)
    cc.set_editor_property("current_focal_length", focal)
    cc.set_editor_property("current_aperture", float(os.environ.get("VM_FSTOP", "2.0")))
    fs = cc.get_editor_property("focus_settings")
    fs.focus_method = unreal.CameraFocusMethod.MANUAL
    # focus on the eye line, ~7 cm in front of the mask origin along its facing direction
    face = (-back[0] * 7.0, -back[1] * 7.0, CAP_TOP + 15.0)
    fs.manual_focus_distance = unreal.MathLibrary.vector_distance(unreal.Vector(*cam_loc), unreal.Vector(*face))
    cc.set_editor_property("focus_settings", fs)
    lens = cc.get_editor_property("lens_settings")
    lens.diaphragm_blade_count = 9
    cc.set_editor_property("lens_settings", lens)
    log("camera focus distance", fs.manual_focus_distance)

    # --- post process (manual exposure, filmic restraint)
    ppv = spawn(unreal.PostProcessVolume, (0, 0, 0), label="PPV_Hero")
    ppv.set_editor_property("unbound", True)
    s = ppv.get_editor_property("settings")
    for k, v in {
        "override_auto_exposure_method": True, "auto_exposure_method": unreal.AutoExposureMethod.AEM_MANUAL,
        "override_auto_exposure_bias": True, "auto_exposure_bias": float(os.environ.get("VM_EV", "-2.5")),
        "override_auto_exposure_apply_physical_camera_exposure": True, "auto_exposure_apply_physical_camera_exposure": False,
        "override_bloom_intensity": True, "bloom_intensity": 0.35,
        "override_vignette_intensity": True, "vignette_intensity": 0.45,
        "override_film_grain_intensity": True, "film_grain_intensity": 0.06,
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
    T = {
        "crk": import_tex("T_Crackle_M.png", "gray"),
        "crkn": import_tex("T_Crackle_N.png", "normal"),
        "sth": import_tex("T_Stone_H.png", "gray"),
        "stn": import_tex("T_Stone_N.png", "normal"),
        "stw": import_tex("T_Stone_W.png", "gray"),
        "wtn": import_tex("T_Water_N.png", "normal"),
    }
    meshes = {
        "mask": import_mesh(os.path.join(SRC, "casanova_bauta", "casanova_bauta_segmented.obj"), G + "/Products/CasanovaBauta", "SM_CasanovaBauta"),
    }
    for key, name in (("cap", "SM_LedgeCap"), ("body", "SM_ParapetBody"), ("pier", "SM_Pier"), ("slab", "SM_FloorSlab")):
        meshes[key] = import_mesh(os.path.join(SRC, "stone", name + ".obj"), G + "/Set", name)
    M = build_materials(T)
    cam = build_level(M, meshes)
    build_sequence(cam)
    with open(os.path.join(ROOT, "reports", "ue_build_hero.txt"), "w") as f:
        f.write("\n".join(REPORT))


main()
