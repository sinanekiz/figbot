# Tek servo ilk hareket testi

V4: `P<açı>,<hız>\n` kadran komutu eklendi. 0–180 komut derecesi 1000–2000 µs
aralığına eşlenir. Hız 0 ise hedef anında gönderilir; 30–360 ise komut derecesi/sn
cinsinden yazılımsal hız sınırı uygulanır. Gerçek fiziksel açı/hız ölçülmez.
Rampa, son üretilmiş sinyal konumundan başlar; gerçek mil geri bildirimi yoktur.
Başlangıçta bu referans 1500 µs'dir. `x` rampayı da iptal eder. Komutsuz
10 saniyelik kapanma geçerlidir. 20 ms aralıklı rampa ve 60 ms GUI hedef güncellemesi
birbirinden bağımsızdır; motor iç kontrolü hızın fiziksel üst sınırını belirler.

Bu program Arduino UNO R3 ve tek, mekanizmaya bağlanmamış MG996R veya MG90S içindir.
Fiziksel test henüz yapılmadı. İlk hareket merkezi gerçek mil konumundan farklı olabilir.

## Bağlantı

- Akü artı -> aküye yakın hat sigortası -> XL4016 IN+; akü eksi -> IN-.
- Servo bağlı değilken XL4016 çıkışını multimetreyle 5,0 V olarak ayarla.
- Gücü kes; XL4016 OUT+ -> servo kırmızı; OUT- -> servo kahverengi/siyah.
- OUT- ile UNO GND arasında ortak toprak bağlantısı kur.
- Servo turuncu/sarı/beyaz sinyal -> UNO D9. Renkleri servonun etiketiyle doğrula.
- UNO bilgisayardan USB ile beslenecek. Servo gücünü UNO 5V pininden alma.
- Akünün 12 V çıkışını servoya bağlama; kabloları enerji kesikken değiştir.
- Servo akımını ince sinyal jumperlarından veya breadboard güç raylarından geçirme.

Sigorta seçimi kullanılan kablo, konnektör ve güç koluna göre doğrulanmalıdır;
mevcut 7,5/10 A sigorta motorun aşırı yük koruması olarak kabul edilmez.

## Kullanım

1. Kol, kavrama mekanizması ve yük bağlı olmasın. Servo gövdesini sabitle, mil serbest kalsın.
2. Arduino IDE ile uno_servo_check.ino dosyasını aç. UNO kartını ve ilgili COM portunu seç.
3. Servo.h bulunamazsa kütüphane yöneticisinden Arduino Servo kütüphanesini kur.
4. Kodu yükle; Seri Monitör'ü 115200 baud ile aç.
5. Ölçülmüş 5 V servo beslemesini aç. `c` gönder: 1500 us merkez komutu.
6. `l`, `c`, `r`, `c` komutlarını aralarında birer saniye bırakarak gönder.
7. `x` sinyali kapatır. Komutsuz 10 saniye sonra sinyal otomatik kapanır.
8. Motor beslemesini fiziksel olarak kes, ardından sıradaki motoru bağla.

V3 (2026-09-05): kullanıcı yön gözlemine göre `l=1600 us`, `r=1400 us`.
`c/l/r/t` komutları sinyal kapalıyken de kullanıcının isteğiyle etkinleştirir;
yeniden hareket için önceden merkezleme gerekmez. Başlangıçta sinyal yine kapalıdır.
`t`, rampasız 1000–2000 us hedefleriyle üç gidiş-dönüş gönderir.
Hedefler arasında 700 ms beklenir; ardından merkezlenir ve sinyal kapanır.
Bu aralık doğrulanmış fiziksel 0–180 derece sınırı değildir. `x` beklemeleri
bloklamadan testi iptal eder. Hızlı test sırasında `x` dışındaki komutlar dikkate
alınmaz. Test devam ederken tekrar `t` süreyi uzatmaz.

`x` ve zaman aşımı elektriği kesmez; gerçek güç kesme yerine geçmez.
Zorlanma, sürekli sert titreme veya hızlı ısınma olursa servo gücünü kes.
Bu test haberleşme ve temel hareket kontrolüdür; hız, tork, ömür veya toplama
kapasitesini doğrulamaz. Aynı eklemi sürecek iki servoyu bu aşamada birbirine bağlama.

Kaynak: https://support.arduino.cc/hc/en-us/articles/360017053760-Troubleshoot-servo-motors

## Yazılım kontrolü

tests altındaki host testi başlangıçta çıkışın kapalı kalmasını, etkinleştirmeyi,
komut aralığını ve zaman aşımını sahte Arduino/Servo arayüzüyle doğrular.
Gerçek UNO derlemesi ve fiziksel hareket ayrıca doğrulanmalıdır.


## V5 provisional wider dial mapping (2026-09-05)
User reports approximately 90 degrees over 1000–2000 us and requests remapping. The dial now maps 0/90/180 to 500/1500/2500 us. This is a provisional linear extrapolation, NOT physically calibrated endpoints. Begin unloaded at centre and approach endpoints gradually; stop and remove servo power if motion stops with buzzing. Initial ramp is 60 command degrees/s; unrestricted mode remains selectable. The automatic three-cycle test deliberately remains 1000–2000 us (narrow range) pending physical verification. Connecting does not command motion.
