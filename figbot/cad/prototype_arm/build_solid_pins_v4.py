"""Solid friction-pin trial. No split, no barb; P5 passive axle unchanged."""
from pathlib import Path
import json,hashlib,zipfile,xml.etree.ElementTree as ET
import cadquery as cq
import trimesh,numpy as np
from cad.utils import ROOT,export_shape,shape_mesh
from cad.prototype_arm import export_aero_v4 as ex
from cad.prototype_arm import build_aero_v4 as a
OUT=ROOT/'cad/prototype_arm/solid_pins_v4'
HEAD_D=6.05;HEAD_H=1.6;NOSE_H=1.2
SPECS={'P1':(7.4,8),'P2':(6.5,4),'P3':(9.6,24),'P4':(26.2,8),'P6':(12.2,4)}
DIAMETERS=[3.05,3.15,3.25,3.35,3.45]

def pin(grip,diam=3.05):
 s=cq.Workplane('XY').circle(HEAD_D/2).extrude(HEAD_H)
 s=s.union(cq.Workplane('XY').circle(diam/2).extrude(grip).translate((0,0,HEAD_H)))
 nose=cq.Workplane('XY').workplane(offset=HEAD_H+grip).circle(diam/2).workplane(offset=NOSE_H).circle((diam-.5)/2).loft()
 return s.union(nose)

def mesh(s):
 m=trimesh.Trimesh(*shape_mesh(s));assert m.is_watertight and m.is_volume;return m

def main():
 OUT.mkdir(exist_ok=True,parents=True)
 rows=[];entries=[];assembly=cq.Assembly(name='SOLID_PIN_PRINT_LAYOUT');scene=trimesh.Scene()
 root=ET.Element('robot',name='SOLID_PIN_LAYOUT_FIXED_REVIEW');ET.SubElement(root,'link',name='plate')
 index=0
 for name,(grip,qty) in SPECS.items():
  s=pin(grip);export_shape(s,OUT/'TEKIL',name+'_D305_DOLU',['stl','step'])
  m=mesh(s);rows.append({'pin':name,'qty':qty,'grip_mm':grip,'total_length_mm':grip+2.8,'diam_mm':3.05,'head_diam_mm':HEAD_D,'volume_mm3':float(m.volume)})
  for n in range(qty):
   at=(15+(index%8)*12,15+(index//8)*12,0);index+=1
   mm=m.copy();mm.apply_translation(at);entries.append((name+'_'+str(n+1),mm))
   obj=s.translate(at);assembly.add(obj,name=name+'_'+str(n+1),color=cq.Color(*a.GOLD))
   mm.visual.face_colors=np.array([*a.GOLD,1])*255;scene.add_geometry(mm,node_name=name+'_'+str(n+1))
   link=ET.SubElement(root,'link',name=name+'_'+str(n+1))
   for tag in ['visual','collision']:
    g=ET.SubElement(ET.SubElement(link,tag),'geometry');ET.SubElement(g,'mesh',filename='TEKIL/'+name+'_D305_DOLU.stl',scale='.001 .001 .001')
   j=ET.SubElement(root,'joint',name=name+'_'+str(n+1)+'_fixed',type='fixed');ET.SubElement(j,'parent',link='plate');ET.SubElement(j,'child',link=name+'_'+str(n+1));ET.SubElement(j,'origin',xyz=' '.join(str(v/1000) for v in at),rpy='0 0 0')
 ex.write_3mf(entries,OUT/'48_ADET_DOLU_PIN_D305.3mf');trimesh.util.concatenate([m for _,m in entries]).export(OUT/'48_ADET_DOLU_PIN_D305.stl')
 assembly.save(str(OUT/'DOLU_PINLER_MONTAJ.step'));scene.export(OUT/'DOLU_PINLER_MONTAJ.glb');ET.indent(root);ET.ElementTree(root).write(OUT/'DOLU_PINLER_INCELEME.urdf',encoding='utf-8',xml_declaration=True)
 samples=[]
 for i,d in enumerate(DIAMETERS):
  s=pin(9.6,d);name='DENEME_D'+str(round(d*100));export_shape(s,OUT/'DENEME_TEKIL',name,['step','stl']);m=mesh(s);m.apply_translation((15+15*i,15,0));samples.append((name,m))
 ex.write_3mf(samples,OUT/'ONCE_DENE_5_CAP.3mf');trimesh.util.concatenate([m for _,m in samples]).export(OUT/'ONCE_DENE_5_CAP.stl')
 items=[a.Item(name,pin(grip).translate((i*16,0,0)),'layout',color=a.GOLD) for i,(name,(grip,q)) in enumerate(SPECS.items())]
 ex.render(items,OUT/'PINLER.png','Dolu pimler: P1 / P2 / P3 / P4 / P6 — yarık ve kilit çıkıntısı yok',az=-75,el=25,w=1100,h=760)
 report={'status':'FIT TRIAL; no guaranteed friction retention','parts':rows,'qty':48,'unchanged':'P5 6mm passive axle excluded',
 'test_diameters_mm':DIAMETERS,'original_holes_mm':[3.3,3.4],'physical_hole_diam_mm':None,
 'full_set_solid_PLA_g':sum(r['volume_mm3']*r['qty'] for r in rows)*.00124,'filament_price_TRY_kg':None,'cost_TRY':None,
 'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'original_pin_generator_sha256':hashlib.sha256(Path(a.__file__).read_bytes()).hexdigest(),'printer_job_sent':False}
 (OUT/'MANIFEST.json').write_text(json.dumps(report,indent=2))
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
