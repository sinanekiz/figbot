"""Reproducible print/assembly package with explicit regional slicer modifiers."""
from collections import Counter
from pathlib import Path
import csv,hashlib,json,math,zipfile
import xml.etree.ElementTree as ET
import cadquery as cq
import numpy as np
import trimesh
from cad.utils import export_shape,shape_mesh
from cad.prototype_arm import build_aero_v5 as a
from cad.prototype_arm import export_aero_v4 as legacy


def mesh(s):
    v,f=shape_mesh(s)
    return trimesh.Trimesh(v,f,process=True)


def orient_region(pid,region):
    # Apply the part's transform, not independent centring of a modifier mesh.
    raw=a.PARTS[pid][0]()
    def rotate(s):
        if pid in ['A5-06-UPPER-TOP','A5-08-FORE-TOP']:return s.rotate((0,0,0),(1,0,0),180)
        if pid in ['A5-04-TOWER-R','A5-05-TOWER-L','A5-13-FINGER','A5-14-PAD']:return s.rotate((0,0,0),(1,0,0),90)
        if pid=='A5-02-YAW-DECK':return s.rotate((0,0,0),(0,1,0),90)
        return s
    b=rotate(raw).val().BoundingBox()
    return rotate(region).translate((-b.xmin,-b.ymin,-b.zmin))


def regions(pid):
    result=[]
    if pid.startswith(('A5-06','A5-07','A5-08','A5-09')):
        fore=pid.startswith(('A5-08','A5-09'));span=a.FORE if fore else a.UPPER
        result=[('ROOT_100pct',a.box(82,160,100,(41,0,0))),
                ('JOINT_100pct',a.box(60,160,100,(span-2,0,0)))]
        result += [(f'BOLT_{k}_100pct',cq.Workplane('XY').center(x,y).circle(9).extrude(40,both=True))
                   for k,(x,y) in enumerate(a.screw_stations(fore))]
    elif 'TOWER' in pid:
        result=[('FOOT_100pct',a.box(100,150,38,(0,0,95)))]
    elif pid=='A5-10-PALM-GUIDE':
        result=[('WRIST_100pct',a.box(40,70,53,(0,0,-20)))]
    out=[]
    for name,s in result:
        clipped=s.intersect(a.PARTS[pid][0]())
        if sum(v.Volume() for v in clipped.solids().vals())>.001:
            out.append((name,mesh(orient_region(pid,clipped))))
    return out


def part_settings(pid):
    kind=a.PARTS[pid][2]
    return {'perimeters':'5','fill_density':'100%' if kind in ['precision','small','finger','wear','reuse_or_fit','fit_first'] else '30%',
            'top_solid_layers':'6','bottom_solid_layers':'6',
            'support_material':'0' if kind in ['precision','small','wear','TPU','reuse_or_fit','fit_first'] else '1'}


