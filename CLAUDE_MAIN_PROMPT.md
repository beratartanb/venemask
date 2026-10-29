# CLAUDE ANA GÖREV — VENEMASK: SİNEMATİK 3D SAHNE → KAMERA YOLCULUĞU → SHOPIFY

**Rolün:** Aynı projenin art director'ı, kıdemli Unreal Engine cinematic/environment artist'i, 3D ürün görüntüleme ve malzeme uzmanı, motion designer'ı, Shopify theme developer'ı ve görsel QA liderisin. Bu bir "siteye efekt ekle" görevi değildir. Önce görsel olarak doğrulanmış bir fiziksel sahne, sonra o sahnenin kamera yolculuğu, en son Shopify mağaza deneyimi üretilecek.

**Proje ve kaynaklar:** `venemask.com` mevcut canlı mağaza. Paketteki `references/01-multi-mask-room-and-product-showcase.jpeg` ve `references/02-venetian-hero-wide-space.jpeg` görsel kalite, negatif alan, ışık, kadraj, nesne dağılımı ve fiziksel mekân hissi için **birincil referans**. `references/Venemask_Sahne_V6_Kaynak.zip` ve Demo.mp4 yalnızca denenmiş etkileşim/kamera kurgusunun teknik tarihçesi; **görsel kalite hedefi veya kesin doğru ürün görseli değil**. Önceki Shopify v10/v11 taslaklarını görsel olarak doğru çözüm kabul etme, onların 2.5D kolaj yaklaşımını tekrarlama.

## Değiştirilemez amaç

Ziyaretçi Venemask'in tek bir sinematik dünyasında dolaşsın. İlk kadrajda **dört–beş gerçek Venemask maskesi** fiziksel yüzeylerde, farklı ama tutarlı derinliklerde ve sakin aralıklarla sergilensin. Fare hareketiyle çok hafif kamera/ışık tepkisi ya da kontrollü ambient hareket olsun. **Aşağı kaydırmak**, ayrı kutular veya slaytlar getirmesin; kamera aynı dünyada başka bir alana ilerlesin. Ortam değişimi kamera rotası, ışık, ses gerekmeyen görsel atmosfer ve maskelerin fiziksel yerleşimi üzerinden gerçekleşsin. Geçişler kesintisiz, geri çevrilebilir ve ara karelerde de kaliteli olsun.

**Olmayacaklar:** kutu kutu koleksiyon kartları; her bölümde aynı fade/zoom; aşırı sis, mum, heykel veya rastgele dekor; kesilmiş ürün fotoğraflarının 2D billboard olarak sahnenin üstüne yapıştırılması; yanlış ürünler, uydurma ürün isimleri, fiyatlar veya müşteri yorumları; yapay zekânın gerçek ürün desenini değiştirmesi; iPhone'da çalışmayan ağır bir demo; yalnızca statik tasarımlar. Marka kimliğini, gerçek ürünleri veya alışveriş işlevlerini değiştirme.

## Önce inceleme, sonra uygulama

1. Paket referanslarını gerçek dosya olarak aç, iki referanstaki kamera açısı, kadrajın sakin alanları, ışık kaynakları, ön/orta/arka plan mesafeleri, mekân ölçeği, obje yüzeyleri, maskelerin fiziki oturuşu ve kompozisyon ritmini görsel notlarla analiz et. Genel internet görsel örnekleriyle değiştirme. Görsellerin tek kare olduğunu; bunlardan gerçek 3D geometri çıkmadığını bil.
2. Gerçek Shopify kataloğuna erişimini doğrula; ürün / koleksiyon isimlerini, görsel URL'lerini, bağlantılarını, fiyatlarını ve ana sayfa içeriklerini mağazadan oku. Yetkisizsen erişimi varmış gibi davranma. `venetian-legacy`, `myth-fantasy-realms`, `cult-fandom-icons`, `league-of-legends`, `slipknot-mask`, `best-seller`, `new-arrivals` koleksiyonlarını özellikle incele. Teknik olarak mağaza kaynağı alınmadan örnek ürünleri gerçek veri gibi sunma.
3. Kullanıcının **bitmiş maskelerinin 3D kaynaklarını** (STL/3MF/OBJ/FBX) ve farklı açılardan, işleme ve renkleri gösteren fotoğraflarını ara. Kaynaklar mevcut değilse, ihtiyacın olan **tek bir gerçek maske için** gerekli dosyaları tek seferde net iste: mesh + ön/yan/arka/detay fotoğrafları. 3MF/STL baskı geometrisi bitmiş üründeki boya, taş, tüy, kayış veya kaplamaları tek başına korumaz. Eksik olan parçaları "birebir aynı" diye üretip onaylama.
4. Oyun projesine dokunmadan ayrı bir `Venemask_Cinematic_Showroom` Unreal Engine projesi oluştur. Kurulu UE sürümünü ve donanımı incele; dokümanı o sürüm için doğrula. Mevcut proje/görsel varsa yok sayma.

