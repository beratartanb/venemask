---
name: venemask-mask-fidelity
description: Gerçek Venemask maskelerini STL/3MF ve fotoğraflardan geometrik ve görsel sadakatle 3D sahne ürünü yapmak ve yanlış maske üretimini engellemek için kullan.
---
# Product Fidelity / Hero Asset Gate

Original products are sold at `venemask.com`. Original photo + shop SKU/handle is the identity source. Reference *concept* images are not products.

## Asset intake
For each mask create an asset entry with: Shopify product id and URL, exact public product name, SKU/variant when relevant, base geometry file path (STL/3MF/FBX/OBJ/GLB), photos for front/left/right/back/detail, approved target mesh, materials and jewelry, whether finished-product details such as feathers/straps/gems are included in geometry, and review status.

- Prefer actual original 3D geometry from fabrication, not generative image-to-3D. STL alone normally has geometry but no reliable color/material/ornaments. Don't infer the final varnish or attachments from STL.
- Normalize scale and axes, inspect normals/UVs, preserve eye cutouts, strap attach points, relief, thickness and decorations. Never "improve" mask symmetry or reshape the product to resemble the fictional reference.
- Build accurate PBR materials from final-object photo evidence: acrylic painted parts, metallic foil, glaze, matte print, jewelry/pearls, natural feathers, fabrics. If physically accurate geometry for decorations is missing, mark the detail as unverified and request evidence rather than claiming fidelity.
- Use an overlay or image-registration comparison of finished real-product photos vs rendered mask views. Record angle, focal length, object scale, gross silhouette, color/value, relief and ornament checkpoints. Do not compare mismatched camera angles and claim 100% fidelity.
- If user provides only one photograph, stage it with limited changes and no unseen-angle orbit. The source photo may be used as a supervised photocomposite, but not as a free rotating 3D model.
- Do not use non-existent masks, fake names/prices/reviews, or unrelated model photographs. Distinguish masks sold together/bundles from single items.

## Deliverables
`mask_asset_manifest.csv`; native model/material files; 4-view reference board; side-by-side visual QA; ACCEPTED/UNVERIFIED state per product. A mask is cleared for final showroom placement only after product-identity approval.
