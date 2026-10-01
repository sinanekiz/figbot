"""Rebuild actual L1 part solids, assemblies, view assets and a review URDF."""
import json, shutil, math, csv
import xml.etree.ElementTree as ET
import numpy as np
import trimesh
import cadquery as cq
from cad.utils import export_shape
from cad.prototype_arm import build_linka_v1 as a
from cad.prototype_arm.export_forma_v6 import mesh,write_3mf
from cad.prototype_arm.linka_render import render
from scripts.arm_engineering_review import TARGETS

def scene(items,stem,step=True):
    sc=trimesh.Scene();ass=cq.Assembly(name=stem)
    for k,i in enumerate(items):
        name=f'{k:03}_{i.name}'.replace(' ','_')
        m=mesh(i.shape);m.visual.face_colors=(np.array([*i.color,1])*255).astype(np.uint8)
        sc.add_geometry(m,node_name=name)
        if step:ass.add(i.shape,name=name,color=cq.Color(*i.color))
    sc.export(a.OUT/(stem+'.glb'))
    if step:ass.save(str(a.OUT/(stem+'.step')),write_pcurves=False)
    dest=a.ROOT/'viewer/public/models/guncel';dest.mkdir(parents=True,exist_ok=True)
    shutil.copy2(a.OUT/(stem+'.glb'),dest/(stem+'.glb'))

def mass_report(items):
    rows=[]
    for i in items:
        m=i.mass_g if i.mass_g is not None else i.shape.val().Volume()*.00124
        c=i.shape.val().Center()
        rows.append(dict(name=i.name,frame=i.frame,pid=i.part_id,mass_g=m,center_mm=[c.x,c.y,c.z],basis='assigned hardware mass' if i.mass_g is not None else ('TPU density UNVERIFIED; CAD estimate uses1.24g/cm3; not weighed' if i.part_id=='L1-18-PAD' else 'CAD solid volume x PLA 1.24 g/cm3; not weighed')))
    totals={f:sum(r['mass_g'] for r in rows if r['frame']==f) for f in set(r['frame'] for r in rows)}
    return dict(rows=rows,frame_totals_g=totals,
        shoulder_downstream_g=sum(totals.get(f,0) for f in ['upper','fore','tool','rod']),
        note='Rotor/crank/yaw stators excluded from shoulder downstream, included in total robot mass. Add wiring and unmodelled fasteners before rating. No continuous-duty rating.')

def urdf(items):
    # Tree cut at D: rod passive distal constraint is explicitly in sidecar.
    root=ET.Element('robot',name='LINKA_L1_REVIEW')
    for frame in ['base','yaw','upper','fore','tool','crank','rod']:
        link=ET.SubElement(root,'link',name=frame)
        entries=[i for i in items if i.frame==frame]
        sc=trimesh.util.concatenate([mesh(i.shape) for i in entries]);sc.apply_scale(.001)
        sc.export(a.OUT/'URDF'/f'{frame}.stl')
        vis=ET.SubElement(link,'visual');geo=ET.SubElement(vis,'geometry');ET.SubElement(geo,'mesh',filename=f'{frame}.stl')
    l=a.solve_linkage(0,0)
    joints=[('yaw','base','revolute',(0,0,0),(0,0,1)),('upper','yaw','revolute',(0,0,a.Z),(0,1,0)),('fore','upper','revolute',(a.U,0,0),(0,1,0)),('tool','fore','revolute',(a.F,a.WRIST_Y,0),(0,1,0)),('crank','yaw','revolute',a.C,(0,1,0)),('rod','crank','continuous',(a.CRANK,0,0),(0,1,0))]
    for child,parent,kind,p,axis in joints:
        j=ET.SubElement(root,'joint',name=child+'_joint',type=kind)
        ET.SubElement(j,'parent',link=parent);ET.SubElement(j,'child',link=child)
        ET.SubElement(j,'origin',xyz=' '.join(str(v/1000) for v in p),rpy='0 0 0')
        ET.SubElement(j,'axis',xyz=' '.join(map(str,axis)))
        if kind=='revolute':ET.SubElement(j,'limit',lower='-3.14159',upper='3.14159',effort='0',velocity='0')
    ET.indent(root);ET.ElementTree(root).write(a.OUT/'URDF/LINKA_L1_REVIEW.urdf',encoding='utf8',xml_declaration=True)
    (a.OUT/'URDF/CLOSED_LOOP.json').write_text(json.dumps(dict(status='VISUALIZATION ONLY; zero effort/velocity; not controller limits',cut_joint='rod tip D to fore tail',rod_tip_mm=[a.ROD,-34,0],fore_tail_mm=[-a.TAIL,-34,0],solver='build_linka_v1.solve_linkage',coupling='gamma=solver(upper,upper+fore).gamma; rod relative angle=rod_angle-gamma',units='CAD mm; URDF m'),indent=2),encoding='utf8')

