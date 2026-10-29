---
name: venemask-unreal-cinematics
description: Unreal Engine'de ayrı Venemask showroom projesi kurmak, sahne, kamera, Sequencer ve Movie Render Queue / Path Tracer üretmek için kullan.
---
# Unreal Cinematic Showroom

Official references:
- https://dev.epicgames.com/documentation/unreal-engine/cinematics-and-movie-making-in-unreal-engine
- https://dev.epicgames.com/documentation/unreal-engine/camera-jibs-and-dollies-in-unreal-engine
- https://dev.epicgames.com/documentation/unreal-engine/movie-render-pipeline-in-unreal-engine
- https://dev.epicgames.com/documentation/unreal-engine/path-tracer-in-unreal-engine
- https://dev.epicgames.com/documentation/unreal-engine/scripting-the-unreal-editor-using-python

## Scope & environment
Use a standalone `Venemask_Cinematic_Showroom` Unreal project; never alter the user's game world project as a shortcut. Inspect installed UE version, source assets, GPU capability, renderer settings and plugin status before writing automation. Scripting available only through properly enabled editor Python and/or verified integration, not imagined remote access.

## Scene pipeline
1. **Source registry**: identify product files and approved textures. Record 3D file provenance.
2. **Blockout**: real dimensions of masks, stone plinths, canal/terrace distances. Place 4-5 products in physical depth so initial hero reads clearly.
3. **Materials & lighting**: realistic stone, water, metal and fabric. Accurate contact and reflected light. Volumetrics only when physically justified. Hero must remain legible at mobile crop.
4. **Cine Camera**: specify sensor/focal length, f-stop/focus distance; Sequencer Level Sequence, Camera Rig Rail / spline, tracked points of interest. Tangents/dolly curves designed for comfort; not fast sweeping or unnatural banking. Add focus/exposure keyframes, check each route interval.
5. **Render**: validate renderer support on installed UE. Use MRQ or MRG for EXR/PNG frame output, save configuration and color pipeline. Path Tracer where supported and worth cost; check hair/feather, transparent materials, denoiser artifacts and temporal stability.
6. **Web master**: render in separate desktop and mobile compositions (do not assume cropping), include poster/keyframes and timeline manifest with actual frame offsets.

## Camera beats
A: Hero 4–5 masks; B: camera physically glides into collection wing; C: move to Best Sellers and visit distinct sculptures; D: another space for New Arrivals; E: dolly closer to selected mask. Reversibility and position persistence mandatory. The subject may not morph into a different product mid-shot.

## Proof
Deliver `.uproject`, level asset paths, actual LevelSequence asset, Movie Render config, source .exr/.png frame names, 3–5 stills at key moments, screen-recorded Sequencer scrub and QA notes. Do not claim a scene or render exists if editor wasn't opened or render wasn't produced.
