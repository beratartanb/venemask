# GATE A-HYBRID — hibrit çevre denemesi (v6 üzerine)

## Tur 2.1 — plaka ağırlıkları düzeltmesi ve AI çevre durumu (29 Ekim 2026, gece)

**Plaka karışımı hatası (doğrulandı, düzeltildi).** Tur 2'deki `w = 1/(d²+1)` (d metre) ile K1'de K1 plakası yalnızca **%38.2** taşıyordu (K0 %31.8, K2 %30.0); "tek plaka baskın" ifadesi yanlıştı. Yeni ağırlık `w = 1/(d⁴ + 1e-6)`, normalize. Ölçülen paylar (`Scripts/plate_weights.py` → `reports/plate_weights.txt`):

| Kamera konumu | K0 plakası | K1 plakası | K2 plakası |
|---|---|---|---|
| K0 | **100.0 %** | 0.0 % | 0.0 % |
| K1 | 0.0 % | **100.0 %** | 0.0 % |
| K2 | 0.0 % | 0.0 % | **100.0 %** |
| K0→K1 %25 / %50 / %75 | 98.8 / 47.3 / 1.2 % | 1.2 / 47.3 / 98.8 % | ~0 / 5.5 / ~0 % |
| K1→K2 %25 / %50 / %75 | 1.1 / 21.6 / 1.3 % | 98.6 / 39.2 / 1.3 % | 0.3 / 39.2 / 97.4 % |

Kamera noktalarında doğru plaka %100; ara hareketlerde iki plaka yalnızca orta noktalar civarında karışır. Karışımın hayalet üretip üretmediği **ölçüldü**: `Scripts/move_diff.ps1`, 48 karenin her birinde uzak katman bandında (üst %45, sol %58; maske ve paye dışarıda) hibrit ile v6 tam geometri arasındaki ortalama mutlak fark (`Renders/gateA_hybrid/move_diff.csv`, `move_diff.png`). Sonuçlar aşağıda "Tur 2.1 ölçüm" bölümünde.

**AI çevre görüntüsü — hâlâ BLOCKED.** Bu turda yeni altyapı denemesi yapılmadı. Hesapta etkin görüntü üretim eklentisi yok (`ListPlugins` boş), makinede yerel üretici yok, API anahtarı yok. Gereken, net olarak:
- **Araç:** eklenti kataloğundaki *Runway API Skills* (image-to-image + referans), *Kling AI* (referans görselden üretim), *MuAPI* (`edit-image`: inpainting/outpainting) veya *CellCog* — biri hesap/API anahtarıyla etkinleştirilmeli. Alternatif: dışarıda üretilip dosya olarak verilmesi.
- **Girdiler (hazır, depoda/yerelde):** `Renders/plate/L_Hero_Plate_LS_Plate_PathTracer.0000.png` + `_K1_` + `_K2_` (24 mm, 4096×2304, aynı üç kamera; img2img için yapı/perspektif kaynağı), `Renders/gateA_hybrid/aov/*WorldDepth*` (derinlik), `references/02-venetian-hero-wide-space.jpeg` (yalnızca stil; maske/yazı alınmayacak).
- **İstenen çıktı:** her üç kamera için aynı Venedik ortamı (aynı binalar, pencereler, ışıklar), maskesiz/yazısız, 4096×2304, PNG (sRGB) veya EXR (linear). Tutarlılık için K0 üretilir, K1/K2 **K0 çıktısından** img2img + düşük denoise ile aynı kameraya göre türetilir (bağımsız üretim yok). Script `T_Plate_K0/K1/K2` dokularını değiştirir; sRGB gelirse linear'a çevrilir, `ExposureComp` ile pozlama eşitlenir.

