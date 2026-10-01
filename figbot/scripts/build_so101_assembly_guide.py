"""Illustrated instructions from pinned print meshes and official assembly references.

Documentation only: never changes CAD, sliced plates, calibration or motor state.
"""
import hashlib
import html
import json
import math
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np
import trimesh
from numba import njit
from PIL import Image, ImageDraw, ImageFont
from scripts.project_paths import ROOT, CURRENT, CAD, ARCHIVE
from scripts.package_so101 import PLATES, LABELS, placed_mesh, source_path, COMMIT

HF = 'https://huggingface.co/docs/lerobot/so101'
WAVE = 'https://www.waveshare.com/wiki/SO-ARM100/101_Kit_Aassembly'
VIDEO = 'https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/lerobot/'
STEPS = [
    ('Taban ve döner omuz', ['P01','P02','P04','P03'], [1], 6, 9, 'Joint1_v2.mp4',
     'M1’e iki metal başlığı tak. Motoru P01’e, P02 tutucuyu motora sabitle. P04’ü iki başlığa bağla; P03’ü yerleştir.',
     'M1 gövdesi: üstten 2 + alttan 2 küçük vida. P02: yanlardan 1 + 1 küçük vida. P04: başlıklara 4 + 4 M3×6. Kabloları taban açıklığı ve P02 kanalından geçir.'),
    ('Omuz ve üst kol', ['P05'], [2], 4, 9, 'Joint2_v2.mp4',
     'İki başlığı takılmış M2’yi omuz yuvasına üstten yerleştir. Gövdesini sabitle; P05’i iki başlığa bağla.',
     'M2 gövdesi: 4 küçük vida. P05: sağ ve sol metal başlığa 4 + 4 M3×6. Uzun parçanın kablo kanalı kablolarla aynı tarafta olsun.'),
    ('Dirsek ve önkol', ['P06'], [3], 4, 9, 'Joint3_v2.mp4',
     'İki başlıklı M3’ü P05’in uç yuvasına yerleştir. P06’yı motorun iki metal başlığına bağla.',
     'M3 gövdesi: 4 küçük vida. P06: başlıklara 4 + 4 M3×6. Kabloyu eklem arasında sıkıştırma.'),
    ('Bilek eğim motoru', ['P07'], [4], 4, 1, 'Joint4_v2.mp4',
     'P07’yi P06’ya geçir. İki başlıklı M4’ü yuvasına yerleştir ve gövdesini sabitle.',
     'M4 gövdesi: 4 küçük vida. Bu aşamada başlıkların çevre delikleri sonraki adım için boş kalır. P07’nin kablo açıklığını soket yönüyle eşleştir.'),
    ('Bilek döndürme grubu', ['P08'], [5], 2, 9, 'Joint5_v2.mp4',
     'M5’i P08’e yerleştir; yalnız tahrikli başlığını tak. P08 grubunu M4’ün iki başlığına bağla.',
     'M5 gövdesi: önden 2 küçük vida. P08 → M4 başlıkları: 4 + 4 M3×6. M5 kablosunu önce P08 açıklığından geçir; dikdörtgen açıklık M4 soket tarafına baksın.'),
    ('Kıskaç — üçüncü tabla', ['P09','P10','P11'], [6], 4, 13, 'Gripper_v2.mp4',
     'P09’u M5 başlığına bağla. M6’yı P09’a yerleştir; iki başlığını tak. P10’u başlıklara bağla.',
     'P09 → M5: 4 M3×6. M6 gövdesi: 4 küçük vida. P10: 4 + 4 M3×6. P11 sürücü kartının tablasıdır; eklem parçası değildir. Kart vidasının ölçüsünü mevcut kart/donanımla kontrol et; burada tahmin edilmedi.'),
]
ASSET_CODES = {
 'base_so101':'P01', 'base_motor_holder_so101':'P02', 'motor_holder_so101_base':'P03',
 'rotation_pitch_so101':'P04', 'upper_arm_so101':'P05', 'under_arm_so101':'P06',
 'motor_holder_so101_wrist':'P07', 'wrist_roll_pitch_so101':'P08',
 'wrist_roll_follower_so101':'P09', 'moving_jaw_so101':'P10', 'waveshare_mounting_plate':'P11'}
