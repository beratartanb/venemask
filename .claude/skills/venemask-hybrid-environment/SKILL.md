---
name: venemask-hybrid-environment
description: Improve Venemask Unreal Gate A hero's environment with physically grounded foreground 3D, camera-projected midground and verified AI panorama/multi-view background, preserving exact product fidelity and testing motion parallax.
---

# Venemask hybrid scene environment

Use this skill when the Venemask Cinema Showroom scene reaches a visual-quality bottleneck in distant architecture, near-stone material realism, or atmospheric depth. The latest known baseline is Gate A round 2 (v6), `c5ed36f9`, report `reports/gate-A.md`, status **FAIL**.

## Non-negotiables

- Read `CLAUDE.md`, `CLAUDE_MAIN_PROMPT.md`, latest `reports/gate-A.md`, and real side-by-side render artifacts before any change.
- Preserve exact Casanova Bauta STL topology, mesh orientation, paint-region segmentation, braid geometry and product truth. Do not give the product AI-generated feathers, gems, outlines, paint or altered geometry.
- Keep real near geometry for contact shadow, mask support, floor/ledge, close water and true reflections.
- Do not overwrite `Renders/gateA/hero_v6_*` or edit the user's Sphirus World game project. Use a new feature branch, experiment level or separate `Renders/gateA_hybrid/` artifacts.
- Do not fetch paid assets or start paid third-party jobs without user approval.

## Environment separation

1. Near: Unreal geometry + authored/PBR material matching, shadow/reflection.
2. Middle: minimal meaningful architectural volumes + camera-projected matte or Composure plate, with camera-correct perspective and occluder masks. Validate current Composure version; Unreal 5.8 feature is Experimental.
3. Far: 360 equirectangular skybox or matte painting. 360 provides angular coverage around its capture point, *not translational parallax*.
4. Alternative: test spatial world synthesis (e.g. World Labs Marble) in a standalone proof only when licensing, export format and Unreal compatibility are verified.
5. Meshy is acceptable for non-product test props/blockout; do not use it to generate the real mask or final precision surfaces.

## Proof before rollout

- Recreate v6 baseline K0 camera pose and two constrained new poses K1/K2; identify their transforms and permissible parallax envelope.
- Render full-geometry baseline and hybrid A/B at identical lens, exposure and resolution.
- QA silhouette, mask texture, real braid material, contact, stone micro-detail, water reflection, architectural perspective, projected occlusion, seams, shadow consistency and light-source directions.
- Compare reference, baseline and hybrids at each camera pose and midpoints of short camera move. FAIL if improvement only holds for static K0 but breaks K1/K2.
- Save beauty + depth/normal/product matte + scene breakdown images + clear PASS/FAIL/BLOCKED report.
- Ask for approval to move from Gate A to camera journeys and later Shopify. No premature global website development.

## State and metadata

- Latest v6 report created braid GEOMETRY, but the thread/material remains UNVERIFIED. Keep these states separate.
- `reports/mask_asset_manifest.csv` may still describe the earlier painted-band fallback; reconcile against v6 reality.
- Check Shopify product price/currency live before inserting product metadata into any report or site. Product details must not be invented.
- Document whether `Content/`, mesh and rendered EXR assets are local-only versus committed; never claim a clean clone reproduces missing files.
