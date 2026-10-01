"""Preserve superseded status/plan prose, then make entry docs describe current work."""
import hashlib,zipfile
from scripts.project_paths import ROOT,ARCHIVE

def main():
    texts={
      'STATUS.md':'''# FIGBOT güncel durum

Güncel model: LINKA L1.3 / DEC-080. Dosyalar GUNCEL içinde; revizyon numarası SURUM.json'da.

- BASKI: tabla paketleri ve yalnız değişen parçaları basma seçenekleri.
- CAD: güncel montaj, parça dosyaları, renderlar ve URDF.
- ALISVERIS: hırdavatçı listesi; hazır/3D baskı burç alternatifleri hâlâ açık.
- YAZILIM: eldeki son sürümler; eski UNO firmware'inin LINKA mekanizmasına uyumu onaylanmadı.

Kablo çıkıntısı7×3,9×5,5mm ölçüldü. Gövde üzerindeki alt kenar konumu ve gerçek montaj/katman dayanımı fiziksel kontrol ister. Klasör düzenlemesinde geometri veya BOM ölçüsü değiştirilmedi.

Eski çıktılar ARSIV/ESKI_SURUMLER.zip içinde doğrulanarak saklandı. Tek sabit önizleme: http://127.0.0.1:5173/kol.html . Ayrıntı: PROJE_HARITASI.md.
''',
      'PLAN.md':'''# FIGBOT devam planı

Dosya üretimi ve teslim için yalnız GUNCEL klasörünü kullan. scripts/project_paths.py sabit yolları tanımlar; scripts/publish_current.py aynı konumları yeniler.

1. Kablo çıkıntısının alt kenarının motor gövdesindeki yüksekliğini doğrula; taban penceresiyle gerçek montaj uyumunu kontrol et.
2. Özel işlem gerektiren burçları hazır malzeme veya doğrulanmış3D baskı çözümleriyle değiştir; satın alma listesindeki bekleyen satırları ancak sonra kesinleştir.
3. Baskı yönü, insert, servo yıldızı ve yük altındaki bağlantı davranışını fiziksel denemeyle doğrula.
4. LINKA bağlantı mekanizmasına uygun firmware/kalibrasyonu tamamla; önceki doğrudan dirsek kontrolünü uyumlu varsayma.

Teknik sınırlar MASTER_SPEC.md; kararlar DECISIONS.md; belirsizlikler ASSUMPTIONS.md. Bu dosya fiziksel imalat onayı değildir.
'''}
    for name,text in texts.items():
        p=ROOT/name;entry='_DOCUMENT_HISTORY/20260914/'+name
        old=p.read_bytes()
        with zipfile.ZipFile(ARCHIVE,'a',compression=zipfile.ZIP_DEFLATED) as z:
            if entry not in z.namelist():z.writestr(entry,old)
        with zipfile.ZipFile(ARCHIVE) as z:
            archived=z.read(entry)
        if p.read_text(encoding='utf-8')!=text and hashlib.sha256(archived).digest()!=hashlib.sha256(old).digest():raise RuntimeError('Unexpected history change')
        p.write_text(text,encoding='utf-8')

if __name__=='__main__':main()
