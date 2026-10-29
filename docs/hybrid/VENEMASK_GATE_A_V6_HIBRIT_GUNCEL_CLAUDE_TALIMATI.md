# VENEMASK — Gate A v6 Üzerine Hibrit Sinematik Çevre Denemesi

**Tarih:** 29 Ekim 2026  
**Repo:** https://github.com/beratartanb/venemask  
**İncelenen son commit:** [`c5ed36f9`](https://github.com/beratartanb/venemask/commit/c5ed36f9fdf612a3a1c89bf810ba28fba400abbb) — Gate A round 2 (v6).  
**Mevcut kalite kapısı:** **FAIL**. Bu belge önceki `CLAUDE_MAIN_PROMPT.md` ve `CLAUDE.md` ile birlikte okunacak **odaklanmış revizyondur**; ürün doğruluğu ve yayın güvenliği kurallarını geçersiz kılmaz.

## 0. Başlamadan önce okuman gereken kanıtlar

1. `reports/gate-A.md` (v6, ikinci tur) — ana durum kaydı.
2. `reports/gate-A.html` — karşılaştırma sunumu.
3. `Renders/gateA/compare_reference_v6.png` — ref 02 / yeni Path Tracer.
4. `Renders/gateA/compare_product_v6.png` — gerçek Casanova fotoğrafları / render.
5. `Renders/gateA/compare_detail_v6.png` — altın örgü ve craquelure.
6. `Scripts/ue_build_hero.py`, `gen_arch.py`, `gen_braid.py`, `gen_stone.py`, `ue_render.py` ve `Config/DefaultEngine.ini`.
7. `references/01-multi-mask-room-and-product-showcase.jpeg` ve `references/02-venetian-hero-wide-space.jpeg` — **yalnızca sanat yönü**. İçlerindeki maskeler, fiyatlar ve diğer içerikler gerçek ürün kaynağı değildir.

Önceki v5 raporuna dönüp aynı işin yeniden yapıldığını iddia etme. İlk geliştirilen v6 seviyesini baz al.

## 1. Korunacak mevcut çalışmalar

- Ayrı `Venemask_Cinematic_Showroom.uproject` ve `/Game/Venemask/Maps/L_Hero` sahnesi. Sphirus World oyun projesine dokunma.
- Casanova Bauta gerçek baskı STL'si, mevcut mesh segmentasyonu, göz/burun/şapka/bukle geometrisi.
- v6'da oluşturulmuş 6.5 mm şapka kenarı scroll örgüsü ve 3.5 mm band gimp **geometrisi**. Bunun iplik PBR'si hâlâ doğrulanmalı.
- Taş korkuluğun, yakın payenin ve yakın su/temas yüzeyinin 3D geometrisi, 12° yaslama çözümü, temas gölgesi ve yansımalar.
- 42 mm f/6.3 Cine Camera, v6 kadrajı, sıcak/soğuk dengeli ışık setup'ı; yalnızca ölçülmüş iyileştirme gerekiyorsa değiştir.
- v6 renderer konfigürasyonları, Path Tracer beauty ve normal/depth/product matte çıktıları.

## 2. Mevcut problem, değişmesi istenen şey

Geometriyi giderek daha karmaşık prosedürel binalarla doldurmak artık öncelik değil. Mevcut raporda mimari kısmen, taş/su yüzeyi kısmen, referans sınıfı ise FAIL. Eksikler: yakın ıslak taşın gerçek PBR/mikro detayları, uzakta okunur tarihî cephe hacmi, pencerelerin iç derinliği, pus ve ışığın ortamdaki kademeli yayılımı. Ürün craquelure haritası ve örgü iplik dokusu da ürün fotoğrafıyla doğrulanmış değil.

**Amaç:** Gerçek ürünün ön ve yakın çevresini koruyarak uzak ve orta çevrede **hibrit fiziksel geometri + matte projection + panorama** yaklaşımını küçük bir kontrollü testte dene. Başarılı olmazsa kanıtla ve v6 tam geometriye dön.

## 3. A/B çevre tekniği — aynı kamera, aynı ürün

Aşağıdaki iki çözümü aynı sanat yönü, ışık ve kamera koşullarında karşılaştır. **Tüm siteyi, tüm koleksiyonları veya Shopify'ı geliştirmeye başlama.**

### Deney A — v6 + 360° panorama + gerektiği kadar projection geometry

- **Gerçek 3D:** Casanova Bauta ve materyalleri; temas eden taş/paye/korkuluk; ön su yüzeyi; gölge/yansıma için gereken hacimler; kamera tarafından görülen yakın mimari.
- **Orta mesafe:** Mevcut v6 mimarisini basitleştirip gerekli blokları koru; gerçek mimari perspektif, pencere içleri, kemerler ve yan hacim hissi için derinlik verilmiş yüzeylere camera-projected matte kullan. Bunlar sadece tek bir düz perde olmamalı; occlusion, parallax ve perspektif kaçışları kamerada tutarlı olmalı.
- **Uzak çevre:** Uzak Venedik kanalı, cephe katmanları, gökyüzü, ay, yumuşak ışık ve mimari silüeti yüksek kaliteli **AI panorama/matte** ile üret. Panorama maske, ürün, uydurma tabela, okunmaz yazı veya ürün fiyatı içermemeli.
- Çevre görüntüsünü mümkünse HDRI/360 equirectangular biçiminde al; ışık yönünü v6'daki fiziksel key/rim/fill ile eşleştir. AI görüntüsünün kendisine ürün fotoğrafını gömme.
- Unreal 5.8'de **Composure** (mevcut sürümde Experimental) veya projektif UV materyali / projection card yaklaşımını teknik olarak karşılaştır. Kurulum başarısızsa sadece "plugin çalışmıyor" deyip durma; alternatif kamera-projection materyali yap ve kanıtla.
- AI panorama **kameranın aynı noktadan dönmesi** için uygundur; geniş yan/ileri kamera hareketinde doğru parallax vermez. Bu sınır için orta alan geometry/projection ve gerekirse ikinci uyumlu matte kullan.

### Deney B — sınırlı kamera hareketine uygun üretken 3D çevre

- Mevcut v6'ya dokunmadan, ayrı bir **deneme klasörü/level** altında **World Labs Marble** gibi görüntü/360/multi-view verisinden mekânsal tutarlılığı hedefleyen çözümleri incele. Export, lisans, yetki ve UE kullanımını **doğrulamadan** doğrudan bağlı veya hazır deme.
- Öncelik gerçekçi uzak/orta çevredir; maske asla yeniden üretilmez. AI ile üretilmiş maske, gösterişli ama üründe bulunmayan tüy, taş ve süsleri kesinlikle kullanma.
- Gerekirse **Meshy** yalnızca arka plan kolon/kemer/korkuluk gibi *ikincil* props için hızlı blockout sağlar; gerçek Casanova geometrisinin veya final üst seviye malzemenin kaynağı değildir.
- Erişim/abonelik engeli varsa satın alma yapma, kullanıcı adına hesap açma; bunu `BLOCKED` olarak yaz, Deney A ile devam et.

## 4. Kalite ölçümü — sadece hero karesi değil, kamera hareketi de

Aynı ürün ve renk yönetimi korunarak şu **kamera testlerini** oluştur:

- **K0:** mevcut v6 42 mm / f6.3 hero kadrajının A/B karşılığı (1920×1080).
- **K1:** maskeden çok uzaklaşmayan sınırlı lateral kamera kayması — uygun mesafeyi önce kamera/parallax sınırına göre ölç, rastgele metre taahhüdü verme.
- **K2:** hafif dolly-in/rotation ve daha görünür mimari perspektif.

Her pozda gerçek maskenin silüeti, altın şerit, beyaz craquelure ve fiziksel gölgeler doğru kalmalı. Panorama/projection dikişleri, gerilmiş pencereler, çift görünen taşlar, hatalı occlusion, yalancı ışık, focus flicker veya farklı mekâna atlama olmamalı.

Aynı ölçekte **v6 tam geometri / Deney A / (mümkünse) Deney B / referans** karşılaştırması yap. Önce 3 sabit render ve kısa K0–K1–K2 kamera test animasyonu; sonra görsel seçim. Bir seçenek yalnızca tek sabit karede iyi görünüp kamera hareketinde dağılıyorsa **FAIL**.

### Ürün doğruluğu ayrı kapı

- Casanova'nın kaynak fotoğraflarıyla **aynı açı ve ölçekli** ürün/texture karşılaştırması; silüet, göz-burun bölgesi, şapka, 3+3 altın bukle, örgü ipliği, yüzey çatlağı.
- Önceki v6 raporundaki altın örgü **GEOMETRY PASS** ancak örgü materyali **UNVERIFIED**. Gerçek çatlak deseni taranmadı. Bu ikisini tam PASS göstermeden raporda açık bırak.
- Referansın hayalî maskesindeki kırmızı tüy, mücevher vb. ayrıntıları gerçek Casanova'ya ekleme.

## 5. Var olan v6 dosyalarında düzeltilmesi gereken kayıtlar

- `reports/mask_asset_manifest.csv` hâlâ önceki turdaki **"gold braid ... painted gold band"** bilgisini içeriyor; v6'daki geometriye ve **dokusu UNVERIFIED** durumuna göre düzelt.
- Gate A raporunda ürün fiyatı **3799.00**, ancak 29 Ekim 2026 bağlı Shopify ürün kaydında bu Casanova varyantının fiyatı **124.99 USD**. Ürünün kimliği/ID/SKU sabit; doğru para birimi ve fiyatı mağazadan tekrar çekip manifestte kaynak/zaman damgasıyla güncelle. Bu aşamada fiyatı Unreal görseline yazma, mağaza kayıtlarını değiştirme.
- `.gitignore` Unreal `Content/`, STL/OBJ, üretilen dokular ve EXR'leri hariç tutuyor. Bunlar GitHub'da olmadığından rapora `LOCAL ONLY` olarak kanıt/kaynak konumlarını ve yeniden üretim komutlarını açıkça ekle; depo tek başına eksiksiz proje gibi gösterilmesin. Büyük dosya eklemek için ayrıca onay iste.

## 6. Kalite eşiği ve teslim

**Yeni Gate A-HYBRID raporu** aşağıdaki çıktıları içermeli:

1. Kullanılan kaynaklar ve hak/lisans bilgisi (AI panorama aracının lisansı dahil); araç sürümü, export biçimi ve erişim.
2. `Renders/gateA/hero_v6_*` başlangıç kanıtlarını koruyan yeni `Renders/gateA_hybrid/` alt klasörü. V6 temel dosyaları üzerine yazma.
3. K0, K1, K2 kareleri + kısa kamera test videosu; her pozun gerçek kamera transform'u ve seçilen panorama/projection kurulumu.
4. Aynı kamera/sunumla A/B kalite karşılaştırması. İyileşen ve bozulmuş öğeleri metinle **kanıta bağlı** açıkla.
5. Maske gerçek fotoğraf / render karşılaştırmaları, eksik kumaş/çatlak dokusu listesi.
6. Kullanılan asset'lerin lisansları ve hangi kısmın 3D, projection, panorama olduğunu gösteren bir sahne haritası.
7. PASS/FAIL/BLOCKED değerlendirmesi; **nihai görsel kabul kullanıcı onayına bağlı**. Test kalitesine ulaşmadan kamera geçişlerini, diğer 4 maskeyi ve Shopify'ı geliştirmeye başlama.

**Özellikle:** Hem Web panoraması hem de World Labs ortamı kontrolsüz yeni Venedik tasarımları üretmeye başlamasın. Mevcut v6 ile aynı mekânın sanat yönünü koru, yalnızca kalite darboğazına odaklan.

## 7. Hangi araçlardan hangi iş bekleniyor?

| Araç/yöntem | Görev | Kritik sınır |
|---|---|---|
| Unreal Engine 5.8.1 | Gerçek maske/taş, fiziksel ışık, Path Tracer, Cine Camera | Önce v6 sahnesini koru |
| Blockade Labs Skybox AI | AI 360 uzak panorama / atmosfer seçeneği | Tek 360 sahne geniş kamera translation'ı çözmez |
| World Labs Marble | Çok açılı çevre veya daha hacimli ortam için alternatif deney | UE aktarım ve kullanılabilir lisans doğrulanmalı |
| Meshy | İkinci plandaki objelerin deneme/blockout'u | Gerçek maskeyi asla yeniden üretme |
| Unreal Composure / projektif texture | Matte plate, holdout, shadow/reflection ve camera projection | UE 5.8 Composure Experimental; alternatif materyal yöntemi hazır tut |
| GitHub | Render, rapor, kanıt/commit takibi | Büyük local varlıklar olmadan yeniden üretilebilirlik iddiası yok |

## 8. Claude Code skill uygulaması

Mevcut `.claude/skills/venemask-art-direction`, `venemask-mask-fidelity`, `venemask-unreal-cinematics`, `venemask-visual-qa` becerilerini kullan. Projeye ek olarak paketteki `.claude/skills/venemask-hybrid-environment/SKILL.md` dosyasını kullanabilirsin. Bu skill, gerçek maskeyi ve yerel geometriyi koruyup panoramik/2.5D matte deneylerini prova etme, 3 açı kontrolü, lisans ve teknik sınırlarını tanımlar. Skill yüklemek, üçüncü taraf servise otomatik abonelik veya erişim sağlamaz.

## 9. Gerçek kaynaklar (okunacak)

- GitHub Gate A v6 raporu: https://github.com/beratartanb/venemask/blob/main/reports/gate-A.md
- GitHub v6 karşılaştırması: https://github.com/beratartanb/venemask/blob/main/Renders/gateA/compare_reference_v6.png
- Unreal Composure 5.8: https://dev.epicgames.com/documentation/unreal-engine/composure
- Unreal Media Plate: https://dev.epicgames.com/documentation/unreal-engine/the-media-plate-actor-in-unreal-engine
- Blockade Labs resmi Skybox AI: https://www.blockadelabs.com/
- World Labs Marble: https://www.worldlabs.ai/
- Meshy resmi belgeleri: https://docs.meshy.ai/en/

**Şimdi ilk görevin:** v6 raporunu ve sahneyi aç, ürün doğruluğunu değiştirmeden en az bir panorama/projection prototipini K0–K1–K2 üzerinden üret, v6 ile kanıtlı karşılaştır. Kabul sonucunu raporla. **Bu turda Shopify veya tüm sayfa tasarımı yok.**
