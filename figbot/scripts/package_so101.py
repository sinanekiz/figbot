"""Pin upstream SO-101 geometry, orient rigidly and package one follower on 256 mm beds.

No mesh repair, hole enlargement, scaling, firmware or motor actions are performed.
"""
import hashlib
import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont
from scripts.project_paths import ROOT, CURRENT, PRINTS, CAD, ARCHIVE

VENDOR = ROOT / 'references/vendor/so101'
REVISION = 'DEC-088'
COMMIT = 'eecbe3e0a9ebb23e25ad7b2759b03884c6660903'
BED = 256
MARGIN = 8
STAGE = ROOT / '.tmp_artifact/so101_delivery'
# Label, original filename stem, X and Y minimum corners, all millimetres.
PLATES = {
    '00_MOTOR_UYUM_DENEMESI': [
        ('G0', 'Gauge_0', 12, 12), ('G1', 'Gauge_tight_1', 80, 12)],
    '01_TABAN_OMUZ': [
        ('P01', 'Base_SO101', 12, 12),
        ('P02', 'Base_motor_holder_SO101', 135, 12),
        ('P03', 'Motor_holder_SO101_Base', 135, 76),
        ('P04', 'Rotation_Pitch_SO101', 12, 98)],
    '02_KOL_BILEK': [
        ('P05', 'Upper_arm_SO101', 12, 12),
        ('P06', 'Under_arm_SO101', 12, 91),
        ('P07', 'Motor_holder_SO101_Wrist', 173, 12),
        ('P08', 'Wrist_Roll_Pitch_SO101', 173, 90)],
    '03_KISKAC': [
        ('P09', 'Wrist_Roll_Follower_SO101', 12, 12),
        ('P10', 'Moving_Jaw_SO101', 12, 80),
        ('P11', 'WaveShare_Mounting_Plate_SO101', 136, 12)],
}
LABELS = {
    'P01': 'Taban', 'P02': 'Taban motor tutucusu', 'P03': 'Omuz motor tutucusu',
    'P04': 'Omuz döner bağlantısı', 'P05': 'Üst kol', 'P06': 'Önkol',
    'P07': 'Bilek motor tutucusu', 'P08': 'Bilek eğim bağlantısı',
    'P09': 'Sabit çene / kıskaç gövdesi', 'P10': 'Hareketli çene',
    'P11': 'Waveshare kart tablası', 'G0': 'Nominal motor mastarı', 'G1': 'Sıkı motor mastarı',
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def source_path(name):
    if name.startswith('Gauge_'):
        return VENDOR / 'STL/Gauges' / (name + '.STL')
    return VENDOR / 'STL/SO101/Individual' / (name + '.stl')


def verify_sources():
    manifest = json.loads((VENDOR/'SOURCE_MANIFEST.json').read_text())
    assert manifest['commit'] == COMMIT
    for item in manifest['files']:
        assert sha(VENDOR/item['path']) == item['sha256'], item['path']
    return manifest


def placed_mesh(name, x, y):
    mesh = trimesh.load_mesh(source_path(name))
    transform = np.eye(4)
    if not name.startswith('Gauge_'):
        rotations = json.loads((ROOT/'manufacturing/so101_orientations.json').read_text())
        transform = np.array(rotations[name]['rotation'])
    assert np.allclose(transform[:3,:3].T @ transform[:3,:3], np.eye(3), atol=1e-7)
    assert np.isclose(np.linalg.det(transform[:3,:3]), 1)
    mesh.apply_transform(transform)
    delta = np.array([x, y, 0]) - mesh.bounds[0]
    mesh.apply_translation(delta)
    transform[:3,3] += delta
    return mesh, transform


def check_plate(meshes):
    for name, mesh in meshes.items():
        assert mesh.is_watertight and mesh.is_winding_consistent, name
        assert np.isfinite(mesh.vertices).all() and mesh.volume > 0, name
        assert np.all(mesh.bounds[0,:2] >= MARGIN-1e-5), name
        assert np.all(mesh.bounds[1,:2] <= BED-MARGIN+1e-5), name
        assert abs(mesh.bounds[0,2]) < 1e-5 and mesh.bounds[1,2] < BED, name
    keys = list(meshes)
    for i, a in enumerate(keys):
        for b in keys[i+1:]:
            aa, bb = meshes[a].bounds, meshes[b].bounds
            separations = np.maximum(bb[0,:2]-aa[1,:2], aa[0,:2]-bb[1,:2])
            assert separations.max() >= 8, (a, b, separations.tolist())


def write_3mf(path, meshes):
    ns = 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
    ET.register_namespace('', ns)
    def tag(n): return '{'+ns+'}'+n
    model = ET.Element(tag('model'), unit='millimeter', attrib={'{http://www.w3.org/XML/1998/namespace}lang':'en-US'})
    resources = ET.SubElement(model, tag('resources'))
    build = ET.SubElement(model, tag('build'))
    for i, (name, mesh) in enumerate(meshes.items(), 1):
        obj = ET.SubElement(resources,tag('object'),id=str(i),type='model',name=name)
        element = ET.SubElement(obj,tag('mesh'))
        vertices = ET.SubElement(element,tag('vertices'))
        for x,y,z in mesh.vertices:
            ET.SubElement(vertices,tag('vertex'),x=f'{x:.6f}',y=f'{y:.6f}',z=f'{z:.6f}')
        triangles = ET.SubElement(element,tag('triangles'))
        for a,b,c in mesh.faces:
            ET.SubElement(triangles,tag('triangle'),v1=str(a),v2=str(b),v3=str(c))
        ET.SubElement(build,tag('item'),objectid=str(i))
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('3D/3dmodel.model', ET.tostring(model,encoding='utf-8',xml_declaration=True))
        z.writestr('[Content_Types].xml','<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
        z.writestr('_rels/.rels','<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')


def preview(path, title, meshes):
    scale=3;left=60;top=105
    img=Image.new('RGB',(920,1120),'#f8faf9');d=ImageDraw.Draw(img)
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22)
    small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',17)
    d.text((left,24),title.replace('_',' '),font=font,fill='#123d3a')
    d.text((left,58),'256 × 256 mm • %100 ölçek • Üstten görünüş',font=small,fill='#384b4b')
    def xy(x,y):return (left+x*scale,top+(BED-y)*scale)
    d.rectangle([xy(0,BED),xy(BED,0)],fill='#e9efed',outline='#56716b',width=2)
    for v in range(0,257,16):
        d.line([xy(v,0),xy(v,BED)],fill='#cedbd6');d.line([xy(0,v),xy(BED,v)],fill='#cedbd6')
    for index,(name,mesh) in enumerate(meshes.items()):
        triangles=mesh.triangles
        for j in np.argsort(triangles[:,:,2].mean(axis=1)):
            t=triangles[j];shade=int(105+65*max(0,mesh.face_normals[j,2]))
            d.polygon([xy(v[0],v[1]) for v in t],fill=(int(shade*.38),shade,int(shade*.93)))
        code=name.split('_')[0]
        x,y=mesh.bounds[0,:2]
        px,py=xy(x,y)
        d.text((px,py+5),code,font=small,fill='#123d3a')
    y=top+BED*scale+45
    for name,mesh in meshes.items():
        code=name.split('_')[0]
        d.text((left,y),f'{code} · {LABELS[code]} · '+ ' × '.join(f'{v:.1f}' for v in mesh.extents)+' mm',font=small,fill='#263d39');y+=30
    img.save(path)


def render_assembly(cad):
    """Build an inspection scene from official URDF visual origins; no simulation claims."""
    tree=ET.parse(cad/'URDF/so101_new_calib.urdf').getroot()
    links={link.attrib['name']:link for link in tree.findall('link')}
    def origin(element):
        o=element.find('origin')
        if o is None:return np.eye(4)
        xyz=[float(v) for v in o.get('xyz','0 0 0').split()]
        rpy=[float(v) for v in o.get('rpy','0 0 0').split()]
        t=trimesh.transformations.euler_matrix(*rpy);t[:3,3]=xyz;return t
    transforms={'base_link':np.eye(4)}
    joints=list(tree.findall('joint'))
    while joints:
        old=len(joints)
        for joint in joints[:]:
            parent=joint.find('parent').get('link');child=joint.find('child').get('link')
            if parent in transforms:
                transforms[child]=transforms[parent]@origin(joint);joints.remove(joint)
        assert len(joints)<old, 'URDF contains unresolved links'
    scene=trimesh.Scene()
    for name,link in links.items():
        for i,visual in enumerate(link.findall('visual')):
            spec=visual.find('geometry/mesh')
            if spec is None:continue
            src=cad/'URDF'/spec.get('filename')
            assert src.is_file(),str(src)
            mesh=trimesh.load_mesh(src)
            mesh.apply_scale([float(v) for v in spec.get('scale','1 1 1').split()])
            mesh.apply_transform(transforms[name]@origin(visual))
            motor='sts3215' in src.name
            mesh.visual.face_colors=[55,65,70,255] if motor else [50,151,139,255]
            scene.add_geometry(mesh,geom_name=f'{name}_{i}')
    scene.export(cad/'SO101_MONTAJ.glb')
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    fig=plt.figure(figsize=(8,8),facecolor='#f5f7f5');ax=fig.add_subplot(111,projection='3d')
    for mesh in scene.geometry.values():
        colors=mesh.visual.face_colors[:,:3]/255
        shade=.55+.45*np.abs(mesh.face_normals@np.array([.3,-.4,.866]))
        ax.add_collection3d(Poly3DCollection(mesh.triangles,facecolors=colors*shade[:,None],linewidths=0,rasterized=True))
    bounds=scene.bounds;mid=bounds.mean(axis=0);span=scene.extents.max()*.56
    ax.set_xlim(mid[0]-span,mid[0]+span);ax.set_ylim(mid[1]-span,mid[1]+span);ax.set_zlim(mid[2]-span,mid[2]+span)
    ax.set_box_aspect([1,1,1]);ax.view_init(elev=22,azim=-50);ax.set_axis_off()
    ax.set_title('SO-101 follower | Resmi URDF referans montajı',fontsize=13)
    fig.savefig(cad/'MONTAJ_ONIZLEME.png',dpi=150,bbox_inches='tight');plt.close(fig)
    return len(scene.geometry)


NOTES = '''# SO-101 — tek follower kolunun baskı paketi

DEC-088 · Resmi SO-101 geometrisi · 256 × 256 × 256 mm tabla · %100 ölçek, mm.

**Sıra:** 00 motor uyum mastarları; 01 taban/omuz; 02 kol/bilek; 03 kıskaç.
01–03 toplam 11 parça, her parçadan bir adet. 00'daki iki parça deneme mastarıdır, kola takılmaz.
P11 yalnız Waveshare Bus Servo Adapter (A) kartının tablasıdır; farklı kart alırsan bunu basma.

Her tabla klasöründeki TABLA.3mf dosyasını aç. Aynı klasördeki TABLA.stl alternatifidir;
ikisini birlikte yükleme. TEK_PARCA klasörü yalnız yeniden tek parça basmak içindir.
3MF geometri ve yerleşim içerir, yazıcı/filament/sıcaklık/destek profili içermez. G-code değildir.
Mevcut ELEGOO Centauri Carbon 2 Combo, 0,4 mm profilini seç; tabla koordinatlarını koru.

Başlangıç: 0,20 mm katman, %20 dolgu. PLA+ upstream tercihi; mevcut PLA'nın sıcaklık ve
akış değerlerini kendi kalibre edilmiş profilinden kullan. 3 duvar yerel başlangıç tercihidir,
dayanım onayı değildir. Destekleri gerektiği yerlerde etkinleştir; yatay vida deliklerinde
destek engelle. 45°'den daha dik yüzeylerde gereksiz destek oluşturma. Dilim önizlemesinde
ilk katmanı, havada kalan yüzeyleri ve çıkarılabilir destekleri incele. Otomatik ölçekleme yapma.

SAMM 22414 / MP03422 ST3215 12 V ürününün resmi SO-101 follower ile katalog uyumu teyit edildi.
Bu ürün için motorları beklemeden 01–03 baskılarına başlanabilir. 00 mastarları isteğe bağlı
ölçü kontrolüdür. Katalog ölçüleri baskı toleransını garanti etmez; motor başlığı, vida ve yuva
fiziksel uyumu henüz test edilmedi. Ayrıntı: SAMM_MOTOR_TEYIDI.md.
Gövdede insert için delik büyütme veya sıcak insert uygulaması yapma.

## Elimizdeki vidalar

Ana montaj ihtiyacı 24 adet M2×6 ve 50 adet M3×6, ayrıca 11 metal motor başlığıdır.
Önce motor paketindeki uygun vidaları/başlıkları ve mevcut M2×6 / M3×6 stokunu say.
Waveshare gövde montajı sivri uçlu paket vidalarını kullanır; mevcut M2×6 makine vidası aynı
diş biçimi kabul edilmez. Gövde için paketin uygun vidasını kullan.
Motor merkez vidasında paketin kendi uygun başlı vidasını kullan. Elindeki M3 DIN912 başı
paketteki alçak baştan yüksek olabilir: kapak/kol açıklığında sürtme varsa zorlayarak sıkma.
Sadece diş çapının eşleşmesi baş yüksekliğinin ve vida ucunun uyduğunu kanıtlamaz.
Eski M2×8/M3×8/M3×10'u M2×6/M3×6 yerine rastgele kullanma; gövdeye fazla girebilir.
Pirinç insertler bu resmi mekanizmanın parçası değildir; mevcut stoğu başka bağlantılar için sakla.
Kartı ve tabanı masaya/şasiye sabitleme sarfı yukarıdaki ana eklem sayısına dahil değildir.

## Kaynak ve sınırlar

[Orijinal CAD ve baskı yönergeleri](https://github.com/TheRobotStudio/SO-ARM100).
[Resimli montaj kılavuzu](https://huggingface.co/docs/lerobot/so101).
Kaynak commit eecbe3e0a9ebb23e25ad7b2759b03884c6660903, Apache-2.0.
Delik, motor yuvası veya kritik ölçüler değiştirilmedi. Yalnız rijit dönüş ve tabla yerleşimi
uygulandı. Montaj STEP ve URDF GUNCEL/CAD'dedir; montaj STEP/GLB/URDF baskı dosyası değildir.
URDF görsel referanstır: upstream notuna göre taban çarpışma geometrisi ve kıskaç kontrol
eşlemesi eksiktir. Çarpışmasız hareket, fiziksel dayanım, incir kavrama ve taşıma kapasitesi
bu dijital kontrollerle doğrulanmış değildir. Bu standart kıskaç henüz incire özel kepçe değildir.
Eski LINKA baskıları bu kolla birleştirilmez; önceki dosyalar ARSIV/ESKI_SURUMLER.zip içindedir.
Eski UNO/PCA9685 uygulaması bu bus servo kolu çalıştıracak yazılım olarak kabul edilmez.
'''


def build():
    manifest=verify_sources()
    # Only task-owned staging directory is replaced.
    assert STAGE.resolve().is_relative_to((ROOT/'.tmp_artifact').resolve())
    if STAGE.exists():shutil.rmtree(STAGE)
    prints=STAGE/'BASKI';cad=STAGE/'CAD';prints.mkdir(parents=True);cad.mkdir()
    audit=[]
    for plate,items in PLATES.items():
        out=prints/plate;out.mkdir();(out/'TEK_PARCA').mkdir()
        meshes={}
        for code,name,x,y in items:
            mesh,transform=placed_mesh(name,x,y)
            source=trimesh.load_mesh(source_path(name))
            assert np.isclose(mesh.volume,source.volume,rtol=1e-6)
            assert len(mesh.faces)==len(source.faces)
            key=code+'_'+name;meshes[key]=mesh
            individual=mesh.copy();individual.apply_translation(-individual.bounds[0]);individual.export(out/'TEK_PARCA'/(key+'.stl'))
            audit.append(dict(code=code,name=name,label=LABELS[code],plate=plate,
                              source_sha256=sha(source_path(name)),faces=len(mesh.faces),
                              volume_mm3=float(mesh.volume),bounds_mm=mesh.bounds.tolist(),
                              transform=transform.tolist(),watertight=bool(mesh.is_watertight)))
        check_plate(meshes)
        write_3mf(out/'TABLA.3mf',meshes)
        trimesh.util.concatenate(list(meshes.values())).export(out/'TABLA.stl')
        preview(out/'ONIZLEME.png',plate,meshes)
        (out/'OKU.md').write_text(f'# {plate}\n\nTABLA.3mf veya alternatif TABLA.stl; ikisini birlikte açma.\n\n'+
            '\n'.join(f'- {code}: {LABELS[code]} — 1 adet' for code,_,_,_ in items)+'\n\nÖlçek %100. Ayarlar için ../ONCE_BUNU_OKU.md.\n',encoding='utf-8')
        shutil.copy2(VENDOR/'LICENSE',out/'LICENSE')
        (out/'KAYNAK.txt').write_text('TheRobotStudio/SO-ARM100, Apache-2.0\nhttps://github.com/TheRobotStudio/SO-ARM100\nCommit: '+COMMIT+'\nFIGBOT changes: rigid print orientation and plate layout only.\n',encoding='utf-8')
        with zipfile.ZipFile(prints/(plate+'.zip'),'w',zipfile.ZIP_DEFLATED) as z:
            for f in out.rglob('*'):
                if f.is_file():z.write(f,f.relative_to(prints))
    (prints/'ONCE_BUNU_OKU.md').write_text(NOTES,encoding='utf-8')
    for destination in [prints,cad]:
        shutil.copy2(ROOT/'manufacturing/so101_samm_check.md',destination/'SAMM_MOTOR_TEYIDI.md')
    write_json(prints/'TABLA_LISTESI.json',audit)
    shutil.copytree(VENDOR/'STEP/SO101',cad/'STEP')
    # Remove non-selected board option from current delivery, keep vendor originals.
    alternate=cad/'STEP/Seeedstudio_Mounting_Plate_SO101.step'
    if alternate.exists():alternate.unlink()
    shutil.copytree(VENDOR/'Simulation/SO101',cad/'URDF')
    shutil.copytree(VENDOR/'STL/SO101/Individual',cad/'ORIJINAL_STL')
    for file in ['LICENSE','SOURCE_MANIFEST.json']:
        shutil.copy2(VENDOR/file,cad/file)
    visual_count=render_assembly(cad)
    write_json(cad/'VALIDATION.json',dict(revision=REVISION,upstream_commit=COMMIT,
        geometry_changed=False,main_part_count=11,gauges=2,bed_mm=[256]*3,
        source_hashes_verified=len(manifest['files']),plate_bounds_and_separation_pass=True,
        rigid_transforms_volume_and_faces_pass=True,watertight_pass=True,
        urdf_visual_meshes=visual_count,physical_approval=False,slicer_toolpath_verified=False,
        moving_jaw_note='Original negative-volume enclosed cavity preserved, not discarded by mesh splitting.'))
    (cad/'OKU.md').write_text(NOTES,encoding='utf-8')
    from scripts.publish_so101_slicing import preserve_current
    if preserve_current(prints):
        validation=json.loads((cad/'VALIDATION.json').read_text(encoding='utf-8'))
        validation.update(slicer_toolpath_verified=True,slicer_revision='DEC-089')
        write_json(cad/'VALIDATION.json',validation)
    return audit


def archive_and_replace():
    roots=[PRINTS,CAD]
    for p in roots:
        assert p.resolve().is_relative_to(CURRENT.resolve()) and p.name in {'BASKI','CAD'}
    # Preserve all superseded current CAD and prints, then verify every byte before deletion.
    old=[p for root in roots for p in root.rglob('*') if p.is_file()]
    shopping=CURRENT/'ALISVERIS'
    obsolete_shopping=[p for p in shopping.rglob('*') if p.is_file() and not p.name.startswith('SO101_')]
    old += obsolete_shopping
    old += [p for p in [CURRENT/'SURUM.json',CURRENT/'BASLA_BURADAN.md'] if p.exists()]
    prefix='SO101_GECIS_ONCESI/'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'/'
    hashes={p.relative_to(CURRENT).as_posix():sha(p) for p in old}
    with zipfile.ZipFile(ARCHIVE,'a',zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as z:
        for p in old:z.write(p,prefix+p.relative_to(CURRENT).as_posix())
        z.writestr(prefix+'SHA256.json',json.dumps(hashes,indent=2))
    with zipfile.ZipFile(ARCHIVE) as z:
        for rel,digest in hashes.items():assert hashlib.sha256(z.read(prefix+rel)).hexdigest()==digest
    for p in obsolete_shopping:
        assert p.resolve().is_relative_to(shopping.resolve())
        p.unlink()
    for p in sorted(shopping.rglob('*'),key=lambda f:len(f.parts),reverse=True):
        if p.is_dir() and not any(p.iterdir()):p.rmdir()
    for p in roots:
        if p.exists():shutil.rmtree(p)
        shutil.copytree(STAGE/p.name,p)
    write_json(CURRENT/'SURUM.json',dict(revision=REVISION,model='SO-101 follower',upstream_commit=COMMIT,
        print_directory='GUNCEL/BASKI',cad_directory='GUNCEL/CAD',physical_approval=False,
        archive_prefix=prefix,previous_files_verified=len(hashes)))
    if (PRINTS/'DILIMLEME_KONTROL.json').exists():
        status=json.loads((CURRENT/'SURUM.json').read_text(encoding='utf-8'))
        status.update(slicer_revision='DEC-089',slicer_profiles_embedded=True,printer_profile='CC2 0.4')
        write_json(CURRENT/'SURUM.json',status)
    (CURRENT/'BASLA_BURADAN.md').write_text('# Güncel kol: SO-101 follower\n\n'+
        'Baskı: BASKI/ONCE_BUNU_OKU.md. SAMM 22414 katalog uyumu teyit edildi; 01–03 basılabilir. 00 isteğe bağlı mastarlar.\n\n'+
        'Alım: ALISVERIS/SO101_ALISVERIS_LISTESI.md. Altı motor sipariş edildi; masa adaptörü alındı.\n\n'+
        'CAD: resmi STEP, URDF ve referans GLB. Katalog eşlemesi SAMM 22414; teslim ve fiziksel uyum henüz ölçülmedi.\n\n'+
        'YAZILIM eski sisteme aittir; SO-101 bus servolar için uyumlu değildir. Webdeki eski LINKA görüntüsü yeni teslimi temsil etmez.\n\n'+
        'Eski baskı ve CAD dosyaları SHA256 doğrulanarak ARSIV/ESKI_SURUMLER.zip içine alındı.\n',encoding='utf-8')


def publish():
    audit=build()
    archive_and_replace()
    from scripts.build_so101_shopping import publish as publish_shopping
    publish_shopping()
    print(json.dumps({'revision':REVISION,'parts':len(audit),'plates':len(PLATES),'physical_approval':False}))


if __name__=='__main__':
    build()
