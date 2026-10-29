"""Hybrid environment test on top of the v6 hero (L_Hero is not modified).

  1. L_Hero_Plate  : copy of L_Hero with the near layer removed; a 24 mm plate camera at the K0 position.
                     Rendered once at 4096x2304 (MRQ_Plate) -> the matte plate (camera projection source).
  2. L_Hero_Hybrid : copy of L_Hero where the far layer (palazzi, windows, lamps, skyline, moon, sky) is
                     replaced by proxy volumes + the sky dome carrying M_Projection (the plate projected from
                     the K0 point). Near layer stays real 3D: mask + braids, parapet caps/body, pier, loggia,
                     water, near mooring poles, practical lights, moonlight.
  3. In L_Hero, L_Hero_Hybrid (and L_Hero_Plate for the plate camera): cameras K0 (v6 hero), K1 (lateral),
     K2 (dolly-in + small yaw) with their LevelSequences, plus LS_Move (K0 -> K1 -> K2, 48 frames).

Run:   UnrealEditor-Cmd <uproject> -ExecutePythonScript=Scripts/ue_hybrid.py            (stage 1: levels + cameras)
       render.ps1 -Config MRQ_Plate -Map L_Hero_Plate -Sequence LS_Plate
       VM_STAGE=plate UnrealEditor-Cmd ... ue_hybrid.py                                   (stage 2: import plate, build projection)
"""
import math
import os
import unreal

ROOT = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
G = "/Game/Venemask"
STAGE = os.environ.get("VM_STAGE", "levels")
REPORT = []

mel = unreal.MaterialEditingLibrary
at = unreal.AssetToolsHelpers.get_asset_tools()
eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

CAP_TOP = 104.0
# v6 hero camera (ue_build_hero.py): position, aim and lens
K0_LOC = (-150.0, -75.0, CAP_TOP + 26.0)
_v = (150.0, 75.0)
_vl = math.hypot(*_v)
_right = (-_v[1] / _vl, _v[0] / _vl)
K0_AIM = (-_right[0] * 26.0, -_right[1] * 26.0, CAP_TOP + 16.0)
FOCAL, FSTOP = 42.0, 6.3
SENSOR = (36.0, 20.25)

# K1: camera slides 45 cm to frame-left along its own right vector, same aim point.
# Parallax envelope for a 45 cm slide: far bank (110 m) 0.23 deg ~ 10 px, mid proxies (16 m) 1.6 deg ~ 70 px,
# so the mid layer must be geometry (proxies) and only the far layer may live on the sphere.
K1_LOC = (K0_LOC[0] - _right[0] * 45.0, K0_LOC[1] - _right[1] * 45.0, K0_LOC[2])
K1_AIM = K0_AIM
# K2: 35 cm dolly-in along the view axis and the aim moved 12 cm toward the mask (~5 deg yaw)
_d = (K0_AIM[0] - K0_LOC[0], K0_AIM[1] - K0_LOC[1], K0_AIM[2] - K0_LOC[2])
_dl = math.sqrt(sum(c * c for c in _d))
_d = tuple(c / _dl for c in _d)
K2_LOC = tuple(K0_LOC[i] + _d[i] * 35.0 for i in range(3))
K2_AIM = (K0_AIM[0] + _right[0] * 12.0, K0_AIM[1] + _right[1] * 12.0, K0_AIM[2] - 2.0)
POSES = {"K0": (K0_LOC, K0_AIM), "K1": (K1_LOC, K1_AIM), "K2": (K2_LOC, K2_AIM)}

NEAR_LABELS = ("Product_", "Cap_", "ParapetBody", "Floor", "Embankment", "PierCourse", "PierCap", "Column", "Arch_",
               "Entablature", "LoggiaBackWall", "LoggiaCeiling", "Canal", "Paline_", "Key_Warm", "Rim_Warm", "Fill_Cool",
               "Ledge_Rake", "NearArchLantern", "LoggiaLantern", "CAM_", "PPV_", "SkyLight", "Moonlight")
