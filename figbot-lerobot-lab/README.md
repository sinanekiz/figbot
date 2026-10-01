# FIGBOT — hazır model deneme alanı

Bu klasör, mevcut FIGBOT projesini değiştirmeden LeRobot/SmolVLA denemek için oluşturuldu.
İki hazır model, örnek veri, ayrı Python ortamı ve test komutları bu klasördedir.

Güncel hedef: model incire yaklaşmayı ve kavramayı öğrenir. Kavrama doğrulanınca
sabit arka kasaya taşıma ve bırakma ayrı bir hareket denetleyicisiyle yapılacaktır.
Bu akışın tasarımı `configs/task_plan.json` içindedir; canlı motor akışı henüz bağlı değildir.

## Hızlı başlangıç

- **SANAL_SURUCU.cmd**: Fareyle kullanılan 3 boyutlu SO101 sürücü. Sol sürükleme kolun ucunu eklemleri birlikte hesaplayarak taşır; tekerlek kıskacı, sağ sürükleme görünümü ayarlar. Shift + sol sürükleme derinliği değiştirir. Gerçek motor pozları okunabilir; fiziksel eşleme tamamlanmadan sürüş kilitlidir. [Kullanım](SANAL_SURUCU.md).
- **TELEFON_KAMERA_TESTI.cmd**: Mevcut FIGBOT v37 uygulamasını kamera modunda açar; USB üzerinden telefondan görüntü alıp model bağlantısını test eder. Telefonun kilidi açık ve USB hata ayıklama izni verilmiş olmalı. Geçici USB bağlantısı test sonunda kaldırılır; ek uygulama gerekmez.
- **DURUM.cmd**: Python, CUDA ve indirilen modelleri gösterir.
- **MODEL_TESTI.cmd**: İki modelde kayıtlı Hugging Face örnekleriyle çıkarım yapar.
- **KAMERA_TESTI.cmd**: PC'ye bağlanan kameradan 5 saniye kayıt alır, son görüntüyü modele verir.
  Fotoğraflar ve sonuçlar `runs/` altındadır. Bu kamera testinde gerçek motor verisi bulunmadığından
  eğitim ortalaması kullanılır. Sonuç, görüntü bağlantısı/gecikme testidir.
  Bu komut normalizasyon bilgileri tam olan `pickplace` modelini kullanır.

Kamera seçmek için PowerShell'de:

```powershell
.\KAMERA_TESTI.cmd --index 1
```

DirectShow kamerayı açamazsa `--backend msmf` veya `--backend auto` kullanılabilir.
Kalibrasyon aracı motor konumlarını ve ayarlarını okuyabilir. Modelin hareket hedefleri JSON dosyasına yazılır; motor sürüşü henüz uygulanmamıştır.

## Yapılanlar

- Ayrı `.venv` içinde LeRobot 0.6.1, SmolVLA, PyTorch CUDA ve veri/eğitim araçları kuruldu.
- Resmî `lerobot/smolvla_base` ve `Harrysunshine/so101-smolvla-9task` indirildi.
- Model, tokenizer ve örnek veri sürümleri `assets.lock.json`; paketler `uv.lock` ile sabitlendi.
- Tam ağırlıklar eksik parametreye izin vermeyen yükleme ile gerçekten çalıştırıldı.
- Eski dört incir gösterimi `data/figbot/DEMO_20260929T022613Z` içine doğrulanarak kopyalandı.
- Zaman ve video bütünlüğü, birim eşlemesi, eğitim bölme ve kamera dosyaları için testler eklendi.
- Sayısal sonuçlar ve sınırlar **DENEY_SONUCLARI.md** dosyasında açıklanır.

## Klasörler

| Konum | İçerik |
|---|---|
| `src/figbot_lab` | Yeni deneme kodu |
| `models/base`, `models/pickplace` | İndirilen hazır model ağırlıkları |
| `models/backbone` | Yerel mimari, tokenizer ve görüntü işleyici dosyaları |
| `data/reference` | Hugging Face toplama örnekleri |
| `data/figbot` | Eski kayıtların SHA256 ile doğrulanmış kopyaları |
| `configs/joint_mapping.template.json` | Doldurulması gereken fiziksel eklem eşlemesi |
| `runs` | Model çıktıları, fotoğraflar, test raporları |
| `references` | Kaynak projeden alınan referans belgeleri ve köken bilgisi |

## Mevcut kayıtla çıkarım

Eski kayıtlar ham enkoder sayımları içerir. Model girdisinin eklem sırası, yönü, sıfırı ve ölçeği
doğrulanmalıdır. Kayıttaki minimum/maksimum sayımlar kalibrasyon sınırı değildir.

