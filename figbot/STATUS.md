# FIGBOT güncel durum — 29 Eylül 2026

## Güncel durum: kullanıcı onarımı bildirdi; doğrulama sürüyor

Kullanıcı, ID1 üzerindeki dönen gövdede saptanan sağ-sol boşluğu giderdiğini
bildirdi; önce 12 V'u kapattı, ardından destekli tutma için yeniden açtı.
Hangi bağlantının gevşek olduğu ve onarımın tüm duruşlarda yeterliliği bağımsız
doğrulanmadı. Önceki yaklaşık 6° dönme / 34,4 mm sapma yazılım ofsetine çevrilmedi.

v33 derlendi: 290 JVM testi, sıfır hata ve Android lint geçti; Xiaomi'de sürüm33
doğrulandı ve yayın betiğiyle güncel APK yayımlandı. Diğer sohbetin
FigTargetGeometry değişiklikleri aynı derlemeye dahildir. 03:56:45–03:56:53
kısa taraması ardından yeşil robot XYZ görüldü. Çevrimdışı kontrolde bu taramanın
kontrol RMS'si 5,185 mm, en büyük hata 6,377 mm; son geçişte açıklanamayan yaw
0,294° çıktı. Yerel iyileşme var; fakat ilk tarama reddedildi ve 03:57:07 kaydı
yeniden 13,5 mm / 6,0° fark gösterdi. Tüm çalışma alanında eşleme veya başarılı
incir toplama doğrulanmış sayılmaz.

Yaklaşık 03:56:55'te DUR, 03:57:30'da Bağlantıyı kes uygulandı. Köprü ölçülen
konumda tutmayı doğrulayıp kapandı; 8873 portunda dinleyici kalmadı. Telefon/kol
kontrolü kamera incelemesini yapan diğer sohbete bırakıldı; bu sohbet donanıma
ve APK'ya yeniden müdahale etmiyor. Son kanıt:
`reports/diagnostics_20260929/repair33_live.log` ve `repair33_stop.png`.
Sayısal takip: `reports/diagnostics_20260929/repair33_after_tightening_analysis.json`.
Aşağıdaki eski sürüm notları tarihsel kayıttır.

## Kalibrasyon akışı düzeltmeleri — APK v0.21.0-measure-calib

Kullanıcı iki engel bildirdi: (1) ekrana dokunmak hiçbir şey yapmıyordu — dokunuş
dinleyicisi ACTION_DOWN'da false döndürüyor, bu yüzden ACTION_UP bu görünüme hiç
gelmiyordu; dinleyici kalibrasyon sırasında DOWN'dan itibaren jesti tüketiyor.
(2) "kolu destekle Tutmayı Aç" mesajı kalibrasyon sırasında yanlış anlaşılıyordu —
kalibrasyon tork KAPALIyken yapılır (kol elle serbest taşınır; enkoderler bağlıyken
her tick yeniden okunur), Tutmayı Aç yalnız kalibrasyon sonrası Hedefe Git için
gerekir. Durum satırı kalibrasyonda "KALİBRASYON n/4 · tork gerekmez" gösterir;
diyalog metni de sırayı açıkça yazar. 120 test, lint 0 hata.

## Ölçümlü kamera kalibrasyonu — APK v0.20.0-measure-calib (önceki sürüm)

Kullanıcı "target cannot be solved; 15 cm önde sağdaki incire nasıl gidemiyor" bildirdi.
Kök neden: v0.15'ten beri kamera dönüşümündeki bakış açıları (yaw -30°, pitch -45°)
TASARIM TAHMİNİ idi; yanlış açı tespitleri erişim dışı koordinatlara taşıyordu. Tahmin
tamamen kaldırıldı: yeni KALİBRE düğmesi kolu kendi ölçüm aracı yapar — kullanıcı kolu
destekler, kıskaç ucunu 4 farklı pozda (≥8 cm ayrık, aynı çizgide değil) tutup ekranda
uca dokunur; uygulama her dokunuşta enkoder+modelden gerçek uç konumunu ve kameradan
aynı noktanın dünya konumunu eşler, mevcut Horn çözücü (WorkspaceCalibration.fit,
RMS≤8 mm / en çok 15 mm / yayılım≥80 mm kapıları) kamera–kol dönüşümünü ÖLÇER. Kalibrasyon
SharedPreferences'a yazılır, açılışta yeniden kurulur; Hedefe Git kalibrasyon yoksa
açıkça reddeder. Erişim dışı hedef artık "aracı incire yaklaştır / KALİBRE'yi yenile"
şeklinde Türkçe söyler. Tahmini asset yalnız etiketsiz yedek olarak kaldı. 120 test,
lint 0 hata. Motor komutu verilmedi; fiziksel kalibrasyon ve deneme kullanıcıya ait.

## Bilek zarfı düzeltmesi — APK v0.19.0-follow (önceki sürüm)