FAR_DETAIL_LABELS = ("Rustic", "Arcade", "ArcadeDepth", "ArcadeLamp", "Cornice", "Reveal", "Pane", "WinArch", "Mullion", "Sill",
                     "WinLamp", "Bridge", "PalineFar", "QuayLantern", "LanternGlass", "LanternPost", "SidePane", "SideReveal",
                     "SideLantern", "SidePaline", "DomeDrum", "DrumWindow", "Dome", "DomeLantern", "DomeFlood", "BelfryArch",
                     "Belfry", "CampanileFlood", "Moon")
PROXY_LABELS = ("Palazzo", "SideCanalHouse", "DomeBase", "Campanile", "SkyDome")


def log(*a):
    s = " ".join(str(x) for x in a)
    REPORT.append(s)
    unreal.log("[VENEMASK] " + s)


def look_at(src, dst):
    return unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*src), unreal.Vector(*dst))


def label_of(a):
    try:
        return a.get_actor_label()
    except Exception:
        return ""


def starts(label, prefixes):
    return any(label.startswith(p) for p in prefixes)


def duplicate_level(src, dst):
    """Copy a level. duplicate_asset()+load_level() asserts ("old world not cleaned up by GC"),
    new_level_from_template() copies the map cleanly."""
    if eas.does_asset_exist(dst):
        eas.delete_asset(dst)
    assert les.new_level_from_template(dst, src), "new_level_from_template failed " + dst
    les.save_current_level()


def find_actor(label):
    for a in actors.get_all_level_actors():
        if label_of(a) == label:
            return a
    return None


def make_camera(name, loc, aim, focal, fstop, track=None):
    cam = actors.spawn_actor_from_class(unreal.CineCameraActor, unreal.Vector(*loc), look_at(loc, aim))
    cam.set_actor_label(name)
    cc = cam.get_cine_camera_component()
    fb = cc.get_editor_property("filmback")
    fb.sensor_width, fb.sensor_height = SENSOR
    cc.set_editor_property("filmback", fb)
    cc.set_editor_property("current_focal_length", focal)
    cc.set_editor_property("current_aperture", fstop)
    fs = cc.get_editor_property("focus_settings")
    if track is not None:
        fs.focus_method = unreal.CameraFocusMethod.TRACKING
        ts = fs.get_editor_property("tracking_focus_settings")
        ts.actor_to_track = track
        ts.relative_offset = unreal.Vector(0, 0, 15.0)
        fs.set_editor_property("tracking_focus_settings", ts)
    else:
        fs.focus_method = unreal.CameraFocusMethod.MANUAL
        fs.manual_focus_distance = unreal.MathLibrary.vector_distance(unreal.Vector(*loc), unreal.Vector(*aim))
    cc.set_editor_property("focus_settings", fs)
    lens = cc.get_editor_property("lens_settings")
    lens.diaphragm_blade_count = 9
    cc.set_editor_property("lens_settings", lens)
    return cam


def make_sequence(name, cam, frames=1, keys=None):
    """keys: list of (frame, loc, aim) for a camera move; None = static one-frame sequence."""
    path = G + "/Cinematics/" + name
    if eas.does_asset_exist(path):
        eas.delete_asset(path)
    seq = at.create_asset(name, G + "/Cinematics", unreal.LevelSequence, unreal.LevelSequenceFactoryNew())
    seq.set_display_rate(unreal.FrameRate(24, 1))
    seq.set_playback_start(0)
    seq.set_playback_end(frames)
    binding = seq.add_possessable(cam)
    cut = seq.add_track(unreal.MovieSceneCameraCutTrack)
    sec = cut.add_section()
    sec.set_range(0, frames)
    sec.set_camera_binding_id(unreal.MovieSceneSequenceExtensions.get_portable_binding_id(seq, seq, binding))
    if keys:
        tr = binding.add_track(unreal.MovieScene3DTransformTrack)
        ts = tr.add_section()
        ts.set_range(0, frames)
        chans = ts.get_all_channels()   # Location.X,Y,Z, Rotation.X,Y,Z, Scale.X,Y,Z
        for f, loc, aim in keys:
            rot = look_at(loc, aim)
            vals = [loc[0], loc[1], loc[2], rot.roll, rot.pitch, rot.yaw, 1.0, 1.0, 1.0]
            for c, v in zip(chans, vals):
                c.add_key(unreal.FrameNumber(f), float(v), 0.0, unreal.MovieSceneTimeUnit.DISPLAY_RATE, unreal.MovieSceneKeyInterpolation.AUTO)
    eas.save_loaded_asset(seq)
    log("sequence", path, "frames", frames)
    return seq


