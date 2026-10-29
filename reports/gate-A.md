# GATE A — FAIL (v6: büyük ilerleme, referans sınıfına henüz değil)

- **Tarih:** 2026-10-29 (ikinci tur)
- **Proje:** `Venemask_Cinematic_Showroom.uproject` (UE 5.8.1, ayrı proje; oyun projesine dokunulmadı)
- **Level / sekans:** `/Game/Venemask/Maps/L_Hero`, `/Game/Venemask/Cinematics/LS_Hero`
- **Render config:** `MRQ_PT` (Path Tracer, 256 spp, OIDN, 1920×1080), `MRQ_AOV`, `MRQ_Lumen`
- **Bu turun render dosyaları:** `Renders/gateA/hero_v6_pathtracer_1920.png` + `.exr`, `hero_v6_worldnormal.png`, `hero_v6_depth.png`, `hero_v6_productmatte.png`, `hero_v6_lumen_preview.png`
- **Karşılaştırmalar (aynı ölçek):** `Renders/gateA/compare_reference_v6.png` (ref 02 ↔ render), `compare_product_v6.png` (mağaza fotoğrafı ↔ render ↔ yan fotoğraf, maske aynı yükseklikte), `compare_detail_v6.png` (şerit + çatlak yakın plan)
- **Sayfa:** `reports/gate-A.html` · önceki tur: `hero_v5_*` dosyaları

## Ürün (değişmedi)
Casanova Bauta Mask - Eyes Wide Shut Inspired · Shopify id 7591523549267 · variant 42664065106003 · SKU 17629779130_3E08 · 3799.00 · kendi baskı STL'iniz (`casanova bauta_3.stl`), şekil değiştirilmedi.

## Bu turda yapılanlar
**Ürün detayı**
- Altın şeritler artık **geometri**: STL'in kendi kenarlarından türetildi (`Scripts/gen_braid.py`). Şapka kenarında ~6.5 mm geniş düz "scroll" şerit + üstünde dalgalı kordon (fotoğraf 01/03'teki yapı); şapka–yüz sınırında ~3.5 mm burgulu gimp. Kaynak kanıt: `SourceAssets/casanova_bauta/inspect/photo01_braid_brim.png`, `photo03_braid_side.png`; sonuç: `inspect/braid_front.png`, `braid_side.png`.
- Craquelure fotoğraf 01 yakın planına göre yeniden ölçeklendi (1–3 mm hücre, sıcak gri-kahve çatlak, parlak sır, hafif leke).
- Altın bukleler mat varak gibi (fotoğraf 03: parlak metal değil; çukurlarda koyu umber).
- Maskeye tüy, taş veya süs **eklenmedi**.

**Çevre / mimari** (`Scripts/gen_arch.py`, `gen_stone.py`, `ue_build_hero.py`)
- Gerçek mimari parçalar: yuvarlak kemer, sivri (gotik) pencere kemeri, entasisli sütun, basamaklı korniş, bağlama kazığı (paline), segment kemerli taş köprü.
- Maskenin yaslandığı paye artık 6 sıra ashlar taş; korkuluk kapağı 7 ayrı taş blok (derzler geometri). Sol kadraj kenarında yakın loggia sütunu (ref 02'deki koyu yakın kütle).
- Karşı kıyı (110 m): rustik zemin kat + kemerli su kapıları, sıvalı katlar (okra / gül / krem / gri varyantları), gotik pencereler (kasa, orta sütun, denizlik, karanlık içbükey, perdeli ışık), kat kornişleri; yan kanal + köprü; kubbe + drum pencereleri + çan kulesi, projektörle aydınlatılmış; ay.
- Işık: sıcak spot key + sıcak spot rim, soğuk gökyüzü dolgusu, ay yönlü ışık (7200 K), rıhtım fenerleri, pencere lambaları, köprü fenerleri. Kamera 42 mm f/6.3, göz hizasının 10 cm üstünde, ~3° aşağı; odak maske gözlerinde (1.63 m).

**Malzeme** (`M_Stone_Istrian`, `M_Facade_Plaster`, `M_Canal`, …)
- Istria kireçtaşı: ashlar derz maskesi (metre UV), su hattında kir bandı (dünya Z), aşağı doğru nem, üst yüzeylerde ıslaklık maskesi; `Brightness`/`WetMul` parametreli instance'lar.
- Sıva: renk parametresi, dökülmüş sıva → tuğla, alt kirlenme.
- Kanal: iki ölçekli dalga normali, çok düşük pürüzlülük.

## Varlıklar
- Makinede bulunan Fab/Megascans içeriği yalnızca orman temalı (yosun, kök, nehir kayaları: `ActionAdventureMovementS/Content/Fab/Megascans`). Venedik taşı/mimarisi için uygun **taranmış varlık yok**; Fab indirmesi editör içinde Epic oturumu gerektirdiği için headless alınamadı.
- Bu yüzden tüm mimari ve dokular prosedürel (`Scripts/`). Önerilen Fab ekleri: "Istrian/limestone ashlar wall", "wet cobblestone", "Venetian plaster peeling", "stone balustrade", "gothic window" — `/Game/Fab` altına eklendiğinde script'te malzeme slotları değiştirilerek kullanılır.

## Kontrol
| Madde | Durum | Not |
|---|---|---|
| Ürün kimliği / geometri | PASS | STL birebir; normal pass'te tam çözünürlük |
| Boya bölgeleri | PASS | fotoğraflarla uyumlu |
| Altın şerit (brim scroll + band gimp) | PASS (geometri) / dokusu UNVERIFIED | ölçü ve yerleşim fotoğraftan; iplik dokusu prosedürel |
| Craquelure | UNVERIFIED | ölçek fotoğrafa göre; gerçek desen taranmadı |
| Fiziksel oturma, temas gölgesi | PASS | |
| Kadraj (ref 02) | PASS | sağ üçte bir maske, solda gökyüzü/kubbe/ay, su, yakın sütun |
| Alan derinliği | PASS | arka plan yumuşak ama okunur (pencereler, kemerler, köprü fenerleri) |
| Mimari okunurluk | KISMEN | cepheler katmanlı ama hâlâ sade; cephe heykeli/balkon yok |
| Taş / su malzeme kalitesi | KISMEN | ashlar + ıslaklık inandırıcı; prosedürel doku yakın planda hâlâ "temiz" |
| Referans sınıfı sinematik his | FAIL | ref 02'deki zenginlik (kadife, çok katmanlı ışık, atmosferik derinlik) yok |

## Referansla kalan 3 büyük fark
1. **Yakın plan malzeme zenginliği:** taranmış taş yok; korkuluk ve paye yüzeyi düz okunuyor.
2. **Atmosfer:** havada hafif pus/ışık saçılması yok (ref 02'nin fenerleri halelidir). Bilinçli olarak "sis eklemeyin" kuralına uyuldu; çok ince, fiziksel bir haze gerekebilir.
3. **Cephe detayı:** balkon, korkuluk, bacalar, kepenkler; pencere içlerinde oda derinliği.

## Karar
**FAIL.** Ürün tarafı Gate A için kabul edilebilir durumda; sahne tarafı referansın yapısını yakaladı ama malzeme zenginliğinde geride. Aşama 2 (kamera rotası, ek maskeler) ve Shopify'a geçilmedi.
