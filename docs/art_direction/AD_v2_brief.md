# Sanat yönü v2 — sıfırdan (29 Ekim 2026)

Karar: v6 / hibrit sahneleri **teknik prototip** olarak durduruldu ve korunuyor (`Renders/gateA*`, `L_Hero*`). Yeni tasarım bunların kadrajını, mimarisini, kompozisyonunu, ay/ufuk konumunu veya yakın taş düzenini **miras almaz**. Kabul ölçütü teknik PASS değil: referanslardaki görsel kalite sınıfı ve marka hissi.

## 1 · Durum: görüntü üretim aracı YOK → BLOCKED

Kontrol (bu oturum): hesapta etkin eklenti yok (`ListPlugins` → boş), oturumda görüntü üreten araç/bağlayıcı yok, makinede yerel üretici (SD/ComfyUI/InvokeAI) yok, ortamda API anahtarı yok. Talimat gereği bu eksiklik **kodla telafi edilmedi**; yeni sahne görüntüsü üretilmedi. Bu teslimatta "yeni tasarım" sütunu yoktur.

Gerçek görüntü üretimi için gereken (biri yeterli):
1. Eklenti kataloğundan bir görüntü üreticinin hesap/API anahtarıyla etkinleştirilmesi — Runway API Skills (image-to-image + referans), Kling AI (referans görselden üretim), MuAPI (`edit-image`, inpaint/outpaint) veya CellCog; **veya**
2. Üretimin dışarıda (Midjourney, Flux, SDXL, Firefly vb.) yapılıp PNG olarak verilmesi; bu durumda aşağıdaki §4 girdileri aynen kullanılır.

## 2 · Referans okuması

**Referans 02 → ana Hero hedefi.** Yatay 16:9, kamera masa yüksekliğinde, ~35–50 mm. Sağ üçte-birde çok yakın, kadrajı dolduran gösterişli maske (kırmızı-altın filigran göz maskesi, çatlak fildişi yüz, koyu kırmızı/siyah tüy taç) koyu bordo kadife üzerinde, altında ıslak yaşlı taş korkuluk. Sol/orta: geniş kanal, su yansımaları, ıslak taş köprü, barok cephe ve kubbe silüeti, **dolunay üst-orta**, bulutlu gece. Sıcak mum/fener ışığı (ön ve orta plan) + soğuk mavi ay ışığı (arka). Sığ alan derinliği: maske net, kanal ve kubbe yumuşak. Renk paleti: bordo, altın, fildişi, is-siyahı, soğuk lacivert. Tipografi/arayüz ve konsept maskeler **alınmayacak**.

**Referans 01 → aynı dünyada çoklu maske sergisi ve kamera yolculuğu.** Üst: barok sütunlu loggia, mermer masa, gösterişli fildişi-altın maske + beyaz devekuşu tüyü, mumlar, kadife; arkada kubbe ve kanal, alacakaranlık. Alt: koleksiyon rafı (Venice/LoL/Slipknot/Nature) ve rıhtımda sıralı maske teşhiri, fenerler, ıslak zemin yansımaları, kayan ışık izi (kamera yolu). Hero'dan loggia içine ve rıhtım boyunca ilerleyen bir yolculuğun hedef kareleri. Fiyat/isim/yıldızlar hayalî, **alınmayacak**.

Ortak dil: geniş Venedik kanalı, mimari derinlik (yakın sütun → orta köprü → uzak kubbe), barok sütunlar, ıslak yaşlanmış taş, koyu bordo kadife, sıcak mum ışığı, soğuk gece ışığı, fiziksel derinlik, kaliteli malzemeler. Hepsi tek kompozisyonun doğal parçası, dekor olarak serpiştirilmiş değil.

## 3 · Ana maske seçimi (gerçek katalog)

Referans 02'nin kimliğine (altın kabartmalı göz maskesi + çatlak fildişi volto yüz + koyu tüy taç + kırmızı vurgu) en yakın gerçek ürün:

**La Regina Nera – Black Feather Venetian Mask** · id 8103565230163 · variant 46133991604307 · SKU 13877354473_3FDSD3 · handle `la-regina-nera-black-feather-venetian-62815` · **299.99 USD** (US pazarı) / **7899.00 TRY** (Türkiye pazarı) · canlı kontrol 2026-10-29 20:15 UTC (`/products/<handle>.js` + `localization` çerezi) · mağaza fotoğrafları: `SourceAssets/la_regina_nera/store_photo_01..04.jpg`.
Ürün: sert plastik volto yüz, çatlak (krakle) beyaz boya, kırmızı dudak, altın kabartmalı göz maskesi, altın örgü şerit, siyah horoz tüyü taç + benekli beç tüyü iç halka, tepe noktasında siyah taş. Form ve süslemeler **değiştirilmeyecek**; referanstaki kırmızı filigran/kırmızı tüy eklenmeyecek.

Yedekler (aynı aile, daha az yakın): Gold Venetian Mask with Blue Feather Headdress (8036599038035; aynı volto tabanı, mavi tüy), Seraphina (8025478987859; siyah tüy, yarım maske), Aurélie (8036598382675; fildişi tüy — referans 01'deki beyaz tüylü maskeye en yakın; koleksiyon sergisi için aday), Bianca Royal Ivory (8025467977811; dantel, kırmızı kristal).

**Kaynak modeli YOK.** Diskte yalnız Casanova Bauta STL'si var (`SourceAssets/casanova_bauta/`, Codex çıktısı). La Regina Nera için STL/3MF/OBJ bulunmuyor. 3D entegrasyon (ürünün gerçek geometrisiyle sahneye yerleşimi) için gereken: volto yüz + göz maskesi taban modeli (STL/3MF, mm) ve mümkünse tüy tacın fotogrametri/çok açılı fotoğrafı. Model gelene kadar ürün yalnız **fotoğraf tabanlı** (mağaza fotoğraflarından kesilip 2D olarak) ana kareye yerleştirilebilir; bu, ürün sadakati açısından güvenli (gerçek fotoğraf) ama kamera hareketine izin vermez.

## 4 · Görüntü üretimi girdileri (ana kare, statik)

- **Hedef:** referans 02 sınıfında tek ana kare, 16:9, en az 3840×2160 (tercihen 4096×2304), **maskesiz** çevre (maske ayrı katman; ürün fotoğrafından/3D'den eklenecek) + maskenin konacağı boş kadife/taş ön plan.
- **Stil referansı:** `references/02-venetian-hero-wide-space.jpeg` (yalnız stil/kompozisyon; içerik kopyalanmaz), ikincil `references/01-...jpeg`.
- **Prompt (EN):** `Cinematic night photograph, Venice Grand Canal, 40mm lens at table height, foreground: wet weathered Istrian stone balustrade draped with dark burgundy velvet, right third left empty for a product; mid: baroque columns, stone bridge, warm candle lanterns reflecting on dark water; far: baroque palazzo facades and a domed church under a full moon, scattered clouds, thin haze; warm candlelight vs cool blue moonlight, shallow depth of field on the foreground, photorealistic, 8k, no people, no text, no masks`
- **Negatif:** `mask, text, letters, logo, watermark, people, boats with text, vignette, cartoon, oversaturated`
- **Çıktı:** PNG sRGB, alfa yok; dosya `Renders/artdir_v2/hero_env_v1.png`.
- Maske birleştirme (ürün): `SourceAssets/la_regina_nera/store_photo_01.jpg` (ön), 03/04 (açılar). Işık yönü sahneyle eşleşmeli (anahtar sıcak soldan/önden, soğuk kenar arkadan).

## 5 · İlk teslimat (bu tur)

`Renders/artdir_v2/compare_refs_vs_v6.png`: referans 02 · referans 01 · v6 hero · hibrit v2.2 K0, aynı ölçekte. Yeni tasarım sütunu yok (§1). Sonraki teslimat, görüntü üretimi mümkün olduğunda: aynı levhaya "yeni ana kare" sütunu + La Regina Nera yerleşimi; 3D projeksiyon ve kamera hareketi ancak bu kare referans sınıfına ulaşınca.
