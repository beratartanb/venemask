# Venemask — Cinematic Showroom

A separate Unreal Engine 5.8 project for the Venemask cinematic store experience. Order of work: (1) one correct product + hero render → (2) camera route → (3) Shopify.

## Gate A-HYBRID round 2.2: far layer was 2 stops dark (tone-curved EXR projected and tone-mapped again) → scene-linear plates; 3-band ghosting check; K0 AI handoff package ready
- Hand-off for the external image tool: [docs/hybrid/AI_PLATE_HANDOFF_K0.md](docs/hybrid/AI_PLATE_HANDOFF_K0.md) (files in [Renders/plate/handoff_K0/](Renders/plate/handoff_K0/)) · PNG→EXR with the measured inverse display transform: [Scripts/exr_tools.py](Scripts/exr_tools.py), [reports/display_inverse_lut.json](reports/display_inverse_lut.json)
- Diagnosis boards: [k1_exposure_diagnosis.png](Renders/gateA_hybrid/k1_exposure_diagnosis.png) · [move_rightband_crops.png](Renders/gateA_hybrid/move_rightband_crops.png) · updated [move_diff.png](Renders/gateA_hybrid/move_diff.png), [compare_fourway_K012.png](Renders/gateA_hybrid/compare_fourway_K012.png), [web preview](Renders/gateA_hybrid/web/index.html)

## Gate A-HYBRID round 2.1: plate weights corrected (pose plate = 100 %), blend measured against v6 per frame; AI plate still BLOCKED
- Weight table: [reports/plate_weights.txt](reports/plate_weights.txt) · per-frame far-layer difference vs v6: [move_diff.png](Renders/gateA_hybrid/move_diff.png)

## Gate A-HYBRID round 2: K1 fixed with 3-plate projection; AI plate BLOCKED (no image tool/access); quality jump FAIL
- Four-way K0/K1/K2: [compare_fourway_K012.png](Renders/gateA_hybrid/compare_fourway_K012.png) · complete camera-test web preview: [Renders/gateA_hybrid/web/index.html](Renders/gateA_hybrid/web/index.html)

## Gate A-HYBRID (round 1): projection pipeline PASS at K0/K2, FAIL at K1; AI panorama / World Labs BLOCKED
- Report: [reports/gate-A-hybrid.md](reports/gate-A-hybrid.md) · page: [reports/gate-A-hybrid.html](reports/gate-A-hybrid.html)
- K0/K1/K2 board: [Renders/gateA_hybrid/compare_K012_v6_vs_hybrid.png](Renders/gateA_hybrid/compare_K012_v6_vs_hybrid.png) · layer map: [scene_layer_map.png](Renders/gateA_hybrid/scene_layer_map.png)
- Price corrected: 124.99 USD (US market) / 3799.00 TRY (Türkiye market), see the manifest.

## Gate A — FAIL (round 2, v6)
- Report: [reports/gate-A.md](reports/gate-A.md) · side-by-side page: [reports/gate-A.html](reports/gate-A.html)
- Hero render (Path Tracer, 1920×1080): [Renders/gateA/hero_v6_pathtracer_1920.png](Renders/gateA/hero_v6_pathtracer_1920.png)
- Comparisons at equal scale: [compare_reference_v6.png](Renders/gateA/compare_reference_v6.png) · [compare_product_v6.png](Renders/gateA/compare_product_v6.png) · [compare_detail_v6.png](Renders/gateA/compare_detail_v6.png)
- Product: Casanova Bauta Mask — Eyes Wide Shut Inspired (Shopify id 7591523549267) · [reports/mask_asset_manifest.csv](reports/mask_asset_manifest.csv)
- Reference analysis: [reports/reference_analysis.md](reports/reference_analysis.md)

## Rebuilding
Not in the repo: Unreal `Content/`, the STL/OBJ meshes and the generated textures. The scripts regenerate them:
1. `Scripts/prep_mask.py` (STL → segmented OBJ), `Scripts/gen_braid.py` (gold trims on the STL edges), `Scripts/gen_stone.py`, `Scripts/gen_arch.py` (arches, columns, cornices, bridge, mooring poles), `Scripts/gen_textures.py`
2. `UnrealEditor-Cmd <uproject> -ExecutePythonScript=Scripts/ue_build_hero.py`
3. `UnrealEditor-Cmd <uproject> -ExecutePythonScript=Scripts/ue_make_configs.py`
4. `Scripts/render.ps1 -Config MRQ_PT`

## Art direction v2 — reset (29 Oct 2026): v6/hybrid kept as technical prototypes, new design starts from the references; image generation BLOCKED
- Brief, chosen real mask (La Regina Nera, 299.99 USD / 7899 TRY; no source model on disk) and the exact inputs needed for real image generation: [docs/art_direction/AD_v2_brief.md](docs/art_direction/AD_v2_brief.md)
- Equal-scale board, references vs current prototypes (no new design column yet): [Renders/artdir_v2/compare_refs_vs_v6.png](Renders/artdir_v2/compare_refs_vs_v6.png)