Kullanıcı "Joint 5 exceeds profile envelope; kol tutuyor ama hareket etmiyor" bildirdi.
Kök neden: kayıtlı oturum profilinde ID5 (pasif bilek dönüşü) zarfı yalnız [3104,3150]
(46 sayım ≈ 4°) idi; kullanıcı kolu elle bıraktığı pozisyonda ID5 bu dar pencerenin
dışında okundu. "Tutmayı Aç" zarf kontrolü yapmadığı için tutma açılıyor, ama IK ve
GoalTrajectory başlangıç pozunu doğrulayınca reddediyordu. Düzeltme: bu uygulamada ID5
asla komut almadığından zarf, referans dalının tamamına genişletildi
(ArmProfile.withWristRollEnvelope → [2161,4095]; dal dışı yine kapalı). ID1–4 aktif
zarfları ve home/basket doğrulamaları değişmedi. 120 Android testi (1 yeni zarf testi),
lint 0 hata. Motor komutu verilmedi; fiziksel deneme kullanıcıya ait.

## Tutma devralma dayanıklılığı — APK v0.18.0-follow (önceki sürüm)

Kullanıcı "ID1 is not stationary" ve "kol DISARMED" bildirdi. Kök neden: 12 V kapat-aç
sonrası motorlar torksuz açılır; torksuz ST3215 tabanı en hafif dokunuşla serbest döner,
tek anlık okuma hız>50 görüp "Tutmayı Aç"ı da engelliyordu. Düzeltme: "Tutmayı Aç" artık
2,5 sn boyunca 250 ms arayla devral→destekli-tutma döngüsünü tekrarlar; yazım öncesi
hatalar DISARMED bıraktığı için deneme güvenli, yazım sonrası hata FAULT_UNKNOWN'a düşer
ve döngü durur. "Hedefe Git"/"Başlangıca Dön"/otomatik bağlantı yalnız devralma döner
(8×200 ms) — tork açma yalnızca kullanıcının bastığı "Tutmayı Aç"ta. Durum satırı ham
"DISARMED" yerine "Tork kapalı · kolu destekle ve TUTMAYI AÇ" yazar. 119 test, lint 0.

## Sıfırdan takip uygulaması — APK v0.17.0-follow (önceki sürüm)

Kullanıcı isteğiyle uygulama sıfırdan tek ekran akışına yazıldı (KolActivity ana ekran;
eski HomeActivity/MainActivity kayıt dışı, kod arşivde durur). Yeni akış: kamera gördüğü
her inciri KOL KOORDİNATLARINDA (kol solda) ekrana yazar — kamera/araç hareket ederken
TURUNCU, 0,7 sn içinde sabitlenince YEŞİL. "Hedefe Git" takibi açar: turuncudayken kol
en yeni konuma en fazla saniyede bir kez yeniden nişan alır (dur-planla-git); yeşile
dönerken tek düzgün bacakla hedefe oturur; varış geri bildirimden (enkoder→ileri
kinematik) 15 mm yarıçapla doğrulanır ve ekrana model sapmasını yazar. Hedef kaybolursa
hareket mevcut bacağı bitirir, yenisi kamera gelene kadar başlamaz.

Bağlantı tek düğme: PC köprüsü (PcServoBus/adb reverse 8873) veya USB-OTG; bağlanınca
mevcut tutma en çok 8 denemeyle otomatik devralınır ("ID1 is not stationary" geçici
yerleşme artığıysa kendiliğinden geçer), olmazsa "Tutmayı Aç" (destekli) kullanılır.
Hızlar Yavaş/Orta/Hızlı = 300/700/1200 sayım/s; DUR her an geçerli; kamera 750 ms
bayatlayınca hareket güvenle durur. Kıskaç açık gider (kavurma yok) — bu sürüm konum
doğrulama aracıdır. Kayıt matrisi/limanlar değişmedi; hareket kayıtlı 2026-09-20/21
oturum haritasıyla açılır (taze uç ölçümü yok).

Doğrulama: 119 Android birim testi (5 yeni FollowBrain testi) ve lint 0 hata.
Motor komutu verilmedi; fiziksel deneme kullanıcıya ait.

## Hedef test modu — APK v0.16.0-target-test (önceki sürüm)

Yeni FIGBOT_INCIR_TARAYICI.apk (versionCode 16) hazır. Kullanıcının istediği basit akış:
kayıtlı kapalı başlangıçtan, kameranın gördüğü incir konumuna TEK deneme hareketi; kıskaç
açık kalır, kavrama yok. Yavaş/Orta/Hızlı (300/700/1200 sayım/s) döngü düğmesi ve
"Başlangıca dön" düğmesi eklendi. Hareket bitince uygulama model hedefini, varılan model
konumunu ve model sapmasını yazar; kullanıcı fiziksel sapmayı incire göre ölçüp bildirecek.

