# Gösterim kamerası ve pasif kayıt — v0.37 / 29 Eylül 2026

Telefon, `teaching_camera=true` ile açıldığında yalnız localhost:8874 üzerinden
ham RGB JPEG kareleri, kamera yakalama zamanı, oturum kimliği ve iç parametreleri
verir. Kola ait etiket görünmese de kayıt çalışır. Kamera modu motor bağlantısını
başlatamaz. Normal otomatik toplama modunun eşleme kapıları değiştirilmedi.

v0.37 öğretim modunda ham görüntüyü ayrı iş olarak aktarır; ArUco ve YOLO
çalıştırarak görüntü kuyruğunu doldurmaz. CPU görüntü zaman kayması100ms,
PC kare yaşı300ms ve aktarım250ms sınırları değiştirilmedi. Hız artışı gerçek
telefon akışında ayrıca ölçülür; bu değişiklik tek başına kesintisizlik garantisi değildir.

PC `phone_teaching.py`, aynı seri portun tek sahibi olarak altı eklemi ve kıskaç
konumunu kamera ile birlikte kaydeder. Yalnız kullanıcı kolu desteklediğini
bildirdikten sonra `--supported-release` ile tork kapatılır; ardından yalnız okuma
vardır. Bitişte otomatik tork açılmaz. İletişim kesilmesi serbest kolu taşımaz.
Kayıt başlamadan kameradan en az üç ayrı taze görüntü doğrulanır.

Kamera ve kol tabanı sabit kalmalı. Görüntüdeki incir konumu ile kayıtlı eklem
hareketi daha sonra eşlenecek; kolun görüntüde olması zorunlu tutulmaz. Kamera
yalnız incirleri görürse kavrama/kaldırma başarısı için kullanıcı etiketi gerekir.
Her incir ayrı bölüm olarak tercih edilir. İlk örnekler kayıt kalitesini ve gerçek
kavrama yolunu doğrular; tek bir gösterim tüm erişim alanına genelleme sağlamaz.

Kayıt `episode/camera.avi`, `episode/samples.jsonl`, `timing.jsonl`, ilk/son görüntü
ve `status.json` dosyalarını üretir. Kameranın gerçek zaman damgası saklanır;
PC karşılığı aktarım gidiş-geliş süresinden yaklaşık çıkarılır, belirsizlik ayrıca
kaydedilir. Kamera/enkoder farkı200ms üzerindeyse kayıt durur.10Hz hedef hızdır;
gerçek hız ve boşluklar ölçülür. Bu bir LeRobot veri seti veya eğitilmiş politika
olarak sunulmaz; pasif örneklerden eylem çıkarımı ayrıca doğrulanmalıdır.

SO-101 resmi kaynak bağlantısı LeRobot'u önerir. LeRobot'un örnek yaklaşımı:
kamera + eklem durumu + gösterilen hareketleri kaydet → modeli eğit → ayrı test.
Kaynaklar: https://github.com/TheRobotStudio/SO-ARM100 ve
https://huggingface.co/docs/lerobot/il_robots . Bu çalışmada veri buluta yüklenmez.

# Yanal açıya duyarlı etiket doğrulaması — v0.35 / 29 Eylül 2026

Etiketin düzlem normali ile kameradan etikete giden ışın arasındaki açı ölçülür;
görüntünün kendi içindeki dönmesi ile yanal bakış ayrılır. Kare perspektif
modeli korunur. Dört köşenin yalnızca piksel uyumu yeterli sayılmaz: görüntüdeki
en dar genişlik ve köşe hatasının 3B konum/yöne etkisi ayrıca değerlendirilir.
Kalibrasyon ve hedef hesabı yalnız taze, tek anlamlı, bu kontrolden geçen
ölçümleri kullanır. Tarama yolları aynı görüş kalitesini öngörerek süzülür.
Kararlı karelerin yönleri artık tek kareden alınmaz; SO(3) üzerinde birleştirilir.

Menüde etiket satırı görüş açısını gösterir. Hedefe Git'e uzun bas → Kamera
mesafesini kontrol et ekranında da açı ve ölçüme uygunluk görünür.
Yetersiz açıda metrik ölçüm sunulmaz; daha karşıdan görüş istenir.

