# Sanal sürücü doğrulaması — 30 Eylül 2026

## Güncel kontrol düzeni: birlikte hareket ve tekerlek

Kullanıcının son düzeltmesi uygulandı: sol sürükleme beş kol eklemini ters
kinematikle birlikte hesaplar; tekerlek kıskacı açar/kapatır; sağ sürükleme
yalnız görünümü döndürür. Shift + sol derinlik, Shift + tekerlek yakınlaştırmadır.
Yeşil referans sabit parmağın kaynak STL köşelerinden türetilmiştir.

- **9 JavaScript testi geçti**, Vite üretim derlemesi başarılı.
- Gerçek kaynak modelle yakındaki hedefe yaklaşma, en az üç eklemin birlikte
  değişmesi, kıskaç açıklığının korunması, erişilemeyen hedefte sonlu/sınırlı
  sonuç, ekran/derinlik yönleri ve bırakınca durma kontrol edildi.
- Gerçek Three.js OrbitControls sınıfıyla sağ sürüklemenin kamerayı döndürdüğü
  ve normal tekerleğin kamerayı yakınlaştırmadığı olay testi geçti.
- IAB sol sürükleme: beş eklem [0°, −20°, 45°, 10°, 0°] konumundan
  [−3°, −19°, 35°, 18°, −2°] konumuna birlikte geçti. Kıskaç değişmedi.
- IAB tekerlek aşağı: kıskaç yaklaşık 0.400 → 0.495 rad; yukarı: 0.400 rad.
  Beş kol eklemi sabit kaldı. Sayfa yenilendikten sonra son derleme de denendi.
- IAB sağ tuşla basılı sürükleme API'si yok; kamera dönüşü gerçek OrbitControls
  olay testiyle doğrulandı. Fiziksel motor sürüşü sınanmadı ve kilitli kalıyor.
- Masaüstü 1566 × 1004 ve telefon 390 × 844 kontrol edildi; telefon içerik
  genişliği/kaydırma genişliği 375/375 px, yatay taşma yok. Boyut ayarı sıfırlandı.
- Kanıt: `runs/virtual_leader_ik_qa/desktop.jpg` ve `mobile.jpg`.

| Tarayıcı kontrolü | Sonuç |
|---|---|
| Sayfa adresi/başlık | http://127.0.0.1:8890/ · FIGBOT · Sanal sürücü |
| Boş sayfa | Model ve kontroller yüklendi |
| Framework hata katmanı | Görülmedi |
| Konsol | İlgili hata veya uyarı yok |
| Ekran kanıtı | Masaüstü ve telefon görüntüleri alındı |
| Etkileşim | Sol sürükleme ve tekerlek görünür değerleri doğru değiştirdi |

Değişen kaynaklar: `src/Kinematics.js`, `src/RobotScene.js`, `src/control.js`,
`src/App.jsx`, `tests/control.test.js`. Mevcut düzen, renkler, yazı boyutları ve
bölüm sırası korundu; kontrol açıklamaları kullanıcının talebine göre değişti.
Hiçbir gerçek motor hedefi, tork veya EEPROM ayarı yazılmadı.

## Önceki sürümün kontrol kaydı

Aşağıdaki bulgular önceki tek eklem sürükleme sürümüne aittir. Güncel fare
düzeni ve JavaScript test sayısı yukarıdaki bölümde belirtilmiştir.

## Sonuç

Sanal eklem kontrolü, konumu koruma, durdur/devam et ve yerel kayıt çalışıyor.
Gerçek kol COM5 üzerinden yalnız okunarak kontrol edildi; altı motor cevap verdi.
Fiziksel sıfır, yön ve çalışma sınırları henüz doğrulanmadığı için gerçek sürüş
düğmesi kilitli. Bu çalışma sırasında motor hedefi, tork veya EEPROM yazılmadı.

## Testler

- Tam Python paketi: **91 geçti**. Son sunucu/denetleyici düzenlemelerinden sonra
  ilgili 19 test yeniden geçti.
- JavaScript: **4 geçti**. Sağ sürükleme yönü, seçili eklem, sınırlı artış,
  pointer bırakılması ve yakalamanın kaybı kontrol edildi.
- Vite üretim derlemesi başarılı. Paket 759.61 kB, gzip 204.37 kB; Vite büyük
  paket uyarısı veriyor. Model/arayüz yerel dosyalardan açılıyor.
- Codex IAB: sol sürüklemede omuz −20° → 1°; bırakınca açı sabit.
  Durdur kontrolleri kilitledi; devam et açtı; sanal poz sıfırlama çalıştı.
- IAB kaydı: `runs/20260930T085229_506172Z_virtual_leader/`, 113 olay;
  `SIMULATION_ONLY`, `camera_included=false`, `training_ready=false` doğrulandı.
