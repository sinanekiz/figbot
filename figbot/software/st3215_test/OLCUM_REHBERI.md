# İlk ortam ölçüleri

![Ölçüm çizimi](OLCUM_REHBERI.png)

Değerleri santimetre olarak sohbete yaz; uygulamaya girmen gerekmiyor.
O, tabanın dik dönme ekseninin kolun sabitlendiği yüzeye izdüşümüdür.
Ön, incir toplama alanına doğru seçilen yöndür. Sağ ve sol bu yöne bakarken belirtilir.

1. O ile sepet merkezinin ileri/geri mesafesi. Çapraz uzaklık değil; öne paralel ölçülür. Sepet gerideyse belirt.
2. Sepet merkezinin yana mesafesi: sağ/sol bilgisini ekle.
3. Sepetin iç çapı. Yuvarlak değilse iç en ve boyunu, şeklini belirt.
4. Kolun sabitlendiği yüzeyden sepetin iç tabanına kadar yükseklik.
5. Aynı yüzeyden sepetin üst kenarına kadar yükseklik.
6. İncirin durduğu yüzeyin kolun sabitlendiği yüzeye göre yüksekliği: aşağı/yukarı belirt. Aynı yüzeydeyse 0.
7. İncirin durduğu yüzeyden tepesine kadar yükseklik; farklı boylar varsa küçük ve büyük örnekleri ölç.

Ölçmek için kolu hareket ettirmek gerekmez. Sepet tabanı veya kenarı referans yüzeyden aşağıdaysa bunu belirt.
Bu çizim ölçekli değildir; robot boyutları veya gerçek kurulum ölçüleri çizimden çıkarılamaz.

## Kalibrasyon durumu

Bu ilk ortam ölçüleri tek başına otonom toplama kalibrasyonu değildir. O bir kullanıcı ölçüm referansıdır; vendor URDF base_link başlangıcıyla aynı olduğu varsayılmaz. Robot koordinatlarına dönüşüm, kamera–kol eşlemesi, kavrama merkezi, çene payı ve fiziksel hedef doğruluğu ayrıca doğrulanmalıdır. Durum: PHYSICAL VALIDATION REQUIRED. Ölçüler gelmeden sayısal uygulama ayarı üretilmez.

Görsel üretim briefi: Türkçe, numaralı 7 ölçü; üstten O–sepet merkezi ileri/yan bileşenleri ve iç çap; yandan ortak montaj düzleminden sepet iç tabanı/üst kenarı; incir yüzey farkı ve incir yüksekliği. Kesin ok uçları için son görsel özgün geometrik çizim olarak scripts/draw_measurement_guide.ps1 ile üretilir.
