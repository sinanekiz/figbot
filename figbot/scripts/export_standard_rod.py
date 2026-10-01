"""DEC-085 standard steel screw + printed sleeve rod joints."""
import csv,json,shutil,hashlib
from collections import Counter
import cadquery as cq
import numpy as np
from cad.prototype_arm import build_linka_v1 as a,rigid_tripod_gripper as g
from cad.prototype_arm.export_forma_v6 import mesh,write_3mf
from cad.prototype_arm.export_linka_v1 import scene,mass_report,urdf
from cad.prototype_arm.linka_render import render
from scripts.export_rigid_tripod import arm_items,full_arm_urdf
from scripts.project_paths import CAD,ROOT,PRINTS
from scripts.package_tripod_plates import entry,check,package,BASE_NOTE

OUT=CAD/'CUBUK_MAFSALI'
PARTS=['L1-15-COUPLER','L1-26-ROD-BUSH']
NOTE='''# Standart vidalı çubuk mafsalı — DEC-085

Yalnız uzun185mm eksen aralıklı bağlantı çubuğu ve iki burç yenilendi. Krank ve önkol plakasındaki mevcut M3×4mm pirinç insert yuvaları değişmedi. Eski4,1mm delikli çubukla bu burçları kullanma; eski çubuğu delme talimatı değildir. Vida METAL olacak.

Her uçta dıştan içe: M3×10 silindirik başlı çelik vida → M3 düz pul (iç3,2/dış7/kalınlık0,5mm) → basılı burç içinden geçiş → mevcut M3×4mm insert. Yeni çubuğun geniş ucunu burcun DIŞINA geçir. İki eski M4 pul bu düzende kullanılmaz. Omuzlu vida satın alınmayacak. Toplam2 vida,2 pul,2 burç; önceki alım miktarları gerçekten alındıysa standart vida/pul yedeklerinden karşılanabilir, stok bilinmiyor.

Burç dış6/iç3,3/boy6mm, çubuk deliği6,3mm; delik çevresi dış14mm, uç kalınlığı5,6mm. Nominal çap boşluğu0,3mm, eksen boşluğu toplam0,4mm. Vida başı altından10mm;6mm burç+0,5mm pul sonrasında nominal3,5mm insert tutuşu. Pul ve burç boyunu rastgele değiştirme. Insert yüzü oturma yüzeyiyle aynı hizada olmalı; gerçek diş derinliği ve vida boyu ölçülmeli, kör deliğin dibine dayanmamalı.

Önce motor enerjisi kapalıyken kontrol et: vida burçtan serbest geçmeli, burç çubukta elle dönebilmeli. Vida sıkıldıktan sonra çubuk sıkışmamalı. Sıkışmayı vidayı gevşek bırakarak çözme; baskı/ölçü hatasını düzelt. Burç, vida sıkmasını taşır ve PLA zamanla ezilebilir/sünebilir; güvenli sıkma torku ve yüklü ömür PHYSICAL VALIDATION REQUIRED. Plastik vida veya metal omuzlu vida ile eşdeğer dayanım iddiası yoktur.

09 tabla yalnız3 parça içerir. 0,4mm nozzle,0,16mm katman,4 duvar,%100 dolgu başlangıç hedefidir. Çubuk yatık, burçlar delik ekseni dik; burçlarda5mm dış brim. Çubuk uçları orta gövdeden0,8mm daha kalındır; gövde altındaki yükselti için tabladan destek aç. Ölçek%100. 3MF geometri yerleşimidir, yazıcı profili değildir. Destek, gerçek çizgi genişliği ve baskı toleransı dilim önizlemesinde kontrol edilmeli.

Bu değişiklik tutucunun bildirilen kırılganlığını çözmez; tutucu gövdesi incelemesi ayrı ve açıktır. Yeni vida/burç bağlantısı önce yüksüz elle denenmelidir.
'''

def current_local():return [i for i in a.local_items() if i.frame!='tool' or 'W1' in i.name]+g.tool_items()

