# Fiziksel kalibrasyon ölçümleri

29 Eylül 2026: COM5 üzerindeki altı motor okundu. Tork kapalı, motorlar sabit.
Başlangıç kanıtı: `runs/20260929T082136_402956Z_calibration_baseline/measurement.json`.
Motorların 0..39 adreslerindeki ayarları dosyada saklandı; donanıma ayar yazılmadı.
Motor kayıtlarındaki 0..4095 sınırları robotun mekanik hareket sınırlarını kanıtlamaz.

## Sıra

1. Kullanıcı kolu destekleyerek rahat orta konuma getirir. Taban ve kamera sabit kalır.
2. `calibration-capture --kind neutral --camera` ile sabit konum kaydedilir.
3. Kullanıcıyla eklem hareketleri ayrı ayrı gözlenir. Bilinçli kalibrasyon
   hareketleri `--kind range --seconds 30` ile kaydedilebilir. Direnç zorlanmaz.
   Gözlenen uç değerler otomatik olarak mekanik sınır veya VERIFIED eşleme olmaz.
4. Eklem yönleri, sayaç sarması ve normalizasyon gözden geçirilir. LeRobot 0.6.1
   `so_follower.calibrate` orta konumda donanım ofsetlerini değiştirir; bu araç
   mevcut projenin ayarlarını korumak için bu işlemi otomatik yapmaz.
   Gerekirse yazılımda koordinat dönüşümü ayrıca uygulanıp doğrulanacaktır.
5. Kullanıcı boş kıskacı beyaz kâğıt üzerinde uygun bırakma yüksekliğinde tutar;
   `--kind drop --camera` ile hedef konum kaydedilir. Tek hedef ölçümü,
   oraya giden çarpışmasız bir hareket yolu oluşturmaz.

## Komutlar

Lab klasöründe:

```powershell
.\.venv\Scripts\python.exe -m figbot_lab.cli calibration-capture --kind baseline --camera
.\.venv\Scripts\python.exe -m figbot_lab.cli calibration-capture --kind neutral --camera
.\.venv\Scripts\python.exe -m figbot_lab.cli calibration-capture --kind range --seconds 30
.\.venv\Scripts\python.exe -m figbot_lab.cli calibration-capture --kind drop --camera
```

Ölçüm boyunca tork açık ise işlem reddedilir. Araç tork açmaz/kapatmaz,
motor hedefi veya EEPROM ayarı yazmaz. İletişim hataları, değişen ayarlar,
sabit pozda hareket ve enkoder sarması başarısız ölçüm olarak kaydedilir.
Kamera seçilmişse görüntüler alınırken motorlar tekrar tekrar okunur. Kayıtta
her görüntü için seçilen enkoder örneği ve en büyük zaman ayrılığı saklanır;
bu ayrılık 200 ms'yi aşarsa ölçüm reddedilir. Fotoğraf sırasındaki örneklerde
konum değişikliği bulunursa, kol sonradan başlangıç konumuna dönse bile ölçüm
reddedilir. Görüntü yaşı için USB aktarım süresi de hesaba katılır.
Fiziksel inceleme tamamlanana kadar `joint_mapping.template.json` UNVERIFIED kalır.
