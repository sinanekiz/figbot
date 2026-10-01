"""PB02: integrated MG996R motor base, captive bearing and keyed shoulder rotor.

Preserve AERO V4 motor and shoulder coordinates. Reuse proven SNAP02 pocket
and opposed caps, but remove its demonstration tongue: torque now goes directly
through one continuous rotor into the four unchanged shoulder tower sockets.
No physical strength claim. PB01 standalone print recommendation is superseded.
"""
from functools import lru_cache
from pathlib import Path
import math, json, hashlib, zipfile
import xml.etree.ElementTree as ET
import cadquery as cq
import numpy as np
import trimesh
from PIL import Image,ImageDraw,ImageFont
from cad.utils import ROOT,export_shape
from cad.prototype_arm import build_aero_v4 as a
from cad.prototype_arm import build_plastic_bearing as pb
from cad.prototype_arm.export_aero_v4 import render,write_3mf

OUT=ROOT/'cad/prototype_arm/motor_bearing_pb02/release_02_clearance'
SPEC=pb.LARGE
BEARING_Z=53.5
UPPER_RACE_CENTRE_Z=7.6
BALL_CENTRE_Z=7.8
CAP_AXIAL_CLEARANCE=1.0  # DEC-071: print trial, physical friction/retention unverified.


def at_bearing(s):return s.translate((0,0,BEARING_Z))


@lru_cache(None)
def star_core():
    # Retain the exact successful pocket, rails and cap stops. The test tongue
    # cannot fit through the70mm bearing bore and is deliberately excluded.
    original=a.large.build()[0]
    core=original.intersect(a.box(60,44,20,(0,0,5)))
    return a.transform(core,a.YAW_HORN)


@lru_cache(None)
def rotor():
    # Bearing output face is74.5mm, exactly the old shoulder-deck underside.
    r=SPEC.pitch_r
    # Close PB01's0.4mm unloaded race gap WITHOUT dropping the horn onto the
    # motor case. Lower groove centre8.0, upper7.6, sphere7.8: nominal tangency
    # at both axial poles. Actual print tolerances still require hand checking.
    upper_groove=cq.Workplane(obj=cq.Solid.makeTorus(r,pb.GROOVE_R,(0,0,UPPER_RACE_CENTRE_Z)))
    s=pb.annulus(r-7,r+9,10,15).cut(upper_groove)
    # Skirt starts above60.8mm so the existing opposed caps can slide in.
    s=s.union(pb.annulus(r-7,r-5,7.5,10.1)).union(pb.annulus(r-7,r+4,14.9,21))
    s=at_bearing(s)
    # Closed centre / torque bridge. No separate loose circular horn inside it.
    neck=cq.Workplane('XY').circle(32).extrude(9.7).translate((0,0,64.9))
    deck=a.old.rb(100,96,4,8,(0,0,76.5))
    s=s.union(neck).union(deck).union(star_core())
    for side in [-1,1]:
        for x in [-38,22]:
            socket=a.box(14,12,12,(x,side*39,84.5))
            socket=socket.cut(a.box(8.4,6.4,11,(x,side*39,86)))
            s=s.union(a.hole_y(socket,x,85.5))
    # Original centre screw is installed from above after seating the horn.
    s=s.cut(cq.Workplane('XY').circle(4).extrude(120))
    return s


