"""Create Movie Render Queue config assets for command-line rendering.

  UnrealEditor-Cmd <uproject> -ExecutePythonScript=Scripts/ue_make_configs.py
Env VM_CONFIGS = "name:mode:spp:WxH:tag;..." (mode pt | lumen | aov); default set below.
Render with Scripts/render.ps1 (UnrealEditor -game -RenderOffscreen -MoviePipelineConfig=...).
"""
import os
import unreal

ROOT = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
DEST = "/Game/Venemask/Cinematics/Render"
at = unreal.AssetToolsHelpers.get_asset_tools()
eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)

DEFAULT = ("MRQ_Lumen:lumen:8:1600x900:lumen_preview;MRQ_PT:pt:256:1920x1080:pt_beauty;MRQ_AOV:aov:8:1920x1080:aov;"
           # hybrid test set: plate (wide, high spp), K-pose stills (named by level + sequence), camera-move sequences
           "MRQ_Plate:pt:512:4096x2304:plate:1;MRQ_PT_K:pt:256:1920x1080:gateA_hybrid/stills:1;"
           "MRQ_AOV_K:aov:8:1920x1080:gateA_hybrid/aov:1;MRQ_PT_Move:pt:96:1280x720:gateA_hybrid/move:48")


def make(name, mode, spp, res, tag, frames="1"):
    w, h = (int(v) for v in res.split("x"))
    path = DEST + "/" + name
    if eas.does_asset_exist(path):
        eas.delete_asset(path)
    cfg = at.create_asset(name, DEST, unreal.MoviePipelinePrimaryConfig, unreal.MoviePipelinePrimaryConfigFactory())

    o = cfg.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting)
    o.output_resolution = unreal.IntPoint(w, h)
    o.output_directory = unreal.DirectoryPath(os.path.join(ROOT, "Renders", tag.replace("/", os.sep)))
    o.file_name_format = "{level_name}_{sequence_name}_{render_pass}.{frame_number}"
    o.override_existing_output = True
    o.use_custom_playback_range = True
    o.custom_start_frame = 0
    o.custom_end_frame = int(frames)

    aa = cfg.find_or_add_setting_by_class(unreal.MoviePipelineAntiAliasingSetting)
    aa.override_anti_aliasing = True
    aa.anti_aliasing_method = unreal.AntiAliasingMethod.AAM_NONE if mode == "pt" else unreal.AntiAliasingMethod.AAM_TEMPORAL_AA
    aa.spatial_sample_count = int(spp)
    aa.temporal_sample_count = 1
    aa.engine_warm_up_count = 64
    aa.render_warm_up_count = 32

    gs = cfg.find_or_add_setting_by_class(unreal.MoviePipelineGameOverrideSetting)
    gs.cinematic_quality_settings = True
    gs.texture_streaming = unreal.MoviePipelineTextureStreamingMethod.FULLY_LOAD

    cv = cfg.find_or_add_setting_by_class(unreal.MoviePipelineConsoleVariableSetting)
    for k, v in {"r.PathTracing.MaxBounces": 12, "r.PathTracing.Denoiser": 1, "r.DepthOfFieldQuality": 4}.items():
        cv.add_or_update_console_variable(k, v)

    if mode == "pt":
        cfg.find_or_add_setting_by_class(unreal.MoviePipelineDeferredPass_PathTracer)
        cfg.find_or_add_setting_by_class(unreal.MoviePipelineImageSequenceOutput_PNG)
        cfg.find_or_add_setting_by_class(unreal.MoviePipelineImageSequenceOutput_EXR)
    else:
        dp = cfg.find_or_add_setting_by_class(unreal.MoviePipelineDeferredPassBase)
        if mode == "aov":
            mats = []
            for p in ("/Game/Venemask/Materials/M_PP_WorldNormal.M_PP_WorldNormal",
                      "/Game/Venemask/Materials/M_PP_ProductMatte.M_PP_ProductMatte",
                      "/MovieRenderPipeline/Materials/MovieRenderQueue_WorldDepth.MovieRenderQueue_WorldDepth"):
                pp = unreal.MoviePipelinePostProcessPass()
                pp.enabled = True
                pp.material = unreal.load_asset(p)
                mats.append(pp)
            dp.set_editor_property("additional_post_process_materials", mats)
            cfg.find_or_add_setting_by_class(unreal.MoviePipelineImageSequenceOutput_EXR)
        cfg.find_or_add_setting_by_class(unreal.MoviePipelineImageSequenceOutput_PNG)
    eas.save_loaded_asset(cfg)
    unreal.log("[VENEMASK] config %s mode=%s spp=%s %s -> Renders/%s" % (path, mode, spp, res, tag))


for spec in os.environ.get("VM_CONFIGS", DEFAULT).split(";"):
    make(*spec.split(":"))