**Tur 2.1 ölçüm (hayalet kontrolü).** Yeni ağırlıklarla K0/K1/K2 stilleri ve 48 karelik hareket yeniden render edildi (`stills/`, `move/`, web önizlemesi güncellendi). Uzak katman bandında v6'ya göre ortalama mutlak fark, kare başına (0–255): kare 0: 8.2 · 6: 8.6 · 12 (K0→K1 orta nokta, %47/%47 karışım): 8.6 · 18: 8.5 · 24 (K1): 8.1 · 30: 8.6 · 36 (K1→K2 orta nokta, %39/%39): 9.1 · 42: 8.3 · 47 (K2): 7.8. Eğri düz; orta noktalarda sıçrama yok (`move_diff.png`, `move_diff.csv`). Taban fark (~8) alan derinliği/gürültü farkından gelir ve plaka karışımından bağımsızdır (tek plakalı v1 de aynı bandda 7.6–9.0 verir; v1'in K1 hatası sağ kenardaydı, bu bant sol %58'i ölçer). Orta nokta kareleri (12, 36) gözle de kontrol edildi: çift pencere/çift fener yok. **Ara hareketlerde hayalet: yok (PASS).**

Yeni çevre üretilmediği için bu turda **kalite sıçraması yok → FAIL devam**. Maske, örgüler ve yakın 3D değişmedi.

## Tur 2 güncellemesi (29 Ekim 2026, akşam)

**1 · AI çevre görüntüsü — BLOCKED.** Bu oturumda görüntü üretim aracı yok: makinede yerel Stable Diffusion/ComfyUI/InvokeAI kurulumu bulunamadı, ortamda API anahtarı yok (OpenAI/Stability/Replicate/fal/Runway/Kling/Blockade), Claude Code oturumunda görüntü üreten bir araç/bağlayıcı etkin değil. Eski sahne yeniden render edilip "AI çevre" olarak **sunulmadı**. Gereken erişim: eklenti kataloğundaki görüntü üreticilerinden biri (Runway API Skills, Kling AI, MuAPI veya CellCog) hesap/API anahtarıyla etkinleştirilmeli; ya da `Renders/plate/L_Hero_Plate_LS_Plate_PathTracer.0000.png` (24 mm K0 plakası) referans alınarak dışarıda üretilmiş, maskesiz/yazısız bir matte (tercihen aynı kadraj, 4096×2304, linear EXR veya sRGB PNG) `Renders/plate/` altına konmalı. sRGB geldiğinde script linear'a çevirir ve `ExposureComp` ile pozlama eşitlenir; perspektif eşleşmesi için K1/K2 plakaları da aynı yöntemle (img2img, aynı kamera) üretilmelidir.

**2 · K1 proxy yan yüzü — DÜZELTİLDİ (blur ile değil).** Tek plaka yerine **üç plaka** (K0, K1, K2 kameralarından 24 mm, 4096×2304, PT 512 spp) ve render kamerasının her plaka kamerasına uzaklığına göre ağırlıklandırılan karışım (`w = 1/(d²+1)`, geçerli alan maskesiyle, normalize). K0/K1/K2'de tek plaka baskın (hayalet yok), aralarda ~45 cm boyunca çapraz geçiş. Sonuç: `stills/L_Hero_Hybrid_LS_K1_Hybrid_PathTracer.0000.png` sağ kenarda gerçek cephe/ufuk gösterir; eski tek plaka hali `stills_singleplate/` altında saklandı.

**3 · Dörtlü karşılaştırma:** `Renders/gateA_hybrid/compare_fourway_K012.png` — referans (tek konsept karesi) · v6 · hibrit v1 (tek plaka) · hibrit v2 (üç plaka). **AI destekli hibrit sütunu yok (BLOCKED)**; v2 sütunu AI plakası içermez.

**4 · Kamera testi web önizlemesi (depoda, eksiksiz):** `Renders/gateA_hybrid/web/index.html` — 3 × 48 kare (960×540 JPEG, ~8 MB), oynat/kaydır. MP4 üretilemedi: makinede ffmpeg yok; `winget install Gyan.FFmpeg` sonrası tek komutla üretilebilir.