@lru_cache(None)
def base():
    # Open pedestal lets the user fit the motor and clamp pins FIRST. The
    # stationary race is fitted later, avoiding a trapped flange or tools.
    s=a.old.rb(116,110,6,10,(0,0,3))
    s=s.union(a.old.mount_plate().translate((0,0,58)))
    for x in [-37,21]:
        for y in [-17,17]:s=s.union(a.old.rb(8,8,32.2,2,(x,y,22.0)))
    for x in [-48,48]:
        for y in [-45,45]:
            theta=math.degrees(math.atan2(y,x))
            s=s.union(a.old.rb(8,8,32,2,(x,y,21.5)))
            web=cq.Workplane('XZ').polyline([(32,5.5),(68,5.5),(68,37.5),(52,37.5)]).close().extrude(2.5,both=True)
            web=web.rotate((0,0,0),(0,0,1),theta)
            bridge=a.box(24,16,4.2,(59,0,39.4)).rotate((0,0,0),(0,0,1),theta)
            s=s.union(web).union(bridge)
    for x in [-43,43]:
        for y in [-40,40]:
            peg=a.box(8,8,11.8,(x,y,47.4))
            bore=cq.Workplane('XZ').center(x,47.5).circle(3.15).extrude(100,both=True)
            s=s.union(peg.cut(bore))
    # Restore six original bench fastener passages after adding structural webs.
    for x in [-50,50]:
        for y in [-43,0,43]:s=a.hole_z(s,x,y,4.5)
    # New columns must not obstruct the ends of the existing motor clamp pins.
    for x in [-32.49,16.21]:
        for y in [-14.85,14.85]:
            s=s.cut(cq.Workplane('XY').center(x,y).circle(2).extrude(38.2))
    return s


@lru_cache(None)
def fixed_race():
    s=at_bearing(pb.lower(SPEC))
    for x in [-43,43]:
        for y in [-40,40]:
            foot=a.box(14,14,12.2,(x,y,47.6))
            foot=foot.cut(a.box(8.4,8.4,12.0,(x,y,47.4)))
            bore=cq.Workplane('XZ').center(x,47.5).circle(3.15).extrude(100,both=True)
            s=s.union(foot.cut(bore))
    return s


@lru_cache(None)
def support_pin():
    nose=cq.Workplane('XY').circle(2.8).workplane(offset=1).circle(3.1).loft()
    shaft=cq.Workplane('XY').circle(3.1).extrude(13.3).translate((0,0,1))
    head=cq.Workplane('XY').circle(4.6).extrude(2).translate((0,0,14.3))
    return nose.union(shaft).union(head)


@lru_cache(None)
def cap_half(side):
    # The closed deck cannot pass through a one-piece retainer. Two halves
    # enter radially below it; two thick solid transverse pins join the ears.
    # Relieve only the inner roof above the rotor flange (local top Z15).
    # Preserve the external wall, bayonet lugs, joining ears and mounting height.
    cap=pb.cap(SPEC).cut(pb.annulus(SPEC.pitch_r+6.4,SPEC.pitch_r+13.4,
                                  15.39,15.+CAP_AXIAL_CLEARANCE))
    s=at_bearing(cap).intersect(a.box(100,180,100,(side*50.15,0,60)))
    for y in [-67,67]:
        ear=a.box(7,12,10,(side*3.65,y,64))
        bore=cq.Workplane('YZ').center(y,64).circle(3.15).extrude(30,both=True)
        s=s.union(ear).cut(bore)
        if side==1:
            head_clearance=cq.Workplane('YZ').center(y,64).circle(4.8).extrude(20).translate((7.15,0,0))
            s=s.cut(head_clearance)
    if side==-1:
        for theta in [120,240]:
            s=s.cut(at_bearing(pb.sector(57.5,63.6,2.6,5.5,theta-30,theta+38)))
    return s


PARTS={
    'PB02_01_SABIT_MOTOR_TABANI':(base,1),
    'PB02_02_YILDIZ_YUVALI_DONER_OMUZ':(rotor,1),
    'PB02_03A_YAN_KAPAK':(lambda:cap_half(1),1),
    'PB02_03B_YAN_KAPAK':(lambda:cap_half(-1),1),
    'PB02_04_BILYE_KAFESI':(lambda:at_bearing(pb.cage(SPEC)),1),
    'PB02_05_BILYE_8MM':(pb.ball,24),
    'PB02_06_DOLU_KAPAK_PIMI':(pb.pin,3),
    'PB02_07_SABIT_YATAK_AYAKLARI':(fixed_race,1),
    'PB02_08_KALIN_AYAK_PIMI':(support_pin,6),
}