def add_cameras(suffix):
    mask = find_actor("Product_CasanovaBauta")
    cams = {}
    for pose, (loc, aim) in POSES.items():
        cams[pose] = make_camera("CAM_" + pose, loc, aim, FOCAL, FSTOP, track=mask)
        make_sequence("LS_%s%s" % (pose, suffix), cams[pose])
        log("camera", pose, suffix, "loc", loc, "aim", aim)
    mover = make_camera("CAM_Move", K0_LOC, K0_AIM, FOCAL, FSTOP, track=mask)
    make_sequence("LS_Move" + suffix, mover, frames=48,
                  keys=[(0, K0_LOC, K0_AIM), (24, K1_LOC, K1_AIM), (47, K2_LOC, K2_AIM)])
    les.save_current_level()


def stage_levels():
    # --- cameras in the untouched v6 level (only new camera actors + sequences are added)
    les.load_level(G + "/Maps/L_Hero")
    for a in actors.get_all_level_actors():
        if label_of(a).startswith("CAM_") and label_of(a) != "CAM_Hero":
            actors.destroy_actor(a)
    add_cameras("")

    # --- plate level: near layer removed, wide plate camera at K0
    duplicate_level(G + "/Maps/L_Hero", G + "/Maps/L_Hero_Plate")
    for a in actors.get_all_level_actors():
        l = label_of(a)
        if starts(l, NEAR_LABELS) and not l.startswith("Moonlight") and not l.startswith("SkyLight") and not l.startswith("PPV_"):
            actors.destroy_actor(a)
    plate_cam = make_camera("CAM_Plate", K0_LOC, K0_AIM, 24.0, 22.0)   # 73.7 deg h-FOV, deep focus
    make_sequence("LS_Plate", plate_cam)
    les.save_current_level()
    log("plate camera", K0_LOC, "aim", K0_AIM, "focal 24 f/22")

    # --- hybrid level: far detail deleted, proxies kept (material assigned in stage 2)
    duplicate_level(G + "/Maps/L_Hero", G + "/Maps/L_Hero_Hybrid")
    removed = 0
    for a in actors.get_all_level_actors():
        if starts(label_of(a), FAR_DETAIL_LABELS):
            actors.destroy_actor(a)
            removed += 1
    log("hybrid: removed far detail actors", removed)
    add_cameras("_Hybrid")


