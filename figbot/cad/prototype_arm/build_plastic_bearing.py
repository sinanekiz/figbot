"""PB01: isolated, all-printed captive bearing experiment, NOT an arm retrofit.

The small coupon and large candidate share the same race cross section.  Real
rolling friction, wear, pull-out resistance and printer fit remain unverified.
No embedded printing supports, no modification of working AERO/horn geometry.
"""
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import math
import json
import hashlib
import zipfile
import xml.etree.ElementTree as ET
import cadquery as cq
import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont
from cad.utils import ROOT, export_shape
from cad.prototype_arm import build_aero_v4 as arm
from cad.prototype_arm.export_aero_v4 import write_3mf, render

OUT = ROOT / 'cad/prototype_arm/plastic_bearing_pb01'
BALL_D = 8.0
GROOVE_R = 4.2
BALL_Z = 8.0


@dataclass(frozen=True)
class Spec:
    name: str
    pitch_r: float
    balls: int


SMALL = Spec('01_ONCE_KUCUK_DENEME', 20., 6)
LARGE = Spec('02_BUYUK_ADAY_KOLA_HENUZ_TAKMA', 45., 24)


def bearing_render(entries,path,title,**kwargs):
    # Reuse CAD projection, but label this experiment rather than AERO horn parts.
    render(entries,path,title,**kwargs)
    im=Image.open(path);d=ImageDraw.Draw(im);w,h=im.size
    d.rectangle((0,h-62,w,h),fill=(248,248,248))
    font=lambda n:ImageFont.truetype('C:/Windows/Fonts/arial.ttf',n)
    d.text((w/2,h-47),'Turuncu: dönen halka • Beyaz: bilye • Mor: kafes • Mavi: sabit yatak/kapak',font=font(18),fill='#16323d',anchor='mt')
    d.text((w/2,h-22),'Yalnızca elle deneme — yük kapasitesi ve kol bağlantısı henüz doğrulanmadı.',font=font(16),fill='#5a6470',anchor='mt')
    im.save(path)


def annulus(inside, outside, bottom, top):
    return cq.Workplane('XY').circle(outside).circle(inside).extrude(top-bottom).translate((0, 0, bottom))


def sector(inside, outside, bottom, top, start, end):
    points = []
    for radius, angles in [(outside, np.linspace(start, end, 30)),
                           (inside, np.linspace(end, start, 30))]:
        points += [(radius*math.cos(math.radians(a)), radius*math.sin(math.radians(a))) for a in angles]
    return cq.Workplane('XY').polyline(points).close().extrude(top-bottom).translate((0,0,bottom))


def groove(spec):
    return cq.Workplane(obj=cq.Solid.makeTorus(spec.pitch_r, GROOVE_R, (0,0,BALL_Z)))


def lock_holes(shape, spec, bottom, top):
    for theta in [0, 120, 240]:
        a = math.radians(theta); radius = spec.pitch_r+16
        tool = cq.Workplane('XY').center(radius*math.cos(a),radius*math.sin(a)).circle(1.65).extrude(top-bottom).translate((0,0,bottom))
        shape = shape.cut(tool)
    return shape


@lru_cache(None)
def lower(spec):
    r = spec.pitch_r
    s = annulus(r-10, r+13, 0, 6).cut(groove(spec))
    # Inner plain guide; supports radial centering independently of the motor.
    s = s.union(annulus(r-10, r-7.5, 0, 10))
    # Broad, unsplit bayonet lugs. Load-bearing retention is NOT a thin clip.
    for theta in [0,120,240]:
        s = s.union(sector(r+12, r+18, 3, 5, theta-6, theta+6))
    return lock_holes(s,spec,0,6)


@lru_cache(None)
def rotor(spec):
    r=spec.pitch_r
    s = annulus(r-7, r+9, 10, 15).cut(groove(spec))
    s = s.union(annulus(r-7, r-5, 6.5, 10.1))
    # Exposed output ring for hand testing / future adapter, clear of retainer.
    s = s.union(annulus(r-7, r+4, 14.9, 21))
    # Four visible blind sockets, NOT claimed to match existing arm holes.
    for theta in [45,135,225,315]:
        a=math.radians(theta); rr=r-1.5
        tool=cq.Workplane('XY').center(rr*math.cos(a),rr*math.sin(a)).rect(4.4,4.4).extrude(5.1).translate((0,0,16))
        s=s.cut(tool)
    return s


@lru_cache(None)
def cap(spec):
    r=spec.pitch_r
    s=annulus(r+13.4,r+20.2,.5,18.4)
    s=s.union(annulus(r+6.5,r+20.2,15.4,18.4))
    # Install with cap rotated -30 degrees, lower vertically, rotate +30.
    # Entry channels are +30 degrees in cap-local coordinates.
    for theta in [0,120,240]:
        s=s.cut(sector(r+12.5,r+20.8,0,5.5,theta+22,theta+38))
        s=s.cut(sector(r+12.5,r+18.6,2.6,5.5,theta-8,theta+38))
    return lock_holes(s,spec,1.4,20)


