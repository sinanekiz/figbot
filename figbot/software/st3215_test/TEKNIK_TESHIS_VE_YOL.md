# FIGBOT: yapılabilirlik, neden kaçırıyor, referans yazılım

**29 Eylül güncellemesi — APK 0.32.0-work-surface:** Kullanıcı taban altının
incirin durduğu masadan **65 mm yukarıda** olduğunu doğruladı. Önceki Z = 0
masa kabulü bu kurulum için yanlıştı. Hedefe Git'e uzun bas → Taban yüksekliği
(cm) → **6,5** kaydıyla masa Z = −65 mm, geçici 25 mm kavrama açıklığı
Z = −40 mm olur. Kamera projeksiyonu ve yol/kalibrasyon zemin kontrolleri
bu aynı düzlemi kullanır; URDF, koordinat başlangıcı ve motor sıfırları değişmez.
Kayıtsız varsayılan 0 eski kurulum uyumu içindir. v32 Xiaomi'ye yüklendi;
6,5 cm UI'dan kaydedildi ve APK yeniden yükleme/uygulamayı yeniden açma sonrasında
`work_surface.xml` içinde korunduğu doğrulandı. Kaydetmek hareket başlatmaz,
kalibrasyon veya deneme geçmişini silmez.

**282 JVM testi ve lint geçti.** Bilinen, değişmemiş etiket bağlantısında yeni
tarama 2 öğrenme + 2 bağımsız kontrol duruşudur; önceki 7 duruşlu kayıtlar kabul
edilir, bilinmeyen bağlantıda 12 duruş korunur. v31'de 02:52:46–02:52:54 arasında
4 duruşlu başarılı tarama canlı gözlendi: kontrol RMS 7,2 / en büyük 8,2 mm.
Tarama çağrılarımızın arasında kullanıcı tarafından başlatıldı; başlatmayı
kendimiz yapmış gibi kaydetmiyoruz. Kanıt: `reports/diagnostics_20260929/calib31_live.log`
ve `tmp/calib31_run1.png`. Sonraki v31 yaklaşma/kapanma/kaldırma, eski yanlış
Z = 0 hesabıyla çalıştı; başarılı incir alma doğrulanmadı.

**Son v32 canlı denemesi:** Yeni telefon kadrajında eski kayıt 44,8 mm / 12,6°
farkla reddedildi. Bu kez başlattığımız 03:10:24–03:10:32 taraması dört duruşu
topladı, ancak kontrol RMS 11,3 / en büyük 15,5 mm ile reddedildi. Kalibrasyon
veya incir toplama başarılı deneme olarak kaydedilmedi.

Ölçümde 3→4 duruşları aynı model dönüşüne sahip. Beklenen etiket ötelemesi
23,094 mm, kamerada ölçülen 34,207 mm: bu çiftteki farkı sabit etiket bağlantı
ofseti veya masa yüksekliği düzeltemez. Son duruş, uydurulan modele göre optik
derinlikte +12,1 mm ve kamera düşeyinde +8,8 mm sapıyor. Görüntü geometrisi yanlılığı
ile gerçek fiziksel hareket arasındaki neden henüz ayrılmadı. Kanıt:
`reports/diagnostics_20260929/ground32_math_diagnosis.json` ve `reports/diagnostics_20260929/ground32_live.log`.

03:13'te PC köprüsü oturumu zaman aşımına uğradı; bağlantı kaybında tutmayı koruma
ayarı doğrulandı. Sonraki doğrudan salt okunur COM5 kontrolünde motorlar durağan,
sıcaklıklar 33–37 °C idi. Ham köşe/iç parametre incelemesi için varsayılan kapalı
`marker_diagnostics` geliştirici seçeneği eklendi: saniyede bir, 32 kayıtlık
PNG/JSON döngüsü. Hareket politikası değişmiyor; bu tanı denemesi sıradaki adımdır.

**Önceki 29 Eylül güncellemesi — APK 0.30.0:** Aşağıdaki incelemede bulunan hız aktarımı,
kıskaç kapanırken gövde hareketi ve belirsiz kavrama sonucu sorunları düzeltildi.
251 birim testi ve lint geçti. Örnek hızlı plan15,905s'den5,417s'ye indi;
bu fiziksel süre ölçümü değildir. Kalıcı kıskaç ayarı ve kapanmadan önce model
uç kontrolü eklendi. Gerçek parmak merkezi/zemin eşlemesi henüz bağımsız
doğrulanmadı; yeni APK ile başarılı incir toplandı iddiası yoktur.

