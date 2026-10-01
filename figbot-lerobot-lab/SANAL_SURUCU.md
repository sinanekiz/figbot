# Fareyle sanal sürücü

`SANAL_SURUCU.cmd` dosyasına çift tıkla. PC'de çalışan arayüz:
http://127.0.0.1:8890 . Sunucu bu bilgisayarın dışına açılmaz.
İnternet, model çıkarımı veya ekran kartında eğitim gerekmez.

## Kullanım

1. Soldaki 3D alanın herhangi bir yerine sol tuşla basıp sürükle.
   Yeşil noktayla gösterilen kol ucu, fare hareketi yönünde taşınır.
   Taban, omuz, dirsek ve bilekler ters kinematik ile birlikte hesaplanır.
   Her harekette her motorun dönmesi gerekmez; hedef için gereken eklemler değişir.
   Bıraktığında sanal kol bulunduğu pozda kalır.
2. **Shift + sol sürükleme** ile derinliği değiştir. Yukarı sürükleme kameradan
   uzağa, aşağı sürükleme kameraya doğru taşır. Normal sol sürükleme ekran
   düzlemindeki sağ/sol ve yukarı/aşağı hareketidir.
3. Fare tekerleğini aşağı çevir: kıskaç açılır; yukarı çevir: kapanır.
   Kolun diğer eklemleri bu işlem sırasında değişmez. Tekerlek hareketi bitince
   açıklık korunur. Fare 3D alanın üzerinde olmalıdır.
4. Sağ tuşu basılı tutup sürükle: bakış açısı döner, kol pozuna komut verilmez.
   Shift + tekerlek yakınlaştırır. Görünümü sıfırla yalnız bakış açısını değiştirir.
5. Durdur veya boşluk tuşu kontrolü durdurur. Simülasyona devam et ile
   aynı sanal pozdan devam edebilirsin. Escape mevcut sürüklemeyi bitirir.
6. **Z basılı + sol sürükleme** yalnız bileğin bükülmesini değiştirir.
   Yukarı/aşağı sürükle; diğer beş eklemin hedefi değişmez. Z bırakılınca
   normal birlikte hareket geri gelir. Sağ tuş görünüm, tekerlek kıskaçtır.

Bu arayüz ters kinematik ile kolun uç konumunu hesaplar; fizik, çarpışma,
zemin teması veya kavrama kuvveti simülasyonu yapmaz. Beş kol eklemi çözülür,
kıskaç açıklığı ayrı tutulur. Uç yönü mümkün olduğunca korunur; bu beş eksenli
kolda her konum ve yönün aynı anda erişilebilir olması garanti edilmez.
Uzanılamayan hedefler birikmez: her fare adımı mevcut uç konumundan hesaplanır;
model sınırları ve adım başına açı değişimi sınırı korunur. Uzanma sınırı
arayüzde gösterilir. Sağdaki kaydırıcılar eklemleri tek tek ayarlamaya devam eder.

Yeşil nokta, sabit kıskaç parmağının STL uç bölgesindeki köşelerinden türetilen
görsel referanstır. Fiziksel kavrama merkezi/TCP kalibrasyonu değildir.
Altı eklem gerçek SO101 modelinin eksenleri ve dönüşümleriyle hareket eder.
CAD geometrisi değişmedi; yeni sayısal model boyutu icat edilmedi.

## Gerçek kol

### Güncel beş motor düzeni — 2026-10-01

Kullanıcı, arızalı bilek motoru4 yerine eski kıskaç motoru6'yı taktı. Hedef
ID6 → ID4 değişimidir; kıskaç motoru artık yoktur. Donanım düzeni
`configs/virtual_leader.hardware.json` içinde açıkça1..5 olarak seçilir.
Eksik motor6 okunmaz, hedef/tork komutu almaz; tekerlek ve kıskaç kaydırıcısı
kapalıdır. Normal sol sürükleme beş eklemle ucu taşır; Z+sol bileği kontrol eder.
Görev şimdilik incire yaklaşmaktır; yaklaşma kaydı başarılı kavrama etiketi değildir.

