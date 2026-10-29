# GATE A — FAIL (referans sınıfına henüz ulaşmadı)

- **Tarih:** 2026-10-29
- **Proje:** `C:\Users\berat\Documents\Venemask_Cinematic_Showroom\Venemask_Cinematic_Showroom.uproject` (UE 5.8.1, ayrı proje; oyun projesine dokunulmadı)
- **Level / sekans:** `/Game/Venemask/Maps/L_Hero`, `/Game/Venemask/Cinematics/LS_Hero`
- **Render config:** `/Game/Venemask/Cinematics/Render/MRQ_PT` (Path Tracer, 256 spp, OIDN), `MRQ_AOV`, `MRQ_Lumen`
- **Render dosyaları:** `Renders/gateA/hero_v5_pathtracer_1920.png` + `.exr`, `hero_v5_worldnormal.png`, `hero_v5_depth.png`, `hero_v5_productmatte.png`, `hero_v5_aov_multilayer.exr`, `hero_v5_lumen_preview.png`
- **Karşılaştırma sayfası:** `reports/gate-A.html`
- **Referanslar:** `references/01-multi-mask-room-and-product-showcase.jpeg`, `references/02-venetian-hero-wide-space.jpeg` (yalnızca sanat yönü)

## Ürün
- Casanova Bauta Mask - Eyes Wide Shut Inspired · Shopify id 7591523549267 · variant 42664065106003 · SKU 17629779130_3E08 · 3799.00 · handle `casanova-mask-bauta-mask-venetian-mask`
- Kaynak mesh: `Documents/Codex/2026-10-02/mas/outputs/casanova bauta_3.stl` (su geçirmez, 556k üçgen, 301×137×258 mm) → `SourceAssets/casanova_bauta/casanova_bauta_segmented.obj`
- Manifest: `reports/mask_asset_manifest.csv`

## Kamera / sahne
Cine Camera 60 mm, 36×20.25 mm sensör, f/4, odak 142 cm, göz hizasında; maske ıslak taş korkuluk üzerinde, taş payeye 12° yaslı. Spot key 2900 K, spot rim 2400 K, soğuk fill 8000 K, karşı kıyıda 2200 K fenerler, gece gökyüzü, kanal yansımaları. Manuel pozlama.

## Doğrulanan
- Geometri birebir (şekil değiştirilmedi; yalnızca boya sınırlarında yüzey üzerinde üçgen bölme).
- Boya bölgeleri ürün fotoğraflarıyla uyumlu; bukle sınırı ölçülen derinlikle.
- Path Tracer'da tam geometri (Nanite kapalı — fallback mesh burun/buklelerde köşelenme yapıyordu).
- Temas gölgesi/yansıması, bokeh ve su yansımaları fiziksel.

## Eksik / UNVERIFIED
- Altın kumaş örgü şerit STL'de yok → boyalı bant yaklaşımı.
- Craquelure prosedürel.
- Taş, su ve mimari dokular prosedürel; taranmış malzeme yok.
- Arka plan mimarisi blokaj seviyesinde.

## Karar
**FAIL.** Ürün doğruluğu ve fiziksel ışık kurulumu kabul edilebilir; ortam zenginliği ve yüzey malzemeleri referans sınıfında değil. Aşama 2'ye ve Shopify'a geçilmedi.
