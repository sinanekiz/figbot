"""Geometric acceptance checks, without contact exclusions or safety claims."""
import json
import hashlib
from pathlib import Path
import numpy as np
from cad.prototype_arm import build_aero_v3 as a
from cad.rover import build_rev_h_review as rover


def intersection(c,d):
    aa,bb=c.shape.val().BoundingBox(),d.shape.val().BoundingBox()
    if any(getattr(aa,k+'max')<=getattr(bb,k+'min')+1e-5 or getattr(bb,k+'max')<=getattr(aa,k+'min')+1e-5 for k in 'xyz'):
        return 0.
    return c.shape.val().intersect(d.shape.val()).Volume()


def clashes(parts,obstacles=()):
    result=[]
    for i,c in enumerate(parts):
        for d in list(parts[i+1:])+list(obstacles):
            v=intersection(c,d)
            if v>.1:result.append([c.name,d.name,round(v,3)])
    return result


def vehicle():
    # Drilled mounting pattern matches V3's base. Rest of Rev-H2 is unchanged.
    parts=[]
    for c in rover.vehicle():
        shape=c.shape
        if c.name in ('arm mount L','arm mount R'):
            by=a.BASE[1] if c.name.endswith('L') else -a.BASE[1]
            for x in (-50,50):
                for y in (-43,43):shape=a.hole(shape,a.BASE[0]+x,by+y,4.5)
        parts.append(a.Component(c.name,shape,c.group,c.color))
    return parts


def dual(name):
    parts=[]
    for side in (1,-1):
        base=(a.BASE[0],side*a.BASE[1],a.BASE[2])
        t=a.TARGETS[name]; target=(t[0],side*t[1],t[2])
        for c in a.assembly(a.ik(target,base),grip=-20 if name in ('pickup','release') else 5,base=base):
            parts.append(a.Component(('L ' if side==1 else 'R ')+c.name,c.shape,c.group,c.color,c.part_id))
    return parts


def build_report():
    obstacles=[c for c in vehicle() if c.group not in ('vehicle',)]
    # Include chassis and drilled arm plates too, rather than hiding contacts.
    obstacles=vehicle()
    poses={k:a.ik(t) for k,t in a.TARGETS.items()}
    samples=[]
    for segment,(start,end) in enumerate(zip(list(poses.values()),list(poses.values())[1:])):
        for f in np.linspace(0,1,11):
            pose=tuple(np.array(start)*(1-f)+np.array(end)*f)
            parts=a.assembly(pose,base=a.BASE)
            hits=clashes(parts,obstacles)
            samples.append({'segment':segment,'fraction':float(f),'joints_deg':pose,
                            'wrist_relative_deg':-pose[2], 'palm_world_pitch_deg':0.,
                            'minimum_ground_mm':round(min(c.shape.val().BoundingBox().zmin for c in parts),4),
                            'collisions_mm3':hits})
    jaws=[]
    for grip in np.linspace(-25,25,11):
        parts=a.assembly(poses['pickup'],grip=float(grip),base=a.BASE)
        jaws.append({'grip_deg':float(grip),'collisions_mm3':clashes(parts),
                     'minimum_ground_mm':round(min(c.shape.val().BoundingBox().zmin for c in parts),4)})
    two_arms=[]
    for name in poses:
        parts=dual(name)
        two_arms.append({'pose':name,'collisions_mm3':clashes(parts,obstacles)})
    # Positive separations on each horn/shaft assembly must not be mistaken for
    # a connected drive. All twelve shaft/horn and horn/printed faces checked.
    parts={c.name:c.shape.val() for c in a.assembly(poses['pickup'],base=a.BASE)}
    interfaces=[]
    mates={'J1':'yaw deck','J2 -1':'upper hub','J2 1':'upper hub','J3':'fore hub','W1':'wrist drive plate','G1':'moving jaw'}
    for name,mate in mates.items():
        interfaces.append({'motor':name,'shaft_horn_gap_mm':parts[name+' shaft'].distance(parts[name+' supplied horn']),
                           'horn_adapter_gap_mm':parts[name+' supplied horn'].distance(parts[mate])})
    for c in samples:
        c['ok']=not c['collisions_mm3'] and c['minimum_ground_mm']>=0
    ok=all(c['ok'] for c in samples) and all(not c['collisions_mm3'] and c['minimum_ground_mm']>=0 for c in jaws) and all(not c['collisions_mm3'] for c in two_arms) and all(c['shaft_horn_gap_mm']<.01 and c['horn_adapter_gap_mm']<.01 for c in interfaces)
    report={'revision':'AERO-V3 / DEC-041','source_sha256':hashlib.sha256(Path(a.__file__).read_bytes()).hexdigest(),'digital_geometry_ok':ok,'motion_samples':samples,'jaw_samples':jaws,'dual_arm_key_poses':two_arms,'drive_interfaces':interfaces,
            'scope':'All solid pairs checked without collision exclusions, 0.1 mm3 tolerance. 22 discrete trajectory samples, 11 jaw positions, 3 dual-arm key poses. Not continuous collision detection, physical fit, motor calibration, cable routing, strength, speed or safety approval.'}
    a.OUT.mkdir(parents=True,exist_ok=True)
    (a.OUT/'GEOMETRY_AUDIT.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('AERO V3 digital geometry:',ok,flush=True)
    return report

if __name__=='__main__':build_report()
