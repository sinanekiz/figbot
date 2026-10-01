"""Build oriented print files, assembly views, kinematic URDF and print ledger."""
import csv
import json
import hashlib
import shutil
import math
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

import cadquery as cq
import numpy as np
from cad.prototype_arm import build_aero_v3 as a
from cad.prototype_arm.audit_aero_v3 import vehicle,dual
from cad.prototype_arm.audit_aero_v2 import mesh_audit
from cad.utils import export_shape,shape_mesh


def oriented(name,shape):
    if name=='V3-02-YAW-DECK':shape=shape.rotate((0,0,0),(1,0,0),180)
    elif any(x in name for x in ('YOKE','HUB','PALM','MOVING-JAW','DRIVE-PLATE')):
        shape=shape.rotate((0,0,0),(1,0,0),-90)
    b=shape.val().BoundingBox()
    return shape.translate((-b.xmin,-b.ymin,-b.zmin))


def render(parts,path,title,side=False):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    fig=plt.figure(figsize=(12,8),facecolor='#f5f3ee')
    ax=fig.add_subplot(111,projection='3d')
    clouds=[]
    for c in parts:
        xyz,faces=shape_mesh(c.shape);clouds.append(xyz)
        ax.add_collection3d(Poly3DCollection(xyz[faces],facecolor=c.color,edgecolor=c.color,linewidth=.025))
    xyz=np.vstack(clouds);lo=xyz.min(axis=0);hi=xyz.max(axis=0);span=hi-lo
    ax.set(xlim=(lo[0]-25,hi[0]+25),ylim=(lo[1]-25,hi[1]+25),zlim=(lo[2]-20,hi[2]+25))
    ax.set_box_aspect(span+50);ax.set_axis_off();ax.view_init(elev=3 if side else 23,azim=-90 if side else 48)
    ax.set_title(title,fontsize=15,pad=15)
    fig.text(.09,.03,'AERO V3 • Dijital prototip • Motor/horn/boru/vida referansları baskı parçası değildir',fontsize=10,color='#8b482c')
    fig.savefig(path,dpi=150,bbox_inches='tight');plt.close(fig)


def model_export(parts,out,name):
    model=cq.Assembly(name=name)
    manifest=[]
    for i,c in enumerate(parts):
        model.add(c.shape,name=f'p{i:03d}_{c.name}',color=cq.Color(*c.color))
        file=f'{i:03d}.brep'
        c.shape.val().exportBrep(str(out/file))
        manifest.append({'id':f'Component{i:03d}','name':c.name,'group':c.group,'color':c.color,'brep':file,'volume':c.shape.val().Volume()})
    model.save(str(out/(name+'.step')),exportType='STEP')
    model.save(str(out/(name+'.glb')),exportType='GLTF',tolerance=.2,angularTolerance=.12)
    (out/'manifest.json').write_text(json.dumps({'parts':manifest,'revision':'AERO-V3'},indent=2),encoding='utf-8')


def frame_for(name):
    if name.startswith(('yaw base','yaw thrust','J1 case','J1 shaft','J1 clamp')):return 'base'
    if name.startswith(('yaw deck','shoulder yoke','J2 ')) and 'supplied horn' not in name:return 'yaw'
    if name.startswith('J1 supplied'):return 'yaw'
    if name.startswith(('upper hub','upper hollow','elbow yoke','J2 ')):return 'upper'
    if name.startswith('J3') and not any(s in name for s in ('supplied horn','sleeve','washer','axle','nut')):return 'upper'
    if name.startswith(('fore hub','fore hollow','wrist yoke','J3')):return 'fore'
    if name.startswith('W1') and not any(s in name for s in ('supplied horn','sleeve','washer','axle','nut')):return 'fore'
    if name in ('moving jaw','moving soft pad','G1 supplied horn'):return 'finger'
    return 'tool'


