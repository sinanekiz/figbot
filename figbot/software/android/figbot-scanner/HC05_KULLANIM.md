# FIGBOT Kontrol v0.9 — sade motor ekranı

Güncel kullanım ve kurulum: `releases/HC05-v0.9-KURULUM.md`. APKv0.9 ile UNOV5 birlikte güncellenmelidir. Hızlar varsayılan360, eklemler her yeni doğrulanmış bağlantıda komuta hazır; başlangıçta hareket yok. Ayarlar ayrı pencerede, kaydırıcı bırakılınca hedef gönderilir. Ortak omuzlar için kademeli darbe aralığı eklendi; fiziksel uçlar yüksüz doğrulanmalıdır. V5 donanım kurulumu bekleniyor.

Aşağıdaki v0.8 açıklamaları geçmiş sürüme aittir; güncel davranış için yukarıdaki v0.9 kılavuzunu kullan.

Telefon paketi: `releases/FIGBOT-Kontrol-HC05-v0.8-debug.apk`.
Kurulum: `releases/HC05-v0.8-360-KURULUM.md`.

## Motor kontrolü

- Kol 1: CH0 taban, CH1+2 ortak omuz, CH3 dirsek, CH4 bilek, CH5 tutucu.
- Kol 2: aynı düzenle CH6..11; ortak omuz CH7+8.
- Her eklemde hız seçenekleri 10/30/60/90/120/150/180/240/300/360 komut derece/saniye. Başlangıç 30. Seçim sonraki hedef komutuna uygulanır.
- Açı barı 0..180 komut ölçeğidir; gerçek mil açısı/hızı ölçülmez. 360°/sn seçimi sürekli dönüş veya daha yüksek tork sağlamaz.
- Omuzlar tek ortak yörüngeyle karşılıklı sürülür; nominal darbeler toplamı 3000 µs, aralık 1000..2000 µs. Omuz geniş aralık ve bağımsız takipçi kontrolü kapalıdır. İlk omuz hedefi 90° merkezdir.
- Tekil eklemlerde 500..2500 µs seçeneği önceki gibi yalnız fiziksel sınırları denenmiş, yükten ayrık motor içindir.
- Uygulama başlangıcı, bağlantı ve etkinleştirme hareket komutu göndermez. Etkinleştirmeden sonraki ilk hedefte gerçek başlangıç konumu bilinmediğinden fiziksel hız sınırlaması garanti edilmez.

## Güncelleme ve bağlantı

Yeni uygulama UNO V4 / STATUS4 gerektirir. V3 veya önceki sürümle hareket açılmaz; telefon ve UNO birlikte güncellenmelidir. Servo beslemesini ayır, kolu destekle, ardından USB üzerinden firmware ve APK kurulumunu yap. Uygulamayı kaldırmak yerine güncelle; kamera kayıtlarını silme.

HC-05 firmware: `firmware/uno_pca9685_hc05/uno_pca9685_hc05.ino`.
USB panel alternatifi: `firmware/uno_pca9685/uno_pca9685.ino`.
HC-05, AltSoftSerial 1.4.0 ile D8 RX / D9 TX, 9600 baud kullanır. Timer1 bu haberleşmeye ayrılır. Servo PWM'i PCA9685 üretir. USB ile Bluetooth aynı anda komut sahibi değildir.

| Kaynak | Hedef |
|---|---|
| HC-05 TXD | UNO D8 |
| UNO D9 | 1 kΩ üzerinden HC-05 RXD düğümü |
| RXD düğümü | 2 kΩ üzerinden GND |
| HC-05 VCC | Taşıyıcı kartın izin verdiği regüle besleme |
| HC-05 GND | UNO/PCA ortak GND |
| UNO A4 / A5 | PCA SDA / SCL |
| UNO 5 V / GND | PCA VCC / GND (mantık beslemesi) |

Mevcut bölücü: A18→1 kΩ→A14, A14→iki seri 1 kΩ→GND. HC-05 EN/KEY/STATE kullanılmaz. D0/D1 kullanılmaz. Akü doğrudan servo V+, HC-05 veya UNO 5 V girişine bağlanmaz; servo akımı UNO üzerinden geçmez. Güç kaynaklarının artı çıkışları birbirine paralel bağlanmaz.

Telefonda HC-05 ile eşleş, Motor testleri → HC-05 bağlan → eşleştirilmiş cihazı seç. Android 12+ yakın cihaz izni gerekir. “HC-05 · UNO V4 · PCA9685 hazır” alınmadan hareket açılamaz. Motor ekranı kamera/ARCore gerektirmez.

## Durdurma

DURDUR bekleyen hareketleri temizleyip X gönderir. Motor ekranından ayrılmak, arka plana geçmek veya kol ekranını değiştirmek durdurmayı tetikler. Otomatik yeniden bağlanma/etkinleştirme yoktur. Hareket gönderimi en fazla 10 komut/sn; heartbeat 300 ms, telefon yanıt süresi 1,2 sn, UNO watchdog 1,5 sn. PWM kapatma motor elektriğini kesmez; desteklenmeyen kol düşebilir. I2C arızasında çıkış kapatma garanti edilemez.

## Fiziksel durum

Kullanıcı omuz merkez/yönlerini yüksüz doğruladığını bildirdi. Sonraki besleme testinde regülatör çıkışı tek motorla 3,44 V, iki motorla 2,40 V; akü ve IN 12,6 V bildirildi. Aynı sistemin powerbank ile düzgün çalıştığı kullanıcı tarafından bildirildi. Kesin kök neden, regülatör OUT multimetre ölçümü ve kaynaklar arasında aynı yük koşulu doğrulanmadı. Bu sonuçlar şarjı bitmiş aküyü kanıtlamaz; regülatör/çıkış yolu araştırılmalıdır. Yük altında düşüşü gerilim ayarını yükselterek telafi etme.

MT-4012C ile eşzamanlı robot yükü ve şarj desteği doğrulanmadı; robotu aküden ayırarak şarj et. V0.8/UNO V4'ün 360°/sn gerçek hareketi ve yüklü kaldırması PHYSICAL VALIDATION REQUIRED. Önceki V3 haberleşme deneylerinin ayrıntıları firmware README ve ASSUMPTIONS.md içinde tarihsel olarak kayıtlıdır.

## Kamera ve testler

Kamera ekranı algılama, ARCore derinlik/zemin, taban koordinatı kaydı ve JSON/HTTP gözlemleri üretir; otonom motor hareketi başlatmaz. `arm_motion_authorized:false` korunur. Gerçek toplama için fiziksel servo kalibrasyonu ve yol/çarpışma doğrulaması gereklidir.

V0.8 APK derlemesi, 13 Java testi ve Android lint tamamlandı (0 hata, 34 uyarı). Firmware ve panel için 13 Python/C++ testi geçti; iki omuz çifti 360 komut derece/sn ile tam komut aralığını 500 ms'de tamamlıyor, 361 reddediliyor. HC-05 ve USB UNO derlemeleri tamamlandı. Donanım yüklemesi ve telefon kurulumu ayrıca doğrulanmalıdır; derleme başarıları gerçek motor hızı ölçümü değildir.