ID değişimi ayrı, yalnız bu6→4 işlemini kabul eden araçla yapılır:
`.venv\Scripts\python.exe -m figbot_lab.motor_replacement --port COM5`.
Kaynak motor yanıtı, boş hedefID, sıcaklık ve tork bırakma doğrulanmadan
EEPROM'a yazılmaz. ID yazımı bir kez yapılır, yeniID okunur, diğer kalıcı
kayıtlar karşılaştırılır ve kilit eski durumuna getirilir. Belirsiz yazım
yanıtında ID yazımı tekrarlanmaz. Başarı kanıtı `runs/.../replacement.json`
dosyasına ve donanım yapılandırmasına kaydedilir. ID doğrulaması beklerken
gerçek kontrol açılmaz. Pasif kalibrasyon ve normal hareket adaptörlerinin
EEPROM yazma yasağı korunur.

Eski motor4 kapalı poz kaydı motor değişince geçersizleşti. Yeni referans
fiziksel olarak belirlenmeden gerçek Başlangıca dön gönderilmez. Modelin
sanal kapalı pozunu sıfırlamak kullanılabilir; bu fiziksel eşleme değildir.

USB motor kartını PC'ye bağla, doğru portu seç ve **Pozu oku** düğmesine bas.
Bu işlem motor konumunu, sıcaklığı ve gerilimi okur; tork açmaz, hareket
hedefi yazmaz. 55°C veya motor koruma hatası görülürse acil tork kapatma
devreye girer. Pasif kalibrasyonun ayrı READ-only arayüzü değişmemiştir.
Bağlantıyı kapatmadan aynı seri port başka bir kontrol uygulamasında açılmamalı.

### Mevcut pozdan deneme kontrolü

Fiziksel eşleme eksikse **Deneme kontrolünü başlat** kullanılabilir. Başlatma,
ölçülen motor pozunu ve o anda ekranda görülen sanal açıları geçici başlangıç
olarak bağlar. Başlatırken varsayılan poza gidilmez; mevcut poz tutulur.
Sol sürükleme, tekerlek, sağ sürükleme ve bırakınca tutma yukarıdaki gibi çalışır.
Başlangıçtan ±22,5 derece sınırı kaldırıldı. Hedefler motorların kayıtlı
konum aralığına göre gönderilir; bu kolda altı motorda da 0..4095 okunmuştur.
Bu kayıtlar fiziksel mekanik sınır ölçümü değildir. Sanal modelin eklem
aralıkları ve enkoderin tek tur aralığı korunur; 4095/0 atlaması yapılmaz.

Deneme yönleri geçici +1 kabulüdür; bütün fiziksel eksen yönleri doğrulanmadı.
Sanal uç yönü ile gerçek uç yönünün aynı olduğu henüz doğrulanmış değildir.
Fare hedefi doğrudan gönderilir; 90 sayım/saniye ve 32 sayım önden gitme
sınırları kaldırıldı. Hız komutu 3400, ivme komutu 50'dir. İlk 150 ivme
isteği motorlar tarafından 50'ye kırpıldı; eşleşmeyen geri okuma açılışı
durdurdu. 3400/50 profili altı motorda mevcut pozda doğrulandı.
Manuel yazılım sıcaklık kesmesi 55°C'dir; her yeniden başlatma altı motorun
güncel ölçümünün en fazla 45°C olmasını gerektirir. Motorun kayıtlı 70°C
koruması değiştirilmedi; EEPROM'a yazılmaz.
Manuel moddaki 10..12,6 V ve akım150 tezgâh kesmeleri kaldırıldı. Gerilim
kontrolü değişmemiş motor kayıtlarından alınır (bu kolda 4..14 V); bu kayıtlar
besleme yeterliliği veya motorun nominal çalışma aralığı kanıtı değildir.
Motorun koruma hata bayrakları yeni hedef gönderilmeden tork kesmesini
kilitler. Aşırı yük/akım/sıcaklık hatası seri okuma kaybı gibi tekrar denenmez.
Bir durum sorgusunun geçici hatası arayüzü kilitlemez. Komut akışı bir saniye kesilirse ölçülen poz
tutulur, oturum ACTIVE kalır; yeni fare hareketiyle devam edilir. Önceki
oturumun gecikmiş komutları hareket vermeden yok sayılır.
Gerçek donanım hataları `runs/..._virtual_leader_fault/fault.json` içinde
yakın geçmiş motor geri bildirimiyle kaydedilir ve hata ekranda gösterilir.