- Sağ tuş sürüklemesi IAB'nin sol tuş sürükleme API'si nedeniyle gerçek tarayıcı
  jesti olarak uygulanamadı; yön ve pointer bırakılması JavaScript olay testinde
  doğrulandı.
- COM5 son okuma: 1966, 805, 3950, 2619, 1253, 743. Tüm torklar 0, hızlar 0.
  Bunlar enkoder sayımlarıdır; fiziksel açı eşlemesi olduğu iddiası yoktur.
- Zaten açık sunucuya ikinci başlatma doğru URL'yi kullanarak çıktı; ikinci
  seri bağlantı veya sunucu oluşturmadı.

## Tasarım karşılaştırması

Konsept: `design/concept.png` (1586 × 992). Yerel IAB ekran görüntüleri:
`design/desktop-native.jpg` aynı ölçüde, `design/desktop.jpg` normal
1566 × 1004 görünümde, `design/mobile.jpg` 390 × 844 görünümün tam sayfası.
Geçici ekran boyutu ayarı sıfırlandı. Konsept ve son `desktop.jpg`, aynı
kontrol sırasında `view_image` ile ayrı ayrı incelendi.

| Nokta | Konsept / ekran kanıtı | Düzeltme veya bilinçli fark |
|---|---|---|
| Metin ve sıra | Sanal sürücü; Eklemler, Kıskaç, Gerçek kol, Gösterim kaydı | Aynı ana başlıklar ve sıra; gerçek durum COM5 ve okuma mesajıyla gösteriliyor. |
| Yerleşim | Beyaz başlık/sağ kontrol bölümü, gri 3D alan, alt durum satırı | Aynı yapı; kontrol bölümü 340 px. Ek fiziksel geri bildirim nedeniyle bölüm dikey kaydırılabilir. |
| Tipografi | Kalın başlıklar, sade sans yazı, küçük açıklamalar | Segoe UI; başlık 26, bölüm 19, kontroller 14, açıklamalar 12 px. Dar ekranda 23 px başlık. |
| Renk | Mavi kol, gri zemin, yeşil seçim, kırmızı durdur | Korundu; beyaz kontrol zemini ve düz renkler. Model ışığı aşırı parlak görünümü azaltacak şekilde ayarlandı. |
| Model | Konseptin çizilmiş ve geometrisi hatalı SO101 örneği | SHA256 doğrulanmış gerçek SO101 STL ve MuJoCo dönüşümleri kullanıldı. Görünümdeki fiziksel şekil farkı kasıtlıdır. |
| Kadraj | Kolun tamamı görünür | İlk sabit kamera büyük ekranda kıskacı kesiyordu; model sınırlarına ve en/boya göre kadraj hesabıyla düzeltildi. |
| Kontrol simgeleri | Çizilmiş fare/robot simgeleri | Metinli fare açıklamaları ve basit kontrol işaretleri kullanıldı; uygulama işlevleri anlaşılır ve erişilebilir etiketlidir. |
| Dar ekran | Konsept masaüstü görünümü | 390 px ekranda başlık ve kontroller, ardından 3D alan ve eklemler alt alta; yatay taşma yok (375 px içerik/375 px kaydırma genişliği). |

İlk ekran metin farkları: fiziksel eşleme açıklaması, bağlantıyı kapat,
motor sayımları, simülasyon kaydında kamera olmadığı bilgisi ve sanal poz
sıfırlama eklendi. Bunlar gerekli işlev/durum bilgisidir. Konseptteki COM3
yerine gerçek COM5 kullanılıyor. İşlevsiz metin veya dekoratif panel eklenmedi.

Uygulamanın düzeni, metin hiyerarşisi, tipografisi ve paleti konsepte göre
doğrulandı. Yukarıdaki model, simge ve bölüm genişliği farkları bilinçlidir;
konseptin birebir piksel kopyası olduğu iddia edilmez. Düzeltilmemiş kadraj
kesilmesi veya yatay taşma görülmedi.

Tarayıcıdaki yorum katmanı bir kontrol sırasında fare olaylarını yakalıyordu;
Escape ile kapatıldıktan sonra sol sürükleme doğrulandı. Son sürümde teşhis
konsol çıktıları kaldırıldı.

## Kanıtın sınırı

Fiziksel hareket, çarpışma, tutuş kuvveti veya otomatik incir toplama sınanmadı.
Kamera verisi kaydedilmedi. Kinematik görselleştirme eğitim/başarı kanıtı değildir.
Yeni kaynaklar eski bilgi grafiğinde takip edilmiyor; bu dosyalar doğrudan
kaynak okumaları, testler ve tarayıcı kontrolüyle doğrulandı.