MOTOR_LINKS = ['base_link','shoulder_link','upper_arm_link','lower_arm_link','wrist_link','gripper_link']

def font(size, bold=False):
    return ImageFont.truetype('C:/Windows/Fonts/arial'+('bd' if bold else '')+'.ttf',size)

@njit(cache=True)
def rasterize(xy, depth, colors, width, height):
    pixels=np.empty((height,width,3),dtype=np.uint8)
    pixels[:,:,0]=241;pixels[:,:,1]=245;pixels[:,:,2]=244
    zbuf=np.full((height,width),-np.inf)
    for i in range(len(xy)):
        a,b,c=xy[i,0],xy[i,1],xy[i,2]
        den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(den)<1e-8:continue
        xmin=max(0,int(np.floor(min(a[0],b[0],c[0]))));xmax=min(width-1,int(np.ceil(max(a[0],b[0],c[0]))))
        ymin=max(0,int(np.floor(min(a[1],b[1],c[1]))));ymax=min(height-1,int(np.ceil(max(a[1],b[1],c[1]))))
        for y in range(ymin,ymax+1):
            for x in range(xmin,xmax+1):
                u=((b[1]-c[1])*(x+.5-c[0])+(c[0]-b[0])*(y+.5-c[1]))/den
                v=((c[1]-a[1])*(x+.5-c[0])+(a[0]-c[0])*(y+.5-c[1]))/den
                w=1-u-v
                if u>=-1e-8 and v>=-1e-8 and w>=-1e-8:
                    z=u*depth[i,0]+v*depth[i,1]+w*depth[i,2]
                    if z>zbuf[y,x]:
                        zbuf[y,x]=z;pixels[y,x]=colors[i]
    return pixels

def render(items, size=(1100,760), azimuth=-50, elevation=24):
    """Opaque orthographic CAD illustration, globally depth-sorted triangles."""
    az,el=math.radians(azimuth),math.radians(elevation)
    right=np.array([-math.sin(az),math.cos(az),0])
    forward=np.array([math.cos(el)*math.cos(az),math.cos(el)*math.sin(az),math.sin(el)])
    up=np.cross(forward,right)
    basis=np.stack([right,up,forward],axis=1)
    tris=np.concatenate([m.triangles@basis for m,c in items])
    colors=[]
    for m,c in items:
        shade=.48+.52*np.clip(m.face_normals@np.array([.35,-.45,.82]),0,1)
        colors.append(np.clip(np.array(c)[None,:]*shade[:,None],0,255).astype(np.uint8))
    colors=np.concatenate(colors)
    lo=tris[:,:,:2].min(axis=(0,1));hi=tris[:,:,:2].max(axis=(0,1))
    scale=min((size[0]-100)/(hi[0]-lo[0]),(size[1]-100)/(hi[1]-lo[1]))
    mid=(lo+hi)/2
    def project(v):
        p=np.asarray(v)@basis
        return np.array([size[0]/2+(p[0]-mid[0])*scale,size[1]/2-(p[1]-mid[1])*scale])
    xy=(tris[:,:,:2]-mid)*scale
    xy[:,:,0]+=size[0]/2;xy[:,:,1]=size[1]/2-xy[:,:,1]
    img=Image.fromarray(rasterize(xy,tris[:,:,2],colors,size[0],size[1]))
    return img,project

