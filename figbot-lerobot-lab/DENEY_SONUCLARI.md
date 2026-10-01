# İlk deney sonuçları — 29 Eylül 2026

## Sonuç

İki hazır SmolVLA modeli bu bilgisayardaki RTX 3050 Ti üzerinde gerçek çıkarım yaptı.
İlk çağrıdan sonra 50 hedeflik hareket bloğu yaklaşık **0,37–0,49 saniyede** üretildi.
PyTorch'un bu denemelerde ölçtüğü tepe ayrılmış CUDA belleği **1.209 MiB** civarındaydı.
Bu ölçüm tüm Windows/GPU bellek tüketimi değildir; eğitim belleği de değildir.

Bu sonuç modelleri denemek için bilgisayarın kullanılabildiğini gösterir.
Fiziksel robotta toplama, canlı kamera/enkoder eşleşmesi veya model başarısı doğrulanmadı.

## Ortam ve dosyalar

- Python 3.12.10; LeRobot 0.6.1; PyTorch 2.10.0+cu128.
- İki modelin tamamı `strict=True` ile yüklendi; eksik parametreye izin verilmedi.
- Model, backbone ve veri commit'leri `assets.lock.json`; paketler `uv.lock` içinde.
- Eski projenin 1.282 karelik / 131,75 saniyelik dört incir kaydı kopyalandı.
- Video kareleri ve zaman kayıtları eşleşti. Kamera/enkoder en büyük zaman farkı 151,93 ms.
- Kaynaktan kopyalanan 9 referans dosyasının ve 9 kayıt dosyasının SHA256 değerleri yeniden kontrol edildi.
- 29 otomatik test geçti; 93 kurulu paketin bağımlılık kontrolü geçti.
- Eğitim formatına dışa aktarım, yapay test verisiyle gerçek LeRobot yazma/okuma API'sinden geçirildi.
- Eğitim ayarı kurulu LeRobot yapılandırma sınıflarıyla ayrıştırıldı. Gerçek incir eğitimi başlatılmadı.
- Kamera/model yolu eski kaydın 300. karesinden alınan gerçek görüntüyle çalıştırıldı; 50 × 6 sonlu hedef üretildi. Eklem girdisi açıkça eğitim ortalamasıydı. Kanıt: `runs/20260929T071934_685900Z_camera_smoke/prediction.json`.

## Referans veride sayısal kontrol

Veri: `lerobot/svla_so101_pickplace`, kare 0, 120 ve 240.
Her gözlemde model durumu sıfırlandı; gerçek hedef eylemler model girdisine verilmedi.
Hedef bloğunun bölüm dışına taşan dolgu adımları hata hesabından çıkarıldı.

| Kare | Base ortalama mutlak hata | Görev modeli hata | Konumu koruma karşılaştırması |
|---|---:|---:|---:|
| 0 | 12,703 | 5,911 | 0,749 |
| 120 | 14,326 | 9,725 | 10,358 |
| 240 | 16,452 | 30,133 | 27,089 |

Birim veri setinin eklem/eylem birimidir; milimetre veya ham enkoder sayımı değildir.
Üç karelik bu sonuç bir başarı oranı oluşturmaz. Modeller bu örneklerde konumu koruma
karşılaştırmasını tutarlı olarak geçmiyor. Model seçimini yalnız bu tabloya göre yapmıyoruz.

İki kurulum da aynı görev/kamera dağılımından gelmiyor:

- Base denemesi referans veri setinin açıkça belirtilen normalizasyon istatistiklerini kullanıyor.
- Görev modeli kendi eğitim istatistiklerini kullanıyor; özgün üst/bilek kamera düzeni burada üst/yan görüntülerle eşleniyor.
- Görev modeline eğitiminde bulunan `Pick up a cube and place in the bin` talimatı verildi.
- Bu referans örneklerin ön eğitimde bulunup bulunmadığı bilinmiyor. Bağımsız genelleme testi değildir.

Kanıt dosyaları:

- `runs/20260929T071824_037213Z_reference_base/summary.json`
- `runs/20260929T071406_606888Z_reference_pickplace/summary.json`
- `runs/source_integrity.json`

## Yakalanan normalizasyon sorunu

Resmî base modelin sabitlenen sürümünde normalizasyon dosyaları eski
`so100*.buffer.action` anahtarlarını içeriyor. Güncel işleyicinin istediği
`observation.state.mean/std` ve `action.mean/std` alanları bulunmuyor.
İlk denemenin metrikleri bu yüzden `INVALIDATED.json` ile geçersiz işaretlendi.
Yeni kod eksik/yanlış boyutlu/sıfır standart sapmalı istatistikleri reddediyor.
Yukarıdaki base sonuçları açık referans istatistikleriyle yeniden alınmıştır.

## PC kamerasıyla sıradaki deneme

`KAMERA_TESTI.cmd`, kamera bağlandığında kısa video ve fotoğraf alıp görev modeline verir.
Kalibrasyon aracı pasif motor okuması yapabilir. Kamera/model bağlantısı için eklem girdisi modelin
eğitim ortalamasıdır ve raporda açıkça işaretlenir. Gerçek robotun pozisyonu sayılmaz.

Fiziksel hareketten önce eski motor sayımlarının hazır modelin eklem birimlerine eşlenmesi gerekir.
`configs/joint_mapping.template.json` bu nedenle boş ve `UNVERIFIED` durumundadır.
Eşleme tamamlandığında `local-test` ve `export-training` hazırdır.
Mevcut kamera kurulumuna uygun ek eğitim gerekip gerekmediği gerçek değerlendirmeyle belirlenecektir.

## Telefon bağlantısı — aynı gün

Kullanıcı telefon kamerasını seçti. Yüklü FIGBOT v37 uygulamasının `teaching_camera`
modu USB/ADB üzerinden yeni projeye bağlandı; eski proje dosyaları ve APK değiştirilmedi.
`TELEFON_KAMERA_TESTI.cmd` bu bağlantıyı tekrar kurar; geçici ADB yönlendirmesini sonunda kaldırır.

5 saniyede 48 farklı 640×480 kare alındı. Ölçülen en büyük kare yaşı 97,91 ms,
en büyük USB istek/yanıt süresi 32 ms idi. Görüntüde dört incir ve kolun bir bölümü var;
bırakma alanının kadrajı henüz net değil. Motor bağlantısı kurulmadı.

Kanıt: `runs/20260929T073219_349233Z_phone_camera/capture.json` ve aynı klasördeki JPEG kareler.
Telefon aktarımıyla ilgili 6 yeni test dahil toplam 35 test geçti.
