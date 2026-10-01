"""Repeatable geometric and static screening; no physical-strength certification."""
import hashlib,json,math
from collections import Counter
from functools import lru_cache
import cadquery as cq
import numpy as np
from cad.prototype_arm import build_aero_v5 as a
from cad.prototype_arm.audit_aero_v4 import overlaps
from cad.rover import build_rev_i_direct_basket as rover

TARGETS=rover.TARGETS


def source_hashes():
    files=['cad/prototype_arm/build_aero_v5.py','cad/prototype_arm/export_aero_v5.py',
        'cad/prototype_arm/validate_aero_v5.py','cad/prototype_arm/build_aero_v4.py',
        'cad/prototype_arm/build_aero_v3.py','cad/prototype_arm/build_snap02.py',
        'cad/prototype_arm/build_snap03b_mg90.py','cad/rover/build_rev_i_direct_basket.py',
        'scripts/build_aero_v5_hardware.py']
    files.extend(str(p.relative_to(a.ROOT)).replace('\\','/') for p in [a.micro.SOURCE,a.v4.large.SOURCE])
    return {f:hashlib.sha256((a.ROOT/f).read_bytes()).hexdigest() for f in files}


@lru_cache(None)
def vehicle():
    result=[]
    for p in rover.vehicle():
        if p.name.startswith('front arm carrier'):continue
        s=p.shape
        if p.name.startswith('front mounting plate'):
            side=1 if p.name.endswith(' 1') else -1
            s=a.box(132,142,6,(550,side*415,63))
            for x in [-50,50]:
                for y in [-43,43]:s=a.bore_z(s,550+x,side*415+y,4.5)
        result.append(a.Item(p.name,s,'vehicle',group=p.group,color=p.color))
    for side in [-1,1]:
        points=[((300,side*280,90),(550,side*280,51)),
            ((500,side*280,51),(550,side*415,51)),
            ((310,side*285,90),(500,side*280,140)),
            ((500,side*280,140),(510,side*320,51)),
            ((510,side*320,51),(550,side*415,51))]
        for k,(p,q) in enumerate(points):
            result.append(a.Item(f'V5 low carrier {side} {k}',rover.gear.rod(p,q,18),'vehicle',group='support',color=a.METAL))
    return result


def fruit_point(q):
    return (a.frames(q)['tool']@np.array([a.TOOL_X,0,-a.TOOL,1]))[:3]+a.ROVER_BASE


def gravity(q,payload_g=100):
    """Full-density CAD prints + nominal motor/metal mass; additional 25g allowance."""
    fs=a.frames(q);origins={j:fs[f][:3,3] for j,f in [('shoulder','upper'),('elbow','fore'),('wrist','tool')]}
    groups={'shoulder':{'upper','fore','tool','cam','finger0','finger1','finger2'},
        'elbow':{'fore','tool','cam','finger0','finger1','finger2'},'wrist':{'tool','cam','finger0','finger1','finger2'}}
    axis=fs['yaw'][:3,:3]@np.array([0,1,0]);mom={k:0. for k in origins};mass={k:0. for k in origins}
    for i in a.assembly(q):
        vol=i.shape.val().Volume()
        if i.group=='servo':m=13.4 if i.name.startswith(('W1','G1')) else 55.
        elif i.group=='metal':m=vol*(.0027 if 'compression' in i.name else .0085 if 'follower sleeve' in i.name else .00785)
        elif i.group=='soft':m=vol*.0012
        else:m=vol*.00124
        c=i.shape.val().Center();p=np.array([c.x,c.y,c.z])
        for j in origins:
            if i.frame in groups[j]:
                mass[j]+=m;mom[j]+=float(np.cross((p-origins[j])/10,[0,0,-m/1000])@axis)
    # Unmodelled clamp/receiver bolts, pivot hardware, wiring: conservative trial
    # allowance at the wrist for shoulder/elbow, at fruit centre for wrist.
    fruit=fruit_point(q)-a.ROVER_BASE
    for j in origins:
        mom[j]+=float(np.cross((fruit-origins[j])/10,[0,0,-payload_g/1000])@axis)
        p=fruit if j=='wrist' else origins['wrist']
        mom[j]+=float(np.cross((p-origins[j])/10,[0,0,-.025])@axis)
    return {'static_kgfcm':{j:abs(v) for j,v in mom.items()},'modeled_moving_mass_g':mass,
        'payload_g':payload_g,'unmodelled_hardware_allowance_g':25,'basis':'CAD full material and nominal 55g/13.4g motors; not measured; no inertia/friction/servo load-sharing or strength validation'}