def bearing_items():
    out=[a.Item('PB02_SABIT_TABAN',base(),'base',color=a.BLUE),
         a.Item('PB02_SABIT_YATAK',fixed_race(),'base',color=a.BLUE),
         a.Item('PB02_YILDIZLI_ROTOR',rotor(),'yaw',color=a.GOLD)]
    for side in [-1,1]:out.append(a.Item(f'PB02_YAN_KAPAK_{side}',cap_half(side),'base',color=a.LIGHT))
    for y in [-67,67]:
        t=a.basis((0,1,0),(1,0,0),(-7.15,y,64))
        out.append(a.Item(f'PB02_KAPAK_BIRLESTIRME_PIMI_{y}',a.transform(support_pin(),t),'base',color=a.DARK))
    for x in [-43,43]:
        for side in [-1,1]:
            t=a.basis((1,0,0),(0,side,0),(x,side*32.7,47.5))
            out.append(a.Item(f'PB02_AYAK_PIMI_{x}_{side}',a.transform(support_pin(),t),'base',color=a.DARK))
    for i in pb.items(SPEC):
        if i.name in ['ALT_YATAK','DONEN_HALKA','BAYONET_KAPAK']:continue
        shape=i.shape
        if i.name=='KAFES' or i.name.startswith('BILYE_'):shape=shape.translate((0,0,BALL_CENTRE_Z-pb.BALL_Z))
        out.append(a.Item(i.name,at_bearing(shape),'base',color=i.color))
    return out


@lru_cache(None)
def local_items():
    removed={'A4-01-BASE','A4-02-SHOULDER-DECK','A4-03-YAW-WASHER',
             'J1 fitted body','J1 sleeve pin 0','J1 sleeve pin 1'}
    return [i for i in a.local_items() if i.name not in removed]+bearing_items()


def assembly(q=(0,-35,75,-40,0)):
    fs=a.frames(q)
    return [a.Item(i.name,a.transform(i.shape,fs[i.frame]),i.frame,i.part_id,i.group,i.color) for i in local_items()]


def base_assembly():
    return [i for i in local_items() if i.frame in ['base','yaw']]


def print_pose(name,s):
    if name in ['PB02_02_YILDIZ_YUVALI_DONER_OMUZ','PB02_03A_YAN_KAPAK','PB02_03B_YAN_KAPAK','PB02_06_DOLU_KAPAK_PIMI','PB02_08_KALIN_AYAK_PIMI']:
        s=s.rotate((0,0,0),(1,0,0),180)
    box=s.val().BoundingBox()
    return s.translate((-box.xmin,-box.ymin,-box.zmin))


def labelled_render(items,path,title,**kw):
    render(items,path,title,**kw)
    im=Image.open(path);d=ImageDraw.Draw(im);w,h=im.size
    d.rectangle((0,h-62,w,h),fill=(248,248,248))
    font=lambda n:ImageFont.truetype('C:/Windows/Fonts/arial.ttf',n)
    d.text((w/2,h-48),'Turuncu: yıldız yuvalı dönen tabla • Mavi: sabit motor gövdesi • Beyaz: bilyeler',font=font(17),fill='#16323d',anchor='mt')
    d.text((w/2,h-22),'Dijital montaj — ölçü uyumu, sürtünme ve yük taşıma fiziksel olarak doğrulanmalı.',font=font(16),fill='#5a6470',anchor='mt')
    im.save(path)


def export_assembly(items,folder,stem):
    assy=cq.Assembly(name=stem);scene=trimesh.Scene()
    for k,i in enumerate(items):
        name=f'{k:03}_{i.name}'.replace(' ','_')
        assy.add(i.shape,name=name,color=cq.Color(*i.color))
        m=pb.mesh(i.shape);m.visual.face_colors=np.array([*i.color,1])*255
        scene.add_geometry(m,node_name=name)
    assy.save(str(folder/(stem+'.step')));scene.export(folder/(stem+'.glb'))


