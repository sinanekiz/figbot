"""Geometric and mass screening only; not structural FEA or motor certification."""
import json,math,hashlib
from functools import lru_cache
import numpy as np
from cad.prototype_arm import build_forma_v6 as a
from cad.prototype_arm import integrate_forma_v6 as integration

TARGETS={'pickup':(740,415,20),'lift':(690,415,175),'clear':(690,415,330),
         'turn':(560,265,330),'release':(480,285,335)}

def source_hashes():
    return {str(p.relative_to(a.ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in
      [a.ROOT/'cad/prototype_arm'/n for n in ['build_forma_v6.py','forma_v6_horns.py','validate_forma_v6.py','integrate_forma_v6.py']]+list(a.original_horns.SOURCES.values())}

def collision_items(items):
    # Screw shanks intentionally occupy threaded inserts/shafts. Heads/washers
    # have NO intended interference and must not disappear from the audit.
    return [i for i in items if not i.name.startswith(('insert ','cord ')) and
            (not i.name.startswith('fastener ') or any(k in i.name for k in
             ['horn mounting head','horn retaining washer','original centre screw head']))]

def volume_overlap(sa,sb):
    aa,bb=sa.val().BoundingBox(),sb.val().BoundingBox()
    return overlap_bounded(sa,sb,aa,bb)

def overlap_bounded(sa,sb,aa,bb):
    if any(getattr(aa,k+'max')<=getattr(bb,k+'min')+.0001 or getattr(bb,k+'max')<=getattr(aa,k+'min')+.0001 for k in 'xyz'):return 0.
    return sum(s.Volume() for s in sa.intersect(sb).solids().vals())

def hits(items,between_frames=False):
    out=[]
    items=collision_items(items)
    bounds=[i.shape.val().BoundingBox() for i in items]
    for n,i in enumerate(items):
        for k,j in enumerate(items[n+1:],n+1):
            if between_frames and i.frame==j.frame:continue
            v=overlap_bounded(i.shape,j.shape,bounds[n],bounds[k])
            if v>.05:out.append([i.name,j.name,round(v,3)])
    return out

def fruit(q,rover=True):return (a.frames(q,rover)['tool']@np.r_[a.FRUIT,1])[:3]

@lru_cache(None)
def obstacle_bounds():return [(j,j.shape.val().BoundingBox()) for j in integration.vehicle()]

def vehicle_hits(q):
    obstacles=obstacle_bounds()
    pieces=a.assembly(q,True)
    pieces=collision_items(pieces)
    out=[]
    for i in pieces:
        bb=i.shape.val().BoundingBox()
        for j,jb in obstacles:
            v=overlap_bounded(i.shape,j.shape,bb,jb)
            if v>.05:out.append([i.name,j.name,round(v,3)])
    sphere=a.cq.Workplane('XY').sphere(20).translate(tuple(fruit(q)))
    bb=sphere.val().BoundingBox()
    for j,jb in obstacles:
        v=overlap_bounded(sphere,j.shape,bb,jb)
        if v>.05:out.append(['illustrative fruit R20',j.name,round(v,3)])
    z=min(i.shape.val().BoundingBox().zmin for i in pieces)
    return {'hits':out,'min_arm_z_mm':z,'fruit_bottom_mm':float(fruit(q)[2]-20)}

def steering_hits():
    wheel=next(p for p in integration.vehicle() if p.name=='wheel FL')
    fixed=a.assembly(a.solve(TARGETS['pickup']),True)
    fixed=[i for i in fixed if i.frame in ['base','yaw'] and not i.name.startswith(('insert ','fastener ','cord '))]
    fixed += [i for i in integration.vehicle() if i.name.startswith(('carrier envelope','F6-16'))]
    rows=[]
    for angle in range(-30,31,5):
        s=wheel.shape.rotate((290,370,0),(290,370,1),angle)
        found=[]
        for i in fixed:
            v=volume_overlap(s,i.shape)
            if v>.05:found.append([i.name,round(v,3)])
        rows.append({'angle_deg':angle,'hits':found})
    return rows

def gravity(q,payload=100.):
    fs=a.frames(q);axis=fs['yaw'][:3,:3]@np.array([0,1.,0])
    groups={'shoulder':{'upper','fore','tool'},'elbow':{'fore','tool'},'wrist':{'tool'}}
    origins={key:fs[f][:3,3] for key,f in [('shoulder','upper'),('elbow','fore'),('wrist','tool')]}
    mass={k:0. for k in groups};moment={k:0. for k in groups}
    for i in a.assembly(q):
        m=i.mass_g if i.mass_g is not None else i.shape.val().Volume()*.00124
        c=i.shape.val().Center();p=np.array(c.toTuple())
        for key,group in groups.items():
            if i.frame in group:
                mass[key]+=m;moment[key]+=float(np.cross((p-origins[key])/10,[0,0,-m/1000])@axis)
    p=fruit(q,False)
    # Additional25g at fruit accounts for unmodelled wires/cord/fasteners as a scenario,
    # not an experimentally proven upper bound. No strength factor is inferred.
    for key in groups:moment[key]+=float(np.cross((p-origins[key])/10,[0,0,-(payload+25)/1000])@axis)
    return {'modeled_mass_g':mass,'static_kgf_cm':{k:abs(v) for k,v in moment.items()},'extra_allowance_g':25.,'payload_g':payload}

def main():
    a.OUT.mkdir(exist_ok=True)
    data={'status':'DIMENSIONAL PROTOTYPE / PHYSICAL VALIDATION REQUIRED','parts':[],'sources':source_hashes(),
          'neutral_hits':hits(a.assembly()),'targets':{},'path':[],'horizontal_screen':gravity((0,0,0,0)),
          'gripper_sweep':[],'steering':steering_hits(),
          'horn_sources':a.original_horns.provenance(),
          'scope':'Discrete nominal rigid geometry only; recovered horn outlines with simplified hubs and original centre screws. Horn screw heads/retaining washers INCLUDED; threaded shanks, insert interference and schematic cords excluded. No continuous arm sweep, FEA, measured fit, torque sharing or strength validation.'}
    for pid,(fn,n,frame) in a.PARTS.items():
        s=fn();p=a.print_pose(pid,s);b=p.val().BoundingBox()
        data['parts'].append({'part':pid,'qty':n,'valid':s.val().isValid(),'solids':len(s.solids().vals()),
          'volume_mm3':s.val().Volume(),'solid_PLA_g':s.val().Volume()*.00124,'print_box_mm':[b.xlen,b.ylen,b.zlen]})
    for name,target in TARGETS.items():
        q=a.solve(target);row={'q_deg':q,'error_mm':float(np.linalg.norm(fruit(q)-target)),'gravity':gravity(q),
            'hits':hits(a.assembly(q),True),'vehicle':vehicle_hits(q)}
        data['targets'][name]=row;print(name,row,flush=True)
    poses=[a.solve(p) for p in TARGETS.values()]
    for segment,(start,end) in enumerate(zip(poses,poses[1:])):
        for f in [.25,.5,.75]:
            q=np.array(start)*(1-f)+np.array(end)*f
            data['path'].append({'segment':segment,'fraction':f,'q_deg':q.tolist(),
                'hits':hits(a.assembly(q),True),'gravity':gravity(q),'vehicle':vehicle_hits(q)})
    for g in [0,-5,-10,-15,-20,-25]:
        data['gripper_sweep'].append({'angle_deg':g,'hits':hits(a.assembly(grip=g))})
    (a.OUT/'VALIDATION.json').write_text(json.dumps(data,indent=2),encoding='utf8')
    print('NEUTRAL',data['neutral_hits'],flush=True)

if __name__=='__main__':main()
