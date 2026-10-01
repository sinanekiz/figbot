# Gösterim kamerası ve pasif kayıt — v0.36 / 29 Eylül 2026

Telefon, `teaching_camera=true` ile açıldığında yalnız localhost:8874 üzerinden
ham RGB JPEG kareleri, kamera yakalama zamanı, oturum kimliği ve iç parametreleri
verir. Kola ait etiket görünmese de kayıt çalışır. Kamera modu motor bağlantısını
başlatamaz. Normal otomatik toplama modunun eşleme kapıları değiştirilmedi.

PC `phone_teaching.py`, aynı seri portun tek sahibi olarak altı eklemi ve kıskaç
konumunu kamera ile birlikte kaydeder. Yalnız kullanıcı kolu desteklediğini
bildirdikten sonra `--supported-release` ile tork kapatılır; ardından yalnız okuma
vardır. Bitişte otomatik tork açılmaz. İletişim kesilmesi serbest kolu taşımaz.
Kayıt başlamadan kameradan en az üç ayrı taze görüntü doğrulanır.

Varsayılan kayıt ve ön kontrol modunda protokol katmanı yalnız 1–6 numaralı
motorlara READ isteğine izin verir; yazma ve yayın paketleri seri hatta çıkmadan
reddedilir. Kamera zamanlama sınırı aşılırsa kayıt kesilir; kesilen hazırlık
kaydı başarılı gösterim olarak etiketlenmez.

Kamera ve kol tabanı sabit kalmalı. Görüntüdeki incir konumu ile kayıtlı eklem
hareketi daha sonra eşlenecek; kolun görüntüde olması zorunlu tutulmaz. Kamera
yalnız incirleri görürse kavrama/kaldırma başarısı için kullanıcı etiketi gerekir.
Her incir ayrı bölüm olarak tercih edilir. İlk örnekler kayıt kalitesini ve gerçek
kavrama yolunu doğrular; tek bir gösterim tüm erişim alanına genelleme sağlamaz.

Kayıt `episode/camera.avi`, `episode/samples.jsonl`, `timing.jsonl`, ilk/son görüntü
ve `status.json` dosyalarını üretir. Kameranın gerçek zaman damgası saklanır;
PC karşılığı aktarım gidiş-geliş süresinden yaklaşık çıkarılır, belirsizlik ayrıca
kaydedilir. Kamera/enkoder farkı200ms üzerindeyse kayıt durur.10Hz hedef hızdır;
gerçek hız ve boşluklar ölçülür. Bu bir LeRobot veri seti veya eğitilmiş politika
olarak sunulmaz; pasif örneklerden eylem çıkarımı ayrıca doğrulanmalıdır.

SO-101 resmi kaynak bağlantısı LeRobot'u önerir. LeRobot'un örnek yaklaşımı:
kamera + eklem durumu + gösterilen hareketleri kaydet → modeli eğit → ayrı test.
Kaynaklar: https://github.com/TheRobotStudio/SO-ARM100 ve
https://huggingface.co/docs/lerobot/il_robots . Bu çalışmada veri buluta yüklenmez.

## Dört incir, düzeltilmiş hedefler ve yerel eğitim — 29 Eylül 2026

Kullanıcı kuralı: **hedefe gitmeden önce kıskaç açılır, yaklaşırken açıklık sabit
kalır; hedefte kavranır, sepette durularak bırakılır.** Ani düşme, sapma ve
gereksiz el hareketleri başarılı toplama etiketi nedeniyle doğru hareket sayılmaz.

`DEMO_20260929T022613Z` kaydı 1282 kare / 131,75 saniyedir. Kullanıcı dört incirin
taşındığını doğruladı. İlk/son beklemeler çıkarılan toplama bölümü yaklaşık75s.
Ham kayıt korunur. Önceki dört tek-incir kaydı, geç açılma incelemesi tamamlanana
kadar yeni modelde kullanılmaz. `training_annotations.json` video/enkoderden
yaklaşık aşama sınırlarını içerir. 1559 enkoder sayımı kayıtta gözlenen açık
konumdur; ortak sentetik hedef olarak kullanıldı, milimetre açıklık veya güç
altında doğrulanmış ayar değildir. Tutma açıklığı her incirin kaydından alınır.

