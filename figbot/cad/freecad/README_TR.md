# FIGBOT – FreeCAD içinde ölçü düzenleme

**2026-09-06 güncellemesi:** Yeni kol tasarımı `FIGBOT_ARM_V3_PARAMETRIC.FCStd`, araç ise `FIGBOT_ROVER_V3_PARAMETRIC.FCStd` dosyasında. V3 aktif MG90S bilek ve aşağı bakan kıskaç içerir. V3 baskı koşulları `cad/prototype_arm/aero_v3/ONCE_OKU_MONTAJ.md` içindedir. Bir ölçü değiştirince varsayılan V3 geometrik kontrolü geçersizleşir ve yeniden kontrol gerekir. Aşağıdaki V2 dosyaları tarihsel olarak korunmuştur; onları yeni baskı paketiyle karıştırmayın.

**Mevcut Rev-H2 / AERO V2 geometrisinin parametrik bağlantısıdır. DEC-039 baskı durdurma kararı devam ediyor.** Bu dosyalar montaj hatalarını düzeltmez.

## Dosyalar ve kullanım

- `FIGBOT_ROVER_PARAMETRIC.FCStd`: iki kollu aracın tamamı, 229 ayrı katı bileşen.
- `FIGBOT_ARM_PARAMETRIC.FCStd`: ayrı kol montajı, 51 bileşen. Motor/horn/vida/ped referansları baskı parçası değildir.

FreeCAD 1.1.3 ile oluşturuldu. Model birimi milimetredir. Varsayılanlar mevcut kontrollü tasarımla aynıdır.

1. FreeCAD önceden açıksa bir kez kapatıp açın; FIGBOT bağlantısı başlangıçta yüklenir.
2. FCStd dosyasını açın. Ağaçtaki **00 - OLCULER (Data sekmesinden duzenle)** öğesini seçin.
3. **Data / Veri → Olculer** bölümünde değeri değiştirip Enter'a basın. Gerekirse **Recompute / Yeniden hesapla (F5)** kullanın.
4. Yeniden üretim sırasında bekleyin. **BuildState** alanında `OK - regenerated geometry` yazmalıdır. `FAILED` yazarsa yeni ölçüler uygulanmamıştır; eski geometri tutulur. Geçerli eski değere dönüp yeniden hesaplayın.
5. Farklı adla kaydedin. STEP, GLB, STL, PNG ve sabit inceleme URDF çıktıları **ExportDirectory** alanındaki ayrı klasördedir.

| Alan | Başlangıç | Değişiklik |
|---|---:|---|
| UpperLength | 300 mm | Omuz–dirsek eksen aralığı; boru referansı, dirsek/bilek yerleşimi, kılıflar |
| ForeLength | 220 mm | Dirsek–bilek eksen aralığı; boru referansı ve kılıflar |
| BasketSlope | 15° | Sepet tabanı, yan duvarlar, ön giriş ve destekler |
| BasketRearHeight | 145 mm | Sepetin arka taban yüksekliği ve bağlı yüzey/destekler |
| ArmBaseX | 380 mm | İki kolun öne/arkaya konumu |
| ArmBaseY | 415 mm | İki kolun merkezden sağa/sola mesafesi |
| ArmBaseZ | 280 mm | İki kol tabanının yerden yüksekliği |

Kol dosyasında yalnızca iki uzunluk gösterilir. Araç dosyasında yedi alan vardır. Motor ölçüleri ve şasi/tekerlekler bu panelde değiştirilebilir yapılmadı. Alan sınırları yazılım giriş sınırlarıdır; güvenli çalışma sınırları değildir.

## Sınırlar ve bağımlılıklar

- Bu yalnızca STEP aktarımı değildir: ölçü değişimi CadQuery üreticisini çalıştırıp gerçek katı geometriyi değiştirir. Ancak parçalar için bağımsız **Sketch / Pad / Pocket** geçmişi oluşturulmadı. Ana kontrol `FeaturePython`, bileşenler `Part::Feature` nesneleridir.
- Yeniden üretim bu bilgisayardaki FIGBOT kaynak klasörüne ve `.venv` ortamına bağlıdır. **FCStd dosyasını tek başına başka bilgisayara taşımak parametrik üreticiyi taşımaz.** Kayıtlı katılar açılır; otomatik ölçü düzenleme için kaynak ve ortam da kurulmalıdır.
- Tek eklenti dosyası: `%APPDATA%/FreeCAD/v1-1/Mod/FIGBOT_Parametric/Init.py`. Projenin `cad/freecad/figbot_freecad.py` modülünü yükler. Başka eklenti veya FreeCAD ayarı değiştirilmedi.
- Araçta başlangıçtaki toplama eklem açıları korunur. Uzunluk değişirse uç konumu değişir; model hedefe kendiliğinden yeniden ulaşmaz. Hareket kontrolü değildir.
- Kollar taşıyıcılarından uzaklaşabilir, sepet ekipmanla çakışabilir, kol zemine girebilir. Bağlantılar, kablolar, karşı dengeleme, toleranslar ve donanım seçimi otomatik yeniden tasarlanmaz. Her varyant mühendislik kontrolü ister.
- Alüminyum borular mevcut modelde dolu referans hacim olarak temsil edilir. **300/220 mm eksen aralığıdır; doğrulanmış metal kesim boyu değildir.**
- Bileşenlere doğrudan yapılan geometri/yerleşim düzenlemelerinin üzerine ana parametreler yeniden üretildiğinde yazılır. Bağımsız elle çalışma için ayrı kopya kullanın.
- Tarayıcıdaki Rev-H sayfası ve kontrollü STEP/STL baskı paketleri otomatik değiştirilmez. Baseline ve deneysel varyantlar ayrıdır.

## Kontrol kayıtları

`tests/test_freecad_variant.py`: hatalı değer reddi, varsayılan aracın kaynakla bileşen bazında hacim/sınır karşılaştırması, uzunlukla gerçek geometri/eklem değişimi ve sepet eğimi.

`NATIVE_TEST_REPORT.json`: FreeCAD'de kaydet/aç → ölçü değiştir → üret → kaydet/aç. Kol uzunluğu ve sepet eğimi gerçekten değiştirilerek denenir. Dijital aktarım testi fiziksel çalışma veya baskı onayı değildir.
