# Venemask — Cinematic Showroom

A separate Unreal Engine 5.8 project for the Venemask cinematic store experience. Order of work: (1) one correct product + hero render → (2) camera route → (3) Shopify.

## Gate A-HYBRID (round 3): projection pipeline PASS at K0/K2, FAIL at K1; AI panorama / World Labs BLOCKED
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