def urdf():
    folder=OUT/'URDF';folder.mkdir(exist_ok=True)
    root=ET.Element('robot',name='PB02_FULL_ARM_GEOMETRY_REVIEW_NO_DYNAMICS')
    for frame in a.frames():
        chunks=[i.shape.val() for i in local_items() if i.frame==frame]
        cq.exporters.export(cq.Compound.makeCompound(chunks),str(folder/(frame+'.stl')),tolerance=.08,angularTolerance=.1)
        link=ET.SubElement(root,'link',name=frame)
        for tag in ['visual','collision']:
            geo=ET.SubElement(ET.SubElement(link,tag),'geometry')
            ET.SubElement(geo,'mesh',filename=frame+'.stl',scale='.001 .001 .001')
    joints=[('J1','base','yaw',(0,0,0),'0 0 1',-30,30),('J2','yaw','upper',(0,0,.124),'0 1 0',-45,-35),
            ('J3','upper','fore',(.300,0,0),'0 1 0',60,75),('W1','fore','tool',(.220,0,0),'0 1 0',-40,-15),
            ('G1','tool','finger',(.030,0,-.066),'0 1 0',-20,0)]
    for name,pa,ch,pos,axis,lo,hi in joints:
        j=ET.SubElement(root,'joint',name=name,type='revolute')
        ET.SubElement(j,'parent',link=pa);ET.SubElement(j,'child',link=ch)
        ET.SubElement(j,'origin',xyz=' '.join(map(str,pos)),rpy='0 0 0');ET.SubElement(j,'axis',xyz=axis)
        ET.SubElement(j,'limit',lower=str(math.radians(lo)),upper=str(math.radians(hi)),effort='0',velocity='0')
    ET.indent(root);ET.ElementTree(root).write(folder/'PB02_ARM_REVIEW.urdf',encoding='utf-8',xml_declaration=True)