## Aşama A — önce TEK kusursuz kadraj

* Yalnızca bir Hero alanı inşa et: Venedik esintili ama birebir bir şehri yeniden kurmayı gerektirmeyen koyu taş/teras/kanal/kemer, mesafeli ışık kaynakları, kontrollü yansıma, doğru yüzey pürüzlülüğü ve gölge.
* Bir adet **doğrulanmış gerçek ürün** seç. Geometriyi doğru ölçekte import et; normalleri ve UV'leri kontrol et. Üründeki boyayı, metal folyoyu, glaze yüzeyi, taşları, ipleri ve tüyleri bitmiş ürün fotoğraflarıyla eşleştir. PBR materyaller, micro-roughness, yansıma ve ışık davranışı gerçekçi olsun. Her detay için ayrı doğrulama kanıtı tut.
* Maskeyi fiziksel bir kaide üzerinde gerçekten duruyormuş gibi göster. Yüzeyle temas gölgesi, environment bounce light ve yakındaki yansıma tutarlı olsun. Maskenin göz boşluğu, yüz açısı, kabartması veya süsleri değişmesin.
* Ana ışık sıcak (kademeli amber/altın), dolgu ve gölge tarafı soğuk ve sakin. Arka plan maskeyi boğmasın; yazı için yeterli negatif alan bırak. **Gerçek alan derinliği** kullan: maske keskin, gerisi sahnenin fiziksel mesafesine göre yumuşasın. DoF karanlık bir bulanıklık filtresine dönüşmesin.
* İlk hero karesi için yüksek çözünürlüklü bir **beauty render**, renk/ışık karşılaştırması, maske orijinaline karşı ön/yan referans eşleştirmesi ve normal/depth/matte pass'leri kaydet.

**GATE A — dur:** Kullanıcı iki referansa bakınca aynı sınıfta sinematik kaliteyi görmüyorsa, sonraki sahnelere veya Shopify'a geçme. Yeni logo veya süs ekleyerek kalite eksikliğini örtme. Önce fiziksel görüntüyü iyileştir. Kullanıcıya referans / render yan yana göster; hangi detayların hâlâ eşleşmediğini açıkla. Render alınmadıysa alındı deme.

## Aşama B — gerçek kamera ve birbirine açılan odalar