`joint_mapping.template.json` dosyasını yeni adla kopyalayıp **doğrulanmış kalibrasyona göre** doldurmak gerekir.
Kod yalnız `VERIFIED` durumu ve kanıt açıklaması bulunan, altı eklemi doğru sıralayan eşlemeyi kabul eder.
Eşleme testleri ölçümün fiziksel doğruluğunu tek başına kanıtlamaz. Bu aşama henüz tamamlanmadı.

```powershell
.venv/Scripts/python.exe -m figbot_lab.cli local-test `
  --episode data/figbot/DEMO_20260929T022613Z `
  --mapping configs/joint_mapping.verified.json --frame 300
```

Tek kamera, yayımlanan görev modelindeki üst/bilek kamera düzeninden farklıdır.
Bu komut bir aktarım denemesidir; nesnenin gerçekten alındığını ölçmez.

## Hazır modelden uyarlama

Kopyalanan eski `corrected_training` verisinin gözden geçirilmiş hedefleri tekrar kullanılabilir.
Kaynak hash'leri denetlenir; şüpheli zaman aralıkları dışlanır; kamera ve eklem zamanları eşleştirilir.
Son incirin bütün çevrimi ayrı doğrulama veri setine ayrılır. Eğitim verisi aynı sahneden geldiği için
sonuç yeni kamera veya yeni nesne konumlarında genelleme garantisi değildir.

Kalibrasyon eşlemesi doğrulandığında:

```powershell
.venv/Scripts/python.exe -m figbot_lab.cli export-training `
  --episode data/figbot/DEMO_20260929T022613Z `
  --mapping configs/joint_mapping.verified.json --name figbot_figs
.venv/Scripts/python.exe -m figbot_lab.cli training-command `
  --dataset data/exported/figbot_figs --model base
```

İkinci komut yerel uyarlama ayarını ve çalıştırılacak komutu üretir. Kendisi eğitimi başlatmaz.
Hazır ağırlıklarla başlar; buluta veri yüklemez. İlk ayar batch=1 ve 1.000 adımlık denemedir.
Bu sayı yeterli eğitim iddiası değildir. 4 GB GPU üzerinde eğitim henüz ölçülmedi.
Doğrulama veri seti eğitim ve eğitim istatistiklerine dahil edilmez.

## Kurulum ve test

Mevcut ortam hazırdır. Yeniden kurmak gerektiğinde:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup.ps1
.venv/Scripts/python.exe -m pytest -q
```

İlk kurulum birkaç GB indirir. Çalışan deneyler yerel model yollarını kullanır.
`download` komutu ilk görülen Hub commit'ini kilitler; sonraki çalıştırmalar aynı sürümü getirir.
Modelin kendi işleyici/normalizasyon dosyaları ağırlıklarla birlikte tutulmalıdır.

İndirilen resmî temel modelin normalizasyon dosyalarında eski `so100*.buffer.action`
anahtarları bulundu; güncel işleyicinin beklediği `observation.state.mean/std` ve
`action.mean/std` alanları yok. Kod bu durumu kontrol eder. `reference-test --model base`
bu yüzden **referans veri setinin istatistiklerini açıkça kullanır** ve kaynağını rapora yazar.
Bu, yeni veri setine uyarlama için bir başlangıç denemesidir; özgün eğitim ölçeğini yeniden
bulduğumuz veya bağımsız test yaptığımız anlamına gelmez. Temel modelle yerel görev eğitimi
de kendi eğitim verisinin istatistiklerini gerektirir. Eksik istatistiklerle sessiz çıkarım yapılmaz.

## Kaynaklar

- [LeRobot](https://github.com/huggingface/lerobot) — kullanılan kütüphane.
- [SmolVLA rehberi](https://huggingface.co/docs/lerobot/smolvla) — uyarlama yöntemi.
- [Resmî model](https://huggingface.co/lerobot/smolvla_base).
- [SO-101 dokuz görevli model](https://huggingface.co/Harrysunshine/so101-smolvla-9task) — fiziksel olarak doğrulanmamış topluluk modeli.
- [Referans veri](https://huggingface.co/datasets/lerobot/svla_so101_pickplace).

Fiziksel doğrulama sınırları `ASSUMPTIONS.md`, seçimlerin nedenleri `DECISIONS.md` içindedir.

## Fiziksel kalibrasyon
Pasif ölçüm aracı ve sıradaki fiziksel adımlar: [KALIBRASYON.md](KALIBRASYON.md). Motor ayarları korunur; ölçümler kendiliğinden doğrulanmış politika eşlemesi veya hareket yolu sayılmaz.

30 Eylül kod incelemesi, düzeltmeler ve doğrulama sonuçları:
[KOD_INCELEMESI_20260930.md](KOD_INCELEMESI_20260930.md).