def assembly():
    tree=ET.parse(CAD/'URDF/so101_new_calib.urdf').getroot()
    def origin(e):
        o=e.find('origin')
        if o is None:return np.eye(4)
        t=trimesh.transformations.euler_matrix(*map(float,o.get('rpy','0 0 0').split()))
        t[:3,3]=list(map(float,o.get('xyz','0 0 0').split()));return t
    transforms={'base_link':np.eye(4)};pending=list(tree.findall('joint'))
    while pending:
        before=len(pending)
        for j in pending[:]:
            parent=j.find('parent').get('link');child=j.find('child').get('link')
            if parent in transforms:
                transforms[child]=transforms[parent]@origin(j);pending.remove(j)
        assert len(pending)<before
    parts={}
    for link in tree.findall('link'):
        lname=link.get('name')
        for v in link.findall('visual'):
            s=v.find('geometry/mesh')
            if s is None:continue
            path=CAD/'URDF'/s.get('filename');m=trimesh.load_mesh(path)
            m.apply_scale(list(map(float,s.get('scale','1 1 1').split())))
            m.apply_transform(transforms[lname]@origin(v))
            code=('M'+str(MOTOR_LINKS.index(lname)+1)) if 'sts3215' in path.name else next(c for k,c in ASSET_CODES.items() if path.stem.startswith(k))
            parts[code]=m
    return parts