Ayar kapıları bu sürümde kalktı: 3 uç-konum ölçümü, sepet ağzı doğrulaması ve manuel kamera
noktaları hedef testi için istenmez. Hareket, kayıtlı 2026-09-20/21 oturumlarında fiziksel
çalıştırılmış enkoder haritasını kullanan `testProfile()` ile açılır
(ArmProfile.withRecordedSessionValidation; taze uç ölçümü YOK — gömülü varsayılan hâlâ
UNVERIFIED). İlk açılışta ölçüler kayıtlı düzen varsayılanlarıyla otomatik kaydedilir; fig
yükseklik aralık filtresi test modunda uygulanmaz ki yanlış kamera açısı hedefleri
sessizce düşürmesin — XY algılamadan, Z ölçülen zemin+kavrama yüksekliğinden gelir.
Çalışma zamanı güvenlik kapıları değişmedi: zarf, takip, hız/ivme, DUR.

Doğrulama: 114 Android birim testi (1 yeni recordedSession testi) ve lint 0 hata.
Motor komutu verilmedi; fiziksel deneme kullanıcıya ait.

## Sabit kamera montajı — APK v0.15.0-fixed-camera (önceki sürüm)

Yeni FIGBOT_INCIR_TARAYICI.apk (versionCode 15) hazır; iki APK adı aynı uygulamayı içerir.
Bu sürüm, telefonun kol tabanına sabit monte edildiği kurulumu esas alır: kamera–taban
dönüşümü assets/camera_calibration.json ile uygulama içinde gömalıdır; 4+3 manuel kamera
eşleme noktası ve üç zemin dokunuşu bu montajda istenmez, kamera pozu her karede otomatik
alınır. Kol duruş öğretme, 3 uç-konum ölçümü ve zemin/sepet ölçüleri (ön dolu varsayılanlarla)
yine gerekir. Montaj konumu kullanıcı ölçümü; bakış açıları tasarım tahmini — bilinen
noktayla ilk doğrulama yapılmalı (ASSUMPTIONS.md). Ölçüler diyaloğuna incir zemin yüksekliği
alanı eklendi; sepet/kavrama varsayılanları kullanıcı düzeninden ön dolu.

Doğrulama: 113 Android birim testi geçti (6 yeni FixedCameraCalibration testi dahil);
test ortamına gerçek org.json eklendi. Python tarafında cartesian/pc_bridge/camera/
kinematics/st3215 testleri (54 test + 4 alt test) geçti. APK derlemesi tamamlandı;
motor komutu verilmedi, fiziksel deneme yapılmadı.

Android v0.14: mevcut iki seçenek korunarak 03 PC üzerinden toplama eklendi.
PC_Uzerinden_Toplama.cmd, ADB reverse ve tek sahipli seri köprüyü başlatır.
Telefon kamera/kalibrasyon/planlayıcı/kontrolcü olarak kalır. 23 Eylül kontrolünde
ADB cihaz listesi boş: APK telefona kurulmadı, PC üzerinden fiziksel toplama ve
hız henüz doğrulanmadı. Ayrıntılı kullanım PC_ILE_TOPLAMA.md dosyasındadır.
Doğrulama: 107 Android birim testi, 14 PC köprü/yayın testi geçti; APK derlemesi
ve lint tamamlandı (0 hata, 54 uyarı). Motor komutu verilmedi.

## Önceki fiziksel denemeler — 20 Eylül 2026

Toplama ve bırakma tamamlandı: incir masadan alınıp sağdaki bant rulosunun içine
bırakıldı; boş kıskaç yukarı çekildi. Taban merkez kaydı düzeltildi: ID1 ofset4080,
güncel kayıt `GUNCEL/YAZILIM/ST3215_TEST/base_reference.json`. Sağ dönüş canlı
olarak doğrulandı. Kanıt: `KAYITLAR/SURUS_20260920T195145Z/incir_bant_icine_birakildi.*`
(ST3215_TEST altında). Otomatik tekrarlanabilir toplama henüz doğrulanmadı.

Gerçek SO-101 kolu COM5 üzerinden canlı kamera gözetiminde sürüldü; kuru incir
kavrandı ve masadan kaldırıldı. Başarılı tek denemenin fotoğrafı ve motor konumları:
`GUNCEL/YAZILIM/ST3215_TEST/KAYITLAR/SURUS_20260920T192232Z/incir_kaldirma_basarili.*`.
Güncel kontrol uygulaması `GUNCEL/YAZILIM/ST3215_TEST` içindedir. Yavaş adım sürüşü,
mevcut tutmayı devralma ve eksik tutmayı geri okuma ile açma eklendi. Otomatik
tekrarlanabilir toplama ve kamera/eklem kalibrasyonu tamamlanmadı. ID5'in önceki
beklenmeyen hareketinin kök nedeni UNVERIFIED; ayrıntı ASSUMPTIONS.md içindedir.

## Önceki LINKA durum kaydı — DEC-086 / 17 Eylül 2026

