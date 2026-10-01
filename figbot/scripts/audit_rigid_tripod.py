"""Sampled exact-solid interference, linkage closure and mass; no physical approval."""
from pathlib import Path
import json,itertools,sys
from cad.prototype_arm import rigid_tripod_gripper as g
from cad.prototype_arm.export_linka_v1 import mass_report
from cad.prototype_arm.linka_render import render

OUT=Path('reports/rigid_tripod');OUT.mkdir(parents=True,exist_ok=True)

def overlap(a,b):
    aa=a.BoundingBox();bb=b.BoundingBox()
    return all(min(getattr(aa,d+'max'),getattr(bb,d+'max'))-max(getattr(aa,d+'min'),getattr(bb,d+'min'))>1e-5 for d in 'xyz')

def run(angles=(0,17.5,35)):
    report={'poses':[]}
    for angle in angles:
        items=g.items(angle)
        check=[i for i in items if i.part_id or i.name in ['G1 servo','G1 original horn','G1 star cover']]
        hits=[]
        for a,b in itertools.combinations(check,2):
            if not overlap(a.shape.val(),b.shape.val()):continue
            v=a.shape.val().intersect(b.shape.val()).Volume()
            if v>1e-4:hits.append([a.name,b.name,round(v,5),a.shape.val().intersect(b.shape.val()).Center().toTuple()])
        report['poses'].append({'angle':angle,'hits':hits})
        print(angle,hits,flush=True)
    report['mass']=mass_report(g.items())
    report['solids']={i.name:{'count':len(i.shape.val().Solids()),'valid':i.shape.val().isValid()} for i in g.items() if i.part_id}
    (OUT/'AUDIT.json').write_text(json.dumps(report,indent=2))
    print([(r['name'],round(r['mass_g'],2)) for r in report['mass']['rows'] if r['pid']],flush=True)
    if '--render' in sys.argv:
        render(g.items(),OUT/'CLOSED.png','DEC-084 / Uc sert kepce',az=-55,el=25,revision='DEC-084')
        render(g.items(g.OPEN),OUT/'OPEN.png','DEC-084 / Acik',az=-55,el=25,revision='DEC-084')
    return report

def service():
    items={i.name:i.shape for i in g.items(g.OPEN)}
    unit=items['RT pinion'].union(items['G1 original horn']).union(items['G1 star cover'])
    frame=items['RT frame'];servo=items['G1 servo'];rack=items['RT rack']
    paths={
      'motor_axial_before_gears':(servo,frame,[(0,y,0) for y in [60,40,20,10,5,2,0]]),
      'gear_side_entry_before_rack':(unit,frame.union(servo),[(x,3,0) for x in [-70,-50,-30,-15,-5,0]]+[(0,y,0) for y in [2,1,0]]),
      'gear_side_entry_with_rack':(unit,frame.union(servo).union(rack),[(x,3,0) for x in [-70,-50,-30,-15,-5,0]]+[(0,y,0) for y in [2,1,0]]),
      'rack_side_entry_before_gear':(rack,frame.union(servo),[(0,y,0) for y in [50,30,20,10,5,2,0]]),
      'rack_side_entry_after_gear':(rack,frame.union(servo).union(unit),[(0,y,0) for y in [50,30,20,10,5,2,0]]),
      'rack_reverse_entry_after_gear':(rack,frame.union(servo).union(unit),[(0,-y,0) for y in [50,30,20,10,5,2,0]]),
    }
    for side in [-1,1]:
        paths['guide_'+str(side)]=(items['RT guide '+str(side)],frame.union(rack),[(0,side*y,0) for y in [30,15,5,2,0]])
    result={}
    for key,(part,obstacle,steps) in paths.items():
        result[key]=[{'offset':v,'collision_mm3':part.translate(v).val().intersect(obstacle.val()).Volume()} for v in steps]
        print(key,result[key],flush=True)
    (OUT/'SERVICE.json').write_text(json.dumps(result,indent=2))
    return result

if __name__=='__main__':
    if '--service' in sys.argv:service()
    else:run([i*3.5 for i in range(11)] if '--dense' in sys.argv else (0,17.5,35))