def urdf_export(out):
    zero=a.assembly((0,0,0),grip=0)
    origins={'base':(0,0,0),'yaw':(0,0,0),'upper':(0,0,a.SHOULDER_Z),'fore':(a.UPPER,0,a.SHOULDER_Z),'tool':(a.UPPER+a.FORE,0,a.SHOULDER_Z),'finger':(a.UPPER+a.FORE+20,0,a.SHOULDER_Z-40)}
    root=ET.Element('robot',name='FIGBOT_AERO_V3_KINEMATIC_REVIEW')
    for frame,origin in origins.items():
        solids=[c.shape.val().translate(tuple(-v for v in origin)) for c in zero if frame_for(c.name)==frame]
        compound=cq.Compound.makeCompound(solids)
        cq.exporters.export(compound,str(out/(frame+'.stl')),tolerance=.2)
        link=ET.SubElement(root,'link',name=frame)
        for kind in ('visual','collision'):
            geom=ET.SubElement(ET.SubElement(link,kind),'geometry')
            ET.SubElement(geom,'mesh',filename=frame+'.stl',scale='0.001 0.001 0.001')
    joints=[('J1','base','yaw',(0,0,0),'0 0 1',-100,100),('J2','yaw','upper',(0,0,a.SHOULDER_Z),'0 1 0',-100,40),('J3','upper','fore',(a.UPPER,0,0),'0 1 0',10,165),('W1','fore','tool',(a.FORE,0,0),'0 1 0',-135,20),('G1','tool','finger',(20,0,-40),'0 1 0',-25,25)]
    for name,parent,child,xyz,axis,low,high in joints:
        j=ET.SubElement(root,'joint',name=name,type='revolute')
        ET.SubElement(j,'parent',link=parent);ET.SubElement(j,'child',link=child)
        ET.SubElement(j,'origin',xyz=' '.join(str(v/1000) for v in xyz),rpy='0 0 0')
        ET.SubElement(j,'axis',xyz=axis)
        # No guessed rated effort/velocity: these are deliberately not a
        # dynamics/control deployment URDF. Zero prevents claiming capability.
        ET.SubElement(j,'limit',lower=str(math.radians(low)),upper=str(math.radians(high)),effort='0',velocity='0')
    ET.ElementTree(root).write(out/'AERO_V3_REVIEW.urdf',encoding='utf-8',xml_declaration=True)


def mass_report():
    rows=[]
    for pose,target in a.TARGETS.items():
        p=a.ik(target);components=a.assembly(p)
        moments={'shoulder':0.,'elbow':0.,'wrist':0.}
        total=0.;wrist_mass=0.
        elbow_x=a.UPPER*math.cos(math.radians(p[1]));wrist_x=elbow_x+a.FORE*math.cos(math.radians(p[2]))
        for c in components:
            frame=frame_for(c.name)
            if frame in ('base','yaw'):continue
            shape=c.shape.val();center=shape.Center()
            # Calculations are in the yawed bench frame; recover radial X.
            radial=center.x*math.cos(math.radians(p[0]))+center.y*math.sin(math.radians(p[0]))
            if c.group=='servo':m=13.4 if c.name.startswith(('W1','G1')) else 55.
            elif c.group=='shaft':m=0. # included in published servo mass
            else:m=shape.Volume()*{'printed':.00127,'tube':.00270,'horn':.00115,'hardware':.00785,'pad':.00035}.get(c.group,.00127)
            total+=m
            moments['shoulder']+=m/1000*radial/10
            if frame in ('fore','tool','finger'):moments['elbow']+=m/1000*(radial-elbow_x)/10
            if frame in ('tool','finger'):
                moments['wrist']+=m/1000*(radial-wrist_x)/10;wrist_mass+=m
        # 100 g test object, representative X at wrist; actual grasp CG TBD.
        moments['shoulder']+=.100*wrist_x/10
        moments['elbow']+=.100*(wrist_x-elbow_x)/10
        rows.append({'pose':pose,'moving_CAD_mass_g':round(total,1),'tool_CAD_mass_g':round(wrist_mass,1),'gravity_torque_100g_kgf_cm':{k:round(abs(v),3) for k,v in moments.items()}})
    return {'basis':'ESTIMATE: full CAD PETG volume at 1.27 g/cm3, aluminium 2.70, MG996R 55 g, MG90S 13.4 g, object 100 g at wrist X. Unmodelled screws, cables, nut preload, friction, acceleration and manufacturing variability excluded. Not a rated-load approval.',
            'wrist_source':'https://towerpro.com.tw/product/mg90s-3/',
            'note':'Original MG90S advertised 1.8 kgf.cm STALL at 4.8 V is not continuous torque or a clone guarantee. Do not infer motor heating or cycle rate from this comparison. First powered trials unloaded, then 40 g; 100 g only after load/current/thermal checks.', 'poses':rows}