def obstacle_hits(items):
    hits=[]
    for p in items:
        for o in vehicle():
            if o.shape.val().BoundingBox().ymax<180:continue
            v=rover.overlaps(p.shape.val(),o.shape.val())
            if v>.002:hits.append([p.name,o.name,float(v)])
    return hits


def main():
    result={'status':a.STATUS,'sources':source_hashes(),'parts':[],'path':[],'gripper':[],'steering':[]}
    for pid,(fn,n,kind) in a.PARTS.items():
        s=fn();result['parts'].append({'part':pid,'qty':n,'solids':len(s.solids().vals()),'valid':s.val().isValid(),'volume_mm3':s.val().Volume()})
    poses=[a.solve(t) for t in TARGETS.values()]
    result['target_errors_mm']={name:float(np.linalg.norm(fruit_point(a.solve(t))-t)) for name,t in TARGETS.items()}
    # Includes all modeled bolt heads, sleeves and gripper followers; contacts OK.
    result['neutral_self_hits']=overlaps(a.assembly())
    for segment,(start,end) in enumerate(zip(poses,poses[1:])):
        for fraction in [0,.25,.5,.75,1]:
            q=np.array(start)+(np.array(end)-start)*fraction
            items=a.assembly(q,rover=True)
            point=fruit_point(q);fruit=a.Item('40mm fruit envelope',cq.Workplane('XY').sphere(20).translate(tuple(point)),'fruit')
            row={'segment':segment,'fraction':fraction,'q':q.tolist(),
                'self_hits':overlaps(items,between_frames_only=True),'rover_hits':obstacle_hits(items+[fruit]),
                'min_moving_z_mm':min(i.shape.val().BoundingBox().zmin for i in items if i.frame not in ['base','yaw']),
                'fruit_bottom_z_mm':float(point[2]-20),'gravity':gravity(q)}
            result['path'].append(row);print('PATH',segment,fraction,'hits',row['self_hits'],row['rover_hits'],flush=True)
    for q in range(-25,26,5):
        items=[i for i in a.assembly((0,0,0,0,q)) if i.frame in ['tool','cam','finger0','finger1','finger2']]
        row={'q':q,'radial_mm':a.cam_radius(q),'hits':overlaps(items)}
        result['gripper'].append(row);print('GRIP',q,len(row['hits']),flush=True)
    wheel=next(p for p in vehicle() if p.name=='wheel FL')
    new=[p for p in vehicle() if p.group in ['basket','support','camera']]
    new.extend(i for i in a.assembly(poses[0],True) if i.frame in ['base','yaw'])
    for angle in range(-30,31,5):
        s=wheel.shape.rotate((290,370,0),(290,370,1),angle)
        hits=[]
        for o in new:
            v=rover.overlaps(s.val(),o.shape.val())
            if v>.002:hits.append([o.name,float(v)])
        result['steering'].append({'angle_deg':angle,'hits':hits})
    result['horizontal_screen']=gravity((0,0,0,0,0))
    result['passed']=all(p['valid'] and p['solids']==1 and p['volume_mm3']>0 for p in result['parts']) and not result['neutral_self_hits'] and all(not x['self_hits'] and not x['rover_hits'] and x['min_moving_z_mm']>=0 and x['fruit_bottom_z_mm']>=-1e-5 for x in result['path']) and all(not x['hits'] for x in result['gripper']+result['steering']) and max(result['target_errors_mm'].values())<1e-6
    result['limits']='Discrete samples only. Ground is flat. Vehicle geometry and opposed arm are reference envelopes. Not swept-volume proof, FEA, bearing/bolt rating, friction/bruise test, camera coverage or real servo calibration. Unmodelled fasteners and cable routing need bench fit.'
    (a.OUT/'GEOMETRY_AUDIT.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('PASS',result['passed'],flush=True)
    assert result['passed']


if __name__=='__main__':main()
