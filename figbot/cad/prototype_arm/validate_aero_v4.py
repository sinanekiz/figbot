"""Release checks for V4 geometry, counts, sampled motions and assembly paths."""
import hashlib,json,itertools
from collections import Counter
from pathlib import Path
import numpy as np
from cad.prototype_arm import build_aero_v4 as a
from cad.prototype_arm.audit_aero_v4 import overlaps

def vol(x,y):return max(0,x.intersect(y).val().Volume())

def main():
    report={'status':'DIGITAL BENCH PROTOTYPE; PHYSICAL FIT/LOAD VALIDATION REQUIRED','source_sha256':hashlib.sha256(Path(a.__file__).read_bytes()).hexdigest()}
    report['default_pose']=list((0,-35,75,-40,0))
    report['default_collisions']=overlaps(a.assembly())
    print('default',len(report['default_collisions']),flush=True)
    pose_results=[]
    for shoulder,elbow,wrist,grip in itertools.product([-45,-35],[60,75],[-40,-15],[-20,0]):
        q=[0,shoulder,elbow,wrist,grip];items=a.assembly(tuple(q));hits=overlaps(items,between_frames_only=True)
        bottom=min(x.shape.val().BoundingBox().zmin for x in items if x.frame not in ['base','yaw'])
        pose_results.append({'q_deg':q,'collisions':hits,'moving_part_min_z_mm':bottom})
        print('pose',q,'hits',len(hits),'min_z',round(bottom,2),flush=True)
    # Rotating base clearance is not independent of the stationary supports.
    for yaw in [-30,-15,15,30]:
        q=(yaw,-35,75,-40,0);hits=overlaps(a.assembly(q),between_frames_only=True)
        pose_results.append({'q_deg':list(q),'collisions':hits})
        print('yaw',yaw,'hits',len(hits),flush=True)
    report['sampled_poses']=pose_results
    report['paths']={}
    # Axial tongue insertion, before installing the retaining pins.
    for micro in [False,True]:
        mod=a.small if micro else a.large;body=mod.build()[0];socket=a.receiver(micro)
        peak=max(vol(body,socket.translate((0,float(d),0))) for d in np.linspace(0,60,31))
        report['paths']['micro_receiver' if micro else 'large_receiver']={'max_overlap_mm3':peak,'samples':31}
    tower=a.shoulder_tower();deck=a.shoulder_deck()
    peak=max(vol(deck,tower.translate((0,0,float(d)))) for d in np.linspace(0,40,21))
    report['paths']['tower_vertical']={'max_overlap_mm3':peak,'samples':21}
    # Pin barb intentionally flexes only during insertion; assembled rigid poses
    # must clear. This is NOT a force/fatigue model.
    report['pin_flex']='UNVERIFIED; printed-layer strength/creep and extraction force require physical test'
    report['cad_solids']={k:{'valid':fn().val().isValid(),'solids':len(fn().solids().vals())} for k,(fn,n) in a.PARTS.items()}
    report['assembly_qty']=dict(Counter(i.part_id for i in a.local_items() if i.part_id))
    report['passed']=not report['default_collisions'] and all(not p['collisions'] and p.get('moving_part_min_z_mm',0)>=0 for p in pose_results) and all(p['max_overlap_mm3']<.002 for p in report['paths'].values()) and all(v['valid'] and v['solids']==1 for v in report['cad_solids'].values())
    (a.OUT/'FINAL_AUDIT.json').write_text(json.dumps(report,indent=2))
    print('PASSED',report['passed'],flush=True)

if __name__=='__main__':main()