28 Eylül 2026. Kinematik, görüntü geometrisi ve yayıncının kaynakları ayrı
incelenip sonuçlar birleştirildi. Bu inceleme sırasında motor hareketi, EEPROM
yazımı veya üretim kontrol kodu değişikliği yapılmadı. Aşağıdaki teşhisler
uygulanmış düzeltme veya başarılı yeni toplama sonucu değildir.

## Karar

**Mevcut SO-101 ile sabit masa üzerinde güvenilir incir toplama geliştirilebilir.
Donanımı atıp yeni kol almak için kanıt yok.** Aynı kol ve kıskaç daha önce kuru
inciri havada tutmuş: [20 Eylül fiziksel kanıtı](KAYITLAR/SURUS_20260920T192232Z/incir_kaldirma_basarili.jpg).
Bu, mekanik olarak bir kavramanın mümkün olduğunu kanıtlar; farklı konumlarda
otonom başarı oranını veya 3 saniyenin altındaki süreyi kanıtlamaz.

Mevcut APK'nın yeni hedeflerden başarılı toplaması henüz gösterilemedi. Son
denemede yaklaşma/kapanma/kaldırma tamamlandı, fakat görüntüde incir masada kaldı.
Sürekli kamera kalibrasyonunu tekrarlamak aşağıdaki bağımsız eksikleri gidermez.

## Sayısal teşhis

| Konu | Bulgu | Anlamı |
|---|---|---|
| Fiziksel kavrama noktası | URDF uç noktası kullanılıyor; iki parmak arasındaki gerçek kavrama merkezine bağımsız ölçüm yok | İyi etiket eşleşmesi, doğru kavrama noktası anlamına gelmiyor |
| Motor sıfırları | Elle hizalanmış bir referans ve gözlemden türetilen yönler kullanılıyor | Matematiksel model doğru yazılmış olsa bile gerçek kol farklı noktaya gidebilir |
| Kapanma | Başarılı eski hedef 780, mevcut hedef 870; ID6 ofseti aynı | Güncel hedef yaklaşık 7,91 derece daha açık. Eski sayıyı körlemesine kullanmak yerine gerçek parmak açıklığı ölçülmeli |
| Bilek | Eski başarılı duruşta ID5=3128, yeni duruşta1151 | Yaklaşık174 derece dönüş, sabit/hareketli parmağın konumunu değiştiriyor; önemsiz bir fark değil |
| Varış | Eklemler tek tek20 sayım yakınsa tamam kabul ediliyor | Son incir duruşunda bu toleransların birleşimi modelde21,3 mm uç hatasına izin verebiliyor; bu gerçek denemenin ölçülmüş hatası değil, sayısal tolerans sınırı |
| Kamera açısı | Son hedefte aşağı bakış açısı yaklaşık15,6 derece | Dikey1 CPU görüntü pikseli yaklaşık3,36 mm;5 piksel yaklaşık16–17,5 mm masa konumu farkı üretiyor |
| Zemin/piksel | Algılama kutusunun alt ortası zemine temas noktası; kavrama yüksekliği sabit25 mm sayılıyor | Bunlar incirin gerçek temas noktası ve yüksekliğinin ölçümü değil |
| Sınıflandırma | Sarı/siyah alet canlı görüntüde incir sanıldı | Kalibrasyon bu yanlış nesne seçimini çözmez; olumsuz örnekler/çalışma alanı ve temas noktası doğrulaması gerekiyor |
| Kuvvet | Temas eşiği akım8 ve hedef farkı12; eski gerçek kavramada akım3/fark7 kaydı var | Akım algısı tek başına incir var/yok veya Newton cinsinden kuvvet ölçümü değildir |

Kamera duyarlılık sayıları mevcut kayıt üzerinden hesaplanmış örneklerdir;
kameranın gerçekten5 piksel veya1 derece hatalı olduğuna dair ölçüm değildir.
Java kinematiği, Python eşlemesi ve sabitlenmiş üretici URDF'si arasında yeni bir
işaret, birim veya geometri aktarma hatası bulunmadı. Mevcut yatay ekran koordinat
dönüşümünde de inceleme kapsamında yeni bir90 derece dönüş hatası saptanmadı.

