"""Arrange existing L1 exports; no CAD geometry or BOM changes."""
from pathlib import Path
import copy
import csv
import json
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter
import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
from scripts.project_paths import CAD as SOURCE, PRINTS as OUT
NS = 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
Q = '{' + NS + '}'
BED = 256
MARGIN = GAP = 8
# (BOM part number, lower-left X, lower-left Y); original print poses retained.
LAYOUTS = [
    ('01_TABAN', 'PLA', [(1,8,12),(2,136,12),(5,12,144)]),
    ('02_MOTOR_TABLASI', 'PLA', [(6,8,8),(3,162,8),(4,8,136,90)]),
    ('03_KOL_PLAKALARI', 'PLA', [(7,12,12),(8,12,68),(10,12,124),(11,12,164),(15,12,204)]),
    ('04_TUTUCU_VE_BAGLANTILAR', 'PLA', [
        (16,12,12),(13,124,12),(19,178,12),(14,12,108),
        (17,115,112),(17,155,112),(17,195,112),
        (20,12,202),(20,66,202),(20,120,202),(20,174,202),
        (21,178,64),(21,216,64),(22,12,162),(22,52,162),
        (9,12,84),(9,36,84),(12,60,84)]),
    ('05_YUMUSAK_PEDLER', 'TPU', [(18,20,20),(18,70,20),(18,120,20)]),
    ('06_PLASTIK_BURCLAR', 'PLA', [(23,20,20),(24,45,20),(24,70,20),(25,20,50),(25,45,50),(25,70,50)]),
]

def font(size):
    return ImageFont.truetype('C:/Windows/Fonts/arial.ttf', size)

def preview(path, name, material, entries):
    im = Image.new('RGB', (1000,1150), '#f4f5f2')
    d = ImageDraw.Draw(im)
    d.text((48,24), name.replace('_',' '), font=font(28), fill='#153f47')
    d.text((48,65), f'{material} | 256 x 256 mm | {len(entries)} parça | üst görünüş', font=font(21), fill='#314c53')
    scale=3.25
    def pt(x,y): return (70+x*scale,960-y*scale)
    d.rectangle([pt(0,BED),pt(BED,0)], fill='white', outline='#44616a', width=2)
    for n in range(0,257,32):
        d.line([pt(n,0),pt(n,BED)], fill='#e8eceb')
        d.line([pt(0,n),pt(BED,n)], fill='#e8eceb')
    for e in entries:
        m=e['mesh']
        for face in m.faces:
            d.polygon([pt(*v[:2]) for v in m.vertices[face]], fill='#41878a')
        b=m.bounds
        label=e['id'].split('-')[1] + '.' + str(e['copy'])
        x,y=pt((b[0,0]+b[1,0])/2,(b[0,1]+b[1,1])/2)
        if max(b[1,:2]-b[0,:2])<16:y-=30  # Keep labels off small bushes.
        d.rounded_rectangle((x-25,y-12,x+25,y+12),4,fill='#fff5d8')
        d.text((x,y),label,font=font(15),fill='#253e43',anchor='mm')
    d.text((70,988),'Etiket: parça numarası.kopya | Yerleşim gerçek STL izdüşümüdür.',font=font(20),fill='#314c53')
    d.text((70,1025),'Destek ve brim alanını dilimleyicide kontrol et. G-code içermez.',font=font(20),fill='#314c53')
    im.save(path)

