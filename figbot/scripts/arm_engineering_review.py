"""Reproducible design screening, not a rated torque or manufacturing release.

R6 masses/centres are recovered from actual CAD; alternative masses are budgets.
No motor, serial, firmware, printer or purchase operations.
"""
import json, math, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/engineering_20260913'
G = 9.80665
TARGETS = {'pickup': (740,415,20), 'lift': (690,415,175),
           'clear': (690,415,330), 'turn': (560,265,330), 'release': (480,285,335)}
SHOULDER = (550,415,166)
SOURCES = {'MG996R':'https://towerpro.com.tw/product/mg996r/',
           'MG90S':'https://towerpro.com.tw/product/mg90s-3/',
           'force_control':'https://manipulation.mit.edu/force.html'}


def solve(target, upper, fore, tool_x, tool_z):
    dx,dy,dz = (target[i]-SHOULDER[i] for i in range(3))
    x,z = math.hypot(dx,dy)-tool_x,dz-tool_z
    c=(x*x+z*z-upper*upper-fore*fore)/(2*upper*fore)
    if abs(c)>1: return None
    elbow=math.acos(c)
    shoulder=math.atan2(-z,x)-math.atan2(fore*math.sin(elbow),upper+fore*math.cos(elbow))
    return [math.degrees(math.atan2(dy,dx)), math.degrees(shoulder),
            math.degrees(elbow), -math.degrees(shoulder+elbow)]


def xz_rotate(x,z,degrees):
    a=math.radians(degrees)
    return x*math.cos(a)+z*math.sin(a), -x*math.sin(a)+z*math.cos(a)


def world_xz(row,q,lengths):
    u,f=lengths
    ex,ez=xz_rotate(u,0,q[1]); wx,wz=xz_rotate(f,0,q[1]+q[2]); wx+=ex;wz+=ez
    angles={'upper':q[1], 'fore':q[1]+q[2], 'tool':sum(q[1:])}
    origins={'upper':(0,0),'fore':(ex,ez),'tool':(wx,wz)}
    x,z=xz_rotate(row['x_mm'],row['z_mm'],angles[row['frame']])
    ox,oz=origins[row['frame']]
    return (x+ox,z+oz),origins


def torque(rows,q,lengths,tool,payload_g,allowance_g=25):
    rows=list(rows)+[dict(frame='tool',x_mm=tool[0],z_mm=tool[1],mass_g=payload_g+allowance_g)]
    groups={'shoulder':{'upper','fore','tool'}, 'elbow':{'fore','tool'},'wrist':{'tool'}}
    frame={'shoulder':'upper','elbow':'fore','wrist':'tool'}
    signed={k:0. for k in groups}
    for row in rows:
        (x,z),origins=world_xz(row,q,lengths)
        for joint,members in groups.items():
            if row['frame'] in members:
                signed[joint]+=row['mass_g']/1000*(x-origins[frame[joint]][0])/10
    return {j:abs(v) for j,v in signed.items()}


def quintic_duration(delta_deg, speed=30., acceleration=60.):
    """Rest-to-rest quintic bound; analytical peak speed and acceleration.
    Values are OFFLINE design scenarios, not calibrated servo settings.
    """
    d=abs(delta_deg)
    if speed<=0 or acceleration<=0:raise ValueError('positive limits required')
    return max(1.875*d/speed,math.sqrt((10/math.sqrt(3))*d/acceleration))


def gripper_transmission(payload_g,mu=.4,efficiency=.75,spool_mm=5.,tendon_arm_mm=8.,contact_arm_mm=35.):
    """Symmetric quasistatic radial-finger scenario; every lever/efficiency is assumed."""
    if min(mu,efficiency,spool_mm,tendon_arm_mm,contact_arm_mm)<=0:raise ValueError('positive parameters required')
    normal=payload_g/1000*G*1.5/(3*mu)
    tendon_each=normal*contact_arm_mm/tendon_arm_mm
    motor_Nm=3*tendon_each*spool_mm/1000/efficiency
    return dict(payload_g=payload_g,mu=mu,assumed_efficiency=efficiency,
        normal_each_N=normal,tendon_each_N=tendon_each,motor_torque_kgfcm=motor_Nm/(G/100),
        fraction_of_published_stall=motor_Nm/(G/100)/1.8,
        motor_120deg_stroke_mm=spool_mm*math.radians(120),
        finger_30deg_stroke_mm=tendon_arm_mm*math.radians(30),
        status='ILLUSTRATIVE LEVERS; COMPLIANCE/FRICTION/REAL ANGLES UNVERIFIED')


def budget_rows(upper,fore):
    # Candidate mass ceilings including ALL listed mechanics, not CAD results.
    return [dict(name=n,frame=f,mass_g=m,x_mm=x,z_mm=0.,status='TARGET NOT ACHIEVED') for n,f,m,x in [
      ('upper printed structure','upper',65,upper/2),
      ('elbow servo + upper hardware','upper',70,upper),
      ('fore printed structure','fore',45,fore/2),
      ('wrist servo + fore hardware','fore',23.4,fore),
      ('complete tool incl gripper servo/pads/fasteners','tool',40,15)]]