Kalibrasyon şu eşitliği uyduruyor:

`B_T(q) × T_M = B_C × C_M`

Burada kol ucu `T` varsayılan model ucudur. Uç çerçevesini `D` kadar değiştirip
etiket bağlantısını `D^-1` ile değiştirince aynı görüntüler yine açıklanabilir.
Bu nedenle5,72 mm kontrol RMS'si gerçek parmak merkezinin doğruluğunu bağımsız
olarak kanıtlamaz. Hareket sonrası12,3 mm/2,6 derece fark da tek başına telefonun
oynadığını kanıtlamaz; model, esneme veya etiket ölçümü de neden olabilir.

## Neden yavaş?

Gerçek Android planlayıcısı motor bağlantısı açılmadan çalıştırıldı. Son hedef
229/-60/25 mm ve önceki ölçülen başlangıç kullanıldığında:

- Kıskaç kapatma hedefi1153→870, hız180 sayım/s: **2,948 saniye**.
- Hızlı seçilse bile sonraki kol aşamaları `min(300, seçilen_hız)` ile sınırlanıyor.
- Bu örnekte yaklaşma→yerleştirme→kapatma→kaldırma→sepet→açma toplamı hızlı
  seçimde yaklaşık **15,905 saniye**; iletişim ve yerleşme beklemeleri hariç.

Bu motorun fiziksel maksimum hızı değildir. Mevcut aşamalı kodun sonucudur.
Kıskacı yaklaşırken açma/kapatma, doğrulanmış kavramadan sonra taşıma ve hedefe
uygun sürekli eklem yörüngeleriyle yeniden zamanlama gerekir. Önce fiziksel
kavrama doğruluğu kanıtlanmalı; hızlandırılmış boş hareket başarı sayılmaz.
Eski kayıtlardaki yaklaşık4 saniyelik öğretme/tekrar çevrimi ve kullanıcı onaylı
bırakma, bu Android yolundan ayrı bir kontrol yoludur. Gerçek3 saniye altı hasat
henüz kanıtlanmadı; referans videodan da böyle bir süre sonucu çıkarılamaz.

## Videodaki adamın farklı yaptığı ne?

