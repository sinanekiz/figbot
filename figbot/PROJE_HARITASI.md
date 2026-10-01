# FIGBOT dosya düzeni

Güncel teslim klasörü **GUNCEL**. Bundan sonra sürüm adıyla yeni teslim klasörü açılmaz.

| Konum | İçerik |
|---|---|
| GUNCEL/BASKI | Tabla bazında3MF/STL, tek parça değiştirme dosyaları, ZIP ve önizlemeler |
| GUNCEL/CAD | Güncel CAD çıktıları, montajlar, doğrulamalar ve URDF |
| GUNCEL/ALISVERIS | A4 alışverişPDF ve VERI içindeki malzeme listesi |
| GUNCEL/YAZILIM | Son eldeki APK/HEX dosyaları; uyumluluk notuyla |
| ARSIV/ESKI_SURUMLER.zip | Önceki teslimler, eski CAD çıktıları ve eski önizlemeler; eski yollarıyla |
| cad, scripts, tests | Parametrik kaynak, üretim araçları ve testler |
| software, firmware, ai, simulation | Yazılım, elektronik kontrol, algılama ve simülasyon kaynakları |
| bom, purchasing, electrical, manufacturing, assembly | Teknik kaynak kayıtları |
| reports, references, docs | Denetim izi, orijinal referanslar ve proje belgeleri |

**GUNCEL_DOSYALAR.cmd** güncel klasörü açar. **GUNCELI_YENILE.cmd** mevcut CAD'den paketleri aynı yola yeniler. CAD kaynakları değiştiğinde `GUNCELI_YENILE.cmd --rebuild-cad` önce güncel dosyaları ZIP içinde tarihli bir kayıtla saklar, sonra CAD/URDF/render ve doğrulamaları yeniler. Fiziksel onay anlamına gelmez.

Tarayıcıdaki sabit kol adresi: http://127.0.0.1:5173/kol.html . Eski önizleme adresleri buraya yönlendirilir.

Eski isimli bazı Python modülleri aktif tasarımın ortak geometri bağımlılıklarıdır; bunlar basılacak eski sürüm klasörleri değildir. Tarihsel raporlardaki eski dosya yolları arşiv içindeki özgün dosyayı tanımlar. Eski tasarımlara ait export testlerini çalıştırmak istersen gereken tarihsel çıktıyı arşivden ayrı bir çalışma alanına çıkar.
