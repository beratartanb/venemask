"""Render LS_Hero through Movie Render Queue, then quit the editor.

Run with the full editor (MRQ PIE executor needs a viewport):
  UnrealEditor <uproject> -ExecutePythonScript=Scripts/ue_render.py
Env:
  VM_MODE  pt   = Path Tracer beauty (PNG + EXR)
           aov  = deferred pass with world normal / depth / product matte post-process passes
           lumen= deferred Lumen beauty (fast preview)
  VM_SPP   path tracer samples per pixel (spatial samples), default 256
  VM_RES   WxH, default 1920x1080
  VM_TAG   output sub-folder name
"""
import os
import unreal

ROOT = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
MODE = os.environ.get("VM_MODE", "pt")
SPP = int(os.environ.get("VM_SPP", "256"))
W, H = (int(v) for v in os.environ.get("VM_RES", "1920x1080").split("x"))
TAG = os.environ.get("VM_TAG", MODE)
OUT = os.path.join(ROOT, "Renders", TAG)
os.makedirs(OUT, exist_ok=True)

qs = unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem)
queue = qs.get_queue()
queue.delete_all_jobs()
job = queue.allocate_new_job(unreal.MoviePipelineExecutorJob)
job.sequence = unreal.SoftObjectPath("/Game/Venemask/Cinematics/LS_Hero.LS_Hero")
job.map = unreal.SoftObjectPath("/Game/Venemask/Maps/L_Hero.L_Hero")
job.job_name = "Hero_" + TAG
cfg = job.get_configuration()

o = cfg.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting)
o.output_resolution = unreal.IntPoint(W, H)
o.output_directory = unreal.DirectoryPath(OUT)
o.file_name_format = "{sequence_name}_{render_pass}.{frame_number}"
o.override_existing_output = True
o.use_custom_playback_range = True
o.custom_start_frame = 0
o.custom_end_frame = 1

aa = cfg.find_or_add_setting_by_class(unreal.MoviePipelineAntiAliasingSetting)
aa.override_anti_aliasing = True
aa.anti_aliasing_method = unreal.AntiAliasingMethod.AAM_NONE if MODE == "pt" else unreal.AntiAliasingMethod.AAM_TEMPORAL_AA
aa.spatial_sample_count = SPP if MODE == "pt" else 8
aa.temporal_sample_count = 1
aa.engine_warm_up_count = 64
aa.render_warm_up_count = 32

gs = cfg.find_or_add_setting_by_class(unreal.MoviePipelineGameOverrideSetting)
gs.cinematic_quality_settings = True
gs.texture_streaming = unreal.MoviePipelineTextureStreamingMethod.FULLY_LOAD

cv = cfg.find_or_add_setting_by_class(unreal.MoviePipelineConsoleVariableSetting)
for k, v in {"r.PathTracing.MaxBounces": 12, "r.PathTracing.Denoiser": 1, "r.DepthOfFieldQuality": 4,
             "r.Lumen.HardwareRayTracing": 1, "r.ScreenPercentage": 100}.items():
    cv.add_or_update_console_variable(k, v)

if MODE == "pt":
    cfg.find_or_add_setting_by_class(unreal.MoviePipelineDeferredPass_PathTracer)
    cfg.find_or_add_setting_by_class(unreal.MoviePipelineImageSequenceOutput_PNG)
    exr = cfg.find_or_add_setting_by_class(unreal.MoviePipelineImageSequenceOutput_EXR)
else:
    dp = cfg.find_or_add_setting_by_class(unreal.MoviePipelineDeferredPassBase)
    if MODE == "aov":
        mats = []
        for path in ("/Game/Venemask/Materials/M_PP_WorldNormal.M_PP_WorldNormal",
                     "/Game/Venemask/Materials/M_PP_ProductMatte.M_PP_ProductMatte",
                     "/MovieRenderPipeline/Materials/MovieRenderQueue_WorldDepth.MovieRenderQueue_WorldDepth"):
            pp = unreal.MoviePipelinePostProcessPass()
            pp.enabled = True
            pp.material = unreal.load_asset(path)
            mats.append(pp)
        dp.set_editor_property("additional_post_process_materials", mats)
    cfg.find_or_add_setting_by_class(unreal.MoviePipelineImageSequenceOutput_PNG)
    if MODE == "aov":
        cfg.find_or_add_setting_by_class(unreal.MoviePipelineImageSequenceOutput_EXR)


def finished(executor, success):
    unreal.log("[VENEMASK] render finished success=%s -> %s" % (success, OUT))
    with open(os.path.join(OUT, "render_done.txt"), "w") as f:
        f.write("success=%s mode=%s spp=%d res=%dx%d\n" % (success, MODE, SPP, W, H))
    unreal.SystemLibrary.quit_editor()


EXECUTOR = None
_ticks = {"n": 0, "handle": None}


def start_when_idle(dt):
    # Starting PIE from -ExecutePythonScript while the editor is still finishing start-up
    # tears PIE down immediately ("PIE Ended while Movie Pipeline was still active").
    global EXECUTOR
    _ticks["n"] += 1
    if _ticks["n"] < 240:
        return
    unreal.unregister_slate_post_tick_callback(_ticks["handle"])
    EXECUTOR = unreal.MoviePipelinePIEExecutor()
    EXECUTOR.on_executor_finished_delegate.add_callable_unique(finished)
    qs.render_queue_with_executor_instance(EXECUTOR)
    unreal.log("[VENEMASK] render queued mode=%s spp=%d" % (MODE, SPP))


_ticks["handle"] = unreal.register_slate_post_tick_callback(start_when_idle)