[Gönderilen video](https://www.youtube.com/watch?v=59JTCvpG_Ec), Nikodem Bartnik'in
SO-101 videosu. Yayıncının kendi açıklaması ACT/VLA eğitimi yaptığını doğruluyor.
Video metadata'sı ve açıklaması alındı; altyazı alınamadığı için videonun tamamı
izlenmiş gibi bir iddia yok. Karşılaştırma kendi yayımladığı dosyalara dayanıyor.

| Yayıncının sistemi | Bizim mevcut APK |
|---|---|
| Ön ve üst olmak üzere iki RGB kamera | Tek telefon kamerası |
| Kamera görüntüleri ve6 eklem durumu | İncir kutusu, hareketli etiket, varsayılan masa düzlemi |
| Gösterimlerden eğitilen model6 eklem hedefi üretir | Görüntü→XYZ→kol modeli→IK zinciri hedef üretir |
| Öğrenilmiş eklem dizisi, toplu motor gönderimi | Ayrı yaklaşma/yerleştirme/kapanma/kaldırma/taşıma/açma aşamaları |
| Aynı ortamda kaydedilmiş başarılı görev gösterimleri | Bağımsız kavrama merkezi doğrulaması eksik |

Yayıncının [ACT görev2 config'i](https://huggingface.co/nikodembartnik/policy-task2/blob/81e0a59e6ef3c20151d1ab4c42f8df242cb43231/config.json)
iki RGB girdiyi ve6 boyutlu eklem eylemini gösteriyor.
[Eğitim config'i](https://huggingface.co/nikodembartnik/policy-task2/blob/81e0a59e6ef3c20151d1ab4c42f8df242cb43231/train_config.json)
100.000 adım ve CUDA kullanıyor. [Verisi](https://huggingface.co/datasets/nikodembartnik/record-clean-bricks/tree/d0e85b51041f950e08e725ab06a9ec41cbb76e37)
50 gösterim bölümü içeriyor; görev incir değil, parçaları kaba koyma.

[LeRobot motor gönderimi](https://github.com/huggingface/lerobot/blob/b74e2a61133b695eca35997334f22389321ed6db/src/lerobot/robots/so101_follower/so101_follower.py#L193)
altı hedefi tek `sync_write` ile yollar.
[ACT eylem seçimi](https://github.com/huggingface/lerobot/blob/b74e2a61133b695eca35997334f22389321ed6db/src/lerobot/policies/act/modeling_act.py#L99)
öğrenilmiş diziden sıradaki hedefi alır. Bu kaynak yolunda ArUco veya milimetrik
IK yoktur. İncelenen upstream sürüm video öncesinden sabitlenmiştir; yayıncının
kullandığı tam git commit'i yayımlanmış config'de bulunmadı.

Hazır model onun kameraları/nesneleri ve motor normalizasyonuyla eğitilmiş.
Ağırlıklarını bizim telefona koymak kendi incir görevimizi öğretmez. Tek telefonla
aynı öğrenme yaklaşımı için bize ait iyi gösterimler ve tek-kamera model ayarı
gerekir. ACT'nin100 adımlık çıktısı30 fps'de3,33 saniyelik bir dizidir; bir nesnenin
3,33 saniyede toplanacağı veya her karede yeniden görsel düzeltme yapılacağı
anlamına gelmez.

## Seçilen uygulama sırası

1. **Tek fiziksel kavramayı doğrula:** gerçek parmak açıklığı, merkez ve mevcut
   bilek yönü için başarılı kapatma/kaldırma duruşunu ölç. Tek başarılı kayıt
   kalibrasyonun tamamı sayılmayacak; aynı noktada tekrarlanabilirlik sınanacak.
2. **Sabit düzlemi bağımsız referansla eşle:** çalışma alanına yayılan ölçülü
   noktalar veya basılı düzlem referansı ile kamera→masa haritasını kur. Robot
   tabanına bağlantısını bağımsız ölç. Kalibrasyona katılmayan noktalarla denetle;
   yalnız hareketli kıskacın modeline dayanma. Sabit kayıt yeniden kullanılacak.
3. **Kavrama noktasına varışı ölç:** geçişteki geniş takip toleransından ayrı,
   kapanma anında gerçek uç/nesne hizası denetlensin. Fark duruşa bağlıysa motor
   sıfırları/esneme/backlash incelensin; tek global XYZ ofsetiyle gizlenmesin.
4. **Kısa alanda öğretme haritasıyla başarıyı göster:** gerekirse ilk prototipte
   birkaç doğrulanmış kavrama duruşu + masa haritası kullan. Sonra bağımsız
   konumlarda20 denemenin başarı, kaçırma ve bırakma sonuçlarını kaydet.
   Hedefin örtülmesi başlamış sonlu çevrimi yeni nesneye yöneltmesin; otomatik
   aynı-konum tekrar yasağı korunsun.20/20 sonuç bile kusursuz saha garantisi değil.
5. **Akışı hızlandır:** doğrulanmış kavrama/bırakma noktaları arasında eşzamanlı
   motor sürüşü ve kıskaç örtüşmesini geri getir. Kullanıcının istediği süre
   sepetten ayrılmaya başlamadan sonraki incirin sepete bırakılmasına kadar
   ölçülsün; ilk açılma veya eve dönüşle karıştırılmasın.
6. **Öğrenilmiş kontrolü sonra değerlendir:** iyi fiziksel gösterimler biriktikçe
   LeRobot ACT için görüntü/eklem/eylem kayıtlarını kullan. Değişken dış zemin,
   örtülme ve ışık için yeni veri ve ayrı saha testi gerekir; masaZ=0 varsayımı
   araziye taşınmaz.

Mevcut PC'de i7-12700H, yaklaşık16 GB RAM ve RTX3050Ti Laptop4 GB VRAM bulundu.
İlk prototip için telefon kamera/arayüz, PC hesap ve kontrol tarafı olabilir;
Raspberry Pi satın almayı gerektiren bir bulgu yok. Bu donanımda ACT eğitimi ve
çıkarım hızı ayrıca ölçülmedi; yayıncının batch ayarları körlemesine kopyalanmaz.

Geliştirici hesapları `reports/diagnostics_20260928/` altında: kinematik ve
görüntü raporları, çevrim süre hesabını çalışan Java kodu, kaynak metadata'sı
ve SHA256 kayıtları. Bunlar fiziksel deneme komutu içermez.