301 JVM testi, lint ve telefonda 8 native test geçti. Native testte 20/40/60/70°
yanal açı × 0/45/90° görüntü dönüşü = 12 sentetik görünüşün hepsi geçti:
en büyük konum farkı 0,637 mm, yön farkı 0,179°. Bunlar fiziksel kol doğruluğu
veya gerçek kamera için genel hata sınırı değildir.

Mevcut gerçek yan görünüş yaklaşık 63,2°; 33,6 piksel dar genişlikle ölçüme
uygun/kararlı bulundu. 14–23 ms örnek görüntü işleme süreleri görüldü; kontrollü
hız karşılaştırması yapılmadı. v34'te bu durağan görünüş zaten kararlıydı:
32 kayıtlı karede konum standart sapmaları yaklaşık 0,028/0,014/0,096 mm.
Dolayısıyla önceki 15,5 mm RMS / 21,2 mm en büyük kamera–kol eşleme farkının
tek başına açıdan kaynaklandığı veya bu sürümle giderildiği kanıtlanmadı.
Yeni fiziksel eşleme/toplama yapılmadı; kalibrasyon kabul sınırları değişmedi.
Kurulumdan önce bağlantı kesildi ve köprü mevcut konum tutmasını doğruladı;
uygulama kamera modunda açık, motor bağlantısı kapalıdır.

# Tam çevrim aday seçimi — v0.34 / 29 Eylül 2026

Mevcut yedi yaklaşma açısı için yaklaşma–yerleştirme–kapatma–kaldırma–sepet–açma
yolları önceden denetlenir. İlk yaklaşımın sonraki aşaması mümkün değilse diğer
açılar denenir; geçerli tam çevrimler arasından nominal süresi en kısa olan
seçilir. Hız/sıcaklık/eklem ve kalibrasyon sınırları korunur. Temas evreleri
en çok600 sayım/s, ID5 pasif;15mm yerleştirme tercih,10mm yedektir.

293 JVM testi ve lint geçti;112 model hedefinde tam yol107→110, kayıp0.
Ortak hedeflerde toplam nominal zaman%2,86 azaldı; bu fiziksel toplama süresi
değildir. Gerçek kavrama merkezi, incirin zemin konumu ve tüm çalışma alanında
kalibrasyon hâlâ doğrulanmalı. Önce yavaş tek alma/kaldırma denemesi, sonra
tekrarlı başarı ölçümüyle hız artırımı. Yeni fiziksel toplama başarısı yok.

Yedi repo incelemesi, uygulanan beceriler ve eksikler:
`ST3215_TEST/KAYNAK_REPOLAR_VE_TOPLAMA.md`.

# Kamera mesafesi düzeltmesi — 2026-09-29

İncir kutuları artık ARCore nokta/derinlik/yüzey isabetini incir mesafesi olarak
göstermez ve bu alternatif kaynaktan robot hedefi üretmez. Doğrulanmış etiket–kol
eşlemesi ve zemin hesabı varsa **Zemin hesabı … cm** gösterilir. Bu mesafe kamera
ile hesaplanan zemin temas noktası arasındadır; Z ise geçici kavrama yüksekliğidir.
Geçerli referans yoksa **Mesafe ölçülemedi** ve gereken adım gösterilir.
Bu düzlem hesabı kamera hareketi veya AR dünya takibine bağlı değildir; referansın
ve gerçek zemin temas noktasının doğruluğu ayrıca fiziksel olarak ölçülmelidir.

**Hedefe Git'e uzun bas → Kamera mesafesini kontrol et:** Mevcut ID 0 etiketinin
kameraya uzaklığını canlı gösterir. Siyah dış kare 36 × 36 mm olmalıdır.
Kamera merceği–etiket merkezi düz mesafesini cetvelle karşılaştır; eğik görüşte
optik eksen mesafesi farklı olabilir. Motor bağlantısı veya hareketi gerekmez.
Etiket mesafesinin doğrulanması tek başına incir konumunu doğrulamaz.

Sabit tek kamera ile bilinmeyen bir sahnenin metrik derinliği yalnız görüntüden
garanti edilemez. ARCore hareketten derinlik üretir; sabit açılış için ölçülü
referans kullanılmalıdır. Bağımsız incir mesafe kontrolü için aynı yüzeye ayrı
ölçülü etiket yerleştirme seçeneği kullanıcıya soruldu; bu değişiklik ayrı zemin
etiketi modu içermez.