İki dişli kepçe ve J1 çevreleyen yıldız kapağı hazır. Aktif teslimat GUNCEL; yeni tablalar07,08,10. Önceki01/02/03/09 parçaları değişmedi. Eski üç parmak ve L1-25 kullanılmaz. Yeni toplam34 baskı parçası; donanım listesi ve A4 PDF eşitlendi. Kaynak değişiklikleri DECISIONS.md; fiziksel belirsizlikler ASSUMPTIONS.md.

73 ilgili test, genel dilimleme ve tarayıcı/PDF kontrolü tamamlandı. CAD kütle tahmini tutucuda72,33→100,18g; bilek momenti artar. Gerçek dayanım/servo torku ve J1 yıldız oturması UNVERIFIED. Yeni hareket kalibrasyonu yapılmadı, motor/yazıcı komutu gönderilmedi.

Önizleme: http://127.0.0.1:5173/kol.html . Tam montaj ve baskı dosyaları GUNCEL/CAD ve GUNCEL/BASKI. Eski çıktılar SHA256 doğrulamasıyla ARSIV/ESKI_SURUMLER.zip içinde.


## 2026-09-20 — Akıcı sürüş artık gerçek kolda çalışıyor
Feetech SDK eşzamanlı yazma bağlı; dört motorun birlikte hareketi ölçüldü. Boş alma-bırakma10.47s, başlangıca dönüş dahil14.00s. XYZ -> IK -> aynı anda motor sürüşü bağlı ve iki yerel hedefte fiziksel olarak denendi. Yerel geometrik referans tahminidir; fiziksel hassasiyet ve telefon-kol dönüşümü henüz doğrulanmadı. Son iki çevrimde incir alınmadı. Uygulamada duruş kaydet/git, çevrim ve XYZ girişleri var. GUNCEL/YAZILIM/ST3215_TEST/AKICI_SURUS.md güncel kullanım ve sınırlardır.


## Maksimum sayısal profil — 2026-09-20
Kullanıcının isteğiyle eşzamanlı sürüşün hız sınırı3072 ->3400 sayım/s,
ivme kayıt sınırı10 ->150 yapıldı. Kaynak: https://www.waveshare.com/wiki/ST3215_Servo
SyncWritePosEx örneği. Varsayılan duruş/XYZ isteği ve kayıtlı çevrim süre istekleri
0.25s oldu; planlayıcı mesafe/hız/ivmeye göre gerekli daha uzun süreyi hesaplar.
Kısa mesafede bütün motorların3400 hızına ulaşacağı anlamına gelmez; hedef süreye
uyum için her motorun profili ayrı hesaplanır. Sıfır/sınırsız profil kullanılmaz.
Konum/akım/sıcaklık/kamera/komut tazeliği/durma kontrolleri değiştirilmedi.
101 ilgili test geçti. Bu profilin fiziksel denemesi kamera geri gelene kadar
PENDING_CAMERA durumundadır; önceki10.47/14.00/12.99s ölçümleri eski ivme10
profiliyle alınmıştır. Yeni profilin ölçümü henüz yoktur.


## Fiziksel maksimum profil sonucu — 2026-09-20 son güncelleme
Başlangıç duruşundan alma-bırakma hareket dizisi5.640s içinde tamamlandı;
başlangıca dönüş bu ölçüme dahil değildir. İncir bantın dışında kaldı.
103 ilgili test geçti. Motorların fabrika Maximum_Acceleration kaydı85,
1bayttır ve altı motorda50 okundu;86 ayrı çarpandır ve1 okundu.
LeRobot resmi STS tablosu bunu doğrular:
https://github.com/huggingface/lerobot/blob/main/src/lerobot/motors/feetech/tables.py
150 gönderildiğinde hedef hız/konum korunurken ivme50'ye kısıldığı için
sıkı geri okuma denetimi hareketi iptal etmişti. 53->50 gözleminin10'luk
basamak yuvarlaması olduğu hipotezi GEÇERSİZDİR ve bu geçici kod kaldırıldı.
Planlayıcı artık her program öncesi85 kaydını salt okur, bütün motorların
ortak en düşük fabrika sınırıyla süre/ivme hesaplar; fabrika kaydını değiştirmez.
Etkin üst sınırlar hız3400 ve donanımdan okunan ivme50'dir; yazılım sayısal
ivme tavanı150 olsa da bu donanımda50 üstü gönderilmez. Önceki PENDING_CAMERA
notu bu başarılı hareket denemesiyle güncellenmiştir. XYZ fiziksel doğruluğu
ve otomatik nesne kavrama hâlâ doğrulanmış değildir.


