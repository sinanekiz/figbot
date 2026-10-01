# 30 Eylül 2026 kod incelemesi

LeRobot deneme alanının 12 kaynak modülü ve üç test dosyası incelendi.
Yapısal aramalar `figbot-lerobot-lab` grafiğiyle yapıldı; kullanılan dosyaların
indeks kapsamı kontrol edildi ve kaynakları doğrudan okundu.

## Düzeltilen bulgular

| Bulgu | Sonuç ve düzeltme |
|---|---|
| Kamera/model testinde sepet komutu sabitti | Güncel görev `configs/current_scene.json` içinden okunuyor. Kullanıcı beyaz kâğıdı seçmişti. CLI'da `--task` ile açık deneme komutu da verilebilir. |
| Eski kayıtlar sepet komutuyla yeniden etiketleniyordu | Yerel çıkarım ve eğitim dışa aktarımı artık kaydın özgün `episode/session.json` görevini kullanıyor. Görev eksikse işlem reddediliyor. |
| Fotoğraf boyunca motor okuması duruyordu | Kamera görüntüleri alınırken ek motor örnekleri kaydediliyor. Fotoğraf sırasında oynayıp başlangıca dönen kol da sabit poz kontrolünden geçemiyor. Her görüntü için örnek eşleşmesi ve zaman belirsizliği raporlanıyor; üst sınır 200 ms. |
| Görüntü yaşı USB gecikmesini içermiyordu | Bildirilen görüntü yaşına USB gidiş dönüş süresi eklenerek PC tarafında 300 ms üst sınırı uygulanıyor. Eksik metadata ve geçersiz odak değerleri açıklayıcı hatayla reddediliyor. |
| ADB temizlik hatası asıl ölçüm hatasını örtebiliyordu | Başarısız kaydın kanıtı ve temizlik hatası ayrı kaydediliyor. Asıl motor/kamera hatası korunuyor. Kesilen kalibrasyonun kanıtı da saklanıyor. |
| Model indirme hash'leri yüklemede kontrol edilmiyordu | Policy ve yerel backbone dosyaları GPU yüklemesinden önce kilitli SHA256 değerleriyle doğrulanıyor. İşleyici istatistiklerinin checkpoint klasörü dışına çıkması reddediliyor. Referans veri de kilidiyle doğrulanıyor. |
| Hatalı kayıt değerleri bazı zaman kontrollerini geçebiliyordu | Ters veya 250 ms'den uzun motor okuma aralıkları, 0..4095 dışı ham konumlar ve 2048'den büyük ardışık enkoder sıçramaları reddediliyor. Tek karelik audit artık boş fark dizisinde hata vermiyor. |
| Çakışan çevrimler eğitim/doğrulama ayrımını bozabiliyordu | Çevrimlerin sonlu, sıralı ve çakışmayan olması gerekiyor. Kaynak video/örnek/zaman hash'lerinin bulunması ve dışlanan aralıkların geçerli olması da denetleniyor. |

## Doğrulama

- Tüm testler: **72 geçti**, 13,24 saniye. Donanım hata senaryoları sentetik
  bağlantılarla denendi; motor hareketi yaptırılmadı.
- `uv pip check`: 94 paket uyumlu.
- Mevcut kayıt: 1.282 kare, 131,75 saniye; kamera/enkoder en büyük ayrılık
  151,93 ms, en büyük enkoder zaman boşluğu 172 ms. Yeni kayıt kontrolleri geçti.
- Gerçek CUDA çıkarımı: 29 Eylül'den kayıtlı görüntü ve checkpoint eğitim
  ortalamasıyla beyaz kâğıt komutu çalıştı. Çıkarım 1,628 saniye,
  en yüksek ayrılmış GPU belleği yaklaşık 1.202 MiB.
  Kanıt: `runs/20260930T064904_015138Z_camera_smoke/prediction.json`.
- Eski projeden referans alınan dokuz dosya ve motor protokolü, başlangıç
  SHA256 değerleriyle hâlâ aynı.

## Açık fiziksel işler

`configs/joint_mapping.template.json` hâlâ UNVERIFIED. Orta konum, eklem
yönleri/aralıkları, sayaç sarması ve beyaz kâğıt üzerindeki bırakma konumu
fiziksel olarak kaydedilip incelenmelidir. Yeni donanım ölçümlerinin eski
kayıtlardaki motor koordinatlarıyla uyumu da doğrulanmalıdır; yalnızca aynı
motor ID'lerinin bulunması yeterli değildir.

Kalibrasyon aracı pasif ölçüm yapar. Normalizasyon eşlemesi, model çıktısını
ham motor hedefine dönüştürme, sınırlandırılmış hareket ve canlı geri bildirim
denetimi henüz toplama akışına bağlanmamıştır. Tek bir bırakma pozu,
çarpışmasız taşıma yolu veya başarılı kavrama kanıtı oluşturmaz.
Model testi gerçek kol konumunu kullanmadığı için robot sürüşüne uygun değildir.
