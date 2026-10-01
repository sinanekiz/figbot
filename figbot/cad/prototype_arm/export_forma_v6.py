"""FORMA V6 exporters. Only generic raster/3MF serialization reused, no old geometry."""
from pathlib import Path
import json, math, csv, zipfile, hashlib, shutil
import xml.etree.ElementTree as ET
import cadquery as cq
import trimesh
import numpy as np
from cad.utils import shape_mesh, export_shape
from cad.prototype_arm import build_forma_v6 as a

def part_settings(pid):
    if pid=='L1-17-FINGER':
        return {'perimeters':'4','fill_density':'100%','top_solid_layers':'5','bottom_solid_layers':'5','brim_width':'5','support_material':'1','support_material_buildplate_only':'1','support_material_style':'snug'}
    if pid=='L1-18-PAD':
        return {'perimeters':'3','fill_density':'100%','top_solid_layers':'4','bottom_solid_layers':'4','brim_width':'5','support_material':'1','support_material_buildplate_only':'1','support_material_style':'snug'}
    if pid in ['L1-23-ELBOW-BUSH-LONG','L1-24-ELBOW-BUSH-SHORT','L1-25-FINGER-BUSH']:
        return {'perimeters':'3','fill_density':'100%','top_solid_layers':'5','bottom_solid_layers':'5','brim_width':'5'}
    if 'SOCKET-COVER' in pid:
        return {'perimeters':'5','fill_density':'100%','top_solid_layers':'5','bottom_solid_layers':'5'}
    if pid in ['F6-08-FINGER','F6-09-SPOOL','F6-12-EAR-FIT','F6-14-MICRO-FIT','F6-15-INSERT-FIT','F6-17-YAW-FIT','F6-18-LARGE-HORN-FIT','F6-19-MICRO-HORN-FIT']:
        return {'perimeters':'5','fill_density':'100%','top_solid_layers':'5','bottom_solid_layers':'5'}
    if pid=='F6-10-SOFT-PAD':
        return {'perimeters':'3','fill_density':'20%','top_solid_layers':'3','bottom_solid_layers':'3'}
    return {'perimeters':'5','fill_density':'30%','top_solid_layers':'5','bottom_solid_layers':'5'}

def mesh(s):
    v,f=shape_mesh(s)
    return trimesh.Trimesh(v,f,process=True)

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
    d.text((w/2,h-63),'FORMA V6 / Dogrudan kulak montaji / Bilyeli taban / 180 + 140 mm',font=font(23),fill='#1d4249',anchor='mt')
    d.text((w/2,h-30),'Boyutlandirma prototipi: motor kulagi, insert ve yuk deneyi gerekli.',font=font(20),fill='#8a4b36',anchor='mt')
    im.save(path)


def export_assembly(items,stem):
    assy=cq.Assembly(name=stem);scene=trimesh.Scene()
    for k,i in enumerate(items):
        name=f'{k:03}_{i.name}'.replace(' ','_');s=i.shape.val()
        assy.add(s.located(cq.Location()),loc=s.location(),name=name,color=cq.Color(*i.color))
        m=mesh(i.shape);m.visual.face_colors=(np.array([*i.color,1])*255).astype(np.uint8);scene.add_geometry(m,node_name=name)
    assy.save(str(a.OUT/(stem+'.step')),write_pcurves=False)
    scene.export(a.OUT/(stem+'.glb'))


def modifier_regions(pid):
    s=a.PARTS[pid][0]();b=s.val().BoundingBox()
    regions=[]
    if pid in ['F6-05-UPPER','F6-06-FORE']:
        span=a.UPPER if pid=='F6-05-UPPER' else a.FORE
        regions=[('ROOT',a.box(102,180,160,(28,0,0))),('MOTOR_EARS',a.box(99,180,160,(span-18,0,0)))]
    elif pid=='F6-02-ROTOR':regions=[('INTEGRATED_EAR_POSTS',a.box(150,150,58,(0,0,86)))]
    elif pid.startswith('F6-03'):regions=[('RETAINER_ROOF_AND_SCREW_LANDS',a.box(150,150,20,(0,0,59)))]
    elif pid=='F6-07-PALM':regions=[('PIVOT_AND_INSERTS',a.box(140,100,70,(30,0,0)))]
    elif pid=='F6-01-BASE':
        regions=[('YAW_EAR_SEATS',a.box(75,40,45,(-10,0,23)))]
        regions += [(f'RETAINER_POST_{k}',a.cz(7,0,55,65*math.cos(math.radians(k+45)),65*math.sin(math.radians(k+45)))) for k in range(0,360,90)]
    elif pid=='F6-16-ROVER-PLATE':regions=[(f'M4_BOSS_{x}_{y}',a.cz(9,-12,15,x,y)) for x in [-50,50] for y in [-50,50]]
    else:return []
    raw=a.print_pose(pid,s);bb=raw.val().BoundingBox()
    # Apply the EXACT same rotation and translation to part and modifier.
    def rotate(q):
        if pid=='F6-02-ROTOR' or pid.startswith('F6-03'):return q.rotate((0,0,0),(1,0,0),180)
        if pid in ['F6-05-UPPER','F6-06-FORE']:return q.rotate((0,0,0),(1,0,0),90)
        return q
    rb=rotate(s).val().BoundingBox();out=[]
    for name,r in regions:
        clipped=s.intersect(r)
        if clipped.val().Volume()>.01:
            out.append((name,mesh(rotate(clipped).translate((-rb.xmin,-rb.ymin,-rb.zmin)))))
    return out


