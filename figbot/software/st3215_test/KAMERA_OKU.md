# Kamera ve konum okuma — kalibrasyon hazırlığı

`GUNCEL/YAZILIM/Kol_Kamera_Konum.cmd` ile açılır. Bu ekran kamera önizlemesi,
motor geri bildirimi ve yerel görüntü/JSON kaydı sağlar. Tam kol kalibrasyonu,
hareket öğretme ve otomatik toplama henüz uygulanmadı.

- Kamerayı aç: ilk kamera 0, gerekirse 1. Telefon Windows'a kamera olarak
  tanıtıldıysa uygun numarayı seç. Kamerayı kullanan başka uygulamayı kapat.
- Motorlar aynı ID'de olabilir. Önce beslemeyi kapatıp zinciri ayır; yalnız
  bir motoru sürücüye bağla. Mekanik montajı sökmek gerekmez; kol destekli olsun.
- Tek motor doğrulamasından sonra mevcut ID'yi okumayı başlatabilirsin.
  Ayrı ID atama ve fiziksel eklem eşleştirmesi bu ekranın işlevi değildir.
- Altı motoru birlikte okuma yalnız her birinin farklı 1–6 ID'si önceden
  doğrulandıysa seçilir. PING yanıtı ID çakışmasının olmadığını kanıtlamaz.
- Yalnız PING/READ paketleri gönderilir. Yazma, hareket, tork, EEPROM ve yayın
  komutları protokol katmanında engellidir. Açılışta USB/kamera açılmaz.
- USB okumayı kapat veya pencereyi kapat motor torkunu değiştirmez ve acil
  durdurma değildir. Başka yazılımın verdiği hareketi durdurmaz.
- Kayıtlar ST3215_TEST/KAYITLAR altında yereldir. Kamera ve motor örnekleri
  eşzamanlı değildir; ayrı yaş/zaman bilgileri vardır. Eski telemetri işaretlenir.
- Mevcut tek-motor test uygulaması monte edilmiş kolun hareketi için kullanılmaz.

Fiziksel kamera, ID eşlemesi ve kalibrasyon: PHYSICAL VALIDATION REQUIRED.

## 20 Eylül kamera erişimi düzeltmesi
Windows Kamera uygulaması çalışırken FIGBOT çalışmıyorsa Windows Ayarlar →
Gizlilik ve güvenlik → Kamera → Masaüstü uygulamalarının kameranıza erişmesine
izin ver anahtarını kontrol et. Bu sistemde kapalıydı; kullanıcı açınca mevcut
DirectShow kamera 2 üzerinden Xiaomi 17 Pro görüntüsü FIGBOT'ta doğrulandı.
Kamera numaraları sistemdeki aygıtlara göre değişebilir.

Güncel uygulama Otomatik / Windows-MSMF / DirectShow seçeneklerini sunar;
Otomatik önce MSMF, sonra DirectShow dener. Bu bilgisayarda doğrulanan telefon
seçimi kamera 2 + DirectShow'dur. Görüntü alınmadan “kamera açık” sayılmaz.
Çözünürlük zorlanmaz; aygıtın verdiği görüntü kullanılır.

Başlatıcı `.venv-camera` ortamını kullanır. Genel proje ortamı değiştirilmedi.
Yeniden kurulum (proje kökünden):
```
.venv/Scripts/python.exe -m venv --system-site-packages .venv-camera
.venv-camera/Scripts/python.exe -m pip install --ignore-installed --no-deps opencv-python==4.14.0.94
.venv-camera/Scripts/python.exe -m pip install pyserial==3.5
```
Genel ortamdaki opencv-python-headless paketinde MSMF yoktu; kamera ortamında
standart paketle MSMF ve DirectShow kullanılabilir. Kamera izni ayrıca gereklidir.

## Kesintisiz elle ölçüm kaydı
Kamera ve altı motorun güncel okumaları açık, tüm tork kayıtları0 iken Elle kalibrasyon kaydını başlat seçilir. En fazla8dakika yerel camera.avi ve samples.jsonl kaydedilir. Her video karesinin motor verileri ve ayrı veri yaşları vardır; donanımsal eşzamanlı kayıt değildir. Sabit hızda oynatılan videonun gerçek zamanını JSONL elapsed_seconds alanından eşleyin. Kaydı bitir veya pencereyi kapat dosyaları sonlandırır. Kamera veya motor verileri2sn eskiyse, motor eksikse veya tork açıksa kayıt durur; bu özellik hiçbir motor komutu göndermez ve fiziksel fren değildir. Değişmeyen görüntü olası donma olarak işaretlenir; sabit sahne de bu uyarıyı üretebilir. Sıra1taban,2omuz,3dirsek,4bilek bükme,5bilek döndürme,6kıskaç. Uçları zorlamayın. Kayıt otomatik güvenli limit üretmez.
