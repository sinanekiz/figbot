# PC üzerinden toplama — APK ana ekranında 03

Telefon ve motor kartı PC’ye iki ayrı USB veri kablosuyla bağlanır. Motor kartının
mevcut 12 V beslemesi ayrıca bağlı kalır. Telefon kamerası, algılama, hedef hesabı,
kalibrasyon ve toplama kontrolü telefonda çalışır; PC seri bağlantıyı aktarır.
01 doğrudan telefon/OTG ve 02 eski Arduino/Bluetooth seçenekleri korunur.

## Bağlantı

1. PC’de motor kartını kullanan diğer FIGBOT panellerini kapat. Aynı COM portunu
   iki uygulama birlikte kullanamaz.
2. Telefonu USB ile PC’ye bağla; telefondaki USB hata ayıklama iznini kabul et.
3. Motor kartını ikinci USB veri kablosuyla PC’ye bağla.
4. `GUNCEL/YAZILIM/PC_Uzerinden_Toplama.cmd` dosyasını aç ve açık bırak.
   Tek USB seri kart varsa COM otomatik seçilir. Birden fazlaysa komut satırında
   `PC_Uzerinden_Toplama.cmd --port COM5` kullan; COM5 yerine kartının portunu yaz.
   Başlatıcı ADB USB tünelini kendisi kurar. ADB ve proje Python ortamı gereklidir.
5. Telefonda FIGBOT → **03 PC üzerinden toplama** → **PC’ye bağlan**.
   Altı motor okundu mesajını bekle. Bu bağlantı kendiliğinden hareket başlatmaz.

## İlk kurulum

Telefonu kol, incirler ve sepeti görecek şekilde sabitle. **Kol ayarları** ekranı
eksik kayıtları listeler. İlk iki moddaki ölçüm kapıları burada da geçerlidir:

- Kapalı başlangıç ve sepet bırakma duruşları, kıskaç açık ve kavrama konumları
  kaydedilir. Elle konumlandırmak gerekiyorsa kol desteklenir, ekrandan serbest
  bırakılır; aynı yerde tutmayı açarken destek korunur. Hareketli duruş kaydedilmez.
- Robotun mekanik taban koordinatında kıskaç ucunun üç farklı XYZ ölçümü modele
  karşı kontrol edilir. Birbirinden uzak ve aynı çizgide olmayan noktalar kullanılır.
- Kamera için ölçülmüş dört referans noktası ve bunlardan farklı üç kontrol noktası
  eklenir: XYZ milimetre girilir, sonra görüntüde aynı noktaya dokunulur.
- Üç zemin noktası; incir/kavrama yüksekliği, kavrama eğimi, kıskaç yakınlık payı
  ve sepetin merkezi, iç yarıçapı, taban/üst kenar yüksekliği girilir.

Sadece kol tabanına tek dokunuş yönü, ölçeği, yüksekliği ve mekanik eksenleri
doğrulamaz. Eski orijin/+X düğmeleri gösterim içindir; ölçülmüş robot eşlemesinin
yerine geçmez. Yanlış model ölçümünde rastgele değer girilmez; referans kalibrasyonu
düzeltilmelidir. AR kamera oturumu değişirse kamera eşlemesi yeniden yapılır.

## Toplama

1. Kol ayarlarında eksik kalmayınca mevcut motor tutmasını devral veya destekli
   duruşta tutmayı aç. Ardından elini kolun yolundan çek.
2. **Önizle** hesaplanan hedefi ve tahmini süreyi gösterir; kolu sürmez.
3. **3 incir topla** görülen ve doğrulanan hedeflerden en çok üç deneme başlatır.
   Her hedef için incire gider, kavrar, kayıtlı sepete taşır ve bırakır; iş sonunda
   kayıtlı başlangıca döner. Yeni hedefe gidiş arasında başlangıca dönmez.
4. **Durdur** çevrimi iptal edip mevcut duruşta tutmayı ister. Ekrandan ayrılma veya
   kamera kaybı da yeni hareketleri durdurur. Başarı sayacı motor hareketinden değil,
   görsel kanıttan hesaplanır; belirsiz kavrama başarılı sayılmaz.

PC bağlantısı koparsa köprü, komut gönderilmiş oturumda yeni ölçülen konumlarda
tutmayı dener ve sonucu PC penceresine yazar. Otomatik tork kesmez veya eski yolu
devam ettirmez. USB motor bağlantısı da yoksa durma doğrulanamaz. Yeni bağlantı
için PC başlatıcısını ve kamera ekranını yeniden aç. Telefon/kol/sepet yerleşimi
değişmişse önce yeniden ölçüm yap.

Bu sürümde tam engel/hacim çarpışma modeli yoktur. İlk gerçek PC çevrimi ve
telefon üzerinden hız ölçümü PHYSICAL VALIDATION REQUIRED; yazılım testleri
dünkü fiziksel hareketin aynı hızda tekrarlanacağını kanıtlamaz.
