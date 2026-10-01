# Uno ile STS3215 kimlik okuma

Hazırlanmış prototip; henüz derlenmedi ve fiziksel olarak denenmedi.
Yalnız READ (komut 2) gönderir. Hareket, tork, EEPROM ve ID değiştirme yoktur.
Bu test iletişimi sınar; yanıt alınması motorun yük altında sağlam olduğunu kanıtlamaz.

## Gerekenler

- Uno Rev3 / ATmega328P (başka Uno modelleri için doğrulanmadı)
- 74HC125, 14 pin DIP; breadboard, kablolar
- 100 nF kondansatör, iki 10 kohm direnç
- Motorun etiketine uygun ayrı besleme; 12 V yalnız 12 V motor varyantında
- Uno için ayrı besleme: örneğin USB çıkarılınca barrel girişinden uygun 7–9 V

Motor fişindeki V+, GND ve DATA konumları bu dosyada varsayılmamıştır.
Motor modelinin üretici pin şemasından veya etiketli kart bağlantısından doğrulayın.
Besleme kapalıyken kurun. Motor DATA hattına veya Uno 5 V pinine 12 V vermeyin.

## 74HC125 bağlantısı (üstten görünüşte üretici pin numaraları)

| Bağlantı | Hedef |
|---|---|
| Pin 14 VCC | Uno 5 V |
| Pin 7 GND | Uno GND ve motor beslemesi eksi |
| Pin 14–7 | 100 nF kondansatör |
| Pin 1 /1OE | Uno D2; ayrıca 10 kohm ile 5 V |
| Pin 2 1A | Uno D1/TX |
| Pin 3 1Y | Motor DATA |
| Pin 4 /2OE | Uno D3; ayrıca 10 kohm ile 5 V |
| Pin 5 2A | Motor DATA |
| Pin 6 2Y | Uno D0/RX |
| Kullanılmayan /OE pinleri 10,13 | 5 V |
| Kullanılmayan girişler 9,12 | GND |
| Kullanılmayan çıkışlar 8,11 | Boş |
| Motor V+ | Etiketine uygun harici besleme artı |

TTL veri seviyesi ile motorun 12 V güç hattı farklıdır.
74HC125, veri gönderirken çıkışı açar, yanıt beklerken yüksek empedansa geçirir.

## İşlem

1. Motor beslemesini kapatın; D0/D1 bağlantılarını yükleme sırasında ayırın.
2. Arduino IDE: Arduino Uno kartını seçip aynı klasördeki .ino dosyasını yükleyin.
3. USB kablosunu Uno'dan çıkarın. D0/D1 bağlantılarını takın.
4. Uno'yu ayrı besleyin, tek motorun beslemesini açın, Uno RESET'e basın.
5. Üç saniye sonra 1..6 ID taranır (1 Mbaud, 500 kbaud, 115200 baud).
6. Dahili L LED'de kısa yanıp sönme sayısı cevap veren motorun ID'sidir.
   Her döngünün başında uzun ışık varsa cevapta hata bayrağı vardır.
   On hızlı yanıp sönme: geçerli cevap alınamadı; arıza kesinleşmiş değildir.

USB bağlıyken kullanmayın: Uno'nun USB–seri devresi D0/D1'i paylaşır ve bu
testte veri hattını etkileyebilir. Seri monitör kullanılmaz, sonuç LED ile gösterilir.
Kısa test sonunda motor beslemesini kapatın; güç açılışındaki tork durumu
bu READ-only program tarafından değiştirilmez. Hızla ısınırsa testi kesin.

Kaynaklar:
- https://www.ti.com/lit/ds/symlink/sn74hc125.pdf
- https://github.com/ftservo/FTServo_Arduino/blob/main/src/SMS_STS.h
- https://docs.arduino.cc/hardware/uno-rev3/
