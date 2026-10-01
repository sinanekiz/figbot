"""Manufacturing pack, explicit quantities, assembly/URDF and CAD-derived views."""
from pathlib import Path
from collections import Counter
import csv,hashlib,json,zipfile,math
import xml.etree.ElementTree as ET
import cadquery as cq
import numpy as np
import trimesh
from PIL import Image,ImageDraw,ImageFont
from cad.utils import export_shape,shape_mesh
from cad.prototype_arm import build_aero_v4 as a

def render(items,path,title,az=-60,el=23,w=1400,h=940):
    meshes=[]
    for x in items:
        v,f=shape_mesh(x.shape);meshes.append((trimesh.Trimesh(v,f),x.color))
    az,el=np.radians([az,el])
    right=np.array([-np.sin(az),np.cos(az),0])
    up=np.array([-np.sin(el)*np.cos(az),-np.sin(el)*np.sin(az),np.cos(el)])
    look=np.array([np.cos(el)*np.cos(az),np.cos(el)*np.sin(az),np.sin(el)])
    matrix=np.stack([right,up,look],axis=1)
    p=np.vstack([m.vertices@matrix for m,c in meshes]);lo=p.min(0);hi=p.max(0);center=(lo+hi)/2
    scale=min((w-100)/(hi[0]-lo[0]),(h-165)/(hi[1]-lo[1]))
    pixels=np.full((h,w,3),248,dtype=np.uint8);depth=np.full((h,w),-np.inf)
    light=np.array([-.4,-.5,1]);light/=np.linalg.norm(light)
    for m,color in meshes:
        shades=.58+.4*np.abs(m.face_normals@light)
        coords=m.vertices@matrix
        coords[:,0]=(coords[:,0]-center[0])*scale+w/2
        coords[:,1]=h/2+15-(coords[:,1]-center[1])*scale
        for k,face in enumerate(m.faces):
            t=coords[face];aa,b,c=t
            x0=max(0,int(np.floor(t[:,0].min())));x1=min(w-1,int(np.ceil(t[:,0].max())))
            y0=max(0,int(np.floor(t[:,1].min())));y1=min(h-1,int(np.ceil(t[:,1].max())))
            det=(b[1]-c[1])*(aa[0]-c[0])+(c[0]-b[0])*(aa[1]-c[1])
            if abs(det)<1e-9 or x1<x0 or y1<y0:continue
            yy,xx=np.mgrid[y0:y1+1,x0:x1+1];xx=xx+.5;yy=yy+.5
            u=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/det
            v=((c[1]-aa[1])*(xx-c[0])+(aa[0]-c[0])*(yy-c[1]))/det
            q=1-u-v;z=u*aa[2]+v*b[2]+q*c[2]
            target=depth[y0:y1+1,x0:x1+1];mask=(u>=-1e-7)&(v>=-1e-7)&(q>=-1e-7)&(z>target)
            target[mask]=z[mask];pixels[y0:y1+1,x0:x1+1][mask]=np.array(color)*shades[k]*255
    im=Image.fromarray(pixels);d=ImageDraw.Draw(im)
    font=lambda n:ImageFont.truetype('C:/Windows/Fonts/arial.ttf',n)
    d.text((w/2,25),title,font=font(28),fill='#16323d',anchor='mt')
    d.text((w/2,h-48),'Mavi: yeni parçalar  •  Açık mavi/mor: oturan bağlantılar  •  Turuncu: kilit pimleri',font=font(20),fill='#16323d',anchor='mt')
    d.text((w/2,h-23),'Dijital prototip — fiziksel dayanım ve yük testi gerekli; motorlar basılmayacak.',font=font(16),fill='#5a6470',anchor='mt')
    path.parent.mkdir(parents=True,exist_ok=True);im.save(path)

def oriented(pid,s):
    # Thin horn-tongue slots point UP: do not trap support in a3.4mm aperture.
    # Any downward large beam socket has a20.5mm mouth for support removal.
    if pid in ['A4-02-SHOULDER-DECK','A4-04-UPPER-CARRIER','A4-06-ELBOW-YOKE','A4-07-FORE-CARRIER','A4-09-WRIST-YOKE']:
        s=s.rotate((0,0,0),(0,1,0),90)
    elif pid in ['A4-14-SHOULDER-TOWER-R','A4-15-SHOULDER-TOWER-L']:
        s=s.rotate((0,0,0),(1,0,0),90)
    b=s.val().BoundingBox();return s.translate((-b.xmin,-b.ymin,-b.zmin))