**Karar (tur 2):** K1 **PASS** (proxy hatası giderildi), projeksiyon K0/K2 **PASS**; görsel kalite sıçraması **YOK → FAIL** (plakalar hâlâ v6 geometrisinden; AI plakası BLOCKED). Gate A **FAIL** devam ediyor; maske/ürün değiştirilmedi; Shopify/koleksiyon işi yok.

---

- **Tarih:** 2026-10-29 · **Temel:** Gate A v6 (`c5ed36f`), `reports/gate-A.md` · v6 dosyaları **korundu** (`Renders/gateA/hero_v6_*` üzerine yazılmadı)
- **Proje:** `Venemask_Cinematic_Showroom.uproject` (UE 5.8.1). v6 sahnesi `L_Hero` değiştirilmedi; yalnızca K0/K1/K2 kamera aktörleri ve sekansları eklendi.
- **Yeni level'lar:** `L_Hero_Plate` (plaka kamerası), `L_Hero_Hybrid` (hibrit A), `L_Hero_LayerMap` (katman haritası)
- **Script:** `Scripts/ue_hybrid.py` (üç aşama: `levels`, `plate`, `layermap`), `Scripts/compare_hybrid.ps1`
- **Çıktılar:** `Renders/gateA_hybrid/` — `stills/` (K0/K1/K2, v6 ve hibrit), `move/` (48 kare × 2), `aov/`, `compare_*.png`, `move_contact_*.png`, `camera_test.html`, `scene_layer_map.png`
- **Ürün:** Casanova Bauta Mask — Eyes Wide Shut Inspired · id 7591523549267 · variant 42664065106003 · SKU 17629779130_3E08 · **124.99 USD** (US/DE/GB pazarı) · 3799.00 **TRY** (Türkiye pazarı, kur 50.58; mağaza temel para birimi USD) · kontrol 2026-10-29 15:25 UTC, `/products/...js` + `localization` çerezi. Manifest: `reports/mask_asset_manifest.csv` (eski "painted gold band" kaydı kaldırıldı).

## Deney A — gerçek 3D yakın + kamera projeksiyonlu orta/uzak

**Yöntem (Composure yerine projektif materyal):** Composure 5.8'de Experimental; kurulum/plugin bağımlılığı yerine aynı işi yapan bir **kamera-projeksiyon materyali** yazıldı (`M_Projection`): K0 noktasındaki 24 mm plaka kamerasının taban vektörleri (F/R/U) ve odak oranlarıyla dünya konumundan plaka UV'si hesaplanır; plaka dışı bölgede v6 gökyüzü degradesi kullanılır. Plaka linear EXR olarak okunur ve MRQ'nun EV −2.5 pozlaması `ExposureComp` ile telafi edilir.

