# FIGBOT — ST3215 motor testi

ST3215 12 V servo + Waveshare Bus Servo Adapter (A) için Windows masaüstü paneli.
Bu program yalnız **mekanizmadan ayrılmış tek motorun masa testidir**. Kol geometrisi,
eklem limitleri ve yük altı hareketleri burada kalibre edilmez. Eski UNO/PCA9685
motor paneli bu seri haberleşmeli motorlar için kullanılmaz.

## Açılış

`GUNCEL/YAZILIM/ST3215_Motor_Test.cmd` dosyasına çift tıkla.
Bilgisayardaki proje `.venv` ortamında Python, Tkinter ve pyserial hazırdır.
Program otomatik bağlanmaz, motoru merkeze götürmez ve otomatik tork açmaz.

## Kablolar — önce tüm güç kapalı

1. Kartın A/B jumperlarını **B / USB** konumuna al.
2. **Yalnız bir motoru**, kutudaki üç damarlı orijinal kablo ile kartın servo
   soketlerinden birine tak. Soketi ters yönde zorlayarak takma. Diğer motorları
   şimdilik bağlama; aynı fabrika ID'sine sahip olabilirler.
3. USB-C **veri** kablosu: bilgisayar → kart. USB tek başına motor güç kaynağı değildir.
4. Motor etiketinin **12 V** olduğunu, adaptörün **12 V DC** ve uç polaritesinin kart
   ile uyumlu olduğunu kontrol et. Aldığın **12 V / 5 A** adaptörü kartın siyah
   DC5521 girişine bağla. Yeşil güç klemensi bu girişe alternatiftir; ikisini birden
   ayrı kaynaklarla besleme. Kart üzerinde gerilim düşürücü yoktur.
5. Gövdeyi sabitle; motor kola/dişliye bağlı olmasın, dönen başlığın çevresi boş kalsın.
   Sonra adaptöre enerji ver. Motor kablolarını değiştirmeden önce beslemeyi kes.

```text
Bilgisayar ─── USB-C veri ───┐
                           ▼
                    Bus Servo Adapter (A) [B]
12 V / 5 A adaptör ── DC ──┘       │
                                  └── 3 uçlu servo kablosu ── TEK ST3215
```

