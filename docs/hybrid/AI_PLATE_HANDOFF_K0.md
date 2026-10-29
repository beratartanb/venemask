# K0 çevre plakası — harici görsel AI aracına teslim paketi

Tarih: 2026-10-29 · Kaynak: `L_Hero_Plate` (v6 sahnesi, yakın katman ve maske çıkarılmış), `CAM_Plate` (K0 konumu, 24 mm) · Üretim: `Scripts/ue_plate_aov.py` + `MRQ_AOV_Plate` / `MRQ_Seg_Plate` · Dosyalar **LOCAL ONLY** (`Renders/plate/` depoda yok).

## 1 · Dosyalar (`Renders/plate/handoff_K0/`)

| Dosya | İçerik | Kullanım |
|---|---|---|
| `K0_beauty_4096x2304_sRGB.png` | Path Tracer 512 spp, 24 mm, EV −2.5, sRGB PNG, **maskesiz/yazısız** | **Görsel AI aracına yüklenecek ana dosya** (image-to-image kaynağı: perspektif, kadraj, ışık yönü, renk sıcaklığı) |
| `K0_depth_lognorm_16bit.png` | Derinlik, 16 bit gri, yakın = beyaz. `v = 1 − log2(d/4 m)/log2(200)`; ters: `d = 4 m · 200^(1−v)` | Depth ControlNet / yapı kilidi. 8 bit kopya: `K0_depth_lognorm_8bit.png` |
| `K0_segmentation.png` | Düz renk bölütleme (aşağıdaki tablo) | Gökyüzü maskesi (inpaint/outpaint), semantik kontrol |
| `K0_normal_world.png` | Dünya normali (0.5 + 0.5·n) | İsteğe bağlı (normal ControlNet) |
| `K0_preview_board.png` | Dört görüntünün 2×2 önizlemesi | Kontrol |

Bölütleme renkleri (render sonrası ölçülen sRGB): gökyüzü **≈ (190, 36, 225)** mor · sıva cephe **(232, 0, 16)** kırmızı · taş/İstria **(192, 200, 208)** açık gri · pencere boşluğu (iç mekân) **(0, 200, 0)** yeşil · lamba/pencere camı turuncu (küçük alanlar) · ay sarı · ahşap/direk kahverengi. Plakada **su yok** (kanal, gerçek 3D yakın katmandadır); ufuk çizgisinin altı yalnız su yansımasında görünür.

## 2 · Kadraj ve sahne sabitleri (AI çıktısında korunacak)