**29 Eylül canlı karşılaştırma:** Sabit açılıştan sonra etikete 23,4 cm gösterildi;
kullanıcı cetvelle yaklaşık 23 cm ölçtüğünü bildirdi. Kayıtlı eşleme taze etiket ve
motor okumalarıyla, yeni tarama yapmadan doğrulandı. Sağ alttaki incirin zemin
temas noktası için 38,8 cm gösterildi; kullanıcı bunu da doğru olarak onayladı.
Bu iki kontrol yaklaşık mesafe uyumudur; tüm alanda milimetrik XYZ doğruluğu veya
incir kavrama başarısı değildir. Kamera kontrolünde motor hareketi verilmedi.
Motor komutlarını reddeden geçici okuma köprüsü bu kontrolün sonunda kapandı.

## Önceki sürüm ve kurulum kaydı: 0.32.0-work-surface

Bu sürüm 36 mm DICT_4X4_50 / ID 0 etiketini canlı izler. Açılış ekranı Kol Kontrol'dür.
İki APK adı aynı uygulamadır; birini yüklemek yeterlidir. Bağlan menüsünde PC köprüsü
ve doğrudan USB seçenekleri vardır.

**Bu kurulum için taban yüksekliği 6,5 cm:** Kullanıcı, kolun taban alt yüzeyinin
incirin durduğu masadan 65 mm yukarıda olduğunu doğruladı. **Hedefe Git'e uzun bas
→ Taban yüksekliği (cm)** yolundan **6,5** veya **6.5** girip bir kez kaydet.
Önceki kurulumlarla uyum için kayıtsız başlangıç değeri 0'dır; bu düzende 0 bırakma.
Kaydetmek hareket başlatmaz, kamera kalibrasyonunu veya denenmiş hedefleri silmez.
Mevcut Xiaomi'ye v32 yüklendi; 6,5 cm kaydı APK yeniden yüklenip uygulama yeniden
açıldıktan sonra da `work_surface.xml` içinde doğrulandı. Yeniden girmen gerekmez.

Bu değerle masa robot koordinatlarında Z = −65 mm, geçici 25 mm kavrama açıklığı
Z = −40 mm olur. Robotun koordinat başlangıcı, URDF ve motor sıfırları değişmez;
kamera–masa kesişimi ile toplama ve kalibrasyon yollarının zemin kontrolleri aynı
masa yüksekliğini kullanır. 25 mm, incirin ölçülmüş yüksekliği değildir.

282 JVM testi ve Android lint geçti. Önceki v31'in 29 Eylül 02:52:46–02:52:54
canlı taraması 4 duruşla tamamlandı (kontrol RMS 7,2 mm; en büyük hata 8,2 mm).
Sonraki yaklaşma/kapanma/kaldırma sırasında başarılı incir alma doğrulanmadı ve
o deneme hâlâ eski Z = 0 masa hesabını kullanıyordu.

**Son canlı v32 sonucu:** Yeni kadrajda eski eşleme 44,8 mm / 12,6° farkla
reddedildi. 03:10:24–03:10:32 arasında başlattığımız tarama dört duruşu topladı,
fakat kontrol RMS 11,3 mm / en büyük 15,5 mm olduğundan kabul edilmedi.
Başarılı v32 kalibrasyonu veya incir alma sonucu yok. Masa yüksekliğini düzeltmek,
bu ayrı etiket/model uyuşmazlığını tek başına gidermedi.

## Kullanım

Kamera ekranı yatay ve dikey kullanılır. **MENÜ** veya kamera alanına dokunmak
kontrolleri açar; **GİZLE**, geri düğmesi veya 6 saniye işlem yapmamak kapatır.
Sağdaki panel kaydırılabilir; bağlantı, kalibrasyon, toplama, hız ve ayrıntılar
buradadır. **DUR** her zaman görünür kalır. Kameraya dokunmak hareket başlatmaz.
Telefonun fiziksel konumunu değiştirirsen kayıtlı kamera eşlemesi yeniden
doğrulanır. Ekranın yön değiştirmesi uygulamanın motor bağlantısını yeniden kurmaz.

