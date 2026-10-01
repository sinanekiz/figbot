"""Export the DEC-083 mechanical review to the single current delivery root.

Does not call old print-package generators or replace a gripper print release.
"""
from pathlib import Path
import csv,json,shutil,math
import xml.etree.ElementTree as ET
import cadquery as cq
import trimesh,numpy as np
from cad.prototype_arm import geared_gripper as g,build_linka_v1 as a
from cad.prototype_arm.export_linka_v1 import mass_report
from cad.prototype_arm.export_forma_v6 import mesh
from cad.prototype_arm.linka_render import render
from scripts.project_paths import ROOT,CAD

OUT=CAD/'DISLI_TUTUCU_INCELEME'
def scene(items,stem):
    ass=cq.Assembly(name=stem);sc=trimesh.Scene()
    for k,i in enumerate(items):
        name=f'{k:03}_{i.name}'.replace(' ','_');m=mesh(i.shape)
        m.visual.face_colors=(np.array([*i.color,1])*255).astype(np.uint8)
        ass.add(i.shape,name=name,color=cq.Color(*i.color));sc.add_geometry(m,node_name=name)
    ass.save(str(OUT/(stem+'.step')),write_pcurves=False);sc.export(OUT/(stem+'.glb'))
    target=ROOT/'viewer/public/models/guncel';target.mkdir(parents=True,exist_ok=True)
    shutil.copy2(OUT/(stem+'.glb'),target/(stem+'.glb'))

def arm_items(angle=0):
    old=a.local_items();items=[i for i in old if i.frame!='tool' or 'W1' in i.name]
    items += [a.Item(i.name,i.shape.translate((0,-g.WRIST_MOUNT_Y,0)),i.frame,i.part_id,i.color,i.mass_g) for i in g.items(angle)]
    fs=a.frames((0,-60,95,-35))
    return [a.Item(i.name,a.h.move(i.shape,fs[i.frame]),i.frame,i.part_id,i.color,i.mass_g) for i in items]

def main():
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'PART_STEP').mkdir(exist_ok=True)
    (OUT/'URDF').mkdir(exist_ok=True)
    items=g.items();parts=[]
    for i in items:
        if not i.part_id:continue
        s=i.shape.val();assert s.isValid() and len(s.Solids())==1,i.name
        cq.exporters.export(i.shape,str(OUT/'PART_STEP'/f'{i.part_id}.step'))
        parts.append(dict(id=i.part_id,volume_mm3=s.Volume(),mass_estimate_g=s.Volume()*.00124,material='TPU' if 'PAD' in i.part_id else 'PLA',status='REVIEW ONLY; no print release'))
    for suffix,angle,exploded in [('GEARED_CLOSED',0,False),('GEARED_OPEN',g.OPEN,False),('GEARED_SERVICE',0,True)]:
        scene(g.items(angle,exploded),'LINKA_L1_'+suffix)
        render(g.items(angle,exploded),OUT/(suffix+'.png'),g.REVISION+' / '+suffix,az=-55,el=30,revision='DEC-083')
    scene(arm_items(),'LINKA_L1_GEARED_ARM')
    render(arm_items(),OUT/'GEARED_ARM.png','DEC-083 / One bakan disli kepce',revision='DEC-083')
    report=mass_report(items);old=mass_report([i for i in a.local_items() if i.frame=='tool'])
    wrist=[i for i in a.local_items() if i.frame=='tool' and 'W1' in i.name]
    full=mass_report(items+wrist)
    report['comparison']={'old_tool_g':old['frame_totals_g']['tool'],'new_with_same_wrist_hardware_g':full['frame_totals_g']['tool'],
       'old_x_moment_g_mm':sum(r['mass_g']*r['center_mm'][0] for r in old['rows']),
       'new_x_moment_g_mm':sum(r['mass_g']*r['center_mm'][0] for r in full['rows']),
       'scope':'CAD/assigned material estimate, not weighed; missing cable and adhesive masses remain unknown'}
    report['parts']=parts;(OUT/'MASS_AND_PARTS.json').write_text(json.dumps(report,indent=2))
    # Mechanism-only review URDF: rigid chassis and two opposite jaw joints.
    root=ET.Element('robot',name='GEARED_GRIPPER_REVIEW')
    for name in ['chassis','left','right']:
        link=ET.SubElement(root,'link',name=name)
        if name=='chassis':selected=[i for i in items if not i.name.startswith(('JAW','PAD')) and not i.name.startswith('G1 original') and 'mounting' not in i.name]
        elif name=='left':selected=[i for i in items if i.name in ['JAW -1','PAD left']]
        else:selected=[i for i in items if i.name=='JAW 1' or i.name.startswith('PAD right')]
        m=trimesh.util.concatenate([mesh(i.shape) for i in selected])
        if name!='chassis':m.apply_translation((-g.CX,g.CY if name=='left' else -g.CY,0))
        m.apply_scale(.001);m.export(OUT/'URDF'/f'{name}.stl')
        vis=ET.SubElement(link,'visual');geo=ET.SubElement(vis,'geometry');ET.SubElement(geo,'mesh',filename=f'{name}.stl')
    for name,sign in [('left',-1),('right',1)]:
        j=ET.SubElement(root,'joint',name=name+'_jaw',type='revolute')
        ET.SubElement(j,'parent',link='chassis');ET.SubElement(j,'child',link=name)
        ET.SubElement(j,'origin',xyz=f'{g.CX/1000} {sign*g.CY/1000} 0');ET.SubElement(j,'axis',xyz='0 0 1')
        ET.SubElement(j,'limit',lower=str(-math.radians(g.OPEN) if sign<0 else 0),upper=str(math.radians(g.OPEN) if sign>0 else 0),effort='0',velocity='0')
        if sign>0:ET.SubElement(j,'mimic',joint='left_jaw',multiplier='-1',offset='0')
    ET.indent(root);ET.ElementTree(root).write(OUT/'URDF/REVIEW.urdf',encoding='utf-8',xml_declaration=True)
    (OUT/'COST_ESTIMATE.json').write_text(json.dumps({'status':'NEW TOOL CANDIDATE; not added to shopping list','motor_purchase':0,'new_hardware_unit_prices':None,'filament_price_per_kg':None,'total_try':None,'notes':'Two retained MG90S including wrist; new frame/gear jaws/cover replace current tool; no priced or approved purchase'},indent=2))
    print(json.dumps(report['comparison']),flush=True)

if __name__=='__main__':main()