Üretici: [USB bağlantı çizimi](https://docs.waveshare.com/Bus_Servo_Adapter_A/Product-Wiring-Example),
[güç girişleri, 5 A sınırı ve CH343 bilgisi](https://docs.waveshare.com/Bus_Servo_Adapter_A/FAQ).

## İlk deneme

1. **Yenile** → kartın USB/CH343 COM portunu seç. Bluetooth COM portlarını seçme.
2. Baud **1000000** → **Bağlan**.
3. Motor ID **1** → **Oku**. ID bilinmiyorsa **ID 1–6 ara**; farklı bilinen ID'yi
   kutuya elle yazabilirsin. Arama sadece okur, motoru hareket ettirmez.
4. Konum, gerilim ve sıcaklık görünmeli. Motorun mekanizmadan ayrı olduğunu
   belirten kutuyu işaretle → **Testi etkinleştir**.
5. **+5° / −5°** ile başla. **Aralık** menüsünde 60°, 180° ve **270°** var;
   başlangıç seçimi kullanıcının isteğiyle 270°. Testi etkinleştirmeden önce seç.
   Sürgünün iki ucu arasındaki fark bu açıdır. Pencere mevcut konumu içerecek
   biçimde motorun 0–4095 sınırları içine yerleştirilir; motorun EEPROM açı
   limitleri daha darsa aralık da daralır. Başlangıçta motor yerinden oynatılmaz.
   Hız başlangıçta kullanıcının isteğiyle **Maksimum**; diğer seçenekler
   15, 30, 60, 120, 180 ve 270°/sn.
   Hız değişikliği bir sonraki sürgü/±5° komutunda uygulanır.
   Maksimum, **hız kaydı 0 + ivme kaydı 0** gönderir. Üretici konum kontrolünde
   bu değerleri maksimum hız ve maksimum ivme olarak tanımlar; **0 burada dur
   demek değildir**. Önceki 3400 adım/sn ve ivme10 profili kaldırılmıştır.
   Gerçek hız garanti değildir; 12 V standart motorun katalog yüksüz hızı
   yaklaşık270°/sn'dir. Sayısal hız seçeneklerinde ivme10 tekrar uygulanır.
   Maksimum profilde başlangıç/duruş daha serttir. Tork kapatma ayrı işlemdir.
   Bu aralık **çıplak motor testi** içindir; kola takılı motor için eklem limiti değildir.
6. Bitirince **Torku kapat** veya **Esc**. Bu işlem motoru serbest bırakır, mekanik
   fren değildir. Kapatma komutu tüm servo hattına gönderilir, yayın yanıtı yoktur;
   USB kopuksa iletim garanti edilemez. Ardından adaptörün gücünü kes.

Program torku açmadan eski hedefi okunan mevcut konumla değiştirip doğrular.
Yalnız konum modu (mod 0) desteklenir. Otomatik merkezleme, açı limiti silme,
kalibrasyon, sürekli dönüş ve toplu hareket yoktur. Motor cevap vermezse bekleyen
hareketler silinir; ekranda eski veriler canlı ölçüm gibi bırakılmaz.

## Altı motoru numaralandırma

Her defasında fiziksel olarak **yalnız bir motor** bağlı olsun.
**Oku** → Yeni ID alanına 1–6 arasında seçtiğin numara → **ID kaydet**.
Program ID'yi tekrar okuyup EEPROM kilidini doğrular. Motora ID etiketi koy.
Gücü kesip sonraki motoru tak. İlk motor 1 olarak kalabilir; diğerlerine 2–6 ver.
Aynı ID'li birden fazla motorun varlığı yazılımla güvenilir biçimde tespit edilemez.
Bu numaralar henüz SO-101 eklem eşlemesi veya kalibrasyonu anlamına gelmez.

## Ekrandaki değerler

- Açı, 4096 adım/tur enkoder dönüşümüdür; robot ekleminin mekanik sıfırı değildir.
- Gerilim ve sıcaklık servo geri bildirimidir.
- **Akım ham** alanı amper değildir; akım ölçeği gelen motor sürümünde henüz
  doğrulanmadığından A/mA uydurulmaz.
- 9–12,6 V ve 60 °C altı yazılımın konservatif tezgâh testi kabul penceresidir;
  motorun veri sayfası sınırlarını yeniden tanımlamaz.
- Kartın üretici sınırı **5 A**. Bu test altı motorun aynı anda yük altında
  beslenebileceği anlamına gelmez. İlk testler tek motor ve yüksüz yapılır.

## Port veya motor bulunamıyorsa

Yenile → veri kablosu → farklı USB girişi → B jumperları → 12 V besleme → tek motor
→ doğru ID ve baud sırasıyla kontrol et. USB kartı hiç görünmüyorsa resmi
[Waveshare kaynaklarındaki CH343 sürücüsünü](https://docs.waveshare.com/Bus_Servo_Adapter_A/Resources)
kullan. UNO firmware yüklemesi gerekmez.

## Doğrulama sınırı ve kaynak

Seri paketler, küçük hareket sınırları, başlatma sırası ve ID yazımı simüle edilmiş
seri hatla test edilmiştir. 19 Eylül 2026'da gerçek CH343 kartı COM5 üzerinden
salt okunur sorguyla yanıt verdi: ID 1, model kodu 777, konum modu 0, 12,4 V,
32 °C, tork kapalı, konum 3235 adım. COM numarası ve ölçümler bağlantıya göre değişir.
Gerçek hareket ve gerçek motora ID yazımı **PHYSICAL VALIDATION REQUIRED**;
bu doğrulamada hareket veya EEPROM yazma komutu gönderilmedi.

Protokol kaynağı: [Waveshare Python örneği](https://docs.waveshare.com/Bus_Servo_Adapter_A/Python_Execution_Example)
ve [resmî SDK ZIP](https://files.waveshare.com/wiki/Bus_Servo_Adapter_A/STServo_Python.zip)
içindeki `scservo_sdk/sms_sts.py`, `protocol_packet_handler.py` (19 Eylül 2026).
Demo geliştirme komutu: `.venv/Scripts/python.exe -m software.st3215_test.app --demo`.
Demo gerçek seri port açmaz; başlıkta DEMO yazar.

Hız referansı: [ST3215 resmî örnek ve teknik değerler](https://www.waveshare.com/wiki/ST3215_Servo),
katalog yüksüz hız 0,222 sn/60° @12 V.
Maksimum profil anlamı: [Waveshare ST servo konum kontrolü](https://www.waveshare.com/wiki/08_Sub-controller_JSON_Command_Set),
`CMD_JOINTS_RAD_CTRL`/`CMD_EOAT_HAND_CTRL`: spd=0 maksimum hız, acc=0 maksimum ivme.
ST3215-TEST-3'ün bu profili fiziksel hız/süre ölçümüyle henüz doğrulanmadı.

## Taban için kaydedilen montaj konumları
Kullanıcı 19 Eylül 2026 tarihinde sıfır=234°, bitiş=113° ve artan yönde
360°/0° üzerinden toplam239° hareket bildirdi. Kayıt `so101_calibration.json`.
Kol açısı0° → motor234°; kol açısı126° → motor0°; kol açısı239° → motor113°.
Bu yalnız kalibrasyon girdisidir; bu tezgâh uygulaması kaydı hareket sınırı olarak
kullanmaz. Motora veya EEPROM'a uygulanmadı. 113° hedefini doğrudan göndermek,
istenen239° yolun izleneceğini garanti etmez; sıfır geçişi tam kol kontrolünde
ayrıca uygulanıp doğrulanmalıdır. Başlık veya enkoder ofseti değişirse kayıt yeniden alınır.