## Kapalı başlangıç ve sürekli çevrim — 2026-09-21
Kullanıcının elle gösterdiği kapalı başlangıç enkoderleri: ID1..6 =
2033, 782, 3946, 2729, 3127, 949. Ofsetler değişmedi. Konum tutma yerinde
etkinleştirildi. İlk kapalı-başla/kapalı-bitir denemesi7.556s, son hata en çok3
sayım. Kalıcı kütüphane ARM_CONTROL/motion_library.json; al_birak çevrimi
kapali_baslangic duruşuyla başlamayı zorunlu kılar ve oraya döner.
Genel jog/XYZ aralıkları değiştirilmedi; yalnız kayıtlı başlangıç rotasında
ID2/4 için ölçülmüş duruşa uzantı kullanılır; iç ara noktalar eski aralıkta.

smooth_path.py, C1 sürekli şekil-koruyan kübik eklem yörüngesi oluşturur.
Ara noktalarda varış/duruş beklemesi yoktur. Analitik hız/ivme sınırı hesabı
hız3400 ve donanımdan okunan ivme50 sınırlarına göre zamanı ölçekler.
Tüm hareketli eklemlerin Goal_Position kayıtları SDK GroupSyncWrite ile ortak
zamanda güncellenir. Bilek dönüşü ID5 sabit tutulur. Kıskaç yaklaşırken kapanır;
kaldırma/taşıma ve bırakma/geri dönüş hareketleri örtüşür. Kuvvet kontrollü
kavrama veya nesnenin alındığını algılama henüz yoktur.

Gerçek sürekli çevrim6.360s tamamlandı;191 güncelleme, en büyük güncelleme
aralığı78ms, en büyük zamanlanmış konum takip farkı73sayım. Kapalı başlangıca
son hata en çok3sayım. İncirin alınıp banda konulduğu doğrulanmadı; simülasyon.
Kayıt: SURUS_20260920T205942Z/first_continuous_result.json.

5.510s zamanlama denemesi açılma sırasında ileri hedef/ölçüm farkı192sayım
sınırını aştığı için iptal oldu (takip hatası76sayım). Eski DUR kodu ivmeyi
50'den10'a düşürüyordu;350ms durma kontrolü tutmayı doğrulamayınca ID2/4/6
torkunu kapattı. Kayıt SURUS_20260920T210246Z/optimized_attempt_fault.json.
Kod artık 192sayım sınırını değiştirmeden ileri bakış zamanını azaltır;
DUR, doğrulanmış mevcut ivme sınırını korur. Bu iki düzeltmenin fiziksel
kontrolü PENDING_SUPPORTED_RECOVERY. Ani durmanın fiziksel davranışı
UNVERIFIED; hızlandırılmış deneme başarılı sayılmaz. 120 ilgili test ve4
alt test geçti. Üç saniye hedefi karşılanmadı. Tam çarpışma modeli yoktur.


## Kullanıcının çevrim süresi tanımı — 2026-09-21
Üç saniye hedefi, önceki incir bırakıldıktan sonra bir sonraki incire doğru
ilk fiziksel hareketin başlamasından yeni incirin sepete fiziksel olarak
bırakılmasına kadardır. İlk kapalı duruştan açılma ve iş sonundaki katlanma
bu metriğe dahil değildir. İş sırasında her incir arasında kapalı duruşa
uğranmaz. Bırakma ile sonraki hareket arasındaki boş süre ayrıca raporlanır.
Kıskaç açma komutu gerçek incirin sepete bırakıldığına kanıt sayılmaz.
Önceki6.36s kapalı-başla/kapalı-bitir ölçümü bu metrikle karşılaştırılmamalı.

Birak -> alma_yaklasma -> kavra -> tasima_gecisi -> birak rotası, aynı
3400 hız/50 fabrika ivme sınırı ve sürekli yörünge hesabıyla çevrimdışı
2.72255s hesaplandı. Bu fiziksel ölçüm veya başarılı toplama kanıtı değildir;
yeni sepetten-sepete çevrim donanımda çalıştırılmadı. Tahmini model uç yüksekliği
en az21.04mm; tam çarpışma kontrolü yok. Fiziksel kavrama, bırakma ve süre
PHYSICAL VALIDATION REQUIRED. Yeni rapor ARM_CONTROL/harvest_cycle_metric.json.
Motorların önceki hata sonrası ID2/4/6 torku0 durumu değiştirilmedi;
kullanıcının destek onayı ve tutmanın geri açılması bekleniyor.


## Elle öğretilen uzak incir / yüksek sepet tekrarı — 2026-09-21
TEACH_20260920T211710_1dac69.jsonl tamamlandı:728 örnek, en uzun aralık0.413s,
enkoder sıçrama bayrağı yok. İlk başarısız öğretim kullanıcı isteğiyle
INVALIDATED_BY_USER_RESTART işaretlendi. Yeni kayıtta kavrama ve bırakma
buton işaretleri yok; olaylar kıskaç izinden çıkarıldı (INFERRED).