def build_projection_material(plate_tex):
    name = "M_Projection"
    path = G + "/Materials/" + name
    if eas.does_asset_exist(path):
        eas.delete_asset(path)
    m = at.create_asset(name, G + "/Materials", unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property("two_sided", True)
    y = [0]

    def e(cls, **props):
        y[0] += 110
        x = mel.create_material_expression(m, cls, -700, y[0])
        for k, v in props.items():
            x.set_editor_property(k, v)
        return x

    def link(a, ao, b, bi): mel.connect_material_expressions(a, ao, b, bi)

    def op(cls, a, b, ao="", bo=""):
        x = e(cls); link(a, ao, x, "A"); link(b, bo, x, "B"); return x

    def un(cls, a, ao=""):
        x = e(cls); link(a, ao, x, ""); return x

    rot = look_at(K0_LOC, K0_AIM)
    F = unreal.MathLibrary.get_forward_vector(rot)
    R = unreal.MathLibrary.get_right_vector(rot)
    U = unreal.MathLibrary.get_up_vector(rot)
    cam = e(unreal.MaterialExpressionVectorParameter, parameter_name="CamPos", default_value=unreal.LinearColor(*K0_LOC, 1))
    fwd = e(unreal.MaterialExpressionVectorParameter, parameter_name="CamFwd", default_value=unreal.LinearColor(F.x, F.y, F.z, 1))
    rgt = e(unreal.MaterialExpressionVectorParameter, parameter_name="CamRight", default_value=unreal.LinearColor(R.x, R.y, R.z, 1))
    up = e(unreal.MaterialExpressionVectorParameter, parameter_name="CamUp", default_value=unreal.LinearColor(U.x, U.y, U.z, 1))
    fx = e(unreal.MaterialExpressionScalarParameter, parameter_name="FX", default_value=24.0 / SENSOR[0])
    fy = e(unreal.MaterialExpressionScalarParameter, parameter_name="FY", default_value=24.0 / SENSOR[1])
    wp = e(unreal.MaterialExpressionWorldPosition)
    d = op(unreal.MaterialExpressionSubtract, wp, cam, "", "RGB")
    dx = op(unreal.MaterialExpressionDotProduct, d, fwd, "", "RGB")
    dy = op(unreal.MaterialExpressionDotProduct, d, rgt, "", "RGB")
    dz = op(unreal.MaterialExpressionDotProduct, d, up, "", "RGB")
    half = e(unreal.MaterialExpressionConstant, r=0.5)
    u = op(unreal.MaterialExpressionAdd, half, op(unreal.MaterialExpressionMultiply, op(unreal.MaterialExpressionDivide, dy, dx), fx))
    v = op(unreal.MaterialExpressionSubtract, half, op(unreal.MaterialExpressionMultiply, op(unreal.MaterialExpressionDivide, dz, dx), fy))
    uv = op(unreal.MaterialExpressionAppendVector, u, v)
    plate = e(unreal.MaterialExpressionTextureSampleParameter2D, parameter_name="Plate", texture=plate_tex,
              sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
    link(uv, "", plate, "UVs")
    # inside-plate mask: in front of the camera and 0..1 in both axes
    big = e(unreal.MaterialExpressionConstant, r=400.0)
    def inside(t):
        return un(unreal.MaterialExpressionSaturate, op(unreal.MaterialExpressionMultiply,
                  op(unreal.MaterialExpressionSubtract, half, un(unreal.MaterialExpressionAbs, op(unreal.MaterialExpressionSubtract, t, half))), big))
    msk = op(unreal.MaterialExpressionMultiply, op(unreal.MaterialExpressionMultiply, inside(u), inside(v)),
             un(unreal.MaterialExpressionSaturate, op(unreal.MaterialExpressionMultiply, dx, big)))
    # fallback outside the plate: the v6 sky gradient
    vn = e(unreal.MaterialExpressionVertexNormalWS)
    nz = e(unreal.MaterialExpressionComponentMask, r=False, g=False, b=True, a=False)
    link(vn, "", nz, "")
    t = un(unreal.MaterialExpressionSaturate, op(unreal.MaterialExpressionMultiply, nz, e(unreal.MaterialExpressionConstant, r=2.2)))
    sky = e(unreal.MaterialExpressionLinearInterpolate)
    link(e(unreal.MaterialExpressionConstant3Vector, constant=unreal.LinearColor(0.17, 0.21, 0.33, 1)), "", sky, "A")
    link(e(unreal.MaterialExpressionConstant3Vector, constant=unreal.LinearColor(0.014, 0.020, 0.042, 1)), "", sky, "B")
    link(t, "", sky, "Alpha")
    # MRQ's EXR is scene-linear but already carries the manual exposure (EV -2.5); the emissive path is
    # exposed again at render time, so compensate by 2^2.5
    comp = e(unreal.MaterialExpressionScalarParameter, parameter_name="ExposureComp", default_value=2.0 ** 2.5)
    plate_lin = op(unreal.MaterialExpressionMultiply, plate, comp, "RGB", "")
    out = e(unreal.MaterialExpressionLinearInterpolate)
    link(sky, "", out, "A")
    link(plate_lin, "", out, "B")
    link(msk, "", out, "Alpha")
    mel.connect_material_property(out, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.layout_material_expressions(m)
    mel.recompile_material(m)
    eas.save_loaded_asset(m)
    log("projection material built; plate camera basis F", F, "R", R, "U", U)
    return m


def stage_plate():
    # the plate must be the linear EXR (scene radiance): the PNG is already exposed/tonemapped and
    # would be exposed again (EV -2.5) through the emissive path -> near black
    exr = os.path.join(ROOT, "Renders", "plate", "L_Hero_Plate_LS_Plate_.0000.exr")
    png = os.path.join(ROOT, "Renders", "plate", "L_Hero_Plate_LS_Plate_PathTracer.0000.png")
    src = exr if os.path.exists(exr) else png
    t = unreal.AssetImportTask()
    t.filename = src
    t.destination_path = G + "/Textures"
    t.destination_name = "T_Plate_K0"
    t.automated = True
    t.replace_existing = True
    t.save = True
    at.import_asset_tasks([t])
    tex = unreal.load_asset(G + "/Textures/T_Plate_K0")
    if src.endswith(".exr"):
        tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_HDR)
        tex.set_editor_property("srgb", False)
    tex.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    tex.set_editor_property("address_x", unreal.TextureAddress.TA_CLAMP)
    tex.set_editor_property("address_y", unreal.TextureAddress.TA_CLAMP)
    eas.save_loaded_asset(tex)
    log("plate texture", src, "size", tex.blueprint_get_size_x(), tex.blueprint_get_size_y())
    mat = build_projection_material(tex)

    les.load_level(G + "/Maps/L_Hero_Hybrid")
    n = 0
    for a in actors.get_all_level_actors():
        if starts(label_of(a), PROXY_LABELS):
            c = a.static_mesh_component
            for i in range(c.get_num_materials()):
                c.set_material(i, mat)
            n += 1
    log("hybrid: projection material on", n, "proxy actors")
    les.save_current_level()


def flat_material(name, rgb):
    path = G + "/Materials/" + name
    if eas.does_asset_exist(path):
        eas.delete_asset(path)
    m = at.create_asset(name, G + "/Materials", unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property("two_sided", True)
    c = mel.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -300, 0)
    c.set_editor_property("constant", unreal.LinearColor(*rgb, 1))
    mel.connect_material_property(c, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(m)
    eas.save_loaded_asset(m)
    return m


def stage_layermap():
    """L_Hero_LayerMap: the hybrid level with flat colours per layer (scene breakdown image).
    white = real product, green = real 3D near set, orange = projected mid proxies, blue = projected far/sky."""
    duplicate_level(G + "/Maps/L_Hero_Hybrid", G + "/Maps/L_Hero_LayerMap")
    cols = {"product": flat_material("M_Layer_Product", (1.0, 1.0, 1.0)), "near": flat_material("M_Layer_Near", (0.05, 0.6, 0.15)),
            "mid": flat_material("M_Layer_Mid", (0.9, 0.35, 0.05)), "far": flat_material("M_Layer_Far", (0.05, 0.2, 0.9))}
    for a in actors.get_all_level_actors():
        l = label_of(a)
        if not hasattr(a, "static_mesh_component"):
            if l.startswith(("Key_", "Rim_", "Fill_", "Ledge_", "NearArch", "LoggiaLantern", "Moonlight")):
                actors.destroy_actor(a)   # unlit colours only
            continue
        key = ("product" if l.startswith("Product_") else "far" if l == "SkyDome" else "mid" if starts(l, PROXY_LABELS) else "near")
        c = a.static_mesh_component
        for i in range(c.get_num_materials()):
            c.set_material(i, cols[key])
    mask = find_actor("Product_CasanovaBauta")
    cam = make_camera("CAM_K0", K0_LOC, K0_AIM, FOCAL, 22.0, track=mask)
    make_sequence("LS_K0_LayerMap", cam)
    les.save_current_level()
    log("layer map level built")


if STAGE == "levels":
    stage_levels()
elif STAGE == "layermap":
    stage_layermap()
else:
    stage_plate()
with open(os.path.join(ROOT, "reports", "ue_hybrid_%s.txt" % STAGE), "w") as f:
    f.write("\n".join(REPORT))