`corrected_training/` altında ham/düzeltilmiş hedef karşılaştırması ve660 temiz
eğitim örneği bulunur. Büyük hareketlerin şüpheli aralıkları ve kamera zaman
boşlukları, geçmiş/gelecek pencereleriyle birlikte dışlanır. Küçük eklem titreşimi
yalnız3 sayımlık sınır içinde azaltılır. Belirsiz düşmelerin doğru fiziksel yolu
bulunmuş kabul edilmez. Video pikselleri ve gözlenen eklem girdileri değiştirilmez.

`trained_policy/`: küçük CNN ve üç eklem gözleminden +0,2/+0,4/+0,6s düzeltilmiş
hedefler üreten ilk yerel model. Son incir tümüyle ayrıldı:497 eğitim /163 kontrol
örneği. Kontrol hatası69,25 sayım; mevcut konumu koruyan karşılaştırma40,77 sayım.
**Model bu kontrolü geçmedi; otomatik sürüşe uygun değildir.** Tüm660 örnekle ayrıca
60 dönem eğitilen ağırlıklar32,11 sayım eğitim hatası verdi; bu genelleme kanıtı
değildir. Modelin rota adaylarını oluşturduğu iddia edilmez; rotalar ayrı hesaplanır.

`corrected_route_candidates/`: incire varış/sepet varış noktalarını koruyan,
şüpheli iç bölümleri çıkaran ve bu boşluklara incelenecek bağlantılar öneren
eklem rotaları. Kıskaç açma/kavrama/bırakma sırasında kol sabit; yaklaşırken ortak
açıklık sabit. PCHIP geçişleri ve hız/ivme zamanlaması sayısal olarak kontrol edilir.

| Önerilen hız sınırı (sayım/sn) | Hesaplanan dört-incir süresi |
| --- | --- |
| 300 | 132,88 sn |
| 600 | 77,09 sn |
| 900 | 60,30 sn |

Bu sınırlar çevrimdışı aday parametreleridir; motora uygulanmış veya fiziksel
olarak doğrulanmış değildir. 900 adayındaki yaklaşık%20 süre azalması hesap
sonucudur. Çarpışma, zemin açıklığı ve yük altında kavrama doğrulanmadı.

Kaynak komutlar proje kökünde çalıştırılır; `--output` için yeni bir boş yol verilir:

```powershell
.venv-imitation/Scripts/python.exe -m ai.training.handguided_data --episode <kayit> --annotations <kayit>/training_annotations.json --output <yeni-veri-yolu>
.venv-imitation/Scripts/python.exe -m ai.training.train_handguided_policy --dataset <yeni-veri-yolu>/dataset.npz --output <yeni-model-yolu> --epochs 60
.venv-imitation/Scripts/python.exe -m ai.training.handguided_routes --episode <kayit> --blend --reviewed
```

Bağımlılıklar `ai/training/requirements-handguided.txt` içinde sabitlenmiştir.
CPU torch önce `pip install torch==2.14.0+cpu --index-url https://download.pytorch.org/whl/cpu`
ile kurulur; sonra kalan gereksinimler aynı sanal ortama kurulur. Yayınlanan araçlar
`IMITATION_TOOLS/` altındadır. Bu araçların seri port veya motor sürüş bağlantısı yoktur.

## İlk düşük hızlı boş deneme sonucu
Kullanıcının alanı boşaltmasından sonra kıskaç önce açıldı ve ilk incirin kayıtlı
konumuna8 ara noktadan23,0s içinde gidildi. Son eklem hatası en fazla3sayım;
kıskaç ölçümü yol boyunca1556sayım. Kullanıcı masaya temas/sürtme olmadığını doğruladı.
Sepete geçişin kaldırma kısmı durdu:omuz(ID2)2405 hedefinde2428 konumunda sabit
kaldı.23sayım fark, mevcut20sayım yerleşme sınırını aştı. Sınır gevşetilmedi;
sepet yolu tamamlanmadı. Kol mevcut konumunu tutuyor. Bu sonuç ilk yaklaşmayı
doğrular; kavrama, sepet varışı veya tüm çevrimin başarısını doğrulamaz.