Taught replay yalnız SHA256 doğrulanan, tamamlanmış ve geçersiz işaretlenmemiş
pasif kaydın gerçek örneklerini kullanır. Ofset/başlangıç duruşu denetlenir;
ID5 gürültüsü hareket olarak tekrarlanmaz. Yerel hareket aralığı kayıtlı yolun
ölçümlerinden gelir; genel jog/XYZ aralıkları genişletilmez. Sürekli yörüngeler
128 düğüme kadar önceden doğrulanabilir; küçük zaman aralıkları nihai kübik
hız/ivme hesabına tabidir. Motor fabrika ivme50/hız3400 sınırları korunur.

İlk elle gösterilen tam yol15.797s içinde fiziksel olarak tekrarlandı. Ardından
aynı kaydın taşıma geçişlerini ters yönde kullanarak iki sepet-incir-sepet
çevrimi eklendi; dönüşte kıskaç açık, son yaklaşmada kapanır, yüksek bırakma
noktasında açılır. Katlanma iki çevrimin sonundadır. İki çevrimli tam program
24.109s tamamlandı; kullanıcı beğenip yeniden istedi, aynı program24.156s
tekrar tamamlandı. Bu toplamlar hasat süresi metriği değildir.

Her sepetten çıkış-yeniden sepet noktası çevriminin program zamanı4.174s.
200ms telemetride fiziksel hareket başlangıcı ve sepet duruşunda açık kıskaç
koşuluyla yaklaşık4.0s/4.0s bulundu; bu enkoder simülasyon ölçümüdür, gerçek
nesnenin sepete düştüğünün ölçümü değildir. Üç saniye hedefi karşılanmadı.
Canlı görüntüde kıskaçta taşınan incir görüldü; gerçek sepete başarılı bırakma
UNVERIFIED. Son tekrar697 güncelleme, en uzun aralık78ms, en büyük zamanlı
izleme farkı111sayım; altı motor konum tutuyor, kol katlı duruşta.

Güncel rota ARM_CONTROL/TEACHING/replay_plan.json; kayıtlar
KAYITLAR/SURUS_20260920T212903Z/harvest_cycle_measurements.json ve
requested_repeat_005.json. 128 ilgili testin ardından kıskaç zamanlama
örtüşmesi için5 taught_replay testi ayrıca geçti. Takip mesafesini aşmadan
ileri bakış kısaltma, bu tekrarlar sırasında kullanıldı; yüksek hızlı acil
DUR davranışının özel fiziksel doğrulaması hâlâ yapılmadı.


## Güncel akıcı sürüş ve erken bırakma düzeltmesi — 2026-09-21

Bu bölüm önceki hız denemelerinin güncel durumunu değiştirir. 3.60s C2 denemesi
taban takip hatası306 sayım ile durdu; motorlar tutmayı korudu. Ardından3.92s
zamanlanan sürüş tamamlandı ancak kullanıcı incirin erken bırakıldığını bildirdi.
Bu sürüm başarılı toplama veya doğru bırakma sayılmaz; c2_early_release_rejected.json
olarak işaretlendi. Kıskacı sepetten önce açarak süre kısaltma kaldırıldı.

Güncel replay_plan.json: hız ve ivmesi sürekli quintic C2 eklem yörüngesi.
Ara taşıma duruşları sonraki kayda doğru dört kol ekseninde en çok64 sayım
yuvarlanır; alma/bırakma duruşları ve ID5 değiştirilmez. Bu hesaplanan geçiş
düzeltmesi tam çarpışma planlaması değildir. Tüm hareketli hedefler aynı
GroupSyncWrite paketinde gider. Genel jog/XYZ limitleri, fabrika ivme50,
sonlu hız3400, takip/ileri hedef192 sayım sınırları değişmedi.

Bırakma, açık kıskaç komutundan önce ölçülen sepet konumuna bağlıdır: kol
eklemleri22 sayım içinde ve hızları en çok100 sayım/s olmalı. Önceki20 sayım
koşulu, yerçekimi altındaki omuzun20/21 sayım sınırındaki ölçüm oynamasıyla
0.472s ek bekleme üretmişti;22 sayım koşulu2 sayımlık ölçüm payı içerir.
Bırakma sonrası kıskaç açıklığı20 sayım içinde doğrulanmadan yola çıkılmaz.
Bu koşullar en çok0.75s bekler, karşılanmazsa sürüş iptal edilir; yörünge
zamanı bekleme süresince dondurulur ve daha sonra ileri sıçramaz. Kıskaç açma
hareketinin kendisi yaklaşık0.55s sürer; bu süre gizlenmez veya nesne bırakma
algılandı diye raporlanmaz. Sıfır toplam duruş/jerk sürekliliği vaat edilmez.

