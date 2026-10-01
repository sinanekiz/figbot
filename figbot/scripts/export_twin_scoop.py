"""Build DEC-086 into internal staging before publishing to stable paths."""
import json,math,shutil,csv
import xml.etree.ElementTree as ET
import cadquery as cq
import trimesh,numpy as np
from cad.prototype_arm import twin_scoop as g,yaw_capture as y,build_linka_v1 as a
from cad.prototype_arm.export_forma_v6 import mesh,write_3mf
from cad.prototype_arm.export_linka_v1 import mass_report,urdf as arm_urdf
from cad.prototype_arm.linka_render import render
from scripts.project_paths import ROOT,CAD

OUT=ROOT/'.codex_artifacts/twin_scoop_build'
PARTS={**g.PARTS,y.PID:(y.cup,1)}
NOTE='''# İki kepçe ve taban yıldız kapağı — DEC-086

07: TS-FRAME gövde, TS-BRIDGE üst köprü, TS-BUSH pasif eksen burcu. 08: birbirinden farklı iki dişli kepçe. 10: yalnız taban yıldızını tutan J1-CAPTURE-CUP. Eski üç parmak, kremayer, bağlantı çubukları ve parmak burçları kullanılmaz. İki mevcut L1-21 küçük yıldız kapağı korunur. Taban dışındaki üç büyük L1-20 kapak korunur. Motor, yıldız ve orijinal merkez vidaları yeniden kullanılır.

Kepçe cidarı2,6mm; kök10x6mm, ağız kenarı ve kökte takviyeler. İki28diş/modül1,25 dişli zıt yönde24derece açılır. Önceki35derece üç parmak kalibrasyonunu kullanma. Servo darbe uçları fiziksel olarak belirlenmedi; yazılım değiştirilmedi. İncirin40–50g ağırlığı bildirildi, eni bilinmiyor; yaklaşık43mm iç ağız ölçüsü adaydır. Baskı geometrisi kuvvet/dayanım garantisi değildir.

Tutucu montajı: önce motoru alttan açık yuvaya yerleştir; iki M2L4 insert, iki M2x6 vida ve0,3mm pullarla kulaklarını bağla. Tahrikli kepçeye orijinal yıldızı ve L1-21 kapağı iki M2x6/M2L4 ile tak. Üst köprü sökükken dişli çeneleri yerleştir; orijinal merkez vida motorun metal miline girer. Pasif kepçeninØ6,4 deliğine TS-BUSH (dış6/iç2,4/boy8mm) girer. Gövdenin pasif eksenindeki M2L4 insert üstü yüzeyle hizalıdır. Köprü dört M2x6/M2L4 ile bağlanır; ortadaki pasif eksen vidası M2x14'tür.8mm burç+3mm köprü sonrasında nominal3mm insert tutuşu kalır; pul yok. Dişli çeneler burç/yuva üzerinde serbest döner. Vida gevşek bırakılarak sıkışma gizlenmez. Bilek yıldızı mevcut iki M2x6/M2L4 bağlantıyı kullanır.

Taban kapağı: mevcut tabanın yıldız yuvası ve motor yüksekliği değişmez. Eski J1 L1-20 düz kapağın yerine J1-CAPTURE-CUP konur. Geniş açıklığı dönen tablaya/yıldız yuvasına bakan yükseltilmiş kenar yukarıda, düz yüz motor tarafındadır. İki M2x8 vida mevcut iki M2L4 inserte girer; eski M2x6 vidaları burada kullanma. Merkezden motorla gelen orijinal vida kullanılır. Yeni kapakOD50, merkez açıklığı12,6, taban4, çevre kenarı2mm; toplam6mm. Yuva dış çapına nominal0,3mm/yan pay. Yıldızın oturmaması/yüksekliğinin yetişmemesi bu parçayla çözülmüş sayılmaz; gerçek sorun tanımı ve fiziksel oturma kontrolü bekleniyor. Rulmanın sabit/dönen yüzlerini birbirine sıkıştırma.

PLA / kayıtlı0,4mm nozzle:0,16mm katman,5 duvar,%100 dolgu başlangıç hedefi. Kepçelerin ağzı yukarı; dış kabuk altında tabladan destek gerekir. Gövde altta, köprü düz, burç dik, taban kapağı düz alt yüzü tablaya oturur.5mm dış brim. 3MF geometri yerleşimidir; gerçek yazıcı profili değildir. Destek kalıntısı dişlerde/yıldız yuvasında/kayma yüzeyinde bırakılmaz. Önce enerjisiz elle hareket; yük, sıkma torku, PLA sünmesi ve meyvede iz PHYSICAL VALIDATION REQUIRED.

Dişli geometri dayanağı: https://khkgears.net/pdf/2023/spur-gears.pdf . Mevcut yıldız STL referanslarının lisans ve kaynakları forma_v6_horns.py içindedir. Gerçek servo yıldız uyumu ölçülmüş kabul edilmez.
'''

def local_items():return y.apply([i for i in a.local_items() if i.frame!='tool' or 'W1' in i.name])+g.tool_items()
def placed(q=(0,-60,95,-35),angle=0):
    fs=a.frames(q);local=y.apply([i for i in a.local_items() if i.frame!='tool' or 'W1' in i.name])+g.tool_items(angle)
    return [a.Item(i.name,a.h.move(i.shape,fs[i.frame]),i.frame,i.part_id,i.color,i.mass_g) for i in local]