* İlk kadrajdaki maskeleri 4–5 gerçek ve **kaynağı doğrulanmış** Venemask modeline çıkar. Fiziksel konumları ve boyları tutarlı olsun. Hepsi tek anda görünür ama birbirine yapışık olmasın.
* `Cine Camera Actor`, uygun lens/fokal uzunluğu, `Sequencer`, `Camera Rig Rail` veya düzgün spline kamera yoluyla **tek yönlü olmayan, geri oynatılabilir** kamera rotası kur. Kamera önce Hero'dan hafif yana/ileri gider, sonra aynı mimarinin yeni bir köşesinde koleksiyonları keşfeder. Ardından fiziksel Best Sellers ve New Arrivals sergilerine geçer.
* **Koleksiyonlar:** Venetian Legacy / Myth & Fantasy Realms / Cult & Fandom Icons ana dünyaları birbirinden farklı ışık ve malzeme tonlarına sahip olabilir; aynı Venemask görsel dili korunmalı. LoL alt dünyasına girince soğuk fantastik/teknolojik vurgu, Slipknot'ta daha sert sahne ışığı ve grafit/kırmızı alt tonları kullanılabilir. Hepsini Venedik dekoruyla doldurma.
* **Best Sellers:** Gerçek, mağazada mevcut en az 5 uygun ürünün fiziksel sergisi. Kullanıcı bir üründen diğerine ilerleyince kamera onun konumuna yakınlaşır, önceki ürün uzakta kalır; ad ve fiyat yalnızca seçili gerçek ürüne ait olur.
* **New Arrivals:** Aynı yöntemin kopyası olmasın. Sahnenin farklı yönüne, yeni ürünlerin olduğu bir bölgeye doğal kamera geçişi. Derinlik, lens, pozlama ve ışıkla farklı ama tutarlı kimlik oluştur. Ürünlerin yerleri tutarlı kalır, teleport/fotoğraf değiştirme yok.
* **Ürün detayı:** Seçilmiş gerçek maskeye yaklaşan camera dolly, 2–3 doğrulanmış açı, malzeme detayı ve satın alma paneli için negatif alan. Nesnenin görünmeyen arka yüzünü uydurma.
* Ara kareleri ve ters oynatmayı kontrol et: kamera mesh içine girmesin, DOF/pozlama patlamasın, zıplama, ışık flicker veya keskin jump olmasın.

**GATE B:** Hero → koleksiyon → best sellers (en az iki ürün) → new arrivals → ürün detayı → geri dönüş akışını ekran kaydıyla göster. İnteraktif önizleme sağlanmıyorsa ayrı kamera sekansları gerçek çıktılarla kanıtlanmalı. Ürünler tek bir slaytta sıra sıra beliren resimler gibi görünüyorsa başarısız say.

## Aşama C — Unreal render'ını web'e aktar: önce teknik seçenekleri karşılaştır

Unreal'da `Movie Render Queue`/`Movie Render Graph` üzerinden EXR/PNG ana çıktı üret; erişilebilir ve uygun olduğu durumda Path Tracer kullan. Path Tracer ile ışıktan yansıma kalitesini artırırken tüy/şeffaflık sorunlarına ve render maliyetine dikkat et.

Web için şu alternatiflerin gerçek iPhone üzerinde karşılaştırmasını yap:
- **A — Önceden render edilmiş optimize görüntü dizisi:** ScrollTrigger benzeri kaydırmaya bağlı kare seçimi; ara kareyi tam kontrol eder, fakat aktarılan veri yükü ve mobil bellek çok artabilir. Bölümlere ayrılmış, talebe göre yüklenen avif/webp dizileri düşün.
- **B — Web için hazırlanmış videonun kontrollü kare araması:** Daha küçük aktarım olabilir; iOS Safari'de `currentTime` seek gecikmesi, çözme ve kare sıçramaları mutlaka test edilmeli. Canlı görüntü doğrulaması olmadan "sorunsuz" deme.
- **C — Hibrit:** Pre-render kamera rotası + canlı HTML/Liquid alışveriş içeriği + sınırlı sahneye uyumlu pointer tepkisi. Benim önceliğim **C**, ama A/B temel görüntü yöntemlerinden hangisinin daha iyi olduğu testle belirlenecek.

Açık gerçek zamanlı 360° mouse kamerayı yalnızca prerender ile vaat etme. Böyle bir özgürlük isteniyorsa optimize edilmiş gerçek mesh/WebGL ile ayrı performans doğrulaması yap. İlk açılışta hemen görünen bir hero poster/still kullan; lazy loading ve farklı mobil kadrajlar hazırla. Hareketi azalt tercihi ve JS kapalı statik fallback zorunlu.

## Aşama D — Shopify teması

