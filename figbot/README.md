# FIGBOT

**Güncel dosyalar: [GUNCEL](GUNCEL/).** Bu klasörün yolu sürüm değişince değişmez.

- [Baskı tablaları](GUNCEL/BASKI/)
- [Güncel CAD ve montajlar](GUNCEL/CAD/)
- [Alışveriş listesi](GUNCEL/ALISVERIS/)
- [Yazılım dosyaları ve uyumluluk notu](GUNCEL/YAZILIM/)
- [Proje haritası](PROJE_HARITASI.md)
- [Eski sürümler ZIP](ARSIV/ESKI_SURUMLER.zip)

GUNCEL_DOSYALAR.cmd klasörü açar. Tarayıcı önizlemesi: http://127.0.0.1:5173/kol.html . Sunucu için `cd viewer` ve `npm run dev`.

## Geliştirme

Teknik kaynak MASTER_SPEC.md; kararlar DECISIONS.md; belirsizlikler ASSUMPTIONS.md. CAD kaynakları cad/prototype_arm/build_linka_v1.py ve kullandığı ortak modüllerdir. Kod ve orijinal referans bağımlılıkları korunmuştur.

Mevcut CAD'den paketleri aynı yola yenile: `.venv/Scripts/python.exe -m scripts.publish_current`.

CAD değişikliği sonrasında: `.venv/Scripts/python.exe -m scripts.publish_current --rebuild-cad`. Bu komut önceki güncel dosyaları arşive alır, ardından montaj/export/render/URDF ve doğrulamaları üretir. İlgili testleri ayrıca çalıştır.

Prototip fiziksel olarak onaylı değildir. Kablo çıkıntısı7×3,9×5,5mm ölçülmüş; gövde üzerindeki konumu hâlâ doğrulanmamıştır. Kaynak arşivleme ve klasör düzenlemesi parça geometrisini değiştirmez.