### Omuz düzeltmesi ve boş rotanın devamı
Kullanıcının düzeltme isteğiyle omuz için sınırlı konum tamamlama eklendi:
`settling.py`. Yalnız durmuş ve tutması doğrulanmış ID2 üzerinde, en fazla üç
12sayım düzeltmesi yapılır. Kamera, diğer eklemler ve geri bildirim sınırları
izlenir. Kalıcı motor ayarı değişmez; fiziksel hedefin20sayım kabul sınırı korunur.
Gerçek testte2405 hedefine karşı2428 ölçümü, küçük hedef düzeltmeleriyle2404'e;
son konum tutmasında2409'a geldi (4sayım hata).

Ardından boş sepet rotasının kalanı11,85s içinde tamamlandı; son eklem hatası en
fazla12sayım, kıskaç açık ve kol duruyor. Bu, kayıtlı bırakma duruşuna boş varışı
doğrular. Yüklü kavrama/taşıma ve sepet içine bırakma henüz test edilmedi.

### İlk gerçek incir denemesi
Sonraki denemede açık yaklaşma ve kapatma yapıldı; kullanıcı incirin kısa
kaldırmada tutulduğunu doğruladı. Taşıma sırasında incir masaya ayrıldı; sepet
teslimi başarısız. Kıskaç ölçümü taşıma boyunca947sayım kaldı, açma komutu yoktu.
Motorların kayıtlı sepet konumuna varması, incirin taşındığı anlamına gelmez.
Kapatma yardımcı kodu `supervised_grasp.py`; ham akım artışı sadece deneysel
durdurma işaretidir, kuvvet ölçümü değildir. Sonraki deneme için kapatma adım
sayısı düzeltildi; kısa kaldırma, yüksek kaldırma ve dönüş ayrı aşamalara bölündü.
Bu değişikliğin daha iyi kavrama sağlayacağı henüz fiziksel olarak doğrulanmadı.

### İkinci deneme: tek incir sepete bırakıldı
Kullanıcı inciri açık parmakların yaklaşma alanına yeniden yerleştirdi. Düzeltilmiş
kapatma935 hedefinde939 ölçümüne ulaştı. Yüksek kaldırmada kullanıcı sağlam tutuşu
doğruladı; ilk dönüşte incir kamerada kıskaçta görüldü. Kıskaç939 korunarak daha
yavaş dönüş ve sepet rotası tamamlandı. Yalnız sepet konumuna varınca açıldı;
kullanıcı incirin sepetin içinde olduğunu doğruladı. Kol açık kıskaçla duruyor.

Bu, sabit düzende elle hizalanmış tek incirin gözetimli başarı kaydıdır. Farklı
konumları kendiliğinden bulma, dört inciri ardışık toplama ve yüksek hız henüz
doğrulanmadı. Sepet kamera dışında; son sonuç kullanıcı gözlemine dayanır.
Konum, kapanma ve hız birlikte değiştiği için başarı tek bir düzeltmeye atfedilemez.
25 ilgili test geçti; başarısız ilk deneme de kanıt olarak korundu.

### Daha hızlı dört-incir denemesi: tamamlanmadı
Kullanıcının isteğiyle açıklık1559'dan1283'e indirildi; bu milimetre cinsinden
yarım açıklık ölçümü değildir. Boş yaklaşma240, yüklü taşıma180 sayım/sn istek
parametresiyle,250 profil üst sınırında denendi. Kavrama60, yakın yaklaşma90
korundu. İlk incir kamerada taşındı ve sepet konumunda dar açma yapıldı; bu
denemenin sepet içi sonucu henüz kullanıcı tarafından doğrulanmadı.

İkinci incir kapatmada ileri kayıp masada kaldı. Üçüncü hedefte kıskaç incirin
önünde kaldığı için kapatma yapılmadı. Dördüncü hedef denenmedi. Üç incir masada;
dört hedeflik dosyalar otonom toplama yeteneği olarak kullanılmamalıdır.

İki kamera gecikmesinden sonra v0.37 telefona kuruldu: öğretim modunda yalnız
ham aktarım çalışır, ArUco/YOLO kuyruğu kullanılmaz. Zaman sınırları değişmedi.
80 ayrı kare kesintisiz alındı; son40 karede yaş en çok95ms. Kamera düzeltmesi,
yanlış kavrama merkezini kendiliğinden düzeltmez. Kanıt:reports/four_fig_pick.

