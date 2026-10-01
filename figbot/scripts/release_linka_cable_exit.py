"""Publish provisional J1 window files, retaining all previous print releases."""
import json,hashlib,shutil,zipfile
from pathlib import Path
import numpy as np
import trimesh
from scripts.package_linka_plates import ROOT,SOURCE,OUT,combine_3mf,preview

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()

def main():
    audit=ROOT/'reports/linka_cable_exit_audit'
    before=json.loads((audit/'before/STL_HASHES.json').read_text(encoding='utf-8-sig'))
    rows=[dict(part=Path(r['Path']).stem,old_sha=r['Hash'],new_sha=sha(SOURCE/'PRINT_STL'/Path(r['Path']).name)) for r in before]
    assert set(r['part'] for r in rows if r['old_sha']!=r['new_sha'])=={'L1-01-BASE','L1-17-FINGER','L1-18-PAD'}
    (audit/'COMPARISON_TO_L12.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
    original=json.loads((ROOT/'reports/linka_l1r1_audit/before/STL_HASHES.json').read_text(encoding='utf-8-sig'))
    (OUT/'PARCA_KARSILASTIRMA.json').write_text(json.dumps([dict(part=Path(r['Path']).stem,old_sha256=r['Hash'],new_sha256=sha(SOURCE/'PRINT_STL'/Path(r['Path']).name),unchanged=sha(SOURCE/'PRINT_STL'/Path(r['Path']).name)==r['Hash']) for r in original],indent=2),encoding='utf-8')
    name='01A_YALNIZ_KABLO_PENCERELI_TABAN';dest=OUT/name;dest.mkdir(exist_ok=True)
    pid='L1-01-BASE';m=trimesh.load_mesh(SOURCE/'PRINT_STL'/f'{pid}.stl')
    translation=(np.array([8,8,0])-m.bounds[0]).tolist();m.apply_translation(translation)
    e=dict(id=pid,copy=1,name=pid+'__1',translation=translation,mesh=m)
    m.export(dest/f'{name}.stl');combine_3mf([e],dest/f'{name}.3mf','PLA');preview(dest/f'{name}.png',name,'PLA',[e])
    note='''# LINKA L1.3 / DEC-080 — kablo penceresi DENEME modeli

Yalnız L1-01 taban değişti. L1.2'nin motor tablası dahil diğer21 parça türü aynıdır.01A ile tam01 paketini birlikte basma. Kullanıcı kablo çıkıntısını7mm en ×3,9mm yükseklik ×5,5mm dışarı uzama olarak ölçtü. Bu ölçü kaydı sonrası baskı geometrisi değişmedi. Çıkıntının gövdedeki alt kenar konumu henüz ölçülmedi; yeni tabanı basmadan konum eşleşmesi kontrol edilmeli.

İki kısa uç destek duvarında ortalanmış12mm genişlikte pencere vardır: tabanZ4, yuvarlatılmış tavanZ28; tam genişlikZ4..22 arasında.4mm alt taban, motor kulağı/insert köprüsü ve rulman izi korunur. Ortalanmış7mm çıkıntıya nominal2,5mm/yan açıklık kalır. Çıkıntı alt kenarı montajZ4,5..17,6 aralığındaysa0,5mm çevresel/tip payla CAD ve STEP çakışma testi geçer. Bu aralık gerçek çıkıntı konumunun ölçüsü değildir. Bu üstten açık kanal değildir; montajda kabloyu önce pencereden geçir. Kablo çıkış ucu, alt kenar konumu, fiş ve bükülme alanı henüz doğrulanmadı.

Gerçek motor/kablo uyumu ve dayanım fiziksel kontrol gerektirir. Eski basılmış tabanda elle kesme veya işleme talimatı verilmemiştir. Metal bağlantı ölçüleri değişmez.3MF/STL %100; dilimleyicide destek, brim ve katman önizlemesi kontrol edilir. G-code değildir.
'''
    (dest/'BASLAMADAN_ONCE.md').write_text(note,encoding='utf-8')
    (OUT/'ONCE_BUNU_OKU.md').write_text(note,encoding='utf-8')
    with zipfile.ZipFile(OUT/f'{name}.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in dest.iterdir():z.write(p,p.name)
    # Rebuild from current CAD, never from a dated release directory.
    from scripts.build_linka_fit_coupon import build as coupon
    coupon()
    deck_name='02A_YALNIZ_YENI_MOTOR_TABLASI';deck_dest=OUT/deck_name;deck_dest.mkdir(exist_ok=True)
    deck=trimesh.load_mesh(SOURCE/'PRINT_STL/L1-06-DECK.stl')
    shift=(np.array([8,8,0])-deck.bounds[0]).tolist();deck.apply_translation(shift)
    de=dict(id='L1-06-DECK',copy=1,name='L1-06-DECK__1',translation=shift,mesh=deck)
    deck.export(deck_dest/f'{deck_name}.stl');combine_3mf([de],deck_dest/f'{deck_name}.3mf','PLA');preview(deck_dest/f'{deck_name}.png',deck_name,'PLA',[de])
    (deck_dest/'BASLAMADAN_ONCE.md').write_text('Yalnız güncel destekli motor tablası. Tam02 ile birlikte basma. Vida/motor eksenleri korunmuştur. Fiziksel uyum ve yük testi gereklidir.',encoding='utf-8')
    with zipfile.ZipFile(OUT/f'{deck_name}.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in deck_dest.iterdir():z.write(p,p.name)
    status=json.loads((SOURCE/'RELEASE_STATUS.json').read_text(encoding='utf-8'))
    status.update(revision='LINKA L1.5 / DEC-082',status='BOOT SIZE USER-MEASURED; POSITION AND PHYSICAL FIT UNVERIFIED',audit_report='reports/linka_cable_exit_audit',printing_reuse='From L1.4: replace L1-17 fingers using04A and L1-18 TPU liners using05; other23 types unchanged. From L1.3 also add06 plastic bushes; prototype only',cable_boot_user_mm={'width':7,'height':3.9,'protrusion':5.5})
    (SOURCE/'RELEASE_STATUS.json').write_text(json.dumps(status,indent=2,ensure_ascii=False),encoding='utf-8')
    notes=SOURCE/'ASSEMBLY_NOTES_TR.md';prior=notes.read_text(encoding='utf-8')
    if '7 × 3,9 × 5,5' not in prior:
        prior='# Kablo ölçü kaydı — 2026-09-14\n\nKablo çıkıntısı 7 × 3,9 × 5,5 mm olarak kullanıcı tarafından ölçüldü.12mm pencere korunur; gövdedeki alt kenar konumu hâlâ doğrulanmadı. Önceki "çıkıntı ölçülmedi" notları yalnız bu üç boyut için geçersizdir.\n\n'+prior
        notes.write_text(prior,encoding='utf-8')
    if '# L1.3' not in prior:
        notes.write_text('# L1.3 / DEC-080 — taban kablo açıklığı deneme modeli\n\nKablo penceresi12mm genişlikte, Z4..28 aralığında; gerçek kablo ölçüsü doğrulanmadan yeni tabanı basma. Önce kabloyu pencereden geçirerek motoru yerleştirmek gerekir. Üstten açık kanal değildir. L1.2 motor tablası ve diğer parçalar korunur.\n\n'+prior,encoding='utf-8')
    viewer=ROOT/'viewer/kol.html'
    viewer.write_text(viewer.read_text(encoding='utf-8').replace('LINKA L1.2','LINKA L1.3').replace('DEC–079','DEC–080'),encoding='utf-8')
    print(json.dumps({'cable_window_unchanged_from_L13':True,'revision':'L1.5','physical_cable_fit':'UNVERIFIED'}))

if __name__=='__main__':main()
