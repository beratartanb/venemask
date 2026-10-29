"""First UE pass: import the mask OBJ, report its bounds/axes and the APIs the build script needs."""
import os
import unreal

ROOT = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
LOG = os.path.join(ROOT, "reports", "ue_probe.txt")
lines = []


def log(*a):
    s = " ".join(str(x) for x in a)
    lines.append(s)
    unreal.log("[VENEMASK] " + s)


log("engine", unreal.SystemLibrary.get_engine_version())
for name in ["MaterialEditingLibrary", "StaticMeshEditorSubsystem", "MoviePipelineQueueSubsystem",
             "MoviePipelineDeferredPass_PathTracer", "MoviePipelinePIEExecutor", "LevelSequenceEditorBlueprintLibrary",
             "MoviePipelineAntiAliasingSetting", "MoviePipelineImageSequenceOutput_PNG", "MoviePipelineImageSequenceOutput_EXR",
             "CineCameraActor", "InterchangeGenericAssetsPipeline", "LevelEditorSubsystem"]:
    log("api", name, hasattr(unreal, name))
sm = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
log("set_nanite_settings", hasattr(sm, "set_nanite_settings"))

task = unreal.AssetImportTask()
task.filename = os.path.join(ROOT, "SourceAssets", "casanova_bauta", "casanova_bauta_segmented.obj")
task.destination_path = "/Game/Venemask/Products/CasanovaBauta"
task.destination_name = "SM_CasanovaBauta"
task.automated = True
task.replace_existing = True
task.save = True
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
log("imported", list(task.imported_object_paths))
mesh = unreal.load_asset("/Game/Venemask/Products/CasanovaBauta/SM_CasanovaBauta")
if mesh:
    b = mesh.get_bounding_box()
    log("bbox min", b.min, "max", b.max)
    for i, m in enumerate(mesh.static_materials):
        log("slot", i, m.material_slot_name, m.material_interface.get_path_name() if m.material_interface else None)
    log("tris lod0", sm.get_number_verts(mesh, 0))
with open(LOG, "w") as f:
    f.write("\n".join(lines))