**Kavramayı ayrı denemek:** MENÜ içindeki **Hedefe Git** düğmesine uzun basıp
**Burada kavra ve 5 cm kaldır** seç. Kol bulunduğu yerde kıskacı kapatır, 5 cm kaldırıp bekler;
sepete gitmez. Bu komut incirin konumuna yaklaşmaz. Aynı penceredeki **Denenmiş hedef kaydını
temizle** yalnız açıkça yeni toplama turu başlatmak içindir; önceki denenmiş
konumların yeniden seçilmesine izin verir. Normal kullanımda kaydı temizleme.

**Kıskaç açıklığı:** Hedefe Git'e uzun bas → Kıskaç açıklığını ayarla → Ayar seç.
20 Eylül başarılı kaldırma kaydındaki 780 / 1153 değerlerini seçebilir veya sabit
kıskacın o anki konumunu açık/kapalı olarak kaydedebilirsin. Bu seçim hareket
başlatmaz; kayıt yeniden açılışta korunur. Değerler motor sayımıdır, kuvvet veya
milimetre değildir. Başlangıçta önceki uygulamanın gerçek 870 / 1153 komutu
korunur; 780 otomatik uygulanmaz. Geçersiz kayıt otomatik hareketi engeller.

29 Eylül kod düzeltmeleri: hız seçimi tüm çevrime taşındı; sonraki hareketleri
300 sayım/s'ye düşüren hata kaldırıldı. Yerleştirme ve kıskaç hareketleri en çok
600 sayım/s, diğer hareketler seçilen hız ve mevcut eklem sınırlarıyla yürür.
Kapanırken gövde eklemleri taze ölçülen konumda tutulur. Model uç konumu
kapanmadan önce 4 mm / 2° içinde doğrulanır; küçük fark için yalnız bir sınırlı
düzeltme yapılır. Bu, gerçek parmak merkezinin ölçülmüş olduğu anlamına gelmez.
Akım teması aday bilgi olarak gösterir; kapanma tek başına incir tutuldu sayılmaz.

v30'daki aynı örneğin hızlı seçenekte plan süresi
15,905 s → 5,417 s; IO, yerleşme ve görüntü gecikmesi hariç matematiksel süredir.
Gerçek toplama süresi veya başarılı kavrama doğrulaması değildir.

Son yaklaşmadaki 1–1,5 cm yatay yerleştirme, parmakların ileri yönünü izler;
başlangıç duruşuna göre ters yöne hesaplanmaz. Yükseklik bu aşamada korunur.
28 Eylül canlı denemesinde kayıt yeniden tarama olmadan doğrulandı; ayrı kavrama
testinde incir alınamadı. Bu APK için başarılı otomatik toplama henüz doğrulanmadı.

Önceki cihaz denemesi (28 Eylül 23:21): sensör/kamera kontrolündeki eski zaman
damgası karşılaştırması düzeltildikten sonra yaklaşma, kapanma ve kaldırma
gereksiz kamera kesintisi olmadan tamamlandı. Kıskaç boş kaldı. Kaldırma sonrası
etiket/model farkı 12,3 mm / 2,6° olduğu için yeni hedef hareketi bekliyor;
bu fark tek başına telefonun oynadığı anlamına gelmez. Gerçek kavrama merkezinin
modelle eşleşmesi henüz doğrulanmadı; sınırlar bu farkı gizlemek için artırılmadı.

1. Telefonu sabitle; kıskaç arkasındaki etiket net görünsün. Mavi çizgi ve
   ETİKET 0 / kamera mesafesi görünür. Mesafe etiket merkezinedir.
2. Motor kartına Bağlan. Bağlantı bir hareket başlatmaz. Mevcut tutmayı devralmayı
   dener; torku kendiliğinden açmaz. Düğme motorlar tutarken Kolu bırak, serbestken Kolu tut olur. Her iki işlemde de kolu alttan destekleyip ekrandaki onayı ver. Tutma doğrulanana kadar desteği koru.