def evaluate(rows,lengths,tool,payload):
    qs={name:solve(t,*lengths,*tool) for name,t in TARGETS.items()}
    valid=[q for q in qs.values() if q is not None]
    samples=list(valid)
    if len(valid)==len(qs):
        for a,b in zip(valid,valid[1:]):
            samples.extend([[x+(y-x)*i/40 for x,y in zip(a,b)] for i in range(1,40)])
    values=[torque(rows,q,lengths,tool,payload) for q in samples]
    return dict(payload_g=payload,all_targets_reachable=len(valid)==len(qs),q_deg=qs,
      nominal_joint_span_deg=[max(q[i] for q in valid)-min(q[i] for q in valid) for i in range(4)],
      path_max_static_kgfcm={j:max(t[j] for t in values) for j in ('shoulder','elbow','wrist')},
      horizontal_static_kgfcm=torque(rows,[0,0,0,0],lengths,tool,payload),
      point_samples=len(samples),collision_checked=False,
      rest_to_rest_transfer_s=sum(max(quintic_duration(y-x) for x,y in zip(a,b)) for a,b in zip(valid,valid[1:])))


def main():
    from cad.prototype_arm import build_forma_v6 as a
    import cadquery as cq
    OUT.mkdir(exist_ok=True,parents=True)
    rows=[]
    for item in a.local_items():
        if item.frame not in ('upper','fore','tool'):continue
        c=item.shape.val().Center()
        m=item.mass_g if item.mass_g is not None else item.shape.val().Volume(1e-6)*.00124
        rows.append(dict(name=item.name,frame=item.frame,mass_g=m,x_mm=c.x,y_mm=c.y,z_mm=c.z,
                         status='CAD volume or assigned mass; not weighed'))
    # Fruit CONTACT was absent from the earlier arm self-collision checks.
    contacts=[]
    for diameter in (30,40,50,60):
        fruit=cq.Workplane('XY').sphere(diameter/2).translate(tuple(a.FRUIT))
        for angle in (0,-2.5,-5,-7.5,-10,-15,-20,-25):
            finger=a.finger().rotate((0,0,0),(0,1,0),angle).translate((a.PALM_X+23,0,-5))
            pad=a.pad().rotate((0,0,0),(0,1,0),angle).translate((a.PALM_X+23,0,-5))
            vol=lambda s:sum(v.Volume() for v in s.intersect(fruit).solids().vals())
            contacts.append(dict(illustrative_diameter_mm=diameter,angle_deg=angle,
                pad_gap_mm=pad.val().distance(fruit.val()),pad_overlap_mm3=vol(pad),rigid_overlap_mm3=vol(finger)))
    candidates=[]
    for lengths in ((180,140),(170,130),(160,130),(150,120)):
        br=budget_rows(*lengths)
        candidates.append(dict(lengths_mm=lengths,tool_offset_mm=[30,-45],mass_rows=br,
            scenarios=[evaluate(br,lengths,(30,-45),p) for p in (40,50,100)]))
    friction=[dict(mu=mu,payload_g=p,normal_force_per_finger_N=p/1000*G*1.5/(3*mu),
                   contact_pressure_kPa=p/1000*G*1.5/(3*mu)/100*1000)
              for p in (50,100) for mu in (.2,.4,.6)]
    r6=[evaluate(rows,(180,140),(38,-66),p) for p in (40,50,100)]
    # Do not label an assumed fraction of stall as continuous rated torque.
    demands=r6[1]['path_max_static_kgfcm']
    sensitivity=[dict(assumed_stall_fraction=f,assumed_pair_efficiency=e,
        shoulder_budget_kgfcm=2*9.4*f*e,elbow_budget_kgfcm=9.4*f,wrist_budget_kgfcm=1.8*f,
        R6_50g_shoulder_static_ratio=demands['shoulder']/(2*9.4*f*e))
        for f in (.25,.4,.5) for e in (.7,.85,1.)]
    data=dict(status='ENGINEERING SCREEN / NO MANUFACTURING RELEASE',date='2026-09-13',
      user_report=dict(R6_printed=False,fruit_mass_g=[40,50],fruit_dimensions_mm='TBD'),
      sources=SOURCES,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in
        ['cad/prototype_arm/build_forma_v6.py','cad/prototype_arm/forma_v6_horns.py','scripts/arm_engineering_review.py']},
      R6_mass_rows=rows,R6_scenarios=r6,R6_fruit_contacts=contacts,
      candidate_mass_budget_total_g=sum(r['mass_g'] for r in budget_rows(150,120)),candidates=candidates,
      friction_only_scenarios=friction,stall_fraction_sensitivity=sensitivity,
      gripper_transmission_scenarios=[gripper_transmission(p,mu,e) for p in (50,100) for mu in (.2,.4,.6) for e in (.5,.75)],
      release_gates=dict(physical_servo_torque='UNKNOWN',printed_material_strength='UNKNOWN',
        fruit_size_and_damage_force='UNKNOWN',actual_supply_under_load='UNRESOLVED',
        R6_closed_40mm_rigid_fruit_contact='FAIL',candidate_3D_collision='NOT RUN',
        candidate_mass_budget='NOT ACHIEVED',candidate_joint_calibration='UNKNOWN'),
      limits=['Alternative masses/centres are targets, not CAD or physical measurements.',
        'Static gravity screening only, no inertia, coupling, friction, compliance or thermal duty proof.',
        'Quintic times are offline rest-to-rest lower bounds at assumed 30deg/s and60deg/s2; no grip/dwell/return.',
        '25g allowance is a scenario, not an upper bound; fruit diameter is illustrative, not measured.',
        'No serial port, printer, purchase, firmware or CAD geometry modified.'])
    (OUT/'engineering.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
    (ROOT/'viewer/public/engineering-review.json').write_text(json.dumps(data,ensure_ascii=False),encoding='utf8')
    print(json.dumps(dict(R6_scenarios=r6,compact=candidates[-1],gates=data['release_gates']),ensure_ascii=False,indent=2))


if __name__=='__main__':main()
