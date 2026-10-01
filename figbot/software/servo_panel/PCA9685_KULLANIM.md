# PCA9685 kol paneli — tezgâh testi

`Motor_Kontrolu.cmd` yeni `pca_app.py` panelini açar. Eski D9 paneli `app.py` ve firmware korunmuştur.
Firmware V5: `firmware/uno_pca9685/uno_pca9685.ino`; UNO115200 baud, PCA9685 0x40. V1/V2/V3/V4 firmware must be updated before using this panel. Bu USB paneli omuzlar için 1000–2000 µs aralığını kullanır; Android v0.9 aralık ayarları ayrı HC-05 sürümündedir.

## Bağlantı

UNO 5V → VCC, GND → GND, A4 → SDA, A5 → SCL. Motor harici düzenlenmiş 5V ile V+ / GND üzerinden beslenir.
Servo kırmızı V+, kahverengi/siyah GND, sarı/turuncu PWM. Etiketleri takip et; 12V aküyü doğrudan bağlama.
2A powerbank yalnızca tek yüksüz motor denemesi içindir; tam kolun beslemesi doğrulanmış değildir.

## İlk deneme

1. Tek yüksüz motoru kanal 0'a tak. Kabloları değiştirirken gücü çıkar.
2. Panelde COM3 → Bağlan. Bağlanmak veya kutucuğu işaretlemek hareket üretmez.
3. CH00 kutucuğunu işaretle. Diğer kanallar kapalı kalsın.
4. Küçük test düğmesi 90→95→85→90 komutlarını verir ve 5 saniye sonunda PWM'yi kapatır.
5. Alternatif: kaydırıcıyı sürükle. Hız 10–360 komut derece/saniye. İlk komutta gerçek mil konumu bilinmediği için hız sınırlaması garanti edilmez.
6. Tüm PWM sinyallerini kapat düğmesi bekleyen hedefleri ve otomatik test adımlarını iptal eder. Yeniden hareket için kutucuğu tekrar işaretle.

## Kanal planı (fiziksel kablolama henüz doğrulanmadı)

| Eklem | Kol 1 | Kol 2 | Motor |
|---|---:|---:|---|
| Taban | 0 | 6 | MG996R |
| Omuz 1 | 1 | 7 | MG996R |
| Omuz 2 | 2 | 8 | MG996R |
| Dirsek | 3 | 9 | MG996R |
| Bilek | 4 | 10 | MG90S |
| Tutucu | 5 | 11 | MG90S |

Bu kanal planı bir yazılım eşlemesidir, satın alınmış ikinci kol iddiası değildir.
## Tek barla karşılıklı omuzlar (V3 / DEC-055 ve DEC-058)

Kol1: CH1+CH2; Kol2: CH7+CH8. Her çiftte ayrı ikinci bar kaldırıldı. A=θ, B=180−θ;
örnek hedefler90/90,100/80,80/100. Ters seçeneği eklemin bütün yönünü değiştirir, tek motorun yönünü değiştirmez.
Her20ms aynı mantıksal rampadan iki tamamlayıcı darbe hesaplanır ve bitişik PCA9685 kayıtlarına tek I2C aktarımıyla yazılır.
MODE2 OCH=0 ile iki yeni PWM kaydı aynı STOP koşulunda güncellenir. Bu, fiziksel millerin aynı anda/hedefte olduğuna dair sensör kanıtı değildir.
Kaynak: [NXP PCA9685, MODE2 OCH ve auto-increment](https://www.nxp.com/docs/en/data-sheet/PCA9685.pdf).

İlk eşleme:

1. Kolu destekle. Servo başlıklarını mekanik omuz yükünden ayır; iki motor birbirini zorlamasın.
2. İki servo için yeterli harici5V beslemeyi kullan. Mevcut5V2A powerbank'in iki MG996R'yi sorunsuz besleyeceği doğrulanmadı.
3. Panelde omuz satırındaki bağlantı/merkez kontrolü kutusunu ve ardından ortak omuz etkinleştirmesini işaretle.
4. Önce90° düğmesine bas. Etkinleştirmeden sonraki ilk omuz hareketi sadece merkez olabilir; bu ilk hareket hız rampasıyla garanti edilemez.
5. Başlıklar ayrıkken küçük açı değişimleriyle karşı yönü gözle. Sonra enerjiyi kesip milleri çevirmeden başlıkları aynı mekanik omuz pozisyonuna oturt.
6. Yüksüz, düşük hızda küçük ortak hareket dene. Vızıltı/zorlama/ısınma varsa durdur, gücü kes; merkez/servo eşleşmesini düzeltmeden devam etme.

Nominal merkezler1500/1500us; darbe toplamı3000us. Bireysel merkez düzeltmesi/gain kalibrasyonu uygulanmadı; mekanik horn hizası ve gerçek servo hareket farkları PHYSICAL VALIDATION REQUIRED.
Omuz: 10-180 command degrees/s, default30. Narrow1000-2000us pulse range only. Physical calibration still required.
`E1`/`E2` birlikte etkinleştirir (hareket yok); `D1`/`D2` birlikte kapatır. Diğer çift7/8 aynıdır.
`S1,angle,speed` veya `S7,angle,speed` tek ortak hedef protokolüdür; `P1/P2/P7/P8` reddedilir.
Kapatma/watchdog sonrası iki kanal da kilitlenir; tekrar etkinleştirme ve merkez komutu gerekir. Otomatik yüklü kol kinematiği hâlâ yok.

## Aralık, durum ve sınırlar

0–180° komut ölçeği varsayılan 1000–2000 µs'ye eşlenir; fiziksel 180° hareket garanti değildir.
Omuz haricindeki Geniş seçeneği eski tek motor deneyindeki 500–2500 µs aralığını verir. Her motorda mekanik uçlar ayrı doğrulanmalıdır.
Ters seçeneği sonraki hedefi ters çevirir; aralık/yön/hız seçimini değiştirmek tek başına hareket göndermez.
Kart hedefi ACK'dır, konum sensörü ölçümü değildir. Nominal 25 MHz osilatör/50 Hz PCA zamanlaması fiziksel ölçülmedi.
UNO tarafında 1.5 saniye haberleşme kesilmesi kanalları kapatır ve etkinleştirme kilidini sıfırlar. PC yanıt zaman aşımı 1.2 saniyedir.
I2C arızasında kapatma yalnızca denenebilir: PCA9685 bağımsız çalışır, arızalı I2C üzerinden durma garanti edilemez.
OE donanımsal kesme bağlı değil. PWM kapatma güç kesme veya güvenlik sınıfı acil durdurma değildir; kolu destekle ve gerekirse servo gücünü fiziksel olarak kes.

## Geliştirme doğrulaması

`python -m pytest software/servo_panel/test_pca.py tests/test_pca_firmware.py software/servo_panel/test_controller.py software/servo_panel/test_app.py -q`

Gerçek UNO derlemesi Arduino CLI `arduino:avr:uno` hedefiyle yapılır. Native firmware testinde gerçek .ino sahte Wire/Serial/saat ile çalışır; donanım testinin yerine geçmez.
PCA kaynak başvurusu: https://github.com/adafruit/Adafruit-PWM-Servo-Driver-Library/blob/master/Adafruit_PWMServoDriver.cpp


V5 henüz karta yüklenmediyse güncel panel eski kartla hareket başlatmaz. Yüklemeden önce servo harici gücünü çıkarıp kolu destekle; UNO bilgisayar USB’sinde kalsın. Akü geçişi için AKU_ILK_GECIS.md dosyasına bak.