Geçici yanıt kaybında seri port açık kalır; eski hareket iptal edilir.
Okumalar 0,1–1 saniye aralıklarla tekrar edilir. Altı motor yeniden okunup
ölçülen pozun tutulması doğrulanınca yeni fare hareketi kabul edilir.
Yanıtı alınamayan hedef WRITE'ı tekrar gönderilmez. Sürekli besleme kaybını
bu yazılım düzeltemez; tutulma doğrulanmadıysa ekranda açıkça belirtilir.

**Başlangıca dön**, `configs/virtual_leader.closed_home.json` içindeki sabit
kapalı fiziksel poza döner. Model kendi kapalı açılarına hemen döner; gerçek
kol kendi ham motor hedeflerine gider. Önceki göreli eşleme bu dönüşü
belirlemez. Tamamlanma güncel motor ölçümleriyle doğrulanınca göreli eşleme
yeniden kurulur. Kayıtlı motor ofsetleri uyuşmuyorsa hareket gönderilmez.
Bu işlem mutlak yön/sınır kalibrasyonu yerine geçmez. Dönüş sırasında fare
engellenir; Pozu tut dönüşü keser. 15 saniye zaman aşımı veya yanıt kaybı
dönüşü iptal eder. Sıcaklık/koruma kesmesinden sonra otomatik dönüş yapılmaz.

**Durdur**, boşluk tuşu ve **Motor torkunu kapat** manuel kontrolde altı motoru
serbest bırakır. **Bağlantıyı kapat** da manuel motora poz tutma hedefi
göndermez; tork bırakmayı doğrulayıp seri portu kapatır. Tork kapanınca kol
kendi ağırlığıyla düşebilir. Bu işlemler adaptörün elektrik beslemesini
kesmez. Yanıt yoksa tork kesildiği iddia edilmez; besleme fiziksel olarak
kapatılmalıdır. Soğuma sonrası yeniden başlatma kullanıcı düğmesiyle yapılır.
Bu mod `RELATIVE_TRIAL`, `profile_verified=false`, `calibration=UNVERIFIED`
olarak kalır. Kayıtlar `COMMANDED_MOTOR_ACTIONS_RELATIVE_TRIAL` ve
`training_ready=false` taşır. `virtual_leader.closed_home.json` geçmiş kapalı
poz kaydıdır; tam fiziksel kalibrasyon değildir. `virtual_leader.trial_reference.json`
tarihsel görsel referanstır ve sabit kapalı başlangıcı belirlemez.

### Doğrulanmış eşlemeyle kontrol

Doğrulanmış **Kontrolü başlat**, fiziksel eşleme eksikse kilitlidir. Sanal modelin açısı ile
gerçek motorun enkoder sayımı henüz aynı referansta değildir. Eski pasif kayıt
minimum/maksimumları çalışma sınırı olarak kullanılmaz. Sadece kolu bağlamak
bu eşlemeyi tamamlamaz. Eşleme olmadan sanal model gerçek kolun fiziksel pozunu
temsil ettiği iddiasında bulunmaz.

Eşleme dosyası: `configs/virtual_leader.verified.json`; şablon:
`configs/virtual_leader.template.json`. Her eklem için gerekli ölçümler:

- `id`: fiziksel olarak doğrulanmış motor 1–6 sırası.
- `zero_raw`: kol modelindeki sıfır pozu fiziksel olarak karşılayan enkoder sayımı.
  Enkoderin otomatik 2048 merkezine eşit olduğu varsayılmaz.
- `direction`: modelde pozitif dönüşün motor sayımını artırması +1, azaltması −1.
  Kıskaç için pozitif model açısı açılma olmalıdır.
- `raw_min` / `raw_max`: o eklem için fiziksel olarak gözden geçirilmiş çalışma
  aralığı. 4095/0 üzerinden geçiş bu denetleyicide desteklenmez.
- `offset_encoded`: değişmemiş 31/32 numaralı motor kayıtlarının kodlanmış ofseti.
- `evidence`: sıfır/yön/sınır doğrulamasının kanıtı. Dosyanın genel durumu
  `VERIFIED` ve genel `evidence` açıklaması ancak bu işlemler tamamlandığında yazılır.

4096 enkoder sayımı bir motor çıkış devridir. Bu eşleme, hazır yapay zekâ
modelinin -100..100 gibi normalizasyon eşlemesinden ayrı tutulur.
Kalibrasyon aracı değiştirilmedi; motorların EEPROM ayarları yazılmaz.

Doğrulanmış eşlemeyle sürüş, iki sabit konum ölçümünden sonra mevcut pozda
tutmayı etkinleştirir. Başlangıçta varsayılan sanal poza gidilmez. Fare hareketi
45 sayım/saniye ilk deney sınırıyla ilerler; donanım hız/ivme profili 57/1'dir.
Bunlar fiziksel güvenlik, kuvvet veya çarpışmasızlık garantisi değildir.
Fare bırakıldığında uzak bekleyen hedef iptal edilir ve ölçülen poz tutulur.
Tarayıcı odağı kaybolduğunda veya fare iletişimi 350 ms kesildiğinde kontrol durur.
Bağlantı koparsa fiziksel tutma doğrulanamayabilir; bu durum arayüzde açıkça görünür.
Yazılımdaki Durdur enerji kesen donanımsal acil durdurma değildir.

## Kayıt

Kaydı başlat / Kaydı bitir hareket olaylarını `runs/..._virtual_leader/` içinde
yerel olarak saklar. Simülasyondaki kayıtlar `SIMULATION_ONLY` olarak işaretlenir.
Gerçek sürüşte ölçülen motor konumları ve gönderilen/geri okunan komutlar ayrı
zamanlarla saklanır. Simülasyon kaydı gerçek kol eğitim verisi yerine kullanılmaz.

Bu sürüm kamera görüntüsü kaydetmez. Görsel model eğitimi için kamera/enkoder/komut
zaman eşlemesi ve başarılı kavramaların gözden geçirilmesi ayrıca gereklidir.
`training_ready=false` korunur. Gerçek kontrolü başlatmak açık simülasyon kaydını bitirir.

## Geliştirici

Kaynak: `virtual-leader/src/`, sunucu ve motor denetleyicisi:
`src/figbot_lab/virtual_server.py`, `virtual_motion.py`.
Model kaynakları SHA256 ile doğrulanarak `virtual-leader/public/robot/` içine kopyalandı.

```powershell
.venv/Scripts/python.exe scripts/prepare_virtual_leader.py
cd virtual-leader
npm.cmd ci --cache ../.cache/npm
npm.cmd test
npm.cmd run build
cd ..
.venv/Scripts/python.exe -m pytest -q
```

Arayüz değişikliklerinden sonra tarayıcıyı yenile. Sunucu değişikliklerinde
önce gerçek bağlantıyı kapat, çalışan sunucuyu kapatıp yeniden başlat.
Eski `figbot/` projesine, CAD/baskı paketlerine, APK'ya veya kalibrasyon dosyalarına
bu çalışma yazmaz. Üretilen arayüz ayrı deneme klasöründe kalır.
