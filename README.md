# Venemask — Cinematic Showroom

A separate Unreal Engine 5.8 project for the Venemask cinematic store experience. Order of work: (1) one correct product + hero render → (2) camera route → (3) Shopify.

## Current status: Gate A — FAIL
- Report: [reports/gate-A.md](reports/gate-A.md) · side-by-side comparison: [reports/gate-A.html](reports/gate-A.html)
- Hero render (Path Tracer, 1920×1080): [Renders/gateA/hero_v5_pathtracer_1920.png](Renders/gateA/hero_v5_pathtracer_1920.png)
- Product: Casanova Bauta Mask — Eyes Wide Shut Inspired (Shopify id 7591523549267) · [reports/mask_asset_manifest.csv](reports/mask_asset_manifest.csv)
- Reference analysis: [reports/reference_analysis.md](reports/reference_analysis.md)

## Rebuilding
Not in the repo: Unreal `Content/`, the STL/OBJ meshes and the generated textures. The scripts regenerate them:
1. `Scripts/prep_mask.py` (STL → segmented OBJ), `Scripts/gen_stone.py`, `Scripts/gen_textures.py`
2. `UnrealEditor-Cmd <uproject> -ExecutePythonScript=Scripts/ue_build_hero.py`
3. `UnrealEditor-Cmd <uproject> -ExecutePythonScript=Scripts/ue_make_configs.py`
4. `Scripts/render.ps1 -Config MRQ_PT`
