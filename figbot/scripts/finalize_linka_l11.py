"""Revision manifest and traceability for parts already being printed; no CAD mutation."""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile
import numpy as np
import trimesh
from scripts.package_linka_plates import OUT, SOURCE, ROOT, combine_3mf, preview

AUDIT=ROOT/'reports/linka_l1r1_audit'

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()

def main():
    before={Path(r['Path']).name:r['Hash'] for r in json.loads((AUDIT/'before/STL_HASHES.json').read_text(encoding='utf-8-sig'))}
    rows=[]
    for p in sorted((SOURCE/'PRINT_STL').glob('*.stl')):
        unchanged=digest(p)==before[p.name]
        rows.append(dict(part=p.stem,unchanged=unchanged,old_sha256=before[p.name],new_sha256=digest(p)))
    expected_unchanged=['L1-01-BASE','L1-02-ROTOR','L1-03-RETAINER-L','L1-04-RETAINER-R','L1-05-CAGE']
    assert all(next(r['unchanged'] for r in rows if r['part']==pid) for pid in expected_unchanged)
    archives=json.loads((AUDIT/'before/PLATE_HASHES.json').read_text(encoding='utf-8-sig'))
    assert all(digest(Path(r['Path']))==r['Hash'] for r in archives),'Original ZIP was changed'
    (AUDIT/'PART_REVISION_COMPARISON.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
    (OUT/'PARCA_KARSILASTIRMA.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
    table='\n'.join(f"| {r['part']} | {'Aynı STL; tekrar basma' if r['unchanged'] else 'Değişti; L1.1 dosyası kullanılmalı'} |" for r in rows)
    doc=f'''# LINKA L1.1 — basılan parçalar ve düzeltmeler

**01 TABAN: üç parça da eski STL ile SHA-256 düzeyinde aynıdır. Tekrar basma.**

**02 MOTOR TABLASI: L1-06 değişti. Eski L1-06 motor tablasını kullanma; yeniden bas. L1-03 ve L1-04 tutucu yarımları aynıdır ve korunur.**

`02A_YALNIZ_YENI_MOTOR_TABLASI.zip` yalnız yeni L1-06 içerir. Tutucu yarımlarını bastıysan bunu kullan. 02 tam tabla ile 02A aynı parçayı tekrar içerir; ikisini birden basma.

Henüz başlanmamış 03 ve 04 için bu klasördeki yeni ZIP'leri kullan. Eski paketler izlenebilirlik için silinmedi veya üzerine yazılmadı. 05 yumuşak pedler aynıdır.

| Parça | Eski baskının durumu |
|---|---|
{table}

## Düzeltilen nominal montaj

- Arka dirsek motoru merkezi 85 → 105 mm yüksekliğe alındı, krank 55 → 65 mm oldu. Eski krank ve yeni tabla karıştırılmaz. Ana kol boyları 150/120 mm, çubuk 185 mm korundu.
- Rulman arkasında 2,5 mm baskı desteği oluşturuldu; kapak insertlerinin çevresindeki et kalınlığı artırıldı. Kapaklarda nominal 0,2 mm eksenel boşluk var.
- Sağ önkolun gömülü somun çıkıntısı kaldırıldı; M5 somun ve rondela dışarıdan erişilir. Dirsek iç bilezikleri metal basma burçlarıyla sıkılır.
- Çubuğun iki mafsalı Ø4×6 omuzlu, M3×7 dişli ISO7379 vidalarıyla döner; normal M3 vida yerine geçmez. Karşı insert boyu 4 mm, eksenel boşluk nominal 0,4 mm.
- Bilek köprüsü önkolun dışına taşınan bağlantı yüzeyiyle yükseltildi; eski kesişme giderildi.
- Motor kulağı, bağ, kapak ve tabla vidalarının boyları/rondelaları montaj kesitine göre yeniden belirlendi. Eski alışveriş listesini kullanma.

## Fiziksel doğrulama

Sayısal uyum baskı çekmesini veya elindeki donanım toleranslarını kanıtlamaz. Önce 00 uyum kuponunu %100 ölçekte bas; insert, 625 rulman, kapak ve gerçek vidaları dene. Tam boy parçayı zorlayarak rulman/vida yerleştirme. Parmak ipleri, kablolar, meyve kavrama ve ivmeli yük deneyleri yapılmadı. Eski doğrudan dirsek motoru firmware'i bu kapalı zincir mekanizmaya uygun değildir.
'''
    (OUT/'ONCE_BUNU_OKU.md').write_text(doc,encoding='utf-8')
    # A separate replacement job saves the already printed retainer halves.
    name='02A_YALNIZ_YENI_MOTOR_TABLASI';dest=OUT/name;dest.mkdir(exist_ok=True)
    pid='L1-06-DECK';m=trimesh.load_mesh(SOURCE/'PRINT_STL'/f'{pid}.stl')
    translation=(np.array([8,8,0])-m.bounds[0]).tolist();m.apply_translation(translation)
    e=dict(id=pid,copy=1,name=pid+'__1',translation=translation,mesh=m)
    m.export(dest/f'{name}.stl');combine_3mf([e],dest/f'{name}.3mf','PLA');preview(dest/f'{name}.png',name,'PLA',[e])
    (dest/'BASLAMADAN_ONCE.md').write_text('LINKA L1.1 / DEC-078. Yalnız L1-06 yeni motor tablası. 02 tam tabla ile birlikte basma. %100 ölçek. 3MF veya STL seç; ikisi birden değil. Modifier, destek/brim ve makine profilini dilimleyicide kontrol et. G-code içermez.\n',encoding='utf-8')
    with zipfile.ZipFile(OUT/f'{name}.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(dest.iterdir()):z.write(p,p.name)
    status=json.loads((SOURCE/'RELEASE_STATUS.json').read_text(encoding='utf-8'))
    status.update(revision='LINKA L1.1 / DEC-078',status='NOMINAL DIGITAL INTERFACE AUDIT; PHYSICAL VALIDATION REQUIRED',audit_report='reports/linka_l1r1_audit',printing_reuse='01 unchanged; 02 retainers unchanged; replace L1-06')
    (SOURCE/'RELEASE_STATUS.json').write_text(json.dumps(status,indent=2,ensure_ascii=False),encoding='utf-8')
    viewer=ROOT/'viewer/linka-v1.html'
    text=viewer.read_text(encoding='utf-8').replace('DEC–077','DEC–078').replace('LINKA L1 ·','LINKA L1.1 ·').replace('LINKA L1 yeni','LINKA L1.1 yeni').replace('LINKA L1 CAD','LINKA L1.1 CAD')
    viewer.write_text(text,encoding='utf-8')
    print(json.dumps({'changed':[r['part'] for r in rows if not r['unchanged']],'old_zips_preserved':True}))

if __name__=='__main__':main()