@lru_cache(None)
def cage(spec):
    r=spec.pitch_r
    # Outer rim >=1.2 mm at each ball opening (not an unprintable0.2mm web).
    s=annulus(r-4.8,r+5.5,7.2,8.8)
    for k in range(spec.balls):
        a=2*math.pi*k/spec.balls
        tool=cq.Workplane('XY').center(r*math.cos(a),r*math.sin(a)).circle(4.3).extrude(4).translate((0,0,6))
        s=s.cut(tool)
    return s


@lru_cache(None)
def ball():
    # Full sphere; zero-flat CAD. Slicer-generated supports MUST be used.
    return cq.Workplane(obj=cq.Solid.makeSphere(BALL_D/2,angleDegrees1=-90,angleDegrees2=90))


@lru_cache(None)
def pin():
    # No split / no barb. The bayonet lugs carry uplift; pins block rotation.
    stem=cq.Workplane('XY').circle(1.5).extrude(16.3)
    head=cq.Workplane('XY').circle(3).extrude(1.8).translate((0,0,16.3))
    return stem.union(head)


def items(spec):
    out=[arm.Item('ALT_YATAK',lower(spec),'fixed',color=arm.BLUE),
         arm.Item('DONEN_HALKA',rotor(spec),'rotor',color=arm.GOLD),
         arm.Item('KAFES',cage(spec),'cage',color=arm.PURPLE),
         arm.Item('BAYONET_KAPAK',cap(spec),'fixed',color=arm.LIGHT)]
    for k in range(spec.balls):
        a=2*math.pi*k/spec.balls
        out.append(arm.Item(f'BILYE_{k+1:02}',ball().translate((spec.pitch_r*math.cos(a),spec.pitch_r*math.sin(a),BALL_Z)), 'balls',color=(.9,.9,.88)))
    for k,theta in enumerate([0,120,240]):
        a=math.radians(theta);rr=spec.pitch_r+16
        out.append(arm.Item(f'KILIT_PIMI_{k+1}',pin().translate((rr*math.cos(a),rr*math.sin(a),2.1)), 'fixed',color=arm.DARK))
    return out


def print_pose(name,s):
    if name in ['DONEN_HALKA','BAYONET_KAPAK','KILIT_PIMI']:
        s=s.rotate((0,0,0),(1,0,0),180)
    b=s.val().BoundingBox()
    return s.translate((-b.xmin,-b.ymin,-b.zmin))


def mesh(s):
    vertices, faces=s.val().tessellate(.03,.06)
    m=trimesh.Trimesh([[p.x,p.y,p.z] for p in vertices],faces,process=True,validate=True)
    m.merge_vertices(digits_vertex=5)
    m.update_faces(m.nondegenerate_faces());m.remove_unreferenced_vertices()
    assert m.is_watertight and m.is_volume
    return m


def fixed_urdf(entries,folder):
    root=ET.Element('robot',name='PB01_FIXED_REVIEW_NOT_DYNAMICS');ET.SubElement(root,'link',name='world')
    for i in entries:
        cq.exporters.export(i.shape,str(folder/(i.name+'.stl')),tolerance=.03,angularTolerance=.06)
        link=ET.SubElement(root,'link',name=i.name)
        for tag in ['visual','collision']:
            geo=ET.SubElement(ET.SubElement(link,tag),'geometry')
            ET.SubElement(geo,'mesh',filename=i.name+'.stl',scale='.001 .001 .001')
        joint=ET.SubElement(root,'joint',name=i.name+'_review',type='fixed')
        ET.SubElement(joint,'parent',link='world');ET.SubElement(joint,'child',link=i.name)
    ET.indent(root);ET.ElementTree(root).write(folder/'PB01_REVIEW.urdf',encoding='utf-8',xml_declaration=True)