- Kamera: 24 mm, sensör 36 × 20.25 mm → yatay FOV 73.7°, konum (−150, −75, 130) cm, hedef (11.6, −23.3, 120) cm; sahne Z-yukarı.
- Ufuk (uzak rıhtım su çizgisi): üstten **%45.7** (satır ≈ 1053 / 2304). Değişmemeli.
- 42 mm hero kadrajı plakanın **merkezî %57.1**'i: piksel kutusu x 878–3218, y 494–1810. Kalite önceliği bu kutu; dış halka K1/K2 paralaksında görünür.
- Ay: (%34.3, %24.3) küçük disk; ay ışığı soğuk (7200 K), pencereler/fenerler sıcak (2900 K). Işık yönü ve sıcaklıkları korunmalı (yakın 3D katman bu ışıkla aydınlatılıyor).
- Orta katman (palazzo blokları) hibrit sahnede **kendi geometrisine** projekte ediliyor: bina siluetleri, blok kenarları ve pencere sıraları `K0_segmentation.png` / depth ile **aynı yerde** kalmalı (kadraj genişliğinin ~%1'i içinde). Blok içi detay, doku, pencere tasarımı, çatı hattı süsü, uzak ışıklar, atmosfer, gökyüzü ve ay parlaması serbest.
- Yasak: maske, yazı/tabela, insan, gondol üzerinde yazı, logo, vinyet, letterbox, film greni, kırpma/zoom/kaydırma (kadraj birebir).

## 3 · Prompt önerisi

```
Cinematic night view of Venice from a stone quay, wide 24mm lens, moonlit Venetian palazzi across the Grand Canal,
gothic arched windows glowing warm candlelight, weathered plaster and Istrian stone facades, dome and campanile on the skyline,
cool blue moonlight from upper left, deep navy night sky, thin haze, photorealistic, ultra detailed matte painting, 8k
```
Negatif: `mask, text, letters, signage, watermark, people, boats with text, vignette, letterbox, film grain, blurry, cartoon`.
Image-to-image ayarı: yapı kilidi için denoise/strength **0.45–0.60** + depth ControlNet (ağırlık ~0.7); referans `references/02-venetian-hero-wide-space.jpeg` yalnızca stil (IP-Adapter/style ref), içerik değil.

## 4 · Çıktı özelliği

**4096 × 2304**, PNG, 8 bit RGB (16 bit de olur), **sRGB**, alfa yok, aynı kadraj. Araç daha küçük üretirse aracın kendi upscaler'ı ile 4096 × 2304'e çıkarılıp teslim edilmeli. Dosya adı: `Renders/plate/ai/K0_ai.png`.

## 5 · Teslim sonrası aktarım yolu (renk yönetimli)

PNG → linear EXR dönüşümü `Scripts/exr_tools.py` (saf Python, Unreal'in `python.exe`'si ile çalışır):

```
python Scripts/exr_tools.py stats   Renders/plate/ai/K0_ai.png
python Scripts/exr_tools.py png2exr Renders/plate/ai/K0_ai.png Renders/plate/ai/K0_ai.exr --lut reports/display_inverse_lut.json --match Renders/plate/handoff_K0/K0_beauty_4096x2304_sRGB.png
python Scripts/exr_tools.py stats   Renders/plate/ai/K0_ai.exr
```

- Çözme eğrisi: **projenin ölçülen ters görüntü dönüşümü** (`--lut`, `reports/display_inverse_lut.json`; `fitlut` ile scene-linear plaka EXR'si ve aynı karenin MRQ PNG'sinden piksel-hizalı fit, ortalama bağıl hata %2.5). Düz sRGB çözme bu projede **yanlış** olur: ton eğrisinin toe/shoulder'ı var (kod 25 → gerçek sahne değeri 0.0283, düz sRGB 0.0097 = 1.5 stop koyu; kod 255 → 11.1). Düz sRGB yalnız gerçekten sRGB-linear kaynaklar için (`--lut` olmadan).
- `--match`: AI görüntüsünün ortalama parlaklığını, aynı yöntemle çözülen render plakasına eşitler; uygulanan kazanç stop olarak yazdırılır (pozlama tahmin değil, ölçüm).
- Çıktı: yarım-float, sıkıştırmasız, B/G/R kanalları, **scene-linear** (MRQ_Plate_Lin plakalarıyla aynı uzay) → `ExposureComp = 2^2.5` (varsayılan, kalibre edildi). Unreal'e `TC_HDR`, sRGB kapalı, mip yok olarak alınır (`import_plate`).

Unreal entegrasyonu (önce yalnız K0, tek plaka):

```
set VM_STAGE=plate
set VM_PLATE_DIR=plate_lin
set VM_PLATES=K0
set VM_PLATE_K0=../plate/ai/K0_ai.exr
UnrealEditor-Cmd Venemask_Cinematic_Showroom.uproject -ExecutePythonScript=Scripts/ue_hybrid.py
Scripts/render.ps1 -Config MRQ_PT_K -Map L_Hero_Hybrid -Sequence LS_K0_Hybrid -WarmUp
Scripts/check_ai_plate.ps1 -Ai Renders/plate/ai/K0_ai.png        (hizalama/parlaklık kontrol levhası)
```

Görsel referansa yaklaşırsa K1/K2 plakaları **K0 çıktısından** türetilir (aynı araç, img2img düşük denoise, kaynak `Renders/plate/L_Hero_Plate_LS_Plate_K1_PathTracer.0000.png` / `_K2_`), bağımsız üretim yapılmaz.

## 6 · Teslim alınınca kontrol listesi

1. Boyut 4096 × 2304, alfa yok, kırpma/kaydırma yok (`check_ai_plate.ps1`: bölütleme kenarları AI görüntüsü üzerine bindirilir).
2. Ufuk satırı %45.7 ± %0.5; bina blok kenarları bölütlemeyle çakışık.
3. `stats` ile ortalama parlaklık ve kanal dengesi; `--match` kazancı ±1 stop içinde olmalı (değilse pozlama/renk sıcaklığı yanlış üretilmiş demektir).
4. Maske/yazı/insan yok (gözle).
5. Hibrit K0 render'ı v6 ve referansla aynı ölçekte karşılaştırılır (`compare_fourway.ps1`); yakın 3D katman, maske ve ışıklar değişmemiş olmalı.