def combine_3mf(entries, path, material):
    ET.register_namespace('',NS)
    model=ET.Element(Q+'model', {'unit':'millimeter', 'xmlns:slic3rpe':'http://schemas.slic3r.org/3mf/2017/06'})
    ET.SubElement(model,Q+'metadata',name='slic3rpe:Version3mf').text='1'
    resources=ET.SubElement(model,Q+'resources'); build=ET.SubElement(model,Q+'build')
    config=ET.Element('config')
    for oid,e in enumerate(entries,1):
        with zipfile.ZipFile(SOURCE/'3MF'/f"{e['id']}.3mf") as z:
            src=ET.fromstring(z.read('3D/3dmodel.model'))
            cfg=ET.fromstring(z.read('Metadata/Slic3r_PE_model.config'))
            obj=copy.deepcopy(src.find(Q+'resources').find(Q+'object'))
            obj.set('id',str(oid)); obj.set('name',e['name'])
            for v in obj.iter(Q+'vertex'):
                rotated=np.array(e.get('rotation',np.eye(3))) @ np.array([float(v.get(k)) for k in ('x','y','z')])
                for i,k in enumerate(('x','y','z')):
                    v.set(k,str(rotated[i]+e['translation'][i]))
            resources.append(obj)
            oc=copy.deepcopy(cfg.find('object'));oc.set('id',str(oid))
            oc.find("metadata[@key='name']").set('value',e['name'])
            config.append(oc)
            ET.SubElement(build,Q+'item',objectid=str(oid))
            package_headers={n:z.read(n) for n in ('[Content_Types].xml','_rels/.rels')}
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for n,data in package_headers.items():z.writestr(n,data)
        z.writestr('3D/3dmodel.model',ET.tostring(model,encoding='utf-8',xml_declaration=True))
        z.writestr('Metadata/Slic3r_PE_model.config',ET.tostring(config,encoding='utf-8',xml_declaration=True))

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    with (SOURCE/'PRINT_BOM.csv').open() as f: bom=list(csv.DictReader(f))
    ids={int(r['id'].split('-')[1]):r['id'] for r in bom}
    manifest={'revision':'LINKA L1.5 / DEC-082','bed_mm':[256,256,256],'edge_margin_mm':MARGIN,'part_gap_mm':GAP,
              'printer':'ELEGOO Centauri Carbon 2 Combo (ASM-052)',
              'status':'LAYOUT VERIFIED; SLICING AND PHYSICAL VALIDATION REQUIRED','plates':[]}
    actual=Counter()
    for name,material,layout in LAYOUTS:
        dest=OUT/name;dest.mkdir(exist_ok=True)
        entries=[]
        for placement in layout:
            number,x,y=placement[:3]
            angle=np.deg2rad(placement[3] if len(placement)>3 else 0)
            rotation=np.array([[np.cos(angle),-np.sin(angle),0],[np.sin(angle),np.cos(angle),0],[0,0,1]])
            pid=ids[number];actual[pid]+=1
            m=trimesh.load_mesh(SOURCE/'PRINT_STL'/f'{pid}.stl')
            m.vertices=m.vertices @ rotation.T
            translation=(np.array([x,y,0])-m.bounds[0]).tolist()
            m.apply_translation(translation)
            entries.append(dict(id=pid,copy=actual[pid],name=f'{pid}__{actual[pid]}',translation=translation,rotation=rotation.tolist(),mesh=m))
        # Only original solid parts in STL; modifiers remain exclusively in 3MF.
        trimesh.util.concatenate([e['mesh'] for e in entries]).export(dest/f'{name}.stl')
        combine_3mf(entries,dest/f'{name}.3mf',material)
        preview(dest/f'{name}.png',name,material,entries)
        counts=Counter(e['id'] for e in entries)
        rows='\n'.join(f'- {p}: {n} adet' for p,n in counts.items())
        notes = ('Yeni1mm kavisli iç astarlar: yalnız TPU ile ayrı basılır. Eski düz silikon ped eşdeğer değildir. PLA kullanma. TPU profili, destek sökümü, yapıştırma ve sertlik fiziksel doğrulama gerektirir.' if material!='PLA' else
            'PLA; 0,4 mm nozzle kayıtlıdır. Mevcut 3MF nesne ayarları ve yerel dolgu bölgeleri korunmuştur. Sıcaklık, hız ve katman yüksekliğini kendi doğrulanmış filament/yazıcı profilinden seç.')
        (dest/'BASLAMADAN_ONCE.md').write_text(f'''# {name} — yalnız bu tablayı bas

{len(entries)} parça. Bu paketi **bir kez** bas; gerekli kopyalar dosyanın içinde yerleştirilmiştir.

{rows}

{notes}

## Açılacak dosya

- Önce `{name}.3mf` dosyasını aç: parçalar ve kopyalar 256 × 256 mm tablaya yerleşiktir.
- STL yalnız alternatif geometridir. **3MF ve STL'yi birlikte basma.** STL yerel dolgu ayarlarını taşımaz.
- 3MF yerel dolgu bilgileri Prusa/Slic3r biçimindedir. ELEGOO veya başka dilimleyicide modifier tanınmasını kontrol et; tanınmayan bölgeleri ek basılacak parça sayma. Gerekirse modelin kök/uç bölgelerinde ayarları elle oluştur.
- Otomatik yerleştirmeyi kullanmadan önce mevcut yerleşimi kontrol et. Nesnelerin bağımsız kopyalar olduğunu koru. Tüm nesneler aynı anda katman katman basılacak; nesne sıralı baskı kullanma.
- 8 mm kenar payı ve en az 8 mm parçalar arası boşluk ayrıldı. Destek/brim bu boşluğu aşarsa parçaları yeniden yerleştir veya bu tablayı iki işe ayır. Yazıcının dışlama alanları profilinden ayrıca kontrol edilmeli.
- Mevcut CAD baskı yönleri korundu. Taban, tabla, rotor, bilek, avuç ve cepli parçaların alt yüzeyleri için destek ihtiyacını dilim önizlemesinde incele. İnce/dik bağlarda brim gerekebilir; tüm parçalar desteksiz ilan edilmemiştir.
- G-code yoktur; bu dosya doğrulanmış ELEGOO makine profili değildir. Dilimleyicide kendi yazıcını seç ve önizlemeyi kontrol et.

LINKA L1.5 / DEC-082: parmak10mm uzadı,49mm geniş kepçe ve1,6mm duvar eklendi. L1-18 artık1mm kavisli TPU astardır. L1.4 sonrası yalnız L1-17 veL1-18 değişti. Parmaklar ağız yukarı basılır; dış yüzeyde tabladan destek ve5mm brim gerekir. Delik ve iç yüzey destek izleri kontrol edilir. Önceki değişiklik kaydı: L1.3 sonrası yalnız üç L1-17 parmağın pivot deliği büyüdü; L1-23/24/25 plastik burçlar eklendi. Eski parmakla yeni burcu karıştırma. Diğer eski parçalar korunur. Burçlar için100% dolgu, en az3 duvar hedefi ve delik ekseni dik baskı; dilim önizlemesinde kesintisiz duvarlar kontrol edilir. Dar delikleri zorlayarak vida sokma. Plastik dirsek burçlarının ezilme/sünme davranışı ve sıkma ayarı doğrulanmadı; ilk kullanım yalnız uyum/yüksüz denemedir. Montaj uyumu ve fiziksel dayanım henüz doğrulanmadı. Vida, insert, motor ve rulmanlar bu baskı listesinin dışında.
''',encoding='utf-8')
        plate={'name':name,'material':material,'instances':[dict(id=e['id'],copy=e['copy'],translation=e['translation'],rotation=e['rotation'],bounds=e['mesh'].bounds.tolist()) for e in entries]}
        manifest['plates'].append(plate)
        with zipfile.ZipFile(OUT/f'{name}.zip','w',zipfile.ZIP_DEFLATED) as z:
            for f in sorted(dest.iterdir()):z.write(f,f.name)
    assert actual==Counter({r['id']:int(r['count']) for r in bom})
    (OUT/'TABLA_LISTESI.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    (OUT/'TABLA_LISTESI.md').write_text('''# LINKA L1.5 — ayrı baskı tablaları

256 × 256 mm kayıtlı tabla için **5 PLA tablası + 1 isteğe bağlı yumuşak ped tablası**. Toplam35 PLA parça ve3 ped. DEC-081 üç parmağı yeniler ve6 plastik burç ekler. L1.4 basılıysa04A kepçe parmaklar ve05 TPU astarlar yenilenir. L1.3 basılıysa ayrıca06 burçları bas; tam04 ile04A birlikte basılmaz. Kablo çıkıntısı7×3,9×5,5mm ölçüldü; gövdedeki konumu doğrulanmadan yeni tabanı basma. Önceki revizyon değişiklikleri ayrıca geçerlidir.

| ZIP | İçerik | Adet |
|---|---|---:|
| [01_TABAN.zip](01_TABAN.zip) | Taban, rotor, bilye kafesi | 3 |
| [02_MOTOR_TABLASI.zip](02_MOTOR_TABLASI.zip) | Motor tablası, iki tutucu yarımı | 3 |
| [03_KOL_PLAKALARI.zip](03_KOL_PLAKALARI.zip) | Üst kol çifti, önkol çifti, bağlantı çubuğu | 5 |
| [04_TUTUCU_VE_BAGLANTILAR.zip](04_TUTUCU_VE_BAGLANTILAR.zip) | Avuç, bilek, üç parmak, krank, makara, bağlar ve kapaklar | 18 |
| [05_YUMUSAK_PEDLER.zip](05_YUMUSAK_PEDLER.zip) | 1mm kavisli TPU astarlar; eski düz ped kullanılmaz | 3 |
| [06_PLASTIK_BURCLAR.zip](06_PLASTIK_BURCLAR.zip) | 1 uzun +2 kısa dirsek burcu,3 parmak burcu | 6 |

Her ZIP ayrı bir baskı işidir. İçindeki 3MF **veya** alternatif STL'yi kullan; ikisini birlikte basma. Kopyalar hazır, elle çoğaltma gerekmez. PNG dosyası numaralı tabla haritasıdır. Malzeme ve destek notları her ZIP içindedir.

3MF modifier uyumluluğu, makine profili, destek/brim ve fiziksel montaj kullanıcı dilimleyicisinde doğrulanmalı. G-code değildir. Düzen mevcut STL/3MF baskı yönlerini korur.
''',encoding='utf-8')
    sheet=Image.new('RGB',(1500,1150),'#f4f5f2')
    for i,(name,_,_) in enumerate(LAYOUTS):
        im=Image.open(OUT/name/f'{name}.png');im.thumbnail((500,575))
        sheet.paste(im,((i%3)*500,(i//3)*575))
    sheet.save(OUT/'TUM_TABLALAR.png')
    print(json.dumps({'plates':len(LAYOUTS),'parts':sum(actual.values()),'output':str(OUT)}))

if __name__=='__main__':main()