def write_3mf(entries,path):
    ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
    root=ET.Element('model',{'unit':'millimeter','xml:lang':'en-US','xmlns':ns})
    res=ET.SubElement(root,'resources');build=ET.SubElement(root,'build')
    for i,(name,m) in enumerate(entries,1):
        obj=ET.SubElement(res,'object',id=str(i),type='model',name=name)
        mesh=ET.SubElement(obj,'mesh');vs=ET.SubElement(mesh,'vertices');fs=ET.SubElement(mesh,'triangles')
        for v in m.vertices:ET.SubElement(vs,'vertex',x=str(v[0]),y=str(v[1]),z=str(v[2]))
        for f in m.faces:ET.SubElement(fs,'triangle',v1=str(f[0]),v2=str(f[1]),v3=str(f[2]))
        ET.SubElement(build,'item',objectid=str(i))
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml','<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
        z.writestr('_rels/.rels','<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
        z.writestr('3D/3dmodel.model',ET.tostring(root,encoding='utf-8',xml_declaration=True))

def plates(manifest):
    # Keep support-free hardware separate from holders requiring slicer supports.
    groups=[('01_PIMLER_KELEPCELER',[p for p in a.PARTS if p.startswith('A4-P') or 'CLAMP' in p]),
            ('02_TABAN',['A4-01-BASE','A4-03-YAW-WASHER']),
            ('03_DONER_TABLA_OMUZ',['A4-02-SHOULDER-DECK','A4-14-SHOULDER-TOWER-R','A4-15-SHOULDER-TOWER-L']),
            ('04_UST_KOL',['A4-04-UPPER-CARRIER','A4-05-UPPER-BEAM','A4-06-ELBOW-YOKE']),
            ('05_ON_KOL',['A4-07-FORE-CARRIER','A4-08-FORE-BEAM','A4-09-WRIST-YOKE']),
            ('06_TUTUCU',['A4-10-PALM-FIXED-FINGER','A4-11-MOVING-FINGER'])]
    rows=[];out=a.OUT/'TABLALAR';out.mkdir(exist_ok=True)
    for group,pids in groups:
        x=y=10.;rowheight=0.;entries=[];sub=1
        def flush():
            if not entries:return
            name=f'{group}_{sub}'
            combined=trimesh.util.concatenate([m for _,m in entries]);combined.export(out/(name+'.stl'))
            write_3mf(entries,out/(name+'.3mf'))
            rows.append({'plate':name,'objects':[n for n,m in entries],'bounds_mm':combined.bounds.tolist(),'components':len(combined.split())})
        for pid in pids:
            original=trimesh.load_mesh(a.OUT/'PRINT'/f'{pid}.stl')
            for n in range(a.PARTS[pid][1]):
                m=original.copy();dx,dy,dz=m.extents
                assert dx<=236 and dy<=236 and dz<=236
                if x+dx>246:x=10.;y+=rowheight+8;rowheight=0
                if y+dy>246:
                    flush();entries=[];sub+=1;x=y=10.;rowheight=0
                m.apply_translation((x,y,0));entries.append((f'{pid}__{n+1}',m));x+=dx+8;rowheight=max(rowheight,dy)
        flush()
    (a.OUT/'TABLA_LISTESI.json').write_text(json.dumps(rows,indent=2))
    return rows

def urdf():
    folder=a.OUT/'URDF';folder.mkdir(exist_ok=True)
    root=ET.Element('robot',name='FIGBOT_AERO_V4_REVIEW_ONLY')
    for frame in a.frames():
        chunks=[i.shape.val() for i in a.local_items() if i.frame==frame]
        shape=cq.Compound.makeCompound(chunks)
        cq.exporters.export(shape,str(folder/(frame+'.stl')),tolerance=.15)
        link=ET.SubElement(root,'link',name=frame)
        for tag in ['visual','collision']:
            g=ET.SubElement(ET.SubElement(link,tag),'geometry');ET.SubElement(g,'mesh',filename=frame+'.stl',scale='.001 .001 .001')
    joints=[('J1','base','yaw',(0,0,0),'0 0 1',-30,30),('J2','yaw','upper',(0,0,.124),'0 1 0',-45,-35),
            ('J3','upper','fore',(.300,0,0),'0 1 0',60,75),('W1','fore','tool',(.220,0,0),'0 1 0',-40,-15),
            ('G1','tool','finger',(.030,0,-.066),'0 1 0',-20,0)]
    for name,pa,ch,pos,axis,lo,hi in joints:
        j=ET.SubElement(root,'joint',name=name,type='revolute');ET.SubElement(j,'parent',link=pa);ET.SubElement(j,'child',link=ch)
        ET.SubElement(j,'origin',xyz=' '.join(map(str,pos)),rpy='0 0 0');ET.SubElement(j,'axis',xyz=axis)
        ET.SubElement(j,'limit',lower=str(math.radians(lo)),upper=str(math.radians(hi)),effort='0',velocity='0')
    ET.indent(root);ET.ElementTree(root).write(folder/'AERO_V4_REVIEW.urdf',encoding='utf-8',xml_declaration=True)

def main():
    a.OUT.mkdir(exist_ok=True,parents=True)
    manifest=[]
    for pid,(fn,qty) in a.PARTS.items():
        s=fn();assert s.val().isValid() and len(s.solids().vals())==1,pid
        p=oriented(pid,s);export_shape(p,a.OUT/'PRINT',pid,['stl','step'])
        m=trimesh.load_mesh(a.OUT/'PRINT'/f'{pid}.stl');assert m.is_watertight and len(m.split())==1,pid
        manifest.append({'part':pid,'qty':qty,'size_mm':m.extents.tolist(),'solid_volume_mm3':float(m.volume),'sha256':hashlib.sha256((a.OUT/'PRINT'/f'{pid}.stl').read_bytes()).hexdigest()})
        print('export',pid,flush=True)
    (a.OUT/'PRINT_MANIFEST.json').write_text(json.dumps(manifest,indent=2))
    with (a.OUT/'BASILACAKLAR.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f,delimiter=';');w.writerow(['Parca','Adet','X_mm','Y_mm','Z_mm'])
        for p in manifest:w.writerow([p['part'],p['qty'],*[round(v,2) for v in p['size_mm']]])
    counts=Counter(i.part_id for i in a.local_items() if i.part_id)
    assert all(counts[k]==n for k,(_,n) in a.PARTS.items()),dict(counts)
    rows=plates(manifest)
    assembly=cq.Assembly(name='AERO_V4_BENCH');scene=trimesh.Scene()
    items=a.assembly()
    for n,i in enumerate(items):
        assembly.add(i.shape,name=f'{n:03}_{i.name}',color=cq.Color(*i.color))
        v,f=shape_mesh(i.shape);m=trimesh.Trimesh(v,f);m.visual.face_colors=np.array([*i.color,1])*255;scene.add_geometry(m,node_name=f'{n:03}_{i.name}')
    assembly.save(str(a.OUT/'AERO_V4_MONTAJ.step'));scene.export(a.OUT/'AERO_V4_MONTAJ.glb')
    urdf()
    render(items,a.OUT/'MONTAJ_GENEL.png','AERO V4 — geçmeli ve isteğe bağlı vidalı prototip')
    render(items,a.OUT/'MONTAJ_YAN.png','AERO V4 — yandan görünüş',az=-90,el=0)
    for frame,title in [('base','01 — Taban motoru ve pimli kelepçeler'),('yaw','02 — Döner tabla ve çıkarılabilir omuz kuleleri'),('upper','03 — Üst kol, omuz bağlantıları ve dirsek'),('fore','04 — Ön kol, dirsek bağlantısı ve bilek')]:
        render([i for i in a.local_items() if i.frame==frame],a.OUT/'MONTAJ'/f'{frame}.png',title,el=35)
    render([i for i in items if i.frame in ['tool','finger']],a.OUT/'MONTAJ'/'tutucu.png','05 — Bilek, sabit parmak ve hareketli parmak',az=-65,el=20)
    # Mass/cost scenario, not a measured slicer weight or a purchase ledger.
    density=.00124
    reusable=sum(i.shape.val().Volume() for i in a.local_items() if i.part_id.startswith(('S02','S03')))
    volume=sum(p['qty']*p['solid_volume_mm3'] for p in manifest)
    estimate={'status':'ESTIMATE; actual slicer mass/support and filament price TBD','pla_density_assumption_g_mm3':density,
        'new_parts_full_solid_g':volume*density,'reused_connections_full_solid_g':reusable*density,
        'filament_price_TRY_kg':None,'new_print_cost_TRY':None,'purchase_ledger_changed':False,
        'new_part_instances':sum(p['qty'] for p in manifest),'plate_count':len(rows)}
    (a.OUT/'MALZEME_MALIYET_TAHMINI.json').write_text(json.dumps(estimate,indent=2))
    print(json.dumps(estimate,indent=2))

if __name__=='__main__':main()