| Katman | İçerik | Teknik |
|---|---|---|
| **Gerçek 3D (yakın)** | Casanova maske + örgü geometrisi, 7 ashlar kapak taşı, korkuluk gövdeleri, 6 sıra paye, yakın sütun + loggia kemer/entablatür, teras döşemesi, rıhtım duvarı, **kanal suyu (gerçek yansıma)**, 2 yakın bağlama kazığı, key/rim/fill/ledge/fener ışıkları, ay yönlü ışığı | `L_Hero` ile aynı aktörler |
| **Projeksiyon (orta)** | Karşı kıyı palazzo hacimleri (kutu proxy'ler), yan kanal evleri, kubbe tabanı, çan kulesi | 18 proxy aktör, `M_Projection` (unlit emissive) |
| **Projeksiyon (uzak)** | Gökyüzü, ay, uzak cephe ışıkları, tüm pencere/fener parlaklıkları | Gök küresi, aynı plaka |
| **Silinen (plakaya pişirildi)** | 804 aktör: pencere kasaları, kornişler, kemerler, fener/lamba ışıkları, köprü, kubbe projektörleri, ay küresi | — |

**Plaka:** `Renders/plate/L_Hero_Plate_LS_Plate_.0000.exr` (LOCAL ONLY, 21 MB) + PNG önizleme; 4096×2304, Path Tracer 512 spp, 24 mm f/22 (h-FOV 73.7°), yakın katman gizli.

**Plakanın kaynağı:** bu turda plaka **v6 geometrisinin kendisinden** pişirildi. Yapay zekâ panorama (Blockade Labs) ve World Labs çıktısı **alınamadı** (aşağıya bak). Dolayısıyla Deney A bu turda **boru hattını ve parallax davranışını** kanıtlar; K0'da v6 ile görsel kalite farkı beklenmez. Daha iyi bir plaka (aynı 24 mm K0 kamerasından, aynı perspektifle boyanmış matte / img2img) `T_Plate_K0` dokusunu değiştirerek sahneye girer; `Renders/plate/*.png` ve `aov/` derinlik bu iş için hazır.

## Kamera testi K0 / K1 / K2

| Poz | Konum (cm) | Hedef (cm) | Lens | Not |
|---|---|---|---|---|
| K0 | (−150, −75, 130) | (11.6, −23.3, 120) | 42 mm f/6.3 | v6 hero kadrajı |
| K1 | (−129.9, −115.2, 130) | aynı | 42 mm f/6.3 | kameranın sağ vektörü boyunca **45 cm sola** kayma |
| K2 | (−116.7, −64.3, 127.9) | (6.3, −12.5, 118) | 42 mm f/6.3 | görüş ekseninde **35 cm dolly-in** + hedef 12 cm maskeye (~5° yaw) |
| Move | K0 → K1 (0–24) → K2 (24–47) | odak maskeyi izler | 48 kare, PT 96 spp, 1280×720 | `camera_test.html` ile kare kare |

**Parallax zarfı (45 cm kayma):** karşı kıyı 110 m → 0.23° ≈ 10 px (1920'de); orta proxy'ler 16–45 m → 0.6–1.6° ≈ 25–70 px. Bu yüzden orta katman geometri (proxy) olmak zorunda; yalnızca uzak katman küreye konabilir.

**Gözlemler (stills):**
- **K0:** hibrit ≈ v6. Paye ve sütun, projeksiyonlu cepheleri doğru örter (occlusion doğru); su proxy'lerin emissive ışığını yansıtır.
- **K1:** maske, örgü, çatlak, temas gölgesi ve yakın taş **değişmedi** (gerçek 3D). Hata: sağ kadraj kenarında bir palazzo proxy kutusunun yan yüzü görünür hale gelir ve plakanın gökyüzü bölgesini gerilmiş olarak taşır (`stills/L_Hero_Hybrid_LS_K1_Hybrid_PathTracer.0000.png`, sağ üst). v6'da aynı yerde gerçek cephe/ufuk var. → proxy'lerin yan yüzleri için ikinci (yan) plaka ya da proxy kutularının kameraya dönük tek yüze indirgenmesi gerekir.
- **K2:** hibrit ≈ v6; dolly-in'de perspektif kayması proxy'ler sayesinde tutarlı, dikiş yok.

## Deney B — World Labs Marble (mekânsal dünya üretimi)

**Durum: BLOCKED (erişim/lisans).** Doğrulanan gerçekler (29 Ekim 2026):
- Girdi: metin, görsel, video, 360 panorama; "3D layout" (Chisel). Çıktı: Gaussian splat **SPZ / PLY**, **360 panorama**, **collider mesh** (Standard plan); **yüksek kaliteli dokulu mesh (GLB)** ve **ticari haklar Pro plan** (docs.worldlabs.ai/marble/export). **Free plan export yapamaz.**
- Hizmet şartları (worldlabs.ai/terms-of-service §3.3): ücretsiz hesaplarda çıktının hakları World Labs'ta kalır, yalnızca kişisel/ticari olmayan kullanım; ücretli hesaplar çıktıyı ticari kullanabilir, istenirse atıf zorunlu.
- Unreal yolu: Gaussian splat plugin'leri (Akiya: .ply; VIVE Mars: .ply/.spz; Volinga) — World Labs'ın kendi karşılaştırma yazısı Path Tracer/Lumen uyumuna değinmiyor; splat'lar v6'nın Path Tracer ışık/yansıma modeline doğrudan katılmaz (gölge/yansıma yok veya yaklaşık).
- Kullanıcı adına hesap açılmadı, ödeme yapılmadı. Denemek için: Pro plan hesabı + aynı K0 bakış açısından üretilmiş dünya + UE splat plugin'i; o zaman K0/K1/K2 testi `L_Hero_Hybrid`'in uzak katmanında tekrarlanır.

**Blockade Labs Skybox AI:** API anahtarı/hesap yok → panorama üretilemedi (BLOCKED). Not: 360 skybox yalnızca açısal kapsama verir; K1 benzeri yan hareketler için orta katman yine proxy/projection olmalı.

## Araçlar ve kaynaklar
| Araç | Sürüm / kaynak | Lisans / durum |
|---|---|---|
| Unreal Engine | 5.8.1, Path Tracer, MRQ, Cine Camera, Python | Epic EULA; proje yerel |
| Composure / Media Plate | 5.8 plugin'leri mevcut, **kullanılmadı** (projektif materyal yeterli, bağımlılık yok) | — |
| Plaka | v6 geometrisinden kendi render'ımız | kendi üretimimiz |
| Mimari parçalar, dokular | `Scripts/gen_*.py` prosedürel | kendi üretimimiz |
| Casanova STL, fotoğraflar | kullanıcının baskı dosyası ve mağaza fotoğrafları | kullanıcı |
| Blockade Labs / World Labs / Meshy | **kullanılmadı** | erişim yok |
| ffmpeg | makinede yok → video yerine 48 kare PNG + `camera_test.html` kaydırıcı + kontak sayfası | — |

## Ürün doğruluğu (değişmedi, ayrı kapı)
- Geometri: STL birebir, boya bölgeleri, 3+3 bukle, göz/burun — PASS.
- Örgü: **GEOMETRİ PASS**, iplik PBR'si **UNVERIFIED**. Craquelure: fotoğraf ölçeğinde prosedürel, **UNVERIFIED**.
- Hibrit deneyinde maskeye hiçbir şey eklenmedi; aynı aktör, aynı malzeme.

## LOCAL ONLY (depoda yok) ve yeniden üretim
`Content/` (tüm .uasset/.umap), `SourceAssets/**/*.stl|*.obj`, `SourceAssets/textures|stone|arch`, tüm `*.exr`, `Renders/plate`, `Renders/gateA_hybrid/move` kareleri (boyut). Yeniden üretim: `prep_mask.py` → `gen_braid.py` → `gen_stone.py` → `gen_arch.py` → `gen_textures.py` → `ue_build_hero.py` → `ue_make_configs.py` → `ue_hybrid.py` (levels) → `render.ps1 -Config MRQ_Plate -Map L_Hero_Plate -Sequence LS_Plate` → `VM_STAGE=plate ue_hybrid.py` → `render.ps1 -Config MRQ_PT_K/MRQ_PT_Move ...` → `compare_hybrid.ps1`. Depo tek başına eksiksiz proje değildir.

## Karar
- **Deney A (boru hattı): PASS** — projeksiyon K0'da v6 ile eşdeğer, K2'de tutarlı, occlusion ve su yansıması doğru.
- **Deney A (K1 yan hareket): FAIL** — proxy yan yüzü artefaktı; düzeltme belli (yan plaka / tek yüz proxy).
- **Deney A (görsel kalite sıçraması): henüz yok** — plaka v6'dan pişirildiği için aynı kalite; sıçrama için harici matte/panorama gerekir (BLOCKED).
- **Deney B: BLOCKED** (ücretli hesap + lisans gerekli).
- **Gate A: FAIL (devam)** — referans sınıfı sinematik kaliteye bu turda ulaşılmadı. Kamera rotası, diğer maskeler ve Shopify'a geçilmedi. Nihai görsel kabul kullanıcı onayına bağlı.