Shopify CLI ile mağazadan mevcut **yayındaki temanın güvenli kopyasını** al. Yalnızca **UNPUBLISHED** yeni tema veya dev theme'de geliştir; kullanıcı açıkça istemedikçe yayınlama veya mevcut ürünü/yorumları değiştirme. Mevcut Safari kenar-to-edge, chat butonu ve yüzen ürün kartı davranışlarını regresyonla doğrula.

Yeni hareketli ana sayfayı gerçek koleksiyonlar, adlar, fiyatlar ve doğru ürün URL'leriyle bağla. Grafik sahne işlevsel UI'yı resmin içine gömmesin: koleksiyon seçimi, ürün detayına gitme, varyant seçimi, miktar, sepete ekleme, arama, değerlendirmeler ve checkout Shopify tarafından çalışsın. Ürün sayfaları da özgün kamera/sahne kompozisyonuna sahip olsun; ancak alışveriş kontrolleri saklanmasın.

Ana sayfa tamamlanıp onaylandıktan sonra diğer sayfalara yay: collection ve alt collection, list collections, ürün, Hakkımızda/Atelier, FAQ, iletişim, yorumlar, sepet, arama. Bunları tek şablonun farklı yazılarla çoğaltılması şeklinde yapma. Ürün sayfası ihtişamlı ama kullanım açısından berrak olsun.

Shopify'daki mevcut Venemask marka logosu, yazı düzeni, kategori başlıkları, menüler ve gerçek metinler kaynak alınsın; referans görsellerin üzerinde uydurulmuş isim ve $ fiyatları kesinlikle gerçek veri kabul etme. Ürün görselleri sahnede yeniden ışıklandırılmış ürünler olmalı; orijinal ürün fotoğrafını yalnızca 2D `<img>` olarak büyük arka planın üzerine koymak yeterli değil.

## Teknik ve görsel kalite kontrol

* Masaüstü en az 1440×900; mobil en az 390×844 ve bir iPhone Safari testi. Aynı kamera anlarında kaynak referans / Unreal render / gerçek tarayıcı çıktısını yan yana koy.
* 0%, 15%, 30%, 50%, 70%, 85%, 100% scroll anlarında; ileri-geri, hızlı kaydırma, yarıda durma ve tekrar geri dönüşte ekran kaydı yap.
* Ürünlerin kendi yüzeyi ve konumuna sadakat; bozuk maske geometrisi, yanlış ürün metni/fiyatı, maskelerin aniden değişmesi veya render karelerinin zıplaması ağır hata sayılır.
* İlk yükleme, LCP/CLS, ağ/bellek yükü, ısı ve pil etkisi; erişilebilirlik, klavye, `prefers-reduced-motion`, dokunma ve varyant/sepete ekleme testleri raporlanmalı. Mobilde ağırsa daha hafif alternatif gerek.
* "Çalışıyor" gibi kanıtsız cümleler yerine gerçek render yolları, sekans dosyaları, test URL'si, kaynak kod yolları ve test ekran kayıtları teslim et.

## Çıktı ve çalışma disiplini

Öncelik sıran: **(1) tek doğru ürün + kusursuz hero render → (2) gerçek sahne ve kamera rotası → (3) Shopify entegrasyonu → (4) diğer sayfalar.** Baştan bütün siteyi yüzeysel şekilde tamamlayıp sunma. Her aşama kapısında PASS / FAIL, eksikler ve görsel kanıt ver. Yetki, model, Unreal kurulumu veya gerçek fotoğraf yetersizse bunu açıkça belirt, hangi dosya ve neden gerektiğini tek mesajda sor; eksik girdiyi hayali bir nesneyle kapatma.

Başlangıç görevin: yüklenen iki görseli analiz et, mevcut proje/ürün varlıklarına bak, **ilk gerçek maskeyi seç**, Stage 1 için sahne dosyalarını oluştur ve ilk karşılaştırmalı hero render'ı üret. Bu render görsel olarak referans sınıfına girmeden Shopify düzenlemesine başlama. **Statik AI mockup veya yeni üretilmiş farklı maske teslim etme.**

> Bu belge önceki genel Venemask promptlarını geçersiz kılar. Hem görsel yönde hem teknik sırada bu brief geçerlidir.