3. Başarılı kalibrasyon varsa Bağlan sonrasında güncel etiket ve motor konumlarıyla
   otomatik doğrulanıp yeniden kullanılır. Uygulamayı kapatmak kaydı silmez.
   Kamera ve kol tabanı birlikte rijit taşındıysa durunca aynı kayıt doğrulanır;
   yeniden tarama gerekmez. Telefon kola göre veya etiket kıskaca göre yer
   değiştirmiş ve fark kalıcıysa Kalibre'ye bas.
   Doğrulama en az 7 yeni etiket karesi ve 600 ms kanıt ister; tek sapmış ölçüm
   kaydı reddetmez. 12 mm / 8° eşleme sınırı korunur. Hareket algısı kaydı silmez;
   başlatılmış kol hareketi durdurulur ve kendiliğinden yeniden başlatılmaz.
   Otomatik hareket, mevcut tutma üzerinden yavaş bir tarama yapar.
   Yalnız telefon taşındıysa “Etiketin kola bağlantısı değişmedi” işaretli kalsın;
   etiketin bilinen bağlantısı korunup yeni kamera konumu hesaplanır. Etiketi
   söküp farklı yere bağladıysan bu işareti kaldır; iki dönüşüm yeniden öğrenilir.
   Bilinen etiket bağlantısıyla tarama duruşları ve aradaki yol, CPU kamera
   görüntüsündeki dört köşenin kadrajda kalması açısından da denetlenir.
   Bu öngörü nesnelerin etiketi örtmesini garanti edemez; canlı takip denetimi sürer.
   Kıskaç boş, kolun çevresi boş ve kol zeminden yüksek olmalıdır. Kayıtlı hareket
   sınırlarında yeterli pay yoksa tarama başlamaz. Sayısal tarama zemine yaklaşırsa
   reddedilir; bu, gerçek ortamda çarpışma olmayacağının kanıtı değildir.
4. Elle ölçüm için önce kolu destekle → Kolu bırak → Destekliyorum, bırak.
   Ardından Kalibre → Elle ölçüm. Kolu
   destekleyerek farklı konumlara taşı; taban yönünü ve bilek eğimini değiştir.
   Her duruşta 1-2 saniye sabit tut. Ekrana nokta seçmek veya XYZ yazmak gerekmez.
5. İlk kurulumda 8 öğrenme + 4 ayrı kontrol duruşu tamamlanır. Etiket bağlantısı
   biliniyor ve değişmediyse yalnız kamera eşlemesi 2 öğrenme + 2 ayrı kontrol
   duruşuyla yenilenir. Önceki 7 duruşlu geçerli kayıtlar da kabul edilir.
   Aynı konumdaki geçerli kayıt için tarama yapılmaz.
   İlk kurulumda kamera eşlemesi ve etiketin kavrama ucuna dönüşümü birlikte hesaplanır. Kontrol hatası fazla,
   etiket yönü belirsiz veya duruş çeşitliliği yetersizse hareket izni verilmez.
6. Tamamlanınca kol bekler. Hedefe Git seçilen incirin konumunu kilitler ve
   yaklaşma, açık kıskaçla yatay 10–15 mm yerleştirme, kapatma, 50 mm kaldırma,
   kayıtlı sepet konumuna taşıma ve açma yolunu
   hareketten önce hesaplar. Başladıktan sonra incir veya etiket örtülse bile
   bu sonlu yol motor konum geri bildirimiyle tamamlanır. Telefonun sabitliği,
   kamera karelerinin güncelliği ve motor kontrolleri devam eder; DUR çevrimi keser.
   Alma başarısız olsa da sepet hareketi yapılır. Gerçek kavrama ayrıca görüntüden
   doğrulanmalıdır; hareket tamamlandı mesajı incirin alındığı anlamına gelmez.
   Kapanırken akım artışı, hedefe kalan açıklık ve parmakların durması birlikte
   izlenir. En az 180 ms tutarlı temas belirtisinde kapanma durdurulur; yalnız
   6 encoder sayımı ek tutma uygulanır ve bu açıklık taşımada korunur.
   Bu, kalibre edilmiş kuvvet ölçümü veya incirin tutulduğunun kanıtı değildir.
   Temas adayı oluşmazsa kayıtlı kapalı hedef kullanılır; gizli 24 sayım eklenmez.
   Sonuç CLOSED_UNVERIFIED olur: incirin tutulduğu veya kıskacın boş olduğu
   yalnız bu sonuçtan anlaşılamaz.
   Motor hatasından sonra DUR, yalnız sabit ve sağlıklı tutma yeniden doğrulanırsa
   hatayı onaylar; hareketi kendiliğinden başlatmaz. İlk hata dosyada da tutulur.
