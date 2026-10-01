"""Place DEC-084 prototype meshes on the recorded 256mm bed; no CAD changes."""
import json, hashlib, zipfile, shutil
from collections import Counter
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
import numpy as np
import trimesh
from PIL import Image
from scripts.project_paths import ROOT, CAD, PRINTS, CURRENT, ARCHIVE
from scripts.package_linka_plates import preview, combine_3mf, NS, Q

REVISION='DEC-085 / TABLA-02'
REMOVED={'L1-16-PALM','L1-17-FINGER','L1-18-PAD','L1-19-SPOOL'}
NEW={
 '07_TUTUCU_MEKANIZMA':[
 ('RT-FRAME',12,12,(0,0,0)),('RT-PINION',138,12,(0,0,0)),
 ('RT-RACK',195,12,(90,0,0)),('RT-GUIDE',138,80,(0,90,0)),
 ('RT-GUIDE',165,80,(0,90,0)),
 ('RT-LINK',12,115,(90,0,0)),('RT-LINK',62,115,(90,0,0)),('RT-LINK',112,115,(90,0,0))],
 '08_KEPCELER_VE_BURCLAR':[
 *[('RT-FINGER',x,20,(0,90,0)) for x in (14,90,166)],
 *[('RT-JOINT-BUSH',20+20*i,105,(0,0,0)) for i in range(6)]]}