def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--preview',action='store_true');p.add_argument('--render',action='store_true');args=p.parse_args()
    a.OUT.mkdir(parents=True,exist_ok=True)
    items=a.assembly();scene(items,'LINKA_L1_ASSEMBLY',step=not args.preview)
    print('ASSEMBLY ready',flush=True)
    if args.preview:return
    for d in ['PRINT_STL','PART_STEP','3MF','URDF','VIEWS']:(a.OUT/d).mkdir(exist_ok=True)
    partrows=[]
    for pid,(fn,n,frame) in a.PARTS.items():
        s=fn()
        if len(s.val().Solids())!=1:raise ValueError(pid+' disconnected solids')
        placed=a.print_pose(pid,s)
        export_shape(placed,a.OUT/'PRINT_STL',pid,['stl'])
        export_shape(s,a.OUT/'PART_STEP',pid,['step'])
        # Actual clipped end/boss modifiers, exported in exactly the part print transform.
        mods=[];b=s.val().BoundingBox()
        if frame in ['upper','fore','rod','crank']:
            for label,x in [('ROOT',b.xmin+18),('TIP',b.xmax-18)]:
                region=s.intersect(a.h.box(36,180,150,(x,0,0)))
                # Transform using part, not each modifier's own bounding box.
                r=region
                if any(t in pid for t in ['UPPER','FORE','COUPLER','CRANK','FINGER','BEARING-CAP']):r=r.rotate((0,0,0),(1,0,0),90)
                raw=s.rotate((0,0,0),(1,0,0),90) if any(t in pid for t in ['UPPER','FORE','COUPLER','CRANK','FINGER','BEARING-CAP']) else s
                bb=raw.val().BoundingBox();r=r.translate((-bb.xmin,-bb.ymin,-bb.zmin))
                if region.val().Volume()>.1:mods.append((label+' 100pct',mesh(r)))
        write_3mf([(pid,pid,mesh(placed),mods)],a.OUT/'3MF'/f'{pid}.3mf')
        partrows.append(dict(id=pid,count=n,frame=frame,mass_each_g=s.val().Volume()*.00124,solid_count=len(s.val().Solids()),valid=s.val().isValid()))
        print(pid,flush=True)
    locals=a.local_items();report=mass_report(locals)
    report['parts']=partrows;report['reference_R6_downstream_g']=301.2308
    (a.OUT/'MASS_AND_PARTS.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    with (a.OUT/'PRINT_BOM.csv').open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=['id','count','material','cad_mass_each_g']);w.writeheader()
        for r in partrows:w.writerow(dict(id=r['id'],count=r['count'],material='TPU' if 'PAD' in r['id'] else 'PLA',cad_mass_each_g=round(r['mass_each_g'],3)))
    (a.OUT/'COST_ESTIMATE.json').write_text(json.dumps(dict(status='PRICING INCOMPLETE; no purchase',currency='TRY',printed_part_instances=sum(r['count'] for r in partrows),cad_solid_mass_g=sum(r['count']*r['mass_each_g'] for r in partrows),filament_price_per_kg=None,hardware_total=None,total=None,note='Unit prices and actual slicer material/support mass TBD. Null is unknown, not zero. Existing motors reused. Cost comparison is not available.'),indent=2),encoding='utf8')
    urdf(locals)
    poses={name:a.ik(t) for name,t in TARGETS.items()}
    (a.OUT/'POSES.json').write_text(json.dumps(poses,indent=2),encoding='utf8')
    for name in ['pickup','release']:
        scene(a.assembly(poses[name]),'LINKA_L1_'+name.upper(),step=True)
    scene([i for i in locals if i.frame=='tool'],'LINKA_L1_GRIPPER',step=True)
    closed=[i for i in a.local_items(a.SCOOP_CLOSED_ANGLE) if i.frame=='tool']
    scene(closed,'LINKA_L1_GRIPPER_CLOSED',step=True)
    scene([i for i in locals if i.frame in ['base','yaw']],'LINKA_L1_BASE',step=True)
    if args.render:
        render(items,a.OUT/'VIEWS/LINKA_L1_ISO.png',a.REVISION+' - Montaj')
        render([i for i in locals if i.frame=='tool'],a.OUT/'VIEWS/LINKA_L1_GRIPPER.png',a.REVISION+' - Uzun kepce parmaklar / acik',az=-65,el=-15)
        render(closed,a.OUT/'VIEWS/LINKA_L1_GRIPPER_CLOSED.png',a.REVISION+' - Kepce parmaklar / kapali aday',az=-65,el=-15)
    print(json.dumps(report['frame_totals_g']),flush=True)

if __name__=='__main__':main()