def build():
    a.OUT.mkdir(parents=True,exist_ok=True)
    printdir=a.OUT/'PRINT_STL';printdir.mkdir(exist_ok=True)
    checks=[];manifest=[]
    for key,(builder,qty) in a.PRINT_PARTS.items():
        s=oriented(key,builder())
        export_shape(s,printdir,key,('stl','step'))
        checks.append(mesh_audit(printdir/(key+'.stl'),s.val()))
        b=s.val().BoundingBox()
        manifest.append([key,qty,round(b.xlen,2),round(b.ylen,2),round(b.zlen,2),round(s.val().Volume()*.00127,2),'PETG candidate','supports: inspect in slicer; not machine sliced'])
    assert all(c['mesh_ok'] for c in checks)
    (a.OUT/'MESH_AUDIT.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
    with (a.OUT/'PRINT_ORDER.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f);w.writerow(['part','quantity','x_mm','y_mm','z_mm','full_CAD_mass_g_each','material','slicing']);w.writerows(manifest)
    for name in a.TARGETS:
        arm_dir=a.OUT/('assembly_'+name);arm_dir.mkdir(exist_ok=True)
        arm=a.assembly(a.ik(a.TARGETS[name]),grip=-20 if name in ('pickup','release') else 5,base=a.BASE)
        model_export(arm,arm_dir,'FIGBOT_AERO_V3_'+name)
        render(arm,a.OUT/(name+'_arm.png'),'AERO V3 | '+name+' | Aktif bilek, aşağı bakan kıskaç',side=name=='pickup')
        rover_dir=a.OUT/('rover_'+name);rover_dir.mkdir(exist_ok=True)
        allparts=vehicle()+dual(name)
        model_export(allparts,rover_dir,'FIGBOT_ROVER_V3_'+name)
        render(allparts,a.OUT/(name+'_rover.png'),'FIGBOT | AERO V3 çift kol ve 15° sepet')
    urdf=a.OUT/'urdf';urdf.mkdir(exist_ok=True);urdf_export(urdf)
    (a.OUT/'MASS_TORQUE_ESTIMATE.json').write_text(json.dumps(mass_report(),indent=2),encoding='utf-8')
    fits=a.OUT/'FIT_STL';fits.mkdir(exist_ok=True)
    fit_shapes={
        'FIT-V3-MG996R-MOUNT':a.mount_plate(),
        'FIT-V3-MG90S-MOUNT':a.mount_plate(True),
        'FIT-V3-MG996R-CLAMP':a.clamp_bar(),
        'FIT-V3-MG90S-CLAMP':a.clamp_bar(True),
        'FIT-V3-HORN-MG996R':a.adapter(a.cyl_y(18,4),2).rotate((0,0,0),(1,0,0),90),
        'FIT-V3-HORN-MG90S':a.adapter(a.cyl_y(14,4),2,True).rotate((0,0,0),(1,0,0),90),
        'FIT-V3-IDLER-SLEEVE':a.pivot_sleeve(),
        'FIT-V3-IDLER-WASHER':a.pivot_washer(),
        'FIT-V3-TUBE-SOCKET':a.box(20,27,27).cut(a.box(24,20.5,20.5)).rotate((0,0,0),(0,1,0),90),
    }
    fit_checks=[]
    for name,s in fit_shapes.items():
        s=oriented(name,s)
        export_shape(s,fits,name,('stl',))
        fit_checks.append(mesh_audit(fits/(name+'.stl'),s.val()))
    assert all(c['mesh_ok'] for c in fit_checks)
    (a.OUT/'FIT_MESH_AUDIT.json').write_text(json.dumps(fit_checks,indent=2),encoding='utf-8')
    with (a.OUT/'FIT_PRINT_ORDER.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f);w.writerow(['part','qty'])
        for name in fit_shapes:w.writerow([name,2 if 'CLAMP' in name or 'WASHER' in name else 1])
    shutil.copy2(a.ROOT/'bom/AERO_V3_BENCH_HARDWARE.csv',a.OUT/'AERO_V3_BENCH_HARDWARE.csv')
    (a.OUT/'EXPORT_SOURCE_SHA256.txt').write_text(hashlib.sha256(Path(a.__file__).read_bytes()).hexdigest(),encoding='utf-8')
    print('V3 exports complete; packaging requires successful geometry audit',flush=True)


def package():
    audit=json.loads((a.OUT/'GEOMETRY_AUDIT.json').read_text(encoding='utf-8'))
    source=hashlib.sha256(Path(a.__file__).read_bytes()).hexdigest()
    assert audit['digital_geometry_ok'] and audit['source_sha256']==source
    assert (a.OUT/'EXPORT_SOURCE_SHA256.txt').read_text()==source
    for kind,folder in (('FIT_CHECK_FIRST','FIT_STL'),('BENCH_PRINT_STL','PRINT_STL')):
        with zipfile.ZipFile(a.OUT/('AERO_V3_'+kind+'.zip'),'w',zipfile.ZIP_DEFLATED) as z:
            for p in (a.OUT/folder).glob('*.stl'):z.write(p,'STL/'+p.name)
            for name in ('ONCE_OKU_MONTAJ.md','PRINT_ORDER.csv','FIT_PRINT_ORDER.csv','AERO_V3_BENCH_HARDWARE.csv','GEOMETRY_AUDIT.json','MESH_AUDIT.json','FIT_MESH_AUDIT.json','MASS_TORQUE_ESTIMATE.json'):
                z.write(a.OUT/name,name)
            z.write(a.OUT/'pickup_arm.png','MONTAJ_GORUNUMU.png')
        with zipfile.ZipFile(a.OUT/('AERO_V3_'+kind+'.zip')) as z:assert z.testzip() is None
    print('Packaged fit and full bench STL sets; physical checks remain required',flush=True)


if __name__=='__main__':build()