def scene(items,key):
    ass=cq.Assembly(name=key);sc=trimesh.Scene()
    for k,i in enumerate(items):
        name=f'{k:03}_{i.name}'.replace(' ','_');m=mesh(i.shape);m.visual.face_colors=(np.array([*i.color,1])*255).astype(np.uint8)
        ass.add(i.shape,name=name,color=cq.Color(*i.color));sc.add_geometry(m,node_name=name)
    ass.save(str(OUT/f'{key}.step'),write_pcurves=False);sc.export(OUT/f'{key}.glb')
def tool_urdf():
    items=g.items();root=ET.Element('robot',name='TWO_SCOOPS_DEC086');path=OUT/'URDF'
    groups={
        'left':[i for i in items if i.name=='JAW -1' or (i.name.startswith('G1 ') and i.name!='G1 servo')],
        'right':[i for i in items if i.name=='JAW 1']}
    used={id(i) for rows in groups.values() for i in rows};groups['chassis']=[i for i in items if id(i) not in used]
    for key,rows in groups.items():
        m=trimesh.util.concatenate([mesh(i.shape) for i in rows])
        if key!='chassis':m.apply_translation((-g.old.CX-g.OFFSET,g.old.CY if key=='left' else -g.old.CY,0))
        m.apply_scale(.001);m.export(path/f'{key}.stl');link=ET.SubElement(root,'link',name=key)
        ET.SubElement(ET.SubElement(ET.SubElement(link,'visual'),'geometry'),'mesh',filename=f'{key}.stl')
    for key,sign in [('left',-1),('right',1)]:
        j=ET.SubElement(root,'joint',name=key+'_jaw',type='revolute');ET.SubElement(j,'parent',link='chassis');ET.SubElement(j,'child',link=key)
        ET.SubElement(j,'origin',xyz=f'{(g.old.CX+g.OFFSET)/1000} {sign*g.old.CY/1000} 0');ET.SubElement(j,'axis',xyz='0 0 1')
        ET.SubElement(j,'limit',lower=str(-math.radians(g.OPEN) if sign<0 else 0),upper=str(math.radians(g.OPEN) if sign>0 else 0),effort='0',velocity='0')
        if sign>0:ET.SubElement(j,'mimic',joint='left_jaw',multiplier='-1',offset='0')
    ET.indent(root);ET.ElementTree(root).write(path/'REVIEW.urdf',encoding='utf-8',xml_declaration=True)

def main():
    for d in ['PART_STEP','PROTOTIP_STL','3MF','URDF','ARM_REVIEW/URDF']:(OUT/d).mkdir(parents=True,exist_ok=True)
    records=[]
    for pid,(fn,n) in PARTS.items():
        s=fn();assert s.val().isValid() and len(s.val().Solids())==1,pid
        cq.exporters.export(s,str(OUT/'PART_STEP'/f'{pid}.step'))
        b=s.val().BoundingBox();m=mesh(s.translate((-b.xmin,-b.ymin,-b.zmin)))
        assert m.is_watertight,pid;m.export(OUT/'PROTOTIP_STL'/f'{pid}.stl');write_3mf([(pid,pid,m,[])],OUT/'3MF'/f'{pid}.3mf')
        records.append(dict(id=pid,count=n,material='PLA',cad_mass_each_g=s.val().Volume()*.00124))
    for key,items in [('TWIN_OPEN',g.items(g.OPEN)),('TWIN_CLOSED',g.items()),('TWIN_SERVICE',g.items(0,True)),('TWIN_ARM',placed()),('YAW_CUP',[i for i in local_items() if i.frame in ['base','yaw'] and ('J1' in i.name or i.name=='L1-02-ROTOR')])]:
        scene(items,'LINKA_L1_'+key);render(items,OUT/(key+'.png'),g.REVISION,az=-55,el=-35 if key=='YAW_CUP' else 30,revision='DEC-086');print(key,flush=True)
    tool_urdf();saved=a.OUT
    try:a.OUT=OUT/'ARM_REVIEW';arm_urdf(local_items())
    finally:a.OUT=saved
    for key in ['pickup','release']:
        q=json.loads((CAD/'POSES.json').read_text())[key];scene(placed(q),'LINKA_L1_'+key.upper())
    scene([i for i in placed() if i.frame in ['base','yaw']],'LINKA_L1_BASE')
    report=mass_report(local_items());report['parts']=records
    (OUT/'MASS_AND_PARTS.json').write_text(json.dumps(report,indent=2))
    note=NOTE.replace('motoru alttan açık yuvaya','dişliler ve köprü sökükken motoru üstten açık yuvaya')
    note+='\nKepçe şasisi bilek yıldızına göre32mm öne alındı. Bu değişim uç momentini artırır; daha hafif olduğu veya mevcut motorun yükü kaldıracağı varsayılmaz. Bilek bağlantısında motorun karşı tarafında12mm geniş taşıyıcı perde vardır. Tam hareket zarfı ve kablo yolu fiziksel doğrulama ister.\n'
    (OUT/'OKU.md').write_text(note,encoding='utf-8')
    (OUT/'STATUS.json').write_text(json.dumps(dict(revision='DEC-086',print_release=False,physical_approval=False,source='cad/prototype_arm/twin_scoop.py',base_fit='UNVERIFIED; assumes existing horn reaches socket',fragility='redesigned; physical strength not tested'),indent=2))
    shutil.copy2(ROOT/'reports/twin_scoop/AUDIT.json',OUT/'AUDIT.json')
    print('STAGED',OUT,flush=True)
if __name__=='__main__':main()