def connection_review(exploded=False):
    """Actual mating stacks shown side-by-side; never a replacement spline STL."""
    out=[]
    for micro,x in [(False,-42),(True,42)]:
        name='MG90S' if micro else 'MG996R'
        if not exploded:
            out.append(a.Item(name+' servo',a.servo(micro).translate((x,0,0)),color=a.BLACK))
        out.append(a.Item(name+' original horn envelope',a.horn(micro).translate((x,0,0)),color=a.BLACK))
        out.append(a.Item('F6-19-MICRO-HORN-FIT' if micro else 'F6-18-LARGE-HORN-FIT',a.horn_receiver(micro).translate((x,0,0)),color=a.WHITE))
        out.append(a.Item('F6-SOCKET-COVER '+name,a.original_horns.closure(micro).translate((x,0,0)),color=a.TEAL))
        for label,s in a.original_horns.hardware(micro):
            if 'insert' not in label:out.append(a.Item('fastener '+name+' '+label,s.translate((x,0,0)),color=a.SILVER))
        for px,py in a.horn_points(micro):
            z=a.original_horns.cover_top(micro)
            ins=a.cz(1.6,z,4,px+x,py).cut(a.cz(1,z-.1,4.2,px+x,py))
            out.append(a.Item('insert '+name+' horn',ins,color=a.GOLD))
    if exploded:
        for item in out:
            shift=0
            if 'HORN-FIT' in item.name or item.name.startswith('insert '):shift=16
            elif 'SOCKET-COVER' in item.name or ('fastener ' in item.name and 'mounting ' in item.name):shift=-9
            if shift:item.shape=item.shape.translate((0,0,shift))
    return out


def urdf():
    folder=a.OUT/'URDF';folder.mkdir(exist_ok=True)
    root=ET.Element('robot',name='FORMA_V6_REVIEW_ONLY')
    for frame in a.frames():
        solids=[i.shape.val() for i in a.local_items() if i.frame==frame and i.part_id not in ['F6-08-FINGER','F6-10-SOFT-PAD']]
        cq.exporters.export(cq.Compound.makeCompound(solids),str(folder/(frame+'.stl')),tolerance=.2)
        link=ET.SubElement(root,'link',name=frame)
        geom=ET.SubElement(ET.SubElement(link,'visual'),'geometry')
        ET.SubElement(geom,'mesh',filename=frame+'.stl',scale='.001 .001 .001')
    for name,parent,child,p,axis,lo,hi in [
       ('yaw','base','yaw',(0,0,0),'0 0 1',-125,10),
       ('shoulder','yaw','upper',(0,0,.1),'0 1 0',-105,-10),
       ('elbow','upper','fore',(.18,0,0),'0 1 0',60,140),
       ('wrist','fore','tool',(.14,0,0),'0 1 0',-100,30)]:
        j=ET.SubElement(root,'joint',name=name,type='revolute');ET.SubElement(j,'parent',link=parent);ET.SubElement(j,'child',link=child)
        ET.SubElement(j,'origin',xyz=' '.join(map(str,p)),rpy='0 0 0');ET.SubElement(j,'axis',xyz=axis)
        ET.SubElement(j,'limit',lower=str(math.radians(lo)),upper=str(math.radians(hi)),effort='0',velocity='0')
    for k in range(3):
        theta=math.tau*k/3;fname='finger'+str(k)
        cq.exporters.export(cq.Compound.makeCompound([a.finger().val(),a.pad().val()]),str(folder/(fname+'.stl')),tolerance=.1)
        link=ET.SubElement(root,'link',name=fname);geom=ET.SubElement(ET.SubElement(link,'visual'),'geometry')
        ET.SubElement(geom,'mesh',filename=fname+'.stl',scale='.001 .001 .001')
        j=ET.SubElement(root,'joint',name=fname,type='revolute');ET.SubElement(j,'parent',link='tool');ET.SubElement(j,'child',link=fname)
        ET.SubElement(j,'origin',xyz=f'{a.PALM_X/1000+.023*math.cos(theta)} {.023*math.sin(theta)} -.005',rpy=f'0 0 {theta}')
        ET.SubElement(j,'axis',xyz='0 1 0');ET.SubElement(j,'limit',lower='-.436332',upper='0',effort='0',velocity='0')
        if k:ET.SubElement(j,'mimic',joint='finger0',multiplier='1',offset='0')
    ET.indent(root);ET.ElementTree(root).write(folder/'FORMA_V6_REVIEW.urdf',encoding='utf8',xml_declaration=True)
    # Same articulated arm located in the recorded vehicle coordinate system.
    from cad.prototype_arm import integrate_forma_v6 as integration
    vehicle=cq.Compound.makeCompound([i.shape.val() for i in integration.vehicle()])
    cq.exporters.export(vehicle,str(folder/'vehicle.stl'),tolerance=.4)
    root.set('name','FORMA_V6_ROVER_REVIEW_ONLY')
    link=ET.Element('link',name='vehicle');geom=ET.SubElement(ET.SubElement(link,'visual'),'geometry')
    ET.SubElement(geom,'mesh',filename='vehicle.stl',scale='.001 .001 .001');root.insert(0,link)
    j=ET.SubElement(root,'joint',name='mount',type='fixed')
    ET.SubElement(j,'parent',link='vehicle');ET.SubElement(j,'child',link='base')
    ET.SubElement(j,'origin',xyz=' '.join(str(v/1000) for v in a.BASE_WORLD),rpy='0 0 0')
    ET.indent(root);ET.ElementTree(root).write(folder/'FORMA_V6_ROVER_REVIEW.urdf',encoding='utf8',xml_declaration=True)