7. Başlatılan hedef konumu hareket komutundan önce kalıcı kaydedilir. Aynı masa
   konumunun 35 mm çevresi tekrar seçilmez; bu, algılama titreşimi için yazılım
   eşleme yarıçapıdır. Yeni turda tekrar denemek istiyorsan Hedefe Git'e uzun bas
   ve Kaydı temizle'yi seç. Uygulamanın kapanması veya kalibrasyonun yenilenmesi
   bu kaydı kendiliğinden silmez. Yeni incir konumu için Hedefe Git'e tekrar bas.
   Yatay yaklaşma mümkün değilse aşağı eğimli kıskaç açıları sırayla denenir;
   eklem sınırları, masa açıklığı ve sonrasında kaldırabilme koşulu korunur.
   Tarama ve yaklaşma hesapları ayrı iş parçacığında yapılır; bu sırada motor
   haberleşmesi devam eder. DUR, bağlantı/kalibrasyon değişimi veya eskiyen
   ölçümler hesaplanan hareketin sonradan başlatılmasına izin vermez.

## Kapsam ve sınırlar

- Baskıdaki siyah dış kare 36 mm, kesilecek kağıt 48 mm. Kullanıcı 36 mm'yi doğruladı.
- Etiket çenelere değil, sabit gripper gövdesine rijit bağlanmalı; karton bükülmemeli.
- Kamera iç parametreleri ARCore CPU görüntüsünden alınır; OpenCV kamera eksenleri
  ARCore eksenlerine açıkça dönüştürülür. İşaret mesafesi için ARCore derinliği gerekmez.
- Kullanıcının 29 Eylül'de doğruladığı mevcut düzende taban altı masadan 65 mm
  yüksektir. Bu bilgi önceki “aynı seviye” kabulünün yerini alır.
  Geçerli kalibrasyonla incir kutusunun alt orta noktasından masa düzlemine ışın
  kesişimi kullanılır. Yükseklik uygulamaya bir kez kaydedilir; eğimli zemin
  tek bir yatay masa yüksekliğiyle modellenmiş sayılmaz.
  Alternatif ARCore derinlik/düzlem ölçümü korunur. Özellik noktası mesafesi yalnız
  yaklaşık ekran bilgisidir, hareket hedefi değildir. Geçici masa denemesi kavrama
  yüksekliği 25 mm'dir; incir yüksekliği ölçümü değildir. Sabit kamerada bu masa
  hesabı için AR derinliği veya kamerayı sallamak gerekmez.
- Telefon hareketi, AR izleme kaybı, uygulamadan çıkış/oturum değişimi veya etiket
  kaybı hareketi durdurur. Kısa görüntü kaybı kaydedilmiş dönüşümü silmez.
  Yeni oturumda kayıt güncel, durağan motor ve etiket okumalarıyla doğrulanır.
- Kalibrasyon SO-101 modeli ve motor okumalarına referanslıdır; motor sıfırlarını
  veya kol geometrisini değiştirmez. Bağımsız fiziksel uç doğruluğu testi gereklidir.
- Canlı görsel uç geri bildirimi ve hareket başında en çok 10 mm düzeltme vardır;
  20 mm'den fazla model/görüntü farkı reddedilir. Her video karesinde rota değiştirmez.
- Bilinen etiket bağlantısıyla 4 duruşlu tarama v31'de canlı gözlendi. Bunun
  kanıtı `reports/diagnostics_20260929/calib31_live.log` ve `tmp/calib31_run1.png`.
  v32'nin yeni masa yüksekliğiyle taraması ise kontrol hatası nedeniyle reddedildi;
  kanıt `reports/diagnostics_20260929/ground32_live.log`. Kavrama doğruluğu
  PHYSICAL VALIDATION REQUIRED; başarılı otomatik incir toplama henüz doğrulanmadı.
- Geliştiriciye özel `marker_diagnostics` intent seçeneği varsayılan kapalıdır.
  Açıldığında ham etiket köşeleri/kamera iç parametrelerini incelemek için saniyede
  en çok bir PNG/JSON çifti kaydeder; 32 kayıtlık döngü kullanır. Hareket izinlerini
  veya kalibrasyon eşiklerini değiştirmez; canlı tanı doğrulaması sürmektedir.

