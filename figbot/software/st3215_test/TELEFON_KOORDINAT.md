# Telefon koordinat bağlantısı

Bu alıcı yalnız ARCore hedef gözlemlerini kaydeder; seri porta erişmez ve motor sürmez.

1. `Telefon_Koordinat_Alici.cmd` dosyasını çalıştır.
2. USB hata ayıklama bağlantısı hazırken `adb reverse tcp:8872 tcp:8872` çalıştır.
3. Telefonda FIGBOT kamera ekranındaki HTTP adresini `http://127.0.0.1:8872/api/targets` yap.
4. Android v0.12'de **Canlı aktarımı başlat** düğmesine bas. Ekran açıkken yaklaşık 500 ms aralıkla gözlem gönderilir; bir istek sürüyorsa yenileri kuyrukta birikmez. FIGBOT'a Gönder tek gönderimdir. Uygulama arka plana geçince aktarım durur. Kamera ekranı açıkken ekran uykuya geçmez.
5. PC durumu: http://127.0.0.1:8872/api/status . Kayıtlar bu klasörün KAYITLAR dizinindedir.

V2 paketinde görüntünün çekim zamanı, kamera pozu, izleme durumu ve derinlik güven haritası yoktur.
Alınma zamanı, çekim zamanı değildir. `phone_latest.json` otomatik hareket girdisi olarak kullanılmaz.
Paket sıra numarası nesnenin kalıcı takip kimliği değildir.

2026-09-20 cihaz testi: Xiaomi 17 Pro, ARCore 1.56 kurulu; dışa aktarılan gerçek pakette
depth_api_supported=true, depth_source=ARCORE_DEPTH_HIT, incir güveni0.8897;
XYZ=(267.546,-2.852,-69.046)mm. Önceki ekran Z=+11mm gösterdi. Kullanıcı orijini
taban motorunun üst tarafında seçtiğini bildirdi; bu referansla aşağıdaki incirin
Z değerinin negatif olması tek başına hata değildir. İki kayıt arasında aynı
kalibrasyonun korunup korunmadığı ve tam seçilen nokta UNVERIFIED.
Taban işaretinin gerçek mekanik orijine uyumu ve robot eklem dönüşümü doğrulanmadı.

V0.12 / V3 paketi görüntü ve derinlik karesi zamanlarını ayrı gönderir. Algılama
ile derinlik tam eşzamanlı değildir: STATIONARY_SCENE_APPROXIMATION. Telefonun
poz farkı 3 mm / 0,5 dereceyi veya görüntü yaşı 750 ms'yi aşarsa XYZ gönderilmez.
Bunlar geçici yazılım eleme eşikleridir; fiziksel doğruluk garantisi değildir.
Nesnenin sabit durması gerekir; nesne hareketi henüz izlenmez. Kamera takibi
kaybolduğunda ve uygulama durakladığında gözlemler temizlenir. Ağ gecikmesi
bilinmediğinden PC'nin capture_age_lower_bound_ms değeri yalnız alt sınırdır.
Güven haritası ve tam eşzamanlı derinlik eşleştirmesi henüz uygulanmadı.

Paket ayrıca oturum kimliği, kalibrasyon revizyonu, AR dünyasındaki orijin/+X,
yatay referans uzunluğu ve kamera pozunu içerir. AR oturumu/kurulum değişince
orijin ve +X yeniden seçilir; dünya koordinatları oturumlar arasında taşınmaz.
Bir paketteki track_id yalnız o karedeki sıradır, kalıcı nesne kimliği değildir.
base_link etiketi kullanıcı referansını adlandırır; vendor URDF dönüşümü değildir.

Kullanıcı X211,1 / Y-130,2 / Z-53,2 mm noktasını doğru olarak onayladı. Bu tek
nokta onayı kaydedildi; tüm çalışma alanı veya eklem sıfırları doğrulanmış sayılmaz.
Sonraki adım: kullanıcı referansı ile SO-101 mekanik referansı arasındaki dönüşüm,
eklem sıfırları ve ters kinematik. Bu alıcı otomatik sürüş başlatmaz.