def main():
    OUT.mkdir(exist_ok=True,parents=True);rows=[];meshes={}
    for name,(fn,qty) in PARTS.items():
        s=fn();assert s.val().isValid() and len(s.solids().vals())==1,name
        p=print_pose(name,s);export_shape(p,OUT/'TEKIL',name,['step','stl'])
        m=pb.mesh(p);m.export(OUT/'TEKIL'/(name+'.stl'));meshes[name]=m
        rows.append({'part':name,'qty':qty,'size_mm':m.extents.tolist(),'volume_mm3':float(m.volume)})
        print('export',name,flush=True)
    groups=[('01_MOTOR_TABANI',['PB02_01_SABIT_MOTOR_TABANI']),
            ('02_SABIT_YATAK_6_KALIN_PIM',['PB02_07_SABIT_YATAK_AYAKLARI','PB02_08_KALIN_AYAK_PIMI']),
            ('03_YILDIZLI_DONER_TABLA',['PB02_02_YILDIZ_YUVALI_DONER_OMUZ']),
            ('04_KAPAK_PIMLER',['PB02_03A_YAN_KAPAK','PB02_03B_YAN_KAPAK','PB02_06_DOLU_KAPAK_PIMI']),
            ('05_KAFES_24_BILYE_DESTEK_ZORUNLU',['PB02_04_BILYE_KAFESI','PB02_05_BILYE_8MM'])]
    plates=[]
    for label,names in groups:
        entries=[];x=y=10.;rh=0
        for name in names:
            for n in range(PARTS[name][1]):
                m=meshes[name].copy();dx,dy,dz=m.extents
                if x+dx>242:x=10.;y+=rh+12;rh=0
                assert y+dy<246 and dz<256,(label,name,y+dy)
                m.apply_translation((x,y,0));entries.append((name+f'__{n+1}',m));x+=dx+12;rh=max(rh,dy)
        write_3mf(entries,OUT/(label+'.3mf'));combined=trimesh.util.concatenate([m for _,m in entries]);combined.export(OUT/(label+'.stl'))
        plates.append({'file':label+'.3mf','objects':[n for n,m in entries],'bounds_mm':combined.bounds.tolist(),
                       'sha256':hashlib.sha256((OUT/(label+'.3mf')).read_bytes()).hexdigest()})
    export_assembly(base_assembly(),OUT,'PB02_MOTORLU_TABAN_MONTAJ')
    export_assembly(assembly(),OUT,'PB02_TAM_KOL_MONTAJ');urdf()
    labelled_render(base_assembly(),OUT/'01_MOTORLU_TABAN.png','PB02 — motor, yıldızlı tabla ve omuz bağlantıları',az=-65,el=30,w=1200,h=900)
    labelled_render(assembly(),OUT/'02_TAM_KOL.png','PB02 — mevcut kol ile tam montaj',az=-65,el=20,w=1400,h=950)
    # Functional rotor underside: show real keyed pocket and old opposed caps.
    core=[a.Item('rotor',rotor(),'yaw',color=a.GOLD)]
    for k,cap in enumerate(a.large.caps_pose(a.large.build()[1],travel=46)):
        core.append(a.Item(f'kapak{k}',a.transform(cap,a.YAW_HORN),'yaw',color=a.PURPLE))
    labelled_render(core,OUT/'03_ALT_YUZ_YILDIZ_YUVASI.png','Üst tablanın alt yüzü — aynı yıldız yuvası ve iki mevcut kapak',az=-90,el=-65,w=1200,h=900)
    cut=a.box(400,200,400,(0,-100,100));section=[]
    for i in base_assembly():
        if i.name.startswith('J2'):continue
        s=i.shape.cut(cut)
        if s.val().Volume()>1e-5:section.append(a.Item(i.name,s,i.frame,color=i.color))
    labelled_render(section,OUT/'04_MOTOR_YATAK_KESIT.png','Kesit — motor sabit, yıldız yuvalı tabla bilyeler üzerinde',az=-90,el=5,w=1200,h=900)
    report={'status':'INTEGRATED DIGITAL PROTOTYPE; PHYSICAL FIT/LOAD VALIDATION REQUIRED',
            'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'dependencies_sha256':{Path(m.__file__).name:hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest() for m in [a,a.large,pb]},
            'parts':rows,'plates':plates,'bearing_z_mm':BEARING_Z,'motor_origin_z_mm':58,
            'upper_race_centre_local_z_mm':UPPER_RACE_CENTRE_Z,'ball_centre_local_z_mm':BALL_CENTRE_Z,
            'revision':'DEC-071 inner retainer roof relief; other interfaces unchanged',
            'retainer_axial_clearance_mm':CAP_AXIAL_CLEARANCE,
            'retainer_inner_roof_remaining_mm':18.4-(15.+CAP_AXIAL_CLEARANCE),
            'shoulder_axis_z_mm':124,'deck_top_z_mm':78.5,'screw_access_diameter_mm':8,
            'star_interface':'same SNAP02 central46x44 pocket/rails/caps; demonstration tongue excluded',
            'stationary_race_mount':'4 keyed8mm feet and4 solid6.2mm cross-pins; physical retention UNVERIFIED',
            'retainer_installation':'2 radial halves, 2 additional6.2mm joining pins, 3 original vertical anti-rotation pins; no top-down cap insertion',
            'reused':['original MG996R horn','2 existing SNAP02 opposed caps','original servo centre screw',
                      'existing J1 motor clamps/pins','existing shoulder towers and their locking pins'],
            'replaced':['A4-01-BASE','A4-02-SHOULDER-DECK','A4-03-YAW-WASHER','J1 SNAP02 separate capsule body and its2 tongue pins'],
            'adapter_complete_digitally':True,'physical_validation':False,'load_capacity_N':None,
            'yaw_loaded_friction_Nm':None,'servo_axial_load_isolation_measured':False,
            'new_print_full_solid_PLA_g_ESTIMATE':sum(r['volume_mm3']*r['qty'] for r in rows)*.00124,
            'PLA_density_g_mm3_ASSUMED':.00124,'filament_TRY_kg':None,'cost_TRY':None,
            'purchased_ledger_changed':False,'printer_job_sent':False}
    (OUT/'MANIFEST.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('PB02 rebuilt',flush=True)


if __name__=='__main__':main()