def main():
    for f in ['PRINT_STL','PART_STEP','3MF','VIEWS']: (a.OUT/f).mkdir(parents=True,exist_ok=True)
    manifest=[]
    for pid,(fn,n,frame) in a.PARTS.items():
        s=fn();posed=a.print_pose(pid,s)
        export_shape(posed,a.OUT/'PRINT_STL',pid,['stl'])
        cq.exporters.export(s,str(a.OUT/'PART_STEP'/(pid+'.step')),opt={'write_pcurves':False})
        write_3mf([(pid,pid,mesh(posed),modifier_regions(pid))],a.OUT/'3MF'/(pid+'.3mf'))
        manifest.append({'part':pid,'qty':n,'material':'TPU or cut silicone' if 'PAD' in pid else 'PLA candidate','CAD_full_material_g':s.val().Volume()*.00124,'type':frame,
          'stl_sha256':hashlib.sha256((a.OUT/'PRINT_STL'/(pid+'.stl')).read_bytes()).hexdigest()})
        print('EXPORTED',pid,flush=True)
    (a.OUT/'MANIFEST.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    export_assembly(a.assembly(),'FORMA_V6_ASSEMBLY');urdf()
    export_assembly(connection_review(),'FORMA_V6_CONNECTIONS')
    export_assembly(connection_review(True),'FORMA_V6_CONNECTIONS_OPEN')
    render(connection_review(),a.OUT/'VIEWS/07_ORIGINAL_BASLIKLAR.png','R6 - Yildiz yuvalari: dis kapak vidalari / delikler kullanilmaz',az=-45,el=145)
    render(connection_review(True),a.OUT/'VIEWS/08_YILDIZ_YUVASI_ACIK.png','R6 - Patlatilmis yuva / motor gizli / montaj konumu degildir',az=-55,el=-35)
    # Service view removes the rotary assembly; this is not a validated insertion animation.
    service=[i for i in a.local_items() if i.name=='F6-01-BASE' or i.name=='J1 servo' or i.name.startswith(('insert J1 ear','fastener J1 ear'))]
    export_assembly(service,'FORMA_V6_BASE_SERVICE')
    render(a.assembly(),a.OUT/'VIEWS/01_YENI_KOL.png','FORMA V6 - Dogrudan kulak montaji')
    render([i for i in a.local_items() if i.frame in ['base','yaw']],a.OUT/'VIEWS/02_BILYELI_TABAN.png','24 x 8 mm bilye - insertli taban',az=-48,el=38)
    render([i for i in a.local_items() if i.frame=='tool'],a.OUT/'VIEWS/03_UC_MEKANIZMA.png','Hafif uc - uc mafsalli parmak',az=-42,el=25)
    from cad.prototype_arm import integrate_forma_v6 as integration
    from cad.prototype_arm.validate_forma_v6 import TARGETS
    for name,index,label in [('pickup',4,'Teker onunden yerden alma'),('release',5,'Yandaki sepete birakma')]:
        q=a.solve(TARGETS[name]);items=integration.scene(q)
        export_assembly(items,'FORMA_V6_ROVER_'+name.upper())
        render(items,a.OUT/f'VIEWS/0{index}_{name.upper()}.png',label,az=40,el=25)
    render(a.assembly(grip=-25),a.OUT/'VIEWS/06_PARMAKLAR_ACIK.png','Uc parmak acik - 25 derece prototip salinim')
    viewer=a.ROOT/'viewer/public/models/forma-v6';viewer.mkdir(parents=True,exist_ok=True)
    for name in ['ASSEMBLY','BASE_SERVICE','ROVER_PICKUP','ROVER_RELEASE','CONNECTIONS','CONNECTIONS_OPEN']:
        shutil.copy2(a.OUT/f'FORMA_V6_{name}.glb',viewer/f'FORMA_V6_{name}.glb')

if __name__=='__main__':main()
