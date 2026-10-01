"""Install stable navigation after original pages have been verified in archive."""
import json
from scripts.project_paths import ROOT,ARCHIVE

def main():
    manifest=json.loads((ROOT/'reports/project_organization/ARCHIVE_MANIFEST.json').read_text(encoding='utf-8'))
    assert manifest['status']=='ZIP_SHA256_VERIFIED' and ARCHIVE.is_file()
    page=ROOT/'viewer/kol.html'
    page.write_text(page.read_text(encoding='utf-8').replace('/models/linka-v1/','/models/guncel/').replace('<a href="/forma-v6.html">Eski R6</a>',''),encoding='utf-8')
    redirect='<!doctype html><html lang="tr"><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=/kol.html"><title>FIGBOT güncel kol</title><a href="/kol.html">Güncel kolu aç</a></html>'
    for row in manifest['files']:
        p=row['path']
        if p.startswith('viewer/') and p.count('/')==1 and p.endswith('.html'):
            (ROOT/p).write_text(redirect,encoding='utf-8')
    (ROOT/'README.md').write_text('''# FIGBOT

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
''',encoding='utf-8')
    banner='''# Güncel dosya yolu — 2026-09-14

Aktif teslim kökü **GUNCEL/**: BASKI, CAD, ALISVERIS, YAZILIM. Revizyon klasör adına eklenmez. Tarihsel `releases/...` çıktıları ARSIV/ESKI_SURUMLER.zip içindedir; baskı için güncel klasörü kullan. Teknik kaynak kodlarının yerleri korunmuştur. Ayrıntı: PROJE_HARITASI.md.

'''
    for name in ['MASTER_SPEC.md','STATUS.md','PLAN.md']:
        p=ROOT/name;data=p.read_text(encoding='utf-8')
        if not data.startswith('# Güncel dosya yolu'):data=banner+data
        # Update current pointers; dated decisions and historical report hashes stay intact.
        data=data.replace('cad/prototype_arm/linka_v1/','GUNCEL/CAD/').replace('`cad/prototype_arm/linka_v1`','`GUNCEL/CAD`').replace('http://127.0.0.1:5173/linka-v1.html','http://127.0.0.1:5173/kol.html').replace('releases/LINKA_L1_2_TABLALAR/02A_YALNIZ_YENI_MOTOR_TABLASI.zip','GUNCEL/BASKI/02A_YALNIZ_YENI_MOTOR_TABLASI.zip')
        p.write_text(data,encoding='utf-8')
    (ROOT/'ARSIV/OKU.md').write_text('Eski dosyalar ESKI_SURUMLER.zip içinde özgün proje yollarıyla saklanır. _ARCHIVE_MANIFEST.json her dosyanın SHA256 özetini içerir. Baskı için ../GUNCEL/BASKI kullan. ZIP içindeki eski sürümleri güncel klasörün üzerine çıkarma.',encoding='utf-8')
    (ROOT/'releases/OKU.md').write_text('Güncel teslimler artık ../GUNCEL altında. Eski sürümler ../ARSIV/ESKI_SURUMLER.zip içinde. Bu klasöre yeni sürüm paketi koyma.',encoding='utf-8')

if __name__=='__main__':main()
