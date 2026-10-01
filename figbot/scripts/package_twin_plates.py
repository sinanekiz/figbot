"""DEC-086 stable plates; retain unrelated meshes and remove obsolete instances."""
import json
from collections import Counter
import numpy as np
import trimesh
from PIL import Image
from scripts.project_paths import CAD,PRINTS,CURRENT
from scripts import package_tripod_plates as p

REVISION='DEC-086'
NEW={
 '07_TUTUCU_MEKANIZMA':[('TS-FRAME',12,12),('TS-BRIDGE',155,12),('TS-BUSH',230,115)],
 '08_KEPCELER_VE_BURCLAR':[('TS-JAW-DRIVE',12,20),('TS-JAW-PASSIVE',130,20)],
 '10_TABAN_YILDIZ_KAPAGI':[('J1-CAPTURE-CUP',12,12)]}

def delivery_notes():
    note='''# Güncel iki kepçeli kol — DEC-086

Önceki kol basılıysa yeni parçalar07,08 ve10 tablalarında: toplam6 parça.01 taban,02 motor tablası,03 kol plakaları ve09 çubuk değişmedi. Bunları yeniden basma. İki mevcut küçük L1-21 yıldız kapağı kullanılır.10 yalnız tabandaki bir büyük yıldız kapağının yerine geçer; diğer üç büyük kapak korunur.

Eski üç parmak, kremayer, kısa bağlantılar ve parmak burçları yeni tutucuya takılmaz.06 artık yalnız üç dirsek burcudur.04 içinde üç büyük ve iki küçük yıldız kapağı bulunur. Sıfırdan tam takım01,02,03,04,06,07,08,09,10:34 basılı parça.00,01A,02A alternatif/deneme baskılarıdır, toplamın üstüne eklenmez.

256×256mm tabla, ölçek%100,0,4mm nozzle ve PLA kaydı esas alındı.07/08/10 için0,16mm katman,5 duvar,%100 dolgu başlangıç hedefi;5mm dış brim. Kepçelerin ağzı yukarı, dış kabuk altında tabladan destek gerekir. Gövde destek gerektirir. Burcu dik ve desteksiz bas.3MF geometri yerleşimidir, gerçek makine profili değildir; yalnız3MF veyaSTL kullan. Yazıcıya komut gönderilmedi.

Kepçe cidarı2,6mm ve geniş kökler, önceki ince bağlantıları değiştirir. Bunun kırılmazlık garantisi yoktur. Nominal CAD çakışma ve genel dilimleme kontrolleri fiziksel mukavemet testi değildir. Firmware değiştirilmedi; eski üç parmak hareket uçları kullanılmaz.

Taban kapağı yıldızın mevcut yuvaya ulaştığı varsayımıyladır. Yükseklik/hiza sorunu ölçülmeden çözüldüğü iddia edilmez.İki M2×8 vida ve mevcut M2L4 insertler kullanılır. Ortadaki vida motorla gelen orijinal vidadır. Montaj sırası ve insertler: CAD/TUTUCU/OKU.md.
'''
    for path in [PRINTS/'ONCE_BUNU_OKU.md',PRINTS/'TABLA_LISTESI.md',CURRENT/'BASLA_BURADAN.md']:
        path.write_text(note,encoding='utf-8')

def main():
    p.REVISION=REVISION
    manifest=json.loads((PRINTS/'TABLA_LISTESI.json').read_text(encoding='utf-8'))
    plates=[]
    for plate in manifest['plates']:
        if not plate['name'].startswith(('01_','02_','03_','04_','06_','09_')):continue
        rows=plate['instances']
        if plate['name'].startswith(('04_','06_')):
            kept=[]
            for e in rows:
                if e['id']=='L1-25-FINGER-BUSH':continue
                if e['id']=='L1-20-MG-COVER' and e['copy']==4:continue
                m=trimesh.load_mesh(CAD/'PRINT_STL'/f"{e['id']}.stl")
                m.vertices=m.vertices@np.array(e.get('rotation',np.eye(3))).T
                m.apply_translation(e['translation'])
                kept.append(dict(e,mesh=m,name=f"{e['id']}__{e['copy']}"))
            plate=p.package(plate['name'],kept,'# DEC-086\n\nYalnız korunan kol bağlantıları. Yeni tutucu07/08, taban kapağı10 içinde.',old=True)
        plates.append(plate)
    for name,layout in NEW.items():
        entries=[p.entry(pid,1,x,y,(0,0,0),CAD/'TUTUCU/PROTOTIP_STL'/f'{pid}.stl') for pid,x,y in layout]
        p.check(entries)
        plates.append(p.package(name,entries,(CAD/'TUTUCU/OKU.md').read_text(encoding='utf-8')))
    plates.sort(key=lambda v:v['name'])
    count=sum(len(v['instances']) for v in plates)
    assert count==34,count
    counts=Counter(e['id'] for v in plates for e in v['instances'])
    assert counts['L1-20-MG-COVER']==3 and counts['L1-21-MICRO-COVER']==2
    out=dict(revision=REVISION,bed_mm=[256,256,256],printer='ELEGOO Centauri Carbon 2 Combo / ASM-052',physical_approval=False,status='PROTOTYPE; physical validation required',plates=plates)
    (PRINTS/'TABLA_LISTESI.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    (CAD/'TUTUCU/PRINT_LAYOUT.json').write_text(json.dumps(dict(revision=REVISION,new_plates=list(NEW),new_instances=6,full_arm_instances=count,physical_approval=False),indent=2))
    sheet=Image.new('RGB',(1500,1725),'#f4f5f2')
    for i,v in enumerate(plates):
        im=Image.open(PRINTS/v['name']/(v['name']+'.png'));im.thumbnail((500,575));sheet.paste(im,((i%3)*500,(i//3)*575))
    sheet.save(PRINTS/'TUM_TABLALAR.png');delivery_notes()
    print('DEC-086',dict(counts),flush=True)

if __name__=='__main__':main()
