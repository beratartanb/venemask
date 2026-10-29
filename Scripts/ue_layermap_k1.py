"""Add the K1 and K2 cameras to L_Hero_LayerMap (layer-colour debug level) so the hybrid can be
checked per layer at every pose:  UnrealEditor-Cmd <uproject> -ExecutePythonScript=Scripts/ue_layermap_k1.py
then render.ps1 -Config MRQ_Lumen -Map L_Hero_LayerMap -Sequence LS_K1_LayerMap"""
import os
import sys
import unreal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["VM_STAGE"] = "none"
import ue_hybrid as H   # noqa: E402

H.les.load_level(H.G + "/Maps/L_Hero_LayerMap")
mask = H.find_actor("Product_CasanovaBauta")
for pose in ("K1", "K2"):
    for a in H.actors.get_all_level_actors():
        if H.label_of(a) == "CAM_" + pose:
            H.actors.destroy_actor(a)
    loc, aim = H.POSES[pose]
    cam = H.make_camera("CAM_" + pose, loc, aim, H.FOCAL, 22.0, track=mask)
    H.make_sequence("LS_%s_LayerMap" % pose, cam)
H.les.save_current_level()