def build(out):
    out.mkdir(parents=True,exist_ok=True)
    records=[]
    for plate,rows in list(PLATES.items())[1:]:
        sheet=Image.new('RGB',(1400,980),'white');d=ImageDraw.Draw(sheet)
        d.text((35,20),plate.replace('_',' '),font=font(32,True),fill='#173e3a')
        for i,(code,stem,x,y) in enumerate(rows):
            m,_=placed_mesh(stem,0,0)
            tile,_=render([(m,(65,174,160))],(660,355),azimuth=-55,elevation=40)
            px=35+(i%2)*695;py=90+(i//2)*425
            sheet.paste(tile,(px,py));d.text((px+15,py+355),code+' · '+LABELS[code],font=font(23,True),fill='#173e3a')
            records.append({'code':code,'stem':stem,'plate':plate,'sha256':hashlib.sha256(source_path(stem).read_bytes()).hexdigest()})
        sheet.save(out/(plate+'.png'))
    parts=assembly()
    model,proj=render([(m,(58,66,74) if k.startswith('M') else (65,174,160)) for k,m in parts.items()],(1080,1020))
    img=Image.new('RGB',(1740,1080),'#f1f5f4');img.paste(model,(330,30))
    d=ImageDraw.Draw(img)
    names=['Taban dönüşü','Omuz','Dirsek','Bilek eğimi','Bilek dönüşü','Kıskaç']
    for i,name in enumerate(names):
        code='M'+str(i+1);point=proj(parts[code].centroid)+np.array([330,30])
        left=i<3;x=12 if left else 1416;y=90+((2-i) if left else (i-3))*330
        edge=(x+310,y+35) if left else (x,y+35)
        d.line([edge,tuple(point)],fill='#d77625',width=3)
        d.ellipse((point[0]-6,point[1]-6,point[0]+6,point[1]+6),fill='#d77625')
        d.rounded_rectangle((x,y,x+310,y+72),12,fill='white',outline='#b6cfca',width=2)
        d.text((x+12,y+10),code+' · '+name,font=font(23,True),fill='#173e3a')
        d.text((x+12,y+40),'Motor ID: '+str(i+1),font=font(19),fill='#526664')
    img.save(out/'MOTOR_YERLERI.png')
    seen=set();cards=[]
    for n,(title,codes,motors,small,m3,video,brief,detail) in enumerate(STEPS,1):
        # M2 and M3 bodies sit on the already assembled neighbouring printed link.
        new=set(codes)|{'M'+str(i) for i in motors};seen|=new
        visible={k:m for k,m in parts.items() if k in seen}
        im,_=render([(m,(58,66,74) if k.startswith('M') else ((235,161,67) if k in new else (91,110,112))) for k,m in visible.items()])
        im.save(out/f'ADIM_{n:02}.png')
        cards.append(f'''<section id="adim{n}"><div class="stephead"><span>{n:02}</span><h2>{title}</h2></div>
        <p class="parts">{' + '.join(codes)} · Motor {', '.join(map(str,motors))}</p>
        <div class="grid"><img src="ADIM_{n:02}.png" alt="{title}: yeni baskılar turuncu, önceki baskılar gri, motorlar siyah"><div>
        <p>{brief}</p><p>{detail}</p><p class="hardware"><b>Bu adım:</b> {small} küçük paket vidası + {m3} M3×6.<br>M3 sayısına yeni motorun 1 merkez vidası dahildir.</p>
        <video controls preload="none" playsinline src="{VIDEO+video}"></video><a href="{VIDEO+video}">Resmî montaj videosunu ayrı aç</a></div></div></section>''')
    doc='''<!doctype html><html lang="tr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>SO-101 · Resimli montaj</title><style>
    *{box-sizing:border-box}body{margin:0;background:#eef3f1;color:#183d39;font:18px/1.6 system-ui,sans-serif}main{max-width:1250px;margin:auto;padding:30px}h1{font-size:42px;line-height:1.15}h2{font-size:28px}a{color:#086d63}section,.intro{background:white;padding:28px;margin:24px 0;border-radius:20px}img{max-width:100%;border-radius:12px}video{width:100%;background:#172521;border-radius:12px;min-height:220px}nav{display:flex;gap:12px;flex-wrap:wrap}nav a{padding:8px 15px;background:#daeee6;border-radius:10px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:25px;align-items:start}.grid>img{position:sticky;top:10px}.parts{color:#086d63;font-weight:700}.stephead{display:flex;gap:18px;align-items:center}.stephead span{font-size:40px;color:#c57628;font-weight:800}.hardware,.note{background:#fff2dc;padding:16px;border-radius:10px}small{color:#576b65}li{margin:10px 0}@media(max-width:800px){.grid{grid-template-columns:1fr}main{padding:12px}h1{font-size:32px}.grid>img{position:static}}@media print{video,nav{display:none}section{break-inside:avoid}.grid{grid-template-columns:1fr 1fr}body{font-size:12px}}
    </style><main><small>FIGBOT / SO-101 FOLLOWER / MONTAJ-1</small><h1>Bastığın parçalarla<br>adım adım montaj</h1>
    <p>İlk iki tabla: taban → omuz → dirsek → bilek. Üçüncü tabla: kıskaç ve kart tablası.</p>
    <nav><a href="#parcalar">Parçaları tanı</a><a href="#vidalar">Vida ve başlık</a>'''+''.join(f'<a href="#adim{i}">{i}. adım</a>' for i in range(1,7))+'''</nav>
    <div class="intro"><b>Başlamadan:</b> Adaptör ve USB çıkarılmış olsun. Destek malzemelerini deliklerden temizle; motoru veya başlığı zorlayarak içeri bastırma. Gövde vidalarını el tornavidasıyla, plastik ezilmeye başlamadan durarak sık.
    <p>Motorları henüz zincirleme bağlamadan tek tek ID 1–6 olarak tanımla ve etiketle. Test yazılımındaki ID atama alanını yalnız tek motor bağlıyken kullan. Mekanik montaj sırasında enerji kapalı kalır.</p>
    <p class="note">270° / maksimum hızlı tek-motor denemesi, monte edilmiş kolun hareket sınırı değildir. İlk çalıştırmadan önce SO-101 eklem kalibrasyonu ve çarpışmasız sınırlar gerekir.</p></div>
    <section id="parcalar"><h2>1. Parçaları numaralarıyla ayır</h2><p>Bu görseller doğrudan baskı STL dosyalarından üretildi. Parçalar eşit ölçekte gösterilmiyor. G0/G1 mastarları kola takılmaz.</p>
    <img src="01_TABAN_OMUZ.png" alt="Birinci tabla P01-P04"><img src="02_KOL_BILEK.png" alt="İkinci tabla P05-P08"><details><summary>Üçüncü tabla: P09–P11</summary><img src="03_KISKAC.png"></details></section>
    <section id="vidalar"><h2>2. Hangi vida nereye?</h2><ul>
    <li><b>Küçük, sivri paket vidaları → motor gövdesi.</b> Basılı parçadan geçip motorun gövde montaj deliklerine girer. Resmî rehber bunları M2×6 olarak adlandırır; elindeki motor paketinin gövde vidalarını kullan, rastgele metrik M2 ile değiştirme.</li>
    <li><b>M3×6 → metal başlık.</b> Plastik kolun deliklerinden geçer ve metal başlığın çevresindeki dişli deliklere tutunur. Pirinç insert takılmaz.</li>
    <li><b>Tahrikli başlık:</b> İçinde diş olan metal disk motorun dişli miline oturur. Merkezine 1 M3×6 başlık sabitleme vidası gelir. Sonra kolun çevre vidaları takılır.</li>
    <li><b>Pasif başlık:</b> Karşı taraftaki düzgün yatağa oturur. Merkezine vida takılmaz; kolun çevre vidalarıyla bağlantı kurulur. M5 hariç her motorda iki başlık kullanılır.</li></ul>
    <p>Toplam: 24 küçük gövde vidası, 50 M3×6 (6 merkez + 44 çevre), 6 tahrikli + 5 pasif metal başlık. Kartı ve tabanı masaya sabitleme donanımı bu sayıya dahil değildir. Paketindeki merkez vidası farklıysa zorlamadan önce ölçüsünü doğrula.</p>
    <p><a href="'''+HF+'''">Hugging Face montaj kaynağı</a> · <a href="'''+WAVE+'''">Waveshare kablo yönleri ve donanım rehberi</a></p></section>
    <section><h2>Motorlar nerede?</h2><img src="MOTOR_YERLERI.png" alt="Altı motorun numaralı yerleşimi"><p>Resmî URDF referans pozu; enerji verirken kendiliğinden gidilecek hedef değildir.</p></section>'''+''.join(cards)+'''
    <section><h2>Kablolar ve son kontrol</h2><p><b>Adapter → M1 → M2 → M3 → M4 → M5 → M6.</b> Her eklemde kabloya hareket payı bırak; sokete çekme yükü gelmesin. Baskı kanallarını kullan. Tabanı masaya sabitlemeden kolu hareket ettirme.</p><p>Parça numaraları FIGBOT baskı listesine aittir. Waveshare rehberindeki F3 bizim P04; F4 bizim P03’tür. Bu sayfada hep P numaralarını takip et.</p><small>Geometri değiştirilmedi. Referans STL commit: '''+COMMIT+'''. Fiziksel montaj ve yük testi henüz doğrulanmadı. Videolar resmî kaynaktan internetle oynatılır; parça görselleri çevrimdışı açılır.</small></section></main></html>'''
    (out/'MONTAJ.html').write_text(doc,encoding='utf-8')
    (out/'KAYNAKLAR.json').write_text(json.dumps({'revision':'MONTAJ-1','commit':COMMIT,'sources':[HF,WAVE],'parts':records,'geometry_modified':False},ensure_ascii=False,indent=2),encoding='utf-8')

def publish():
    stage=ROOT/'.tmp_artifact/so101_assembly_guide';build(stage)
    target=CAD/'MONTAJ';target.mkdir(parents=True,exist_ok=True)
    files=list(stage.iterdir());changed=[p for p in files if (target/p.name).exists() and (target/p.name).read_bytes()!=p.read_bytes()]
    if changed:
        prefix='MONTAJ_ONCEKI/'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'/'
        with zipfile.ZipFile(ARCHIVE,'a',zipfile.ZIP_DEFLATED) as z:
            for p in changed:z.write(target/p.name,prefix+p.name)
        with zipfile.ZipFile(ARCHIVE) as z:
            for p in changed:assert hashlib.sha256(z.read(prefix+p.name)).digest()==hashlib.sha256((target/p.name).read_bytes()).digest()
    for p in files:(target/p.name).write_bytes(p.read_bytes())
    records=[{'path':p.relative_to(CURRENT).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(CURRENT.rglob('*')) if p.is_file() and p.name!='DOSYA_LISTESI.json' and '__pycache__' not in p.parts]
    (CURRENT/'DOSYA_LISTESI.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
    print(target/'MONTAJ.html')

if __name__=='__main__':publish()
