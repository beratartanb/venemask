# Venemask — Claude Code Hazır Başlangıç Paketi (29 Ekim 2026)

**Amaç:** Önce Unreal Engine'de gerçek maskeyle sinematik, doğrulanmış sahne. Sonra gerçek kamera, sonra Shopify. Bu paket maskelerin 3D kaynaklarını içermez; kullanıcıdan alınmaları gerekir.

## Kurulum

1. ZIP'i aç. Dosyalar **`.claude/skills/` klasörü korunacak** şekilde bir Claude Code çalışma klasörüne yerleşsin.
2. Claude Code'u bu klasörde aç. `CLAUDE.md` ve `CLAUDE_MAIN_PROMPT.md` dosyalarını okumasını iste. Ekli iki JPG ve V6 kaynak ZIP'i otomatik olarak çalışma klasöründe bulunur.
3. İsteğe bağlı, resmi Claude Code eklentisi `frontend-design` yükle: Claude Code içinde `/plugin install frontend-design@claude-plugins-official`. Yüklü değilse önce `/plugin` menüsünden resmi plugin dizinini kontrol et. Tasarım becerisi Unreal Engine, mask modelleme veya render yetkisi vermez.
4. Unreal Engine, sahne projesi ve kullanıcının gerçek maskesi STL/3MF dosyaları Claude Code'un eriştiği bilgisayarda olmalı. Eksikse Claude bunu açıkça belirtmeli. Birinin mevcut oyun projesini yeni mağaza seti için değiştirmemeli.
5. `CLAUDE_MAIN_PROMPT.md` içeriğini Claude'a gönder ya da "Bu dosyaya göre işi uygula" de. İlk teslimat **bir gerçek maskenin doğrulanmış tek beauty render'ı** olacak.

## Kaynaklar

`references/01-...jpeg`: Çok maskeli vitrin, mekânın görsel sürekliliği, ürünler arası sakin boşluklar.
`references/02-...jpeg`: Ana hero, fiziksel materyaller, sinematik boşluk ve ışık.
`references/Venemask_Sahne_V6_Kaynak.zip`: Eski çalışan web prototipi; sadece etkileşim başlangıcı.
`references/Venemask_Sahne_V6_Demo.mp4`: Kullanıcının önceki hareket kurgusu.

## İşlem kapıları

**A:** Bir gerçek maske + orijinale bağlı mesh/material + örnek düzeyinde hero render.
**B:** 4–5 gerçek maske + doğru kamera rotası + ara kare kontrolleri.
**C:** Render sonrası scroll / touch / hover karşılaştırmalı çalışan web prototipi.
**D:** Gerçek ürünleri alan, yayınlanmamış Shopify tema taslağı.

Önceki denemelerin hatası: gerçek sinematik sahne oluşmadan CSS ile maske fotoğraflarını yüzey üzerine ekleyip hareket ettirmek. Bu paket bunun tekrarını açıkça yasaklar.