def archive_remove(paths):
    """Exact-path archive verification before removing obsolete print deliveries."""
    paths=[p for p in paths if p.exists()]
    if not paths:return
    files=[f for p in paths for f in (list(p.rglob('*')) if p.is_dir() else [p]) if f.is_file()]
    prefix='PRINT_BEFORE_TRIPOD/'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'/'
    hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    ARCHIVE.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(ARCHIVE,'a',zipfile.ZIP_DEFLATED,compresslevel=1) as z:
        for p in files:z.write(p,prefix+p.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(ARCHIVE) as z:
        for p in files:assert hashlib.sha256(z.read(prefix+p.relative_to(ROOT).as_posix())).hexdigest()==hashes[str(p)]
    for p in paths:
        assert p.resolve().is_relative_to(PRINTS.resolve()) and p.resolve()!=PRINTS.resolve()
        shutil.rmtree(p) if p.is_dir() else p.unlink()

def entry(pid,copy,x,y,angles,source):
    m=trimesh.load_mesh(source,process=True)
    transform=trimesh.transformations.euler_matrix(*np.radians(angles))
    m.apply_transform(transform)
    shift=np.array([x,y,0])-m.bounds[0];m.apply_translation(shift)
    assert m.is_watertight and m.is_winding_consistent,pid
    return dict(id=pid,copy=copy,name=f'{pid}__{copy}',mesh=m,rotation=transform[:3,:3].tolist(),translation=shift.tolist(),source=str(source.relative_to(ROOT)),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest())

def check(entries):
    for e in entries:
        lo,hi=e['mesh'].bounds
        assert min(lo[:2])>=8-1e-5 and max(hi[:2])<=248+1e-5,e['name']
        assert abs(lo[2])<1e-5 and hi[2]<=256,e['name']
    for i,a in enumerate(entries):
        for b in entries[i+1:]:
            aa,bb=a['mesh'].bounds,b['mesh'].bounds
            gap=np.maximum(aa[0,:2]-bb[1,:2],bb[0,:2]-aa[1,:2])
            assert np.max(gap)>=12-1e-5,(a['name'],b['name'],gap)

def geometry_3mf(entries,path):
    ET.register_namespace('',NS)
    model=ET.Element(Q+'model',unit='millimeter');res=ET.SubElement(model,Q+'resources');build=ET.SubElement(model,Q+'build')
    ET.SubElement(model,Q+'metadata',name='Title').text='FIGBOT '+REVISION+' prototype layout'
    for oid,e in enumerate(entries,1):
        obj=ET.SubElement(res,Q+'object',id=str(oid),type='model',name=e['name']);mesh=ET.SubElement(obj,Q+'mesh')
        vs=ET.SubElement(mesh,Q+'vertices');ts=ET.SubElement(mesh,Q+'triangles')
        for v in e['mesh'].vertices:ET.SubElement(vs,Q+'vertex',dict(zip(('x','y','z'),map(str,v))))
        for t in e['mesh'].faces:ET.SubElement(ts,Q+'triangle',dict(zip(('v1','v2','v3'),map(str,t))))
        ET.SubElement(build,Q+'item',objectid=str(oid))
    with zipfile.ZipFile(CAD/'3MF/L1-21-MICRO-COVER.3mf') as src:
        headers={n:src.read(n) for n in ('[Content_Types].xml','_rels/.rels')}
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for n,b in headers.items():z.writestr(n,b)
        z.writestr('3D/3dmodel.model',ET.tostring(model,encoding='utf-8',xml_declaration=True))

def package(name,entries,note,old=False):
    dest=PRINTS/name;dest.mkdir(exist_ok=True)
    trimesh.util.concatenate([e['mesh'] for e in entries]).export(dest/f'{name}.stl')
    (combine_3mf(entries,dest/f'{name}.3mf','PLA') if old else geometry_3mf(entries,dest/f'{name}.3mf'))
    preview(dest/f'{name}.png',name,'PLA',entries)
    (dest/'BASLAMADAN_ONCE.md').write_text(note+'\n\n'+ '\n'.join(f"- {p}: {n} adet" for p,n in Counter(e['id'] for e in entries).items()),encoding='utf-8')
    with zipfile.ZipFile(PRINTS/f'{name}.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(dest.iterdir()):z.write(p,p.name)
    return dict(name=name,material='PLA',instances=[{k:v for k,v in e.items() if k!='mesh'}|{'bounds':e['mesh'].bounds.tolist()} for e in entries])

BASE_NOTE='''# DEC-084 — prototip baskı yerleşimi

256 × 256 mm tabla, PLA, kayıtlı 0,4 mm nozzle. Ölçek %100. Her tablayı bir kez bas; gerekli kopyalar içeride. 3MF VEYA alternatif STL kullan, ikisini birlikte ekleme. 3MF geometri paketidir; yazıcı, destek ve dolgu profili içermez. Kendi ELEGOO profilini seç. Nesne sıralı baskı değil, katman katman tüm parçalar. G-code gönderilmedi.

Başlangıç hedefi: 0,16 mm katman, 4 duvar, %100 dolgu. İnce 1,2 mm kepçede gerçek çizgi genişliği ve kesintisiz kabuğu dilim önizlemesinde kontrol et. Yeni tablalarda en az12 mm parça aralığı var;5 mm brim kullanıldığında iki tarafta toplam10 mm ayrılır. Destek dalları bu alanı aşarsa ayrı işlere böl. Makine dışlama alanlarını kendi profilinde kontrol et. Sıcaklık ve hız için doğrulanmış PLA profilini kullan; yeni bir makine profili verilmedi.

Fiziksel uyum, destek sökümü, incir tutma ve yük dayanımı PHYSICAL VALIDATION REQUIRED. Bu yerleşim CAD ölçülerini değiştirmez. Eski firmware yeni aktarım için kalibre edilmedi.
'''

def delivery_notes():
    note='''# Güncel kol — DEC-084 prototip baskı tablaları

**Önceki LINKA kolu basılıysa yalnız07 ve08 yeni parçaları bas.** Eski üç L1-25 parmak burcunu ve iki mikro yıldız kapağını yeniden kullan. 01,02,03 ve kol bağlantıları değişmedi.

Sıfırdan tam kol için01,02,03,04,06,07,08: toplam47 PLA parça. Her numaralı tablayı bir kez bas.04 artık yalnız korunan kol bağlantılarıdır; eski avuç, makara ve parmaklar kaldırıldı.05 ve04A eski tutucuya aittir ve arşivlendi.00 uyum kuponu,01A ve02A tek-parça alternatiflerdir; tam01/02 ile birlikte basılmaz.

- 07_TUTUCU_MEKANIZMA: gövde, dişli, kremayer,2 kılavuz,3 bağlantı kolu (8 parça).
- 08_KEPCELER_VE_BURCLAR:3 ince kepçe,6 yeni küçük bağlantı burcu (9 parça).

07 gövdesi destek gerektirir;08 kepçelerinin içi yukarı yönlendirildi, dış yüzey/tabladan destek gerekir. Her iki yeni tablaya 5mm dış brim önerilir. Burç delikleri dik; küçük burçlarda destek kapalı. Dişli yıldız yuvasında ve kılavuz kanallarında otomatik desteğin temasını incele. Ayrıntılar tabla klasörlerinde.

3MF/STL ölçülü yerleşimdir, hazır yazıcı G-code'u değildir. Fiziksel doğrulama henüz yok. Nozzle0,4mm/PLA kaydı kullanıldı; profil, destek ve ince duvar takım yollarını dilim önizlemesinde kontrol et. Elle montaj/serbest hareket denenmeden motorlu kavramaya geçilmez.
'''
    note=note.replace('DEC-084','DEC-085').replace('**Önceki LINKA kolu basılıysa yalnız07 ve08 yeni parçaları bas.**','**07 ve08 dahil kol basılıysa yalnız09_CUBUK_VE_BURCLAR tablasını bas.**').replace('01,02,03 ve kol bağlantıları değişmedi.','01 ve02 değişmedi. Yeni çubuk03 yerine09 içinde; eski çubuğu kullanma.').replace('01,02,03,04,06,07,08: toplam47','01,02,03,04,06,07,08,09: toplam49')
    note+='\n\n09: bir yeni uzun çubuk ve iki plastik burç. Her uç M3×10 METAL vida +0,5mm M3 pul ile mevcut M3×4 insertine bağlanır. Omuzlu vida ve eski M4 pullar kullanılmaz. CAD/CUBUK_MAFSALI/MONTAJ.md dosyasını oku. Tutucunun bildirilen kırılganlığı bu değişiklikle giderilmedi; yüklü çalışma onayı yok.\n'
    (PRINTS/'ONCE_BUNU_OKU.md').write_text(note,encoding='utf-8')
    (PRINTS/'TABLA_LISTESI.md').write_text(note,encoding='utf-8')
    (CURRENT/'BASLA_BURADAN.md').write_text(note+'\n\nCAD: CAD/TUTUCU. Malzeme farkları: CAD/TUTUCU/MALZEME_KARSILASTIRMASI.json. Önceki alım adetleri gerçekten alındıysa yeni vida alımı öngörülmüyor; eldeki stok doğrulanmadı. Yazılım: YAZILIM; yeni tutucu kalibrasyonu yapılmadı.\n',encoding='utf-8')

def main():
    manifest=json.loads((PRINTS/'TABLA_LISTESI.json').read_text(encoding='utf-8'))
    old04=next(p for p in manifest['plates'] if p['name']=='04_TUTUCU_VE_BAGLANTILAR')
    # Snapshot only on transition; future packaging is deterministic.
    obsolete=[PRINTS/n for n in ['04A_YALNIZ_YENI_PARMAKLAR','04A_YALNIZ_YENI_PARMAKLAR.zip','05_YUMUSAK_PEDLER','05_YUMUSAK_PEDLER.zip']]
    if any(p.exists() for p in obsolete):
        from scripts.publish_current import snapshot_before_rebuild
        snapshot_before_rebuild();archive_remove(obsolete)
    retained=[]
    for e in old04['instances']:
        if e['id'] in REMOVED:continue
        m=trimesh.load_mesh(CAD/'PRINT_STL'/f"{e['id']}.stl")
        m.vertices=m.vertices@np.array(e.get('rotation',np.eye(3))).T;m.apply_translation(e['translation'])
        retained.append(dict(e,mesh=m,name=f"{e['id']}__{e['copy']}"))
    plates=[p for p in manifest['plates'] if p['name'].startswith(('01_','02_','03_','06_'))]
    old03=next(p for p in plates if p['name'].startswith('03_'))
    keep03=[]
    for e in old03['instances']:
        if e['id']=='L1-15-COUPLER':continue
        m=trimesh.load_mesh(CAD/'PRINT_STL'/f"{e['id']}.stl")
        m.vertices=m.vertices@np.array(e.get('rotation',np.eye(3))).T;m.apply_translation(e['translation'])
        keep03.append(dict(e,mesh=m,name=f"{e['id']}__{e['copy']}"))
    plates=[p for p in plates if p!=old03]
    plates.append(package(old03['name'],keep03,BASE_NOTE+'\nDEC-085: uzun çubuk09 tablasına taşındı; bu tablaya ayrıca ekleme.',old=True))
    plates.append(package('04_TUTUCU_VE_BAGLANTILAR',retained,BASE_NOTE+'\nKorunan bilek, krank, ara bağlar ve yıldız/rulman kapakları. Eski avuç/makara/parmak bu tablaya dahil değil. Önceki04 basılıysa bunları yeniden basma. Mevcut nesne modifier bilgileri bu04 3MF içinde korunur.',old=True))
    for name,layout in NEW.items():
        counts=Counter();entries=[]
        for pid,x,y,angles in layout:
            counts[pid]+=1;entries.append(entry(pid,counts[pid],x,y,angles,CAD/'TUTUCU/PROTOTIP_STL'/f'{pid}.stl'))
        check(entries)
        extra=('\nGövde mevcut düzleminde: aşağı uzanan motor/kılavuz bölümleri ilk katmandadır; geniş avuç altı için destek gerekir. Gövdeyi desteksiz basma. Kremayer/linkler yatık, dişli ekseni dik, kılavuzların vida ekseni dik. Destek yıldız cebini veya kayma yüzeylerini dolduruyorsa elle düzenle.' if name.startswith('07') else '\nKepçelerin iç bükey ağzı yukarı. Kepçelerde tabladan dış destek ve5mm brim; burçlarda destek kapalı,5mm dış brim ve%100 dolgu. Delik/brim artıklarını montaj yüzeyinde bırakma. İnce kepçeyi destekten ayırırken zorlama.')
        plates.append(package(name,entries,BASE_NOTE+extra))
    from scripts.export_standard_rod import print_plate
    plates.append(print_plate())
    plates.sort(key=lambda p:p['name'])
    out=dict(revision=REVISION,bed_mm=[256,256,256],printer='ELEGOO Centauri Carbon 2 Combo / ASM-052',status='PROTOTYPE LAYOUT; SLICING AND PHYSICAL VALIDATION REQUIRED',physical_approval=False,plates=plates)
    assert sum(len(p['instances']) for p in plates)==49
    (PRINTS/'TABLA_LISTESI.json').write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf-8')
    (CAD/'TUTUCU/PRINT_LAYOUT.json').write_text(json.dumps({'revision':REVISION,'print_layout_available':True,'physical_approval':False,'new_plates':list(NEW),'new_instances':17},indent=2),encoding='utf-8')
    sheet=Image.new('RGB',(1500,1725),'#f4f5f2')
    for i,p in enumerate(plates):
        im=Image.open(PRINTS/p['name']/(p['name']+'.png'));im.thumbnail((500,575));sheet.paste(im,((i%3)*500,(i//3)*575))
    sheet.save(PRINTS/'TUM_TABLALAR.png');delivery_notes()
    print(json.dumps({'new_plates':list(NEW)+['09_CUBUK_VE_BURCLAR'],'full_arm_parts':49}))

if __name__=='__main__':main()