Windows/Python3.12 üzerinde eski monotonic saati GetTickCount64/15.625ms idi.
Event.wait(3ms)20 örnekte ortalama15.59ms, time.sleep(3ms)3.37ms ölçüldü.
Artık QueryPerformanceCounter tabanlı perf_counter ve son tarihe göre,
en çok20ms bekleme kullanılır. JPEG kodlama/dosya yazımı kamera iş parçacığına
taşındı. Tork40 ve geri bildirim56–70 tek31 baytlık okumada alınır; motor
başına ayrı iki okuma kaldırıldı. COM5'in tek sahibi korunur. Firmware veya
Windows genel zamanlayıcı ayarları değiştirilmedi.

Son fiziksel tekrar: iki ardışık simülasyon çevrimi ve kapalı başlangıca dönüş
tamamlandı. Sonlu hedef yörüngesi ayrıca sayısal1430 sayım/s tavanıyla zamanlandı.
Programlanan hasat çevrimleri4.135s/4.135s; açık kıskaç ölçümleri arasındaki
gerçek süreler4.181s/4.158s. 200ms telemetride ilk taban ayrılışından açık
kıskaç geri bildirimine3.87s/4.01s bulundu (ENCODER_SIMULATION_PROXY).
Gerçek incirin sepete düştüğü doğrulanmadı. Üç saniye hedefi karşılanmadı.

Tam açılma/iki çevrim/katlanma22.932s;1082 hedef güncellemesi, ortalama47.18Hz,
en uzun aralık46.64ms, en büyük takip farkı123 sayım. Son iki çevrimli programda
ek bırakma doğrulama beklemesi toplam0.0685s. Önceki düzeltilmiş sürümde31.83Hz,
94ms ve0.4719s idi. Bu fark fiziksel hızın yüzde50 arttığı anlamına gelmez;
komut akışı daha sık ve düzenlidir. Son durumda altı motor tutuyor, kol kapalı.

Kanıt: GUNCEL/YAZILIM/ST3215_TEST/KAYITLAR/SURUS_20260920T220749Z/
flow_optimized_measurements.json, flow_optimized_status.json, sync_005.json.
140 ilgili test ve4 alt test geçti. Bir sonraki hız denemesinde gerçek
kavrama/bırakma ve sepet hacmi ayrıca gözlenmeli; nesne/kuvvet algılama,
tam çarpışma modeli ve3s altı gerçek toplama PHYSICAL VALIDATION REQUIRED.


## Yaklaşma sırasında kıskaç açma — 2026-09-21

Kullanıcı, incir doğru bölgeye ulaştığı sürece kıskaç açılmasının sepet
yaklaşmasıyla örtüşmesini açıkça istedi. Güncel kayıtlı rotada açılma için
0.18s yaklaşma penceresi var; bunun yanında gerçek kol konumları bırakma
duruşuna en çok64 sayım, sabit bilek dönüşü22 sayım uzaklıkta olmalı ve kol
hedeften uzaklaşmamalı. Bu, yalnız bu kayıtlı yol için denenmiş bir eklem
yakınlığı koşuludur; hesaplanmış balistik atış açısı/sepet hacmi modeli değildir.

Kıskaç kendi C2 zamanlamasını ölçülen açma koşulunun sağlandığı anda başlatır.
Öngörü bu koşulu atlayamaz. Koşul geç sağlanırsa açılma eğrisine ortadan
atlanmaz; kol yaklaşmaya devam eder, kıskaç kapalı tutulur. Açılma süresinden
0.18s kol yaklaşmasına taşındı; kıskaç hız/ivme limitleri değiştirilmedi.
Tam açık geri bildirimi gelmeden sepetten ayrılma engeli korunur. Bırakma
sonunda kol22/kıskaç20 sayım ölçüm payı kullanılır; taşıma/takip limitleri aynı.

İki fiziksel çevrim tamamlandı: açık kıskaç ölçümleri arası3.9778s ve3.9824s.
Program zamanı çevrim başına3.9776s; ilk açılma ve son katlanma hariçtir.
Açılma nominal sepet varışından0.10–0.17s önce başladı; varıştan açık kıskaç
ölçümüne kalan süre0.398–0.403s oldu (önce yaklaşık0.55s). Ek konum/kıskaç
doğrulama beklemesi0s. Bu zamanlar enkoder ölçümüdür, meyvenin uçuş veya
düşüş zamanını ölçmez. Kullanıcı son deneme için “Doğru bölgede bıraktı”
yanıtını verdi: USER_CONFIRMED_CORRECT_RELEASE_REGION. Otomatik nesne/kuvvet
algılaması ve3s altı toplama hâlâ doğrulanmadı.

Tam program22.4644s,1052 güncelleme, en büyük takip farkı160 sayım. En uzun
tek güncelleme aralığı0.223s görüldü;0.25s iptal eşiği aşılmadı. Bu nedenle
kesintisiz zamanlama garantisi verilmez. Son durum altı motor tutuyor,
kol kapalı başlangıçta.151 test ve15 alt test geçti. Güncel rota
GUNCEL/YAZILIM/ST3215_TEST/ARM_CONTROL/TEACHING/replay_plan.json.
Kanıt KAYITLAR/SURUS_20260920T222241Z/approach_release_measurements.json,
approach_release_status.json ve sync_004.json. Önceki sabit yerde açma rotası
verified_stationary_release.json adıyla geri dönüş için saklandı.