def plate(entries,path):
    write_3mf(entries,path.with_suffix('.3mf'))
    combined=trimesh.util.concatenate([m for _,m in entries]);combined.export(path.with_suffix('.stl'))
    return {'file':path.name+'.3mf','objects':[n for n,m in entries], 'bounds_mm':combined.bounds.tolist(),
            'machine_profile':None,'integrated_supports':False}


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    reports=[]
    for spec in [SMALL,LARGE]:
        folder=OUT/spec.name;folder.mkdir(exist_ok=True)
        parts={'ALT_YATAK':(lower(spec),1),'DONEN_HALKA':(rotor(spec),1),
               'KAFES':(cage(spec),1),'BAYONET_KAPAK':(cap(spec),1),
               'BILYE_8MM':(ball(),spec.balls),'KILIT_PIMI':(pin(),3)}
        rows=[];body_entries=[];x=y=10.;rh=0
        # Split large bodies onto two beds; do not combine unrelated arm parts.
        plates=[];index=1
        for name,(s,qty) in parts.items():
            assert s.val().isValid() and len(s.solids().vals())==1,name
            p=print_pose(name,s)
            export_shape(p,folder/'TEKIL',name,['stl','step'])
            m=mesh(p);m.export(folder/'TEKIL'/f'{name}.stl')
            rows.append({'part':name,'qty':qty,'solid_volume_mm3':float(m.volume),'size_mm':m.extents.tolist()})
            if name=='BILYE_8MM':continue
            for k in range(qty):
                mm=m.copy();dx,dy,dz=mm.extents
                if x+dx>246:x=10.;y+=rh+10;rh=0
                if y+dy>246:
                    plates.append(plate(body_entries,folder/f'GOVDE_TABLA_{index}'));index+=1
                    body_entries=[];x=y=10.;rh=0
                mm.apply_translation((x,y,0));body_entries.append((name+f'_{k+1}',mm));x+=dx+10;rh=max(rh,dy)
        if body_entries:plates.append(plate(body_entries,folder/f'GOVDE_TABLA_{index}'))
        balls=[];m=mesh(print_pose('BILYE_8MM',ball()))
        for k in range(spec.balls):
            mm=m.copy();mm.apply_translation((15+(k%6)*18,15+(k//6)*18,0));balls.append((f'BILYE_{k+1}',mm))
        plates.append(plate(balls,folder/'BILYELER_DESTEK_ZORUNLU'))
        assembly=cq.Assembly(name='PB01_HAND_TEST_ONLY');scene=trimesh.Scene();entries=items(spec)
        for i in entries:
            assembly.add(i.shape,name=i.name,color=cq.Color(*i.color))
            mm=mesh(i.shape);mm.visual.face_colors=np.array([*i.color,1])*255;scene.add_geometry(mm,node_name=i.name)
        assembly.save(str(folder/'MONTAJ.step'));scene.export(folder/'MONTAJ.glb')
        ur=folder/'URDF';ur.mkdir(exist_ok=True);fixed_urdf(entries,ur)
        bearing_render(entries,folder/'MONTAJ.png','PB01 — elle denenecek plastik bilyalı yatak',az=-65,el=35,w=1100,h=780)
        cut=arm.box(400,200,100,(0,-100,0))
        section=[]
        for i in entries:
            s=i.shape.cut(cut)
            if s.val().Volume()>1e-6:section.append(arm.Item(i.name,s,i.frame,color=i.color))
        bearing_render(section,folder/'KESIT.png','Kesit — turuncu halka, beyaz bilyeler, mavi tutucu',az=-90,el=15,w=1100,h=780)
        exploded=[]
        for i in entries:
            dz=0 if i.name=='ALT_YATAK' else 14 if i.name.startswith(('KAFES','BILYE')) else 32 if i.name=='DONEN_HALKA' else 52
            exploded.append(arm.Item(i.name,i.shape.translate((0,0,dz)),i.frame,color=i.color))
        bearing_render(exploded,folder/'MONTAJ_SIRASI.png','Alt yatak → kafes/bilyeler → dönen halka → kapak/pimler',az=-65,el=25,w=1100,h=1000)
        volume=sum(r['solid_volume_mm3']*r['qty'] for r in rows)
        report={'variant':spec.name,'status':'HAND FIT TRIAL ONLY; PHYSICAL VALIDATION REQUIRED',
                'pitch_diameter_mm':spec.pitch_r*2,'ball_diameter_mm':BALL_D,'ball_qty':spec.balls,
                'outside_diameter_mm':2*(spec.pitch_r+20.2),'clear_bore_mm':2*(spec.pitch_r-10),
                'race_radius_mm':GROOVE_R,'nominal_radial_guide_clearance_mm':.5,
                'nominal_rotor_to_retainer_gap_mm':.4,'bayonet_rotation_deg':30,
                'parts':rows,'plates':plates,'full_solid_PLA_g_ESTIMATE':volume*.00124,
                'density_g_mm3_ASSUMED':.00124,'filament_price_TRY_kg':None,'cost_TRY':None,
                'support_mass_g':None,'purchase_ledger_changed':False,'arm_adapter_complete':False,
                'printer_job_sent':False,'load_capacity_N':None,'friction_torque_Nm':None,
                'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
        (folder/'MANIFEST.json').write_text(json.dumps(report,indent=2),encoding='utf-8');reports.append(report)
        print(spec.name,round(volume*.00124,2),'g full-solid estimate',flush=True)
    (OUT/'MANIFEST.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')


if __name__=='__main__':main()