def write_3mf(entries,path):
    """Prusa volume metadata; generic readers may show modifiers as solids."""
    ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
    root=ET.Element('model',{'unit':'millimeter','xml:lang':'en-US','xmlns':ns,
                          'xmlns:slic3rpe':'http://schemas.slic3r.org/3mf/2017/06'})
    ET.SubElement(root,'metadata',name='slic3rpe:Version3mf').text='1'
    resources=ET.SubElement(root,'resources');build=ET.SubElement(root,'build')
    config=ET.Element('config')
    for oid,(name,pid,base,mods) in enumerate(entries,1):
        obj=ET.SubElement(resources,'object',id=str(oid),type='model',name=name)
        meshnode=ET.SubElement(obj,'mesh');verts=ET.SubElement(meshnode,'vertices');faces=ET.SubElement(meshnode,'triangles')
        objcfg=ET.SubElement(config,'object',id=str(oid),instances_count='1')
        for key,value in {'name':name,**part_settings(pid)}.items():
            ET.SubElement(objcfg,'metadata',type='object',key=key,value=value)
        vo=fo=0
        for index,(label,m) in enumerate([(name,base)]+mods):
            for v in m.vertices:ET.SubElement(verts,'vertex',x=str(v[0]),y=str(v[1]),z=str(v[2]))
            for f in m.faces:ET.SubElement(faces,'triangle',v1=str(f[0]+vo),v2=str(f[1]+vo),v3=str(f[2]+vo))
            vol=ET.SubElement(objcfg,'volume',firstid=str(fo),lastid=str(fo+len(m.faces)-1))
            settings={'name':label,'volume_type':'ParameterModifier' if index else 'ModelPart'}
            if index:settings.update({'modifier':'1','fill_density':'100%','perimeters':'7'})
            for key,value in settings.items():ET.SubElement(vol,'metadata',type='volume',key=key,value=value)
            vo+=len(m.vertices);fo+=len(m.faces)
        ET.SubElement(build,'item',objectid=str(oid))
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml','<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
        z.writestr('_rels/.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
        z.writestr('3D/3dmodel.model',ET.tostring(root,encoding='utf-8',xml_declaration=True))
        z.writestr('Metadata/Slic3r_PE_model.config',ET.tostring(config,encoding='utf-8',xml_declaration=True))


def render(items,path,title,az=-58,el=24):
    # CAD z-buffer renderer; do not use generated artwork as dimensional evidence.
    from PIL import Image,ImageDraw,ImageFont
    w,h=1600,1100;meshes=[(mesh(i.shape),i.color) for i in items]
    az,el=np.radians([az,el]);basis=np.array([[-np.sin(az),-np.sin(el)*np.cos(az),np.cos(el)*np.cos(az)],
        [np.cos(az),-np.sin(el)*np.sin(az),np.cos(el)*np.sin(az)],[0,np.cos(el),np.sin(el)]])
    points=np.vstack([m.vertices@basis for m,c in meshes]);center=(points.min(0)+points.max(0))/2
    scale=min((w-140)/np.ptp(points[:,0]),(h-200)/np.ptp(points[:,1]))
    pixels=np.full((h,w,3),(244,243,239),dtype=np.uint8);depth=np.full((h,w),-np.inf)
    light=np.array([-.4,-.5,1]);light/=np.linalg.norm(light)
    for m,color in meshes:
        shades=.62+.37*np.abs(m.face_normals@light);coords=m.vertices@basis
        coords[:,0]=(coords[:,0]-center[0])*scale+w/2
        coords[:,1]=h/2-(coords[:,1]-center[1])*scale
        for k,face in enumerate(m.faces):
            t=coords[face];aa,b,c=t
            x0=max(0,int(np.floor(t[:,0].min())));x1=min(w-1,int(np.ceil(t[:,0].max())))
            y0=max(0,int(np.floor(t[:,1].min())));y1=min(h-1,int(np.ceil(t[:,1].max())))
            det=(b[1]-c[1])*(aa[0]-c[0])+(c[0]-b[0])*(aa[1]-c[1])
            if abs(det)<1e-9 or x1<x0 or y1<y0:continue
            yy,xx=np.mgrid[y0:y1+1,x0:x1+1];xx=xx+.5;yy=yy+.5
            u=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/det
            v=((c[1]-aa[1])*(xx-c[0])+(aa[0]-c[0])*(yy-c[1]))/det
            q=1-u-v;z=u*aa[2]+v*b[2]+q*c[2];target=depth[y0:y1+1,x0:x1+1]
            mask=(u>=-1e-7)&(v>=-1e-7)&(q>=-1e-7)&(z>target)
            target[mask]=z[mask];pixels[y0:y1+1,x0:x1+1][mask]=np.clip(np.array(color)*shades[k]*255,0,255)
    im=Image.fromarray(pixels);d=ImageDraw.Draw(im)
    font=lambda n:ImageFont.truetype('C:/Windows/Fonts/arial.ttf',n)
    d.text((w/2,24),title,font=font(31),fill='#1d4249',anchor='mt')
    d.text((w/2,h-63),'AERO V5  /  180 + 140 mm  /  Mevcut 4 MG996R + 2 MG90S',font=font(23),fill='#1d4249',anchor='mt')
    d.text((w/2,h-30),'Baskı prototipi: gerçek motor uyumu ve yük altında dayanım denenmeli.',font=font(20),fill='#8a4b36',anchor='mt')
    im.save(path)


def export_assembly(items,stem):
    assy=cq.Assembly(name=stem);scene=trimesh.Scene()
    for k,i in enumerate(items):
        name=f'{k:03}_{i.name}'.replace(' ','_')
        shape=i.shape.val()
        assy.add(shape.located(cq.Location()),loc=shape.location(),name=name,color=cq.Color(*i.color))
        m=mesh(i.shape);m.visual.face_colors=np.array([*i.color,1])*255;scene.add_geometry(m,node_name=name)
    # OCCT's STEP pcurves can invalidate a rotated ruled-loft face on re-import.
    # Export its 3D curves/surfaces and let the reader reconstruct pcurves.
    assy.save(str(a.OUT/(stem+'.step')),write_pcurves=False);scene.export(a.OUT/(stem+'.glb'))


def urdf():
    folder=a.OUT/'URDF';folder.mkdir(exist_ok=True)
    root=ET.Element('robot',name='AERO_V5_KINEMATIC_REVIEW_NOT_CONTROL')
    for frame in a.frames():
        ss=[i.shape.val() for i in a.local_items() if i.frame==frame]
        cq.exporters.export(cq.Compound.makeCompound(ss),str(folder/f'{frame}.stl'),tolerance=.15)
        link=ET.SubElement(root,'link',name=frame)
        visual=ET.SubElement(link,'visual');geom=ET.SubElement(visual,'geometry')
        ET.SubElement(geom,'mesh',filename=f'{frame}.stl',scale='.001 .001 .001')
    joints=[('J1','base','yaw',(0,0,0),'0 0 1',-135,15),
            ('J2','yaw','upper',(0,0,.124),'0 1 0',-105,-15),
            ('J3','upper','fore',(.180,0,0),'0 1 0',45,140),
            ('W1','fore','tool',(.140,0,0),'0 1 0',-115,40),
            ('G1','tool','cam',(a.TOOL_X/1000,0,0),'0 0 1',-25,25)]
    for name,pa,ch,pos,axis,lo,hi in joints:
        j=ET.SubElement(root,'joint',name=name,type='revolute')
        ET.SubElement(j,'parent',link=pa);ET.SubElement(j,'child',link=ch)
        ET.SubElement(j,'origin',xyz=' '.join(map(str,pos)),rpy='0 0 0');ET.SubElement(j,'axis',xyz=axis)
        ET.SubElement(j,'limit',lower=str(math.radians(lo)),upper=str(math.radians(hi)),effort='0',velocity='0')
    for k in range(3):
        theta=math.radians(k*120);j=ET.SubElement(root,'joint',name=f'G1_follower_{k}',type='prismatic')
        ET.SubElement(j,'parent',link='tool');ET.SubElement(j,'child',link=f'finger{k}')
        ET.SubElement(j,'origin',xyz=f'{a.TOOL_X/1000+.026*math.cos(theta)} {.026*math.sin(theta)} 0',rpy=f'0 0 {theta}')
        ET.SubElement(j,'axis',xyz='1 0 0');ET.SubElement(j,'limit',lower='-.007',upper='.007',effort='0',velocity='0')
        ET.SubElement(j,'mimic',joint='G1',multiplier=str(-.00028*180/math.pi),offset='0')
    ET.indent(root);ET.ElementTree(root).write(folder/'AERO_V5_REVIEW.urdf',encoding='utf-8',xml_declaration=True)


def export_rover_review():
    from cad.prototype_arm import validate_aero_v5 as check
    vehicle=check.vehicle()
    for name in ['pickup','release']:
        items=vehicle+a.assembly(a.solve(check.TARGETS[name]),rover=True)
        export_assembly(items,'ROVER_'+name.upper()+'_REVIEW')
        render(items,a.OUT/'VIEWS'/f'ROVER_{name.upper()}.png',
               'Teker önünden alma' if name=='pickup' else 'Yan sepete bırakma',az=-48,el=25)
    folder=a.OUT/'URDF'
    cq.exporters.export(cq.Compound.makeCompound([i.shape.val() for i in vehicle]),str(folder/'vehicle.stl'),tolerance=.5)
    tree=ET.parse(folder/'AERO_V5_REVIEW.urdf');root=tree.getroot()
    root.set('name','AERO_V5_ROVER_SINGLE_ARM_REVIEW_NOT_CONTROL')
    link=ET.SubElement(root,'link',name='vehicle');geom=ET.SubElement(ET.SubElement(link,'visual'),'geometry')
    ET.SubElement(geom,'mesh',filename='vehicle.stl',scale='.001 .001 .001')
    j=ET.SubElement(root,'joint',name='mount',type='fixed')
    ET.SubElement(j,'parent',link='vehicle');ET.SubElement(j,'child',link='base')
    ET.SubElement(j,'origin',xyz='.550 .415 .066',rpy='0 0 0')
    ET.indent(root);tree.write(folder/'ROVER_MOUNT_REVIEW.urdf',encoding='utf-8',xml_declaration=True)


def main():
    a.OUT.mkdir(parents=True,exist_ok=True)
    for folder in ['PRINT_STL','PART_STEP','SLICER_3MF','VIEWS']: (a.OUT/folder).mkdir(exist_ok=True)
    manifest=[];entries=[]
    for pid,(fn,qty,kind) in a.PARTS.items():
        raw=fn();assert raw.val().isValid() and len(raw.solids().vals())==1 and raw.val().Volume()>0,pid
        s=a.print_pose(pid,raw);export_shape(s,a.OUT/'PRINT_STL',pid,['stl'])
        cq.exporters.export(raw,str(a.OUT/'PART_STEP'/(pid+'.step')),opt={'write_pcurves':False})
        m=trimesh.load_mesh(a.OUT/'PRINT_STL'/f'{pid}.stl')
        assert m.is_watertight and m.is_winding_consistent and m.volume>0 and len(m.split())==1,pid
        assert max(m.extents[:2])<=236 and m.extents[2]<=246,pid
        mods=regions(pid)
        move=np.array([10,10,0]);placed=m.copy();placed.apply_translation(move)
        placedmods=[]
        for name,mod in mods:
            mod=mod.copy();mod.apply_translation(move);placedmods.append((name,mod))
        write_3mf([(pid,pid,placed,placedmods)],a.OUT/'SLICER_3MF'/f'{pid}.3mf')
        row={'part':pid,'qty_per_arm':qty,'class':kind,'size_mm':m.extents.tolist(),
             'volume_mm3':float(m.volume),'material':'TPU_OR_CUT_SILICONE' if kind=='TPU' else 'PLA_FIT_PROTOTYPE',
             'sha256':hashlib.sha256((a.OUT/'PRINT_STL'/f'{pid}.stl').read_bytes()).hexdigest(),
             'settings':part_settings(pid),'modifier_names':[n for n,_ in mods]}
        manifest.append(row);print('EXPORT',pid,len(mods),'modifiers',flush=True)
    counts=Counter(i.part_id for i in a.local_items() if i.part_id)
    assert counts==Counter({p:n for p,(_,n,_) in a.PARTS.items()}),(counts,a.PARTS.keys())
    (a.OUT/'PRINT_MANIFEST.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    with (a.OUT/'PRINT_QUANTITIES.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f,delimiter=';');w.writerow(['Part','Qty_per_arm','Material','X','Y','Z'])
        for p in manifest:w.writerow([p['part'],p['qty_per_arm'],p['material'],*[round(v,2) for v in p['size_mm']]])
    # Individual 3MFs preserve local modifiers; a separate packing overview is visual only.
    items=a.assembly();export_assembly(items,'AERO_V5_ASSEMBLY');urdf()
    render(items,a.OUT/'VIEWS'/'ASSEMBLY.png','FIGBOT  /  AERO V5',az=-60)
    exploded=[]
    for i in a.local_items():
        if i.frame=='upper':
            shift=(0,0,24 if 'TOP' in i.part_id else -24 if 'BOTTOM' in i.part_id else 0)
            exploded.append(a.Item(i.name,i.shape.translate(shift),i.frame,i.part_id,i.group,i.color))
    render(exploded,a.OUT/'VIEWS'/'UPPER_EXPLODED.png','Üst kol  /  Açılan kabuklar ve metal ara burçlar',az=-65,el=35)
    for q,name in [(-25,'OPEN'),(25,'CLOSED')]:
        items=[i for i in a.assembly((0,0,0,0,q)) if i.frame in ['tool','cam','finger0','finger1','finger2']]
        render(items,a.OUT/'VIEWS'/f'GRIPPER_{name}.png',f'Üç parmak  /  {"Açık" if q<0 else "Kapalı"}',az=-65,el=-15)
    export_rover_review()
    from cad.prototype_arm.validate_aero_v5 import source_hashes
    (a.OUT/'EXPORT_SOURCES.json').write_text(json.dumps(source_hashes(),indent=2),encoding='utf-8')
    print('EXPORT COMPLETE',len(manifest),'part types',sum(p['qty_per_arm'] for p in manifest),'instances',flush=True)


if __name__=='__main__':main()