Geliştirme: OpenCV 4.12.0; yerel birim testleri ve telefonda motora/kameraya erişmeyen
native matematik testleri. Eski AR oturumundan kaydedilmiş 4-dokunuş kalibrasyonu
hareket yetkisi olarak yeniden yüklenmez; doğrulanmamış sabit kamera asset'i
Kol Kontrol ekranında hedef koordinatı üretmez.

## Kalibrasyon neden başlamadı?

Kalibre penceresi iki yöntem için eksik koşulları canlı gösterir.
“Joint … exceeds profile envelope” hatası, mevcut motor konumunun önceki
kayıtlardan alınan hareket aralığı dışında olduğunu belirtir. v23 bunu Türkçe,
eklem adı, okunan konum ve izinli aralıkla gösterir. Bu aralık üreticinin tüm
fiziksel erişimi değildir; yazılım onu ölçmeden genişletmez. Kolu destekleyip
Kolu bırak ile elle konumlandırabilir veya motorlar serbestken Elle ölçüm
yapabilirsin. Elle ölçüm hareket aralığını otomatik genişletmez.

Kol dururken kısa etiket kaybı artık ölçümü hemen iptal etmez; o duruşta 15 sn
bekler. Hareket sırasında görüntü kaybında durdurma korunur. Son hata altta
kalıcı görünür; dokununca tamamı açılır. Başarılı yeni ölçüm başlangıcında temizlenir.

## v24: kapalı duruştan kalibrasyon

- Pasif bilek dönüşü ID5 artık tüm 0–4095 okumalarında yalnız ölçülür; hareket
  komutu verilmez. Sıfır geçişindeki periyodik açı FK'da kullanılır. Diğer motorlarda
  belirsiz encoder dalı reddi korunur.
- Tarama, eklem uçlarında merkezi içeri kaydırır. Kayıtlı aralık dışında en fazla
  8 sayımlık başlangıç farkı yalnız o kalibrasyonun içeri dönüş rotasında kabul
  edilir. Sonraki tüm hedefler asıl aralık içinde kalır; genel hareket sınırı büyümez.
- Model uç yüksekliği 0–30 mm ise ilk ayrılış yalnız yukarı doğru planlanır;
  devam eden tarama en az 30 mm yüksekte kalır. Bunlar model kontrolleridir,
  gerçek masayı/engelleri ölçerek çarpışmasızlık doğrulaması değildir.
- PC seri portunun ilk açılışına yalnız ilk kimlik okumasında 1 sn süre tanınır;
  normal motor işlemlerindeki 180 ms zaman aşımı değişmez.

PC'de kamera verisi: eski tarayıcıdaki MainActivity, ARCore'dan çözümlenmiş
hedef XYZ/depth kaynağı ve kamera oturumu bilgilerini target_receiver.py'ye
aktarabilen ayrı akıştır. Kol Kontrol bu eski aktarımı henüz başlatmaz. Bu,
USB kameranın ham derinlik videosu değildir; PC'ye geçmek tek başına kol-kamera
eşlemesi ihtiyacını ortadan kaldırmaz.

## v29: Mesafe ile eşleme hatasını ayırma

Etiket satırındaki cm kamera–etiket merkezi uzaklığıdır. Kalibrasyondaki mm ise
kameranın gördüğü kol konumu ile motor/model hesabının uyuşmazlığıdır. Mesafenin
metreyle doğru çıkması tek başına üç boyutlu eşlemenin doğruluğunu göstermez.
v29 iki dönüşümü sekiz öğrenme duruşunda birlikte iyileştirir; dört kontrol
duruşu hesaba katılmaz. Öğrenme RMS 6 / en çok 10 mm ve kontrol RMS 8 / en çok
12 mm sınırları korunur. Başarısız ölçüm önceki başarılı kaydı silmez.

Sıcaklık >=55 °C okunduğunda üç ayrı register63 okuması ve bir yeni tam geri
bildirim alınır. Yalnız üç sıcaklık okuması da 55'in altında ve 2 °C içinde
tutarlıysa en yeni sıcaklık kullanılır; diğer alanlar yeni tam okumadan gelir.
İlk soğuk değerler tutarsızsa en fazla iki ek okuma yapılır; son üçü yine
2 °C içinde olmalıdır. Herhangi bir doğrudan yüksek sıcaklık durdurmayı korur.
Doğrulanan yüksek sıcaklık, akım/voltaj ve hareket hataları durdurmayı sürdürür.