def joints_audit():
    # Exact solids, including unchanged fixed seats and inserts, in their common joint datum.
    rows=[]
    rod=a.rod();bush=a.rod_bush().rotate((0,0,0),(1,0,0),-90).translate((0,-37,0))
    washer=a.washer_y(7,3.2,-37.5,.5);bolt=a.rod_shoulder_screw(0)
    fixed=[('crank',a.crank().translate((-a.CRANK,0,0))),('fore',a.fore_side(-1).translate((a.TAIL,0,0)))]
    for label,f in fixed:
        for angle in [-60,-30,0,30,60]:
            moving=rod.rotate((0,0,0),(0,1,0),angle)
            # local joint region only; full arm nominal test separately below
            near=moving.intersect(a.h.box(22,40,22,(0,-30,0)))
            for name,s in [('seat',f),('bush',bush),('washer',washer),('bolt',bolt)]:
                v=near.intersect(s).val().Volume();rows.append(dict(seat=label,angle=angle,other=name,collision_mm3=v))
    out=dict(revision='DEC-085',nominal_radial_diametral_clearance_mm=.3,axial_clearance_mm=.4,thread_engagement_mm=3.5,physical_approval=False,local_contacts=rows)
    assert all(r['collision_mm3']<1e-5 for r in rows),[r for r in rows if r['collision_mm3']>1e-5]
    return out

def print_plate():
    name='09_CUBUK_VE_BURCLAR';entries=[]
    for pid,n,x,y in [('L1-15-COUPLER',1,12,20),('L1-26-ROD-BUSH',1,25,65),('L1-26-ROD-BUSH',2,50,65)]:
        entries.append(entry(pid,n,x,y,(0,0,0),CAD/'PRINT_STL'/f'{pid}.stl'))
    check(entries);return package(name,entries,BASE_NOTE+'\n'+NOTE)

def main():
    OUT.mkdir(exist_ok=True)
    records=[]
    for pid in PARTS:
        s=a.PARTS[pid][0]();assert s.val().isValid() and len(s.val().Solids())==1
        cq.exporters.export(s,str(CAD/'PART_STEP'/f'{pid}.step'))
        m=mesh(a.print_pose(pid,s));assert m.is_watertight;m.export(CAD/'PRINT_STL'/f'{pid}.stl')
        write_3mf([(pid,pid,m,[])],CAD/'3MF'/f'{pid}.3mf')
        records.append(dict(id=pid,count=a.PARTS[pid][1],material='PLA',cad_mass_each_g=round(s.val().Volume()*.00124,3)))
    with (CAD/'PRINT_BOM.csv').open(encoding='utf-8') as f:rows=list(csv.DictReader(f))
    rows=[r for r in rows if r['id'] not in PARTS]+records
    with (CAD/'PRINT_BOM.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['id','count','material','cad_mass_each_g']);w.writeheader();w.writerows(sorted(rows,key=lambda r:r['id']))
    items=arm_items(0);scene(items,'LINKA_L1_ASSEMBLY');scene(items,'LINKA_L1_TRIPOD_ARM')
    shutil.copy2(CAD/'LINKA_L1_TRIPOD_ARM.glb',CAD/'TUTUCU/LINKA_L1_TRIPOD_ARM.glb')
    shutil.copy2(CAD/'LINKA_L1_TRIPOD_ARM.step',CAD/'TUTUCU/LINKA_L1_TRIPOD_ARM.step')
    render(items,OUT/'YENI_CUBUK_KOL.png','DEC-085 / Standart M3 vidali cubuk',revision='DEC-085')
    shutil.copy2(OUT/'YENI_CUBUK_KOL.png',CAD/'TUTUCU/TRIPOD_ARM.png')
    local=current_local();urdf(local);full_arm_urdf()
    for name in ['PICKUP','RELEASE']:
        poses=json.loads((CAD/'POSES.json').read_text())[name.lower()];fs=a.frames(poses)
        placed=[a.Item(i.name,a.h.move(i.shape,fs[i.frame]),i.frame,i.part_id,i.color,i.mass_g) for i in local]
        scene(placed,'LINKA_L1_'+name)
    joint=[i for i in a.local_items() if i.frame=='rod']
    render(joint,OUT/'CUBUK_VE_BURCLAR.png','DEC-085 / Cubuk ve iki basili burc',az=-65,el=35,revision='DEC-085')
    (OUT/'AUDIT.json').write_text(json.dumps(joints_audit(),indent=2),encoding='utf-8')
    (OUT/'MASS_AND_PARTS.json').write_text(json.dumps(mass_report(local),indent=2),encoding='utf-8')
    (OUT/'MONTAJ.md').write_text(NOTE,encoding='utf-8')
    (OUT/'STATUS.json').write_text(json.dumps(dict(revision='DEC-085',physical_approval=False,reprint=PARTS,reuse=['L1-10-FORE-L','L1-14-DRIVE-CRANK'],dimensions_changed=['rod end bores','rod end thickness/width'],assumed_hardware='M3x10 / washer3.2x7x0.5; actual dimensions UNVERIFIED'),indent=2))
    print_plate();print('DEC-085 CAD/STEP/STL/3MF/assemblies/renders/URDF complete',flush=True)

if __name__=='__main__':main()
