---
name: venemask-visual-qa
description: Venemask sahne render ve Shopify ekranları için kanıta dayalı görsel kalite testleri, karşılaştırma ve aşama geçiş PASS/FAIL kararı verirken kullan.
---
# Venemask Visual QA & Stage Gates

The goal is to stop false completion. Progress is not a substitute for source/reference comparison. Code compiles != frame is cinematic.

## Compare visually
Source references: `references/01-multi-mask-room-and-product-showcase.jpeg`, `references/02-venetian-hero-wide-space.jpeg`.
- Match viewport, crop, focal point, object occupancy and color space before judgment.
- Show original product photo and rendered product at comparable angle in a distinct comparison (reference artistic inspiration is different from item identity truth).
- Review: mask exactness, lens, negative space, light bounce, contact shadow, physical object geometry, material response, background depth, color mood, compositional restraint, readable UI.
- Artifact identity and accurate pricing are hard gates. Never accept an image-generation guess as a real product.

## Gates
- Gate A first product + one hero beauty render: required render file, product match evidence, user-review candidate. Fail if decorated background + pasted photo, fake mask, clipping, shape change or visual density mismatch.
- Gate B full hero 4–5 real models + Sequencer camera path: stills at route checkpoints + reverse scrub recording. Fail if slideshow, teleports, unreal camera jump or isolated photo panels.
- Gate C mobile web proof: actual test build, rendered browser screenshots and screen capture; video/frame scrubbing forward/back; reduced-motion fallback; memory/performance report. Fail if only static UI images.
- Gate D Shopify end-to-end: unpublished preview + correct catalog data, cart/variant flow, all key pages, regression for Safari safe areas and product sticky/chat UI. No publishing without permission.

## Output contract
For each gate write `reports/gate-A.md` etc with: source file path; actual render/screenshot paths; viewport; current build hash or commit; what was tested; screenshot comparison notes; P0/P1/P2 issues; PASS/FAIL and unresolved blockers. If no browser/editor access, say BLOCKED (not PASS). Explicitly ask for only missing essential source artifacts, not preferences already answered.