YUV görüntü hazırlığı tek geçiş ve yeniden kullanılan tamponlarla hızlandırıldı.
Canlı ölçümde hazırlık 178–431 ms yerine ısınma sonrası 17–22 ms gözlendi.
Bu süre tüm toplama çevrimi veya bağımsız algılama doğruluğu ölçümü değildir.

## v25: görüntü kararlılığı

Etiket algılama bağımsız iş parçacığında yaklaşık 10 Hz hedefiyle çalışır; incir
modelinin bitmesini beklemez. Motor/kamera duruşu sabitken son 1,5 saniyede en az
5 ayrı, net etiket karesinin 3 mm / 3 derece içinde uyuşması aranır. Eksik veya
yönü belirsiz kare ölçüme katılmaz; tek kötü kare biriken tüm iyi kareleri silmez.
Motor hareketi veya encoder duruşunun değişmesi ölçüm penceresini sıfırlar.

Ekrandaki etiket ve incir işaretleri kısa kesintilerde en fazla 0,8 sn korunur.
Bu yalnız gösterimdir; kayıp/eski algı yeni motor hedefi oluşturmaz. Etiketin
400 ms ve incirin 750 ms ölçüm geçerliliği korunur. İncir için derinlik yoksa
algılanan nesne kaybolmak yerine “derinlik bekleniyor” diye görünür.

Telefonun takibi kaybolursa veya uygulama arka plana giderse görüntü hafızası
sıfırlanır; eski kamera oturumunun sonucu kullanılamaz. “Etiket … kararlı” yalnız
mevcut duruşun görüntü ölçümünü belirtir; 12 duruşlu kalibrasyonun tamamlandığı
veya robotun inciri alabileceği anlamına gelmez.

## v26 — kısa kamera takip kaybından devam

Tek karelik AR konum sıçraması artık kalibrasyon ölçümlerini silmez. Referans
şüpheliyse veya güncel etiket kaybolursa kol kontrollü tutmaya geçer; bu sırada
ölçüm/hedef üretilmez. Aynı kamera referansı ve güncel etiket 250 ms boyunca
geri gelirse yarıda kalan otomatik tarama hedefi mevcut motor konumundan yeniden
planlanır. İlk kamera referansı değiştirilmez. Referans 1,5 sn içinde doğrulanamazsa
kalibrasyon iptal edilir. Bu mesaj telefonun fiziksel hareket ettiğini iddia etmez;
AR dünya koordinatları da kaymış olabilir. Etiket beklemesi için duruş başına
15 sn ve toplam 180 sn sınırları sürer. DUR, uygulamadan çıkış veya motor hatası
sonrası otomatik devam edilmez. Bu süreler fiziksel doğruluk garantisi değildir.

## v27 — sabit telefon, kamera koordinatlarında kalibrasyon

Kalibrasyon ve görülen uç artık ArUco'nun doğrudan kamera koordinatlarından
hesaplanır. AR dünya koordinatlarındaki yeniden hizalanma bu eşlemeyi değiştirmez.
İncirin AR derinlik/düzlem noktası aynı karenin kamera dönüşümüyle kamera uzayına
alınır. Telefon ayaklığı fiziksel olarak sabit kalmalıdır. İvme ve dönme sensörleri
hareketi denetler; yavaş, salt ötelemeyi kesin algılama garantisi yoktur. Ayaklık
oynatılırsa yeniden Kalibre gerekir. Yeni oturum kalibrasyonu yine siler.

Gerçek cihazda ID3/4 için 34 → 62/97 → 34 °C tekil blok okuma sıçramaları görüldü.
Yakın zamanda serin ölçülen motorda ani yüksek sıcaklık ayrı 63 numaralı kayıttan
iki kez ve tam geri bildirimden bir kez yeniden okunur. Üç yeni okuma da 55 °C
altında ve birbirine 2 °C yakınsa yeni tam geri bildirim kullanılır. Doğrulama
başarısızsa hata sürer; sıcaklık/akım/voltaj sınırları yükseltilmedi. Frenleme
sonrasında tutma için 100 ms boyunca kararlı geri bildirim gerekir.
