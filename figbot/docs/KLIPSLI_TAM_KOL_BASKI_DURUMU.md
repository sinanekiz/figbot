# Tam klipsli kol — 7 Eylül 2026 kontrolü

**Güncelleme — DEC-050:** Aşağıdaki metin V4 öncesi eksiklerin tarihsel listesidir. Kullanıcının sonraki isteğiyle geçmeli/pimli tam masa prototipi artık `cad/prototype_arm/aero_v4` içinde uygulanmıştır. Güncel baskı ve montaj kaynağı o klasördeki `ONCE_OKU.md` ve `FINAL_AUDIT.json` dosyalarıdır. V3 parçaları yeni sete karıştırılmaz. Motor merkez vidaları korunur; fiziksel dayanım doğrulanmış sayılmaz.

**Tam kol seti henüz klipsli olarak uygulanmadı.** Bu, yalnızca dayanımın ölçülmemesi değildir: aşağıdaki eski bağlantılar yeni başlık gövdeleriyle aynı montaj arayüzünü kullanmıyor. Eski dosyaları bir araya getirerek basmak eksik entegrasyonu çözmez.

## Hazır olan sınırlı baskılar

| Dosya | İçerik | Kapsam |
|---|---|---|
| `cad/prototype_arm/snap02/S02_TEK_TABLA_3_PARCA.stl` | MG996R altı kollu başlık: 1 gövde + 2 kapak | Enerjisiz uyum, ardından şartlı yüksüz kısa uzantı denemesi |
| `cad/prototype_arm/snap03_mg90/S03_TEK_TABLA_3_PARCA.stl` | MG90 çapraz başlık: 1 gövde + 2 kapak | Aynı sınırlı deneme; başlık 35 × 16,3 mm |

Bu dosyalar motor gövdesi tutucusu değildir. Orijinal başlığı sarıp dönen kısa çıkış bağlantısıdır. Servo milinin merkez vidası korunur. Başlık kapakları klipslidir; bütün robot vidasız değildir.

## Ana kolda kalan tasarım işleri

| Mevcut V3 parçası | Adet/kol | Klipsli sürüm için gereken iş |
|---|---:|---|
| V3-01 Yaw base | 1 | Motor gövdesi tutma yük yolu ve tabana sabitleme; mevcut M3 kelepçe kaldırılmadan yeni tutucu tasarlanmalı |
| V3-02 Yaw deck | 1 | Altı kollu cep/kapakları döner tablaya entegre et; merkez vida erişimi ve alttan kapak takılma yolu |
| V3-03 Thrust washer | 1 | Yeni tablanın eksenel istifi sonrasında kalınlık/sürtünme boşluğunu kontrol et |
| V3-04 Shoulder yoke | 1 | İki motorun gövde tutucuları, taban bağlantısı ve kapaklara erişim |
| V3-05 Upper hub | 1 | İki karşılıklı MG996R cebi; çift motor eksenleri, dönme yönleri ve kapak erişimi; profil bağlantısı |
| V3-06 Elbow yoke | 1 | Motor tutucu, karşı yatak, kol profilinin kilidi |
| V3-07 Fore hub | 1 | MG996R cebi, karşı pivot eksenel tutması ve profil bağlantısı |
| V3-08 Wrist yoke | 1 | MG90 kasası tutucu, karşı pivot ve yeni dönen gövde açıklığı |
| V3-09 Wrist palm / fixed jaw | 1 | Bilek sürücüsüyle mekanik kilit; kıskaç motoru tutucu ve hareketli çene açıklığı |
| V3-10 Moving jaw | 1 | Eski Ø20 mm bağlantı yerine 35 mm uzun çapraz başlık cebi; parmakla tek parça yük yolu ve tüm kavrama hareketi |
| V3-11 MG996R clamp | 8 | Vidalı kelepçelerin yerine ayrı tasarlanmış, sökülebilir ve gövdeyi kaydırmayan tutucu |
| V3-12 MG90 clamp | 4 | Mikro servo için ayrı tutucu; büyük motor klipsini ölçeklemek yeterli değil |
| V3-13 Idler sleeve | 2 | Mevcut M4 mil yerine seçilecek pivotla eşleşme ve radyal boşluk |
| V3-14 Idler washers | 4 | Karşı pivotun eksenel kilidi ve sürtünme boşluğu |
| V3-15 Wrist drive plate | 1 | MG90 çapraz cep ile avuç bağlantısını yeniden kur; mevcut iki M3 birleştirme vidası hâlâ modelde |

300/220 mm eklem mesafeleri ve 124 mm omuz yüksekliği korunuyor. Mevcut 20 × 20 × 1,5 mm metal profil kesimleri 235/161 mm; bunlar basılacak STL parçası değil. Tamamen basılı kirişlere geçmek ayrıca kütle/sehim/katman dayanımı hesabı ve DECISIONS kaydı gerektirir.

## Uygulama sırası

1. SNAP02 ve SNAP03 gerçek başlık, merkez vida ve motor kasasıyla enerjisiz denenir. Cep oturması, kapağın tam kilitlenmesi ve kasaya sürtmeme ayrı ayrı doğrulanır. Gerekli gerçek toleranslar ana eklemlere aktarılır.
2. Dönme yükünü taşıyan cep, eklemin kendi gövdesine entegre edilir. Bağımsız kısa deneme uzantısı nihai eklem değildir. Karşı yataklar korunur; motor miline tek başına eğilme yükü yüklenmez.
3. Motor kasaları ve profil kilitleri ayrı tasarlanır. Klips mandalı tek başına ana tork yoluna konmaz; yükü omuz/durdurucu yüzeyler taşır. Eksenel mil tutma için yalnız kapağın kilitlenmesine güvenilmez.
4. Tam montaj, kapakların takılma/sökülme yolları, merkez vida erişimi, kablolar ve hareket boyunca çarpışmalar kontrol edilir. Ardından STL/STEP, montaj, URDF ve testler birlikte yenilenir.
5. Küçük uyum baskısından sonra eklem eklem basılır. İlk baskı gözetiminde ilk katman ve klips yarıkları kontrol edilir. Başarılı tek başlık uyumu yük/ömür/fırlatma performansı anlamına gelmez.

## Evde yokken baskı konusu

Bu çalışmada yazıcıya dosya veya başlatma komutu gönderilmedi. Yazıcının mevcut tablosu, filament ve dilimleme önizlemesi kontrol edilmiş değil. Otomatik parça çıkarma doğrulanmış değil: birden fazla ayrı tabla, arada biri parçaları almadan sırayla tamamlanamaz. Bağlantı örnekleri dışındaki eski tam seti yeni klipsli sürüm diye başlatmayın.
