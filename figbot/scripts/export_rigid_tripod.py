"""DEC-084 reproducible review export. Does not overwrite released print plates."""
import json,csv,math,shutil
from collections import Counter
import xml.etree.ElementTree as ET
import numpy as np
import cadquery as cq
import trimesh
from cad.prototype_arm import rigid_tripod_gripper as g,build_linka_v1 as a
from cad.prototype_arm.export_linka_v1 import mass_report,urdf as arm_urdf
from cad.prototype_arm.export_forma_v6 import mesh
from cad.prototype_arm.linka_render import render
from scripts.project_paths import CAD,ROOT

OUT=CAD/'TUTUCU'
PARTS={'RT-FRAME':(g.frame,1),'RT-GUIDE':(g.guide_cap,2),'RT-RACK':(g.rack_slider,1),
       'RT-PINION':(g.pinion,1),'RT-FINGER':(g.finger,3),'RT-LINK':(g.link,3),'RT-JOINT-BUSH':(g.joint_bush,6)}

def arm_items(deg):
    old=[i for i in a.local_items() if i.frame!='tool' or 'W1' in i.name]
    fs=a.frames((0,-60,95,-35))
    return [a.Item(i.name,a.h.move(i.shape,fs[i.frame]),i.frame,i.part_id,i.color,i.mass_g) for i in old+g.tool_items(deg)]

def scene(items,key):
    assembly=cq.Assembly(name=key);sc=trimesh.Scene()
    for k,i in enumerate(items):
        name=f'{k:03}_{i.name}'.replace(' ','_');t=mesh(i.shape)
        t.visual.face_colors=(np.array([*i.color,1])*255).astype(np.uint8)
        assembly.add(i.shape,name=name,color=cq.Color(*i.color));sc.add_geometry(t,node_name=name)
    assembly.save(str(OUT/(key+'.step')),write_pcurves=False);sc.export(OUT/(key+'.glb'))
    target=ROOT/'viewer/public/models/guncel';target.mkdir(exist_ok=True,parents=True)
    shutil.copy2(OUT/(key+'.glb'),target/(key+'.glb'))

def urdf():
    items=g.items();q=g.state(0);groups={};used=set()
    def pick(name,predicate,origin):
        rows=[i for i in items if predicate(i.name)];used.update(id(i) for i in rows);groups[name]=(rows,np.array(origin))
    pick('gear',lambda n:n=='RT pinion' or (n.startswith('G1 ') and n not in ['G1 servo'] and 'ear ' not in n),(g.PX,g.MOTOR_Y,g.PZ))
    pick('slider',lambda n:n=='RT rack' or n.startswith('slider '),(0,0,q['slider'][2]))
    for phi in [0,120,240]:
        r=a.h.rz(phi)
        pick('finger'+str(phi),lambda n:n=='RT finger '+str(phi) or n.startswith('finger ') and n.endswith(' '+str(phi)),r@np.array([g.PIVOT,0,0]))
        pick('rod'+str(phi),lambda n:n=='RT link '+str(phi),r@q['slider'])
    groups['base']=([i for i in items if id(i) not in used],np.zeros(3))
    root=ET.Element('robot',name='THREE_RIGID_FINGERS_GEOMETRY_REVIEW')
    for key,(rows,origin) in groups.items():
        m=trimesh.util.concatenate([mesh(i.shape) for i in rows]);m.apply_translation(-origin);m.apply_scale(.001);m.export(OUT/'URDF'/f'{key}.stl')
        link=ET.SubElement(root,'link',name=key);v=ET.SubElement(link,'visual');geo=ET.SubElement(v,'geometry');ET.SubElement(geo,'mesh',filename=f'{key}.stl')
    def joint(name,parent,axis,lo,hi,kind='revolute'):
        j=ET.SubElement(root,'joint',name=name+'_joint',type=kind);ET.SubElement(j,'parent',link=parent);ET.SubElement(j,'child',link=name)
        origin=(groups[name][1]-groups[parent][1])/1000
        ET.SubElement(j,'origin',xyz=' '.join(map(str,origin)));ET.SubElement(j,'axis',xyz=' '.join(map(str,axis)))
        ET.SubElement(j,'limit',lower=str(lo),upper=str(hi),effort='0',velocity='0')
    joint('gear','base',(0,1,0),math.radians(g.state(g.OPEN)['gear_deg']),0)
    joint('slider','base',(0,0,1),0,(g.state(g.OPEN)['slider'][2]-q['slider'][2])/1000,'prismatic')
    for phi in [0,120,240]:
        axis=a.h.rz(phi)@np.array([0,1,0]);joint('finger'+str(phi),'base',axis,0,math.radians(g.OPEN))
        joint('rod'+str(phi),'slider',axis,0,math.radians(g.state(g.OPEN)['link_angle']-q['link_angle']))
    ET.indent(root);ET.ElementTree(root).write(OUT/'URDF/REVIEW.urdf',encoding='utf-8',xml_declaration=True)
    states=[{'finger_deg':v,'slider_mm':g.state(v)['slider'][2]-q['slider'][2],'gear_deg':g.state(v)['gear_deg'],
       'rod_relative_deg':g.state(v)['link_angle']-q['link_angle'],'closure_error_mm':float(abs(np.linalg.norm(g.state(v)['crank']-g.state(v)['slider'])-g.LINK))} for v in np.linspace(0,g.OPEN,101)]
    (OUT/'URDF/CLOSED_LOOP.json').write_text(json.dumps({'status':'Geometry-only cut tree; rod distal pivots close on fingers. Use all states together, not independent joints. No actuator configuration.', 'states':states},indent=2))

