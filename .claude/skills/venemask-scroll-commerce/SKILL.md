---
name: venemask-scroll-commerce
description: Unreal sinematik kamera çıktısını kaydırmayla kontrol edilen mobil uyumlu Shopify Liquid tema deneyimine bağlamak ve gerçek alışveriş işlevlerini korumak için kullan.
---
# Scroll-Driven Shopify Cinema

References:
- https://gsap.com/docs/v3/Plugins/ScrollTrigger/
- https://gsap.com/docs/v3/HelperFunctions/helpers/imageSequenceScrub/
- https://shopify.dev/docs/storefronts/themes/tools/cli
- https://shopify.dev/docs/api/shopify-cli/theme/theme-dev
- https://shopify.dev/docs/api/shopify-cli/theme/theme-push

## Technology decision
First choose by measured iOS Safari QA, not preference alone:
- frame sequence with poster + chunked/lazy image fetching + scroll scrub;
- encoded video with seek tests, respecting iOS decoding latency;
- hybrid of high-quality prerender cinematics, anchored DOM overlays, and restrained pointer parallax.
Pre-rendered film cannot provide arbitrary 360° real-time camera control. Disclose exact interactive degrees of freedom. If true full camera orbit is required, evaluate a separate WebGL 3D asset/LOD budget.

## Shopify contract
- Pull from actual store and unpublished backup theme. Use native sections / snippets / assets and product objects; support customization in Shopify theme editor. Avoid destructively replacing user's existing header, checkout, product variants, money formatting, Shopify Markets, reviews or cart drawer.
- Real product titles, variants, prices and item links come from Shopify. Product-list event click must always resolve to the correct SKU/variant.
- Overlay text and button UI remains accessible HTML, NOT baked into cinematic frames. Search, collections, cart and account remain operational.
- Hero renders immediately as a still poster while the scroll sequence preloads progressively. Responsive canvas, CSS safe areas and current Safari behavior validated.
- If media can't load, text, links, product listing and add-to-cart remain available.
- Respect `prefers-reduced-motion`, keyboard access, focus, touch and natural mobile scrolling. Prevent scroll hijacking, captive scrolling or touch-swipe vs vertical-scroll conflict.
- Verify store-specific Theme Check, performance budget (LCP, CLS, total transfer), browser console, mobile frame drops and iPhone real-device results.

## Non-negotiable QA
Check at 0/15/30/50/70/85/100% scroll; pause mid-transition; reverse; change collection while hovering; new arrivals->product detail->back; test all product names and prices; add-to-cart and variants without altering checkout. Store remains UNPUBLISHED unless user explicitly authorizes.