## Doğrudan hedef rotası — 2026-09-21 (güncel)

Kullanıcının isteğiyle elle tarif edilen ara rota kaldırıldı. Yeni direct_goals
planlayıcısı yalnız kapalı başlangıç (örnek417), kavrama hedefi (232) ve sepet
açık hedefini (324) kullanır. Eklemler birlikte C2 beşinci derece eğriyle sürülür;
hesaplanan orta düğümde durulmaz. Omuz için64 sayımlık sınırlı açıklık yayı
üretilir. Bilek dönüşü ID5 sabit kalır. Bu, eklem uzayında hedeflerden üretilen
rotadır; görüntüden öğrenilmiş politika veya engelleri algılayan yol planlayıcı
değildir. Mutlak Kartezyen model/table plane kalibrasyonu UNVERIFIED.

Güncel aktarım tepe hız ayarı1200 sayım/s; ilk açılma ve son kapanışta omuz/dirsek
ayrıca1000 sayım/s ile sınırlandırılır. Donanım sonlu profil3400/ivme50 olarak
kalır; gerçek yörünge bu daha düşük tepe hızlara göre zamanlanır. Kıskaç yaklaşırken
kapanır, sepet yaklaşmasının son0.18s bölümünde ölçülen yakınlık koşulu sağlanırsa
açılır. Bırakma konumu/kıskaç geri bildirim koşulları ve192 sayımlık hedef/takip
sınırları korunur. Gerçek kavrama/nesne tutma algısı yoktur.

İlk1550 denemesi ilk açılmada omuz takip farkı196 sayımda durdu.1000 açılma
sınırıyla sonraki deneme ilk taşımanın taban takibinde199 sayımda durdu.1200
aktarımı denemesinde181ms ana bilgisayar aralığı sonrası193 sayım omuz takip
hatası oluştu. Bunlar başarılı çevrim değildir; ilk2.932s hesap fiziksel olarak
başarılamadı. Eski sabit0.35s durdurma doğrulaması, hareketli motor durup yakalanan
hedefe geri gelirken tutmayı erken kesiyordu. Artık ölçülen başlangıç hızına göre
0.35–0.9s sonlu yerleşme payı var;192 sayımdan fazla sapma anında ilgili motoru
durdurur, son12 sayım/50 sayım/s doğrulaması aynıdır. Bu süre fiziksel frenleme
garantisi değildir. Otomatik yeniden tork açma veya eski rotaya devam yoktur.

80–250ms örnekleme boşluğunda yörünge zamanı en çok40ms ilerler; kayıp süre
raporlanır, özgün bitiş süresi uzatılmaz.250ms üzeri kesinti hâlâ iptal eder.
Başarılı son koşuda bu telafi gerekmedi. İki gerçek kol simülasyon çevrimi
3.6641693s ve3.6964537s sürdü (açık kıskaç ölçümünden sonraki açık kıskaç ölçümüne;
ilk açılma/son kapanış hariç). Önceki3.9778/3.9824s ortalamaya göre yaklaşık%7.5
azalma. İlk açılma ve son kapanış dahil program15.581737s;741 güncelleme,
47.56Hz ortalama,44.30ms en büyük aralık,77 sayım en büyük takip hatası.
Ek konum doğrulama veya zamanlama beklemesi0s. Son konum kapalı; altı motorun
tutması doğrulandı. Üç saniyenin altı ve donanımın gerçek maksimum hızı henüz
kanıtlanmadı. Gerçek incirin yeni rotada tutulup sepete bırakılması PHYSICAL
VALIDATION REQUIRED; önceki rota için kullanıcı onayı bu yeni rotaya aktarılmaz.

Güncel plan: GUNCEL/YAZILIM/ST3215_TEST/ARM_CONTROL/TEACHING/replay_plan.json.
Başarılı yedek: verified_direct_goals.json. Önceki kullanıcı onaylı yaklaşarak
bırakma rotası verified_approach_taught_route.json içinde korunur. Kanıt:
KAYITLAR/SURUS_20260920T225245Z/direct_goal_measurements.json,
direct_goal_status.json ve sync_003.json.171 test ve75 alt test geçti.

Deneme sırasında C: dolduğu için bazı kayıt yazımları başarısız oldu. Güncel
APK ile SHA256 eşliği doğrulanan143884632 baytlık build/outputs/apk/debug
önbellek kopyası temizlendi; güncel APK korundu. Android build/intermediates
silinmeden NTFS sıkıştırıldı (292450219→197733465 bayt). Başarılı son durum ve
ölçüm dosyaları yeniden yazılıp doğrulandı; bu işlem eski hata anının eksik
kamera kaydını yeniden üretmez.
