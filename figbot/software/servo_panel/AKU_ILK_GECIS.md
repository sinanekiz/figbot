# Aküye ilk geçiş — henüz enerji verme

Mevcut12V akü ve XL4016 satın alma geçmişine göre planlandı. Modülün gerçek klemenslerini ve mevcut sigorta bağlantısını fotoğrafla doğrulamadan kablo yerini tahmin etmeyin. Kolu mekanik olarak destekleyin; PWM kapatılması yükün düşmesini engellemez.

## İlk hazırlık

1. Servo powerbank beslemesini tamamen ayırın. UNO bilgisayar USB’sinde kalabilir. Firmware yüklemesi için servo gücü kapalı olduğunu bildirin.
2. XL4016'nın IN+/IN− ve OUT+/OUT− yazıları görünen fotoğrafını ve akü bağlantılarını paylaşın. Aküyü henüz PCA9685'e bağlamayın.
3. Planlanan enerji yolu: **akü → aküye yakın, kablo/konnektöre uygun sigorta ve kesme düzeni → XL4016 girişi → ölçülmüş5.0V çıkış → servo beslemesi**. Sigorta seçimi/hat akım kapasitesi bu yazıyla doğrulanmış değildir. Yüksek akım yolunda ince Dupont kablo kullanmayın; akü kutuplarını çıplak bırakmayın.
4. Çıkış ayarını motorlar ve PCA9685 ayrıyken yapın. Multimetre DC voltaj modunda, siyah prob COM ve kırmızı VΩ girişinde olsun; OUT+/OUT− arasında yaklaşık+5.0V ölçülmeli. **Akım modunda probları akü veya çıkışın iki ucuna değdirmeyin: kısa devre olur.**
5. Ayar doğrulandıktan sonra enerjiyi tekrar kesin; çıkış bağlantılarını bundan sonra yapın. Ham12V hiçbir koşulda servo kırmızı kablosuna, PCA9685 V+/VCC'ye veya UNO5V pinine gitmemeli.

## Doğrulama sonrası hedef bağlantı

| Bağlantı | Hedef |
|---|---|
| XL4016 OUT+ (ölçülmüş5.0V) | PCA9685 servo güç klemensi V+ |
| XL4016 OUT− | Aynı güç klemensinin GND/− ucu |
| UNO GND | PCA9685 GND (ortak sinyal referansı; mevcut bağlantı korunur) |
| UNO5V | PCA9685 VCC (lojik besleme; mevcut bağlantı korunur) |
| UNO A4 / A5 | PCA9685 SDA / SCL (mevcut bağlantı korunur) |

İlk denemede yalnız omuz çifti kullanılır; diğer servoların güç bağlantıları enerji kapalıyken ayrılır ve kol desteklenir. Bu tablo tüm servoların tek kart üzerinden yüksek akımda beslenmesine onay değildir. Gerçek kart klemens/yol kapasitesi bilinmiyor.

**İki XL4016'nın artı çıkışlarını birleştirmeyin.** Tipik PCA9685 kartında tüm servo kırmızı/V+ uçları ortak hattır. Farklı kanallara iki regülatör bağlamak onları ayırmaz. İkinci regülatörle ayrı servo grubu beslenecekse grubun artı kabloları PCA V+ hattından ayrılmalı; eksi/sinyal referansları ortak kalmalı. Bunu fotoğraf üzerinden ayrıca planlayacağız. INA2193.2A modüllerini de akım kapasitesi doğrulanmadan omuz güç yoluna seri eklemeyin.

Daha güçlü kaynak motorun tork/hız sınırını ortadan kaldırmaz. İlk deneme30°/sn ve küçük açı farklarıyla yapılır; ancak güç kararlılığı, mekanik uyum ve sıcaklık kontrolünden sonra hız kademeli artırılır. Sarsılma, uğultuyla durma, gevşeyen pim veya ısınma halinde servo beslemesini kesin. Aküyle güçlendirme fiziksel olarak henüz yapılmadı.

Kaynak: [Adafruit PCA9685 bağlantı ve ayrı servo beslemesi](https://learn.adafruit.com/16-channel-pwm-servo-driver?view=all). Kullanıcının klon kartının akım kapasitesi bu kaynakla doğrulanmış sayılmaz.