def procurement():
    source=json.loads((ROOT/'GUNCEL/ALISVERIS/VERI/MALZEMELER.json').read_text(encoding='utf-8'))
    deltas={'S28':6,'S26':4}
    for r in source['rows']:
        if 'M2 pirinç' in r['part']:deltas[r['code']]=6 if 'boy3' in r['part'] else 4
    rows=[]
    for r in source['rows']:
        if r['code'] not in deltas:continue
        d=deltas[r['code']];previous=r.get('previous_required',r['required']);new=previous+d
        rows.append({'code':r['code'],'part':r['part'],'previous_required':previous,'new_required':new,'added_use':d,
           'previous_buy_quantity':r['buy_quantity'],'additional_units_if_original_list_was_bought':max(0,new-r['buy_quantity']),
           'actual_owned':'UNVERIFIED','historical_price_per_pack_try':r['price_per_pack'],'pack_quantity':r['pack_quantity']})
    return {'status':'DESIGN COMPARISON, NOT A PURCHASE RECORD OR NEW SHOPPING RELEASE','new_motor_bearing_shaft_types':0,'rows':rows,
      'additional_buy_cost_if_list_was_bought_try':0 if all(r['additional_units_if_original_list_was_bought']==0 for r in rows) else None,
      'actual_buy_cost_try':None,'filament_price_per_kg_try':None,'total_print_cost_try':None,
      'notes':'No tendon or return elastic. Reuse3 M2x14 pivots and3 L1-25 printed bushes. New six printed linkage bushes. TPU not required; optional soft liner not dimensioned. Actual stock and print cost unknown.'}

def full_arm_urdf():
    saved=a.OUT
    try:
        a.OUT=OUT/'ARM_REVIEW';(a.OUT/'URDF').mkdir(parents=True,exist_ok=True)
        local=[i for i in a.local_items() if i.frame!='tool' or 'W1' in i.name]+g.tool_items()
        arm_urdf(local)
        (a.OUT/'OKU.md').write_text('Full arm geometry review with gripper fixed at CLOSED. The separate ../URDF contains the gripper joints and loop constraints. Neither is a controller configuration. Original arm linkage calibration and new tool reach remain unverified.\n')
    finally:a.OUT=saved

def main():
    for d in ['PART_STEP','PROTOTIP_STL','URDF']: (OUT/d).mkdir(parents=True,exist_ok=True)
    parts=[]
    for pid,(fn,count) in PARTS.items():
        s=fn();assert s.val().isValid() and len(s.val().Solids())==1,pid
        cq.exporters.export(s,str(OUT/'PART_STEP'/f'{pid}.step'));m=mesh(s)
        assert m.is_watertight,pid;m.export(OUT/'PROTOTIP_STL'/f'{pid}.stl')
        parts.append({'id':pid,'count':count,'material':'PLA','cad_mass_each_g':s.val().Volume()*.00124})
    for key,deg in [('TRIPOD_CLOSED',0),('TRIPOD_OPEN',g.OPEN)]:
        scene(g.tool_items(deg),'LINKA_L1_'+key)
        render(g.tool_items(deg),OUT/(key+'.png'),g.REVISION,az=-65,el=24,revision='DEC-084')
    scene(arm_items(0),'LINKA_L1_TRIPOD_ARM')
    render(arm_items(0),OUT/'TRIPOD_ARM.png',g.REVISION,revision='DEC-084')
    scene(g.items(0,True),'LINKA_L1_TRIPOD_SERVICE')
    render(g.items(0,True),OUT/'TRIPOD_SERVICE.png','Iki yandan sokulen kilavuz / DEC-084',revision='DEC-084')
    old=[i for i in a.local_items() if i.frame=='tool'];wrist=[i for i in old if 'W1' in i.name]
    report=mass_report(g.tool_items()+wrist);previous=mass_report(old)
    report['previous_tool_g']=previous['frame_totals_g']['tool'];report['parts']=parts
    report['old_gravity_moment_g_mm']=sum(r['mass_g']*r['center_mm'][0] for r in previous['rows'])
    report['new_gravity_moment_g_mm']=sum(r['mass_g']*r['center_mm'][0] for r in report['rows'])
    (OUT/'MASS_AND_PARTS.json').write_text(json.dumps(report,indent=2))
    (OUT/'MALZEME_KARSILASTIRMASI.json').write_text(json.dumps(procurement(),ensure_ascii=False,indent=2),encoding='utf-8')
    urdf();full_arm_urdf()
    for filename in ['AUDIT.json','SERVICE.json','ARM_INTERFACE.json']:
        shutil.copy2(ROOT/'reports/rigid_tripod'/filename,OUT/filename)
    (OUT/'STATUS.json').write_text(json.dumps({'revision':g.REVISION,'print_release':False,'physical_validation':'REQUIRED','scope':'Three rigid scoop fingers, existing G1 servo; no tendon.','source':'cad/prototype_arm/rigid_tripod_gripper.py'},indent=2))
    print(json.dumps({'tool_g':report['frame_totals_g']['tool'],'previous_g':report['previous_tool_g'],'parts':len(parts),'pieces':sum(p['count'] for p in parts)}),flush=True)

if __name__=='__main__':main()
