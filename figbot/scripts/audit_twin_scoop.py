"""Exact nominal solids and sampled assembly/service clearance; no load certification."""
from pathlib import Path
import json,itertools,numpy as np
from cad.prototype_arm import twin_scoop as g,yaw_capture as y,build_linka_v1 as a
from cad.prototype_arm.export_linka_v1 import mass_report
from scripts.audit_rigid_tripod import overlap

OUT=Path('reports/twin_scoop')
def run():
    OUT.mkdir(exist_ok=True);poses=[]
    for angle in [0,3,6,9,12,15,18,21,24]:
        items=g.items(angle)
        check=[i for i in items if i.part_id or i.name in ['G1 servo','G1 original horn','G1 star closure']]
        hits=[]
        for aa,bb in itertools.combinations(check,2):
            if not overlap(aa.shape.val(),bb.shape.val()):continue
            v=aa.shape.intersect(bb.shape).val().Volume()
            if v>1e-4:hits.append([aa.name,bb.name,v])
        poses.append(dict(angle=angle,hits=hits));print('pose',angle,hits,flush=True)
    service=[];items={i.name:i.shape for i in g.items()}
    # Lid and jaws removed: motor enters from above, then jaws and lid.
    for name,part,obstacle,direction in [
        ('motor',items['G1 servo'],items['FRAME'],(0,0,1)),
        ('drive-jaw',items['JAW -1'].union(items['G1 original horn']).union(items['G1 star closure']),items['FRAME'].union(items['G1 servo']),(0,0,1)),
        ('passive-jaw',items['JAW 1'],items['FRAME'],(0,0,1)),
        ('bridge',items['BRIDGE'],items['FRAME'].union(items['JAW -1']).union(items['JAW 1']),(0,0,1))]:
        steps=[]
        for d in [40,20,10,5,2,0]:
            v=part.translate(tuple(d*c for c in direction)).intersect(obstacle).val().Volume()
            steps.append(dict(offset=d,collision_mm3=v))
        service.append(dict(name=name,steps=steps));print('service',name,max(v['collision_mm3'] for v in steps),flush=True)
    local=y.apply([i for i in a.local_items() if i.frame!='tool' or 'W1' in i.name])+g.tool_items()
    fs=a.frames((0,-60,95,-35));tool=[i for i in local if i.frame=='tool'];arm=[i for i in local if i.frame=='fore' and (i.part_id or i.name=='W1 servo')]
    arm_hits=[]
    for aa in tool:
        if not aa.part_id:continue
        for bb in arm:
            transformed=a.h.move(aa.shape,np.linalg.inv(fs['fore'])@fs['tool'])
            if not overlap(transformed.val(),bb.shape.val()):continue
            v=transformed.intersect(bb.shape).val().Volume()
            if v>1e-4:arm_hits.append([aa.name,bb.name,v])
    interface_poses=[]
    recorded=json.loads((a.OUT/'POSES.json').read_text())
    for label,q in recorded.items():
        fs=a.frames(q);hits=[]
        for aa in tool:
            if not aa.part_id or not aa.part_id.startswith('TS-'):continue
            for bb in local:
                if bb.frame=='tool' or bb.frame=='base':continue
                if not bb.part_id and not bb.name.endswith('servo'):continue
                moving=a.h.move(aa.shape,np.linalg.inv(fs[bb.frame])@fs['tool'])
                if not overlap(moving.val(),bb.shape.val()):continue
                v=moving.intersect(bb.shape).val().Volume()
                if v>1e-4:hits.append([aa.name,bb.name,v])
        interface_poses.append(dict(pose=label,q=q,hits=hits))
        print('arm pose',label,hits,flush=True)
    cap=y.cup().translate((0,0,50));basecheck=[]
    for name in ['L1-01-BASE','L1-02-ROTOR','J1 servo','J1 original horn']:
        fixed=next(i for i in a.local_items() if i.name==name)
        basecheck.append(dict(part=name,collision_mm3=cap.intersect(fixed.shape).val().Volume()))
    out=dict(revision='DEC-086',poses=poses,service=service,arm_hits=arm_hits,interface_poses=interface_poses,base_cap=basecheck,physical_approval=False,mass=mass_report(local),scope='Sampled hard solids only; not swept paths. Actual horn fit, fruit size, torque, layer strength, creep and calibration unverified')
    (OUT/'AUDIT.json').write_text(json.dumps(out,indent=2))
    assert not arm_hits,arm_hits
    assert all(not p['hits'] for p in interface_poses),interface_poses
    assert all(not p['hits'] for p in poses)
    assert all(v['collision_mm3']<1e-4 for s in service for v in s['steps']),service
    assert all(v['collision_mm3']<1e-4 for v in basecheck)
    return out
if __name__=='__main__':run()
