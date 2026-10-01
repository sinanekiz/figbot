"""Offline L1 mechanism / mesh / gravity screening. Never sends motor commands."""
import json, math
import numpy as np
import trimesh
from cad.prototype_arm import build_linka_v1 as a
from cad.prototype_arm.export_linka_v1 import mass_report
from scripts.arm_engineering_review import TARGETS

def potential(rows,alpha,beta,payload_g=50,allowance_g=25):
    # Tool remains horizontal when upper/fore move; wrist motor also contributes
    # to virtual work. Therefore these generalized torques are NOT servo ratings.
    fs=a.frames([0,alpha,beta-alpha,-beta]);total=0.
    for r in rows:
        p=fs[r['frame']]@np.array([*r['center_mm'],1.])
        total+=r['mass_g']*.001*9.80665*p[2]*.001
    fruit=fs['tool']@np.array([a.PALM_X,0.,-45.,1.])
    return total+(payload_g+allowance_g)*.001*9.80665*fruit[2]*.001

def gravity(rows,alpha,beta):
    e=.002;rad=math.radians(e)
    va=(potential(rows,alpha+e,beta)-potential(rows,alpha-e,beta))/(2*rad)
    vb=(potential(rows,alpha,beta+e)-potential(rows,alpha,beta-e))/(2*rad)
    ga=(a.solve_linkage(alpha+e,beta)['gamma']-a.solve_linkage(alpha-e,beta)['gamma'])/(2*e)
    gb=(a.solve_linkage(alpha,beta+e)['gamma']-a.solve_linkage(alpha,beta-e)['gamma'])/(2*e)
    return dict(upper_generalized_kgfcm=abs((va-vb*ga/gb)/.0980665),crank_generalized_kgfcm=abs(vb/gb/.0980665),d_gamma_d_beta=gb)

def main():
    locals=a.local_items();m=mass_report(locals);qs=[a.ik(t) for t in TARGETS.values()]
    scan=[]
    for q,r in zip(qs,qs[1:]):
        for t in np.linspace(0,1,41):
            v=np.array(q)*(1-t)+np.array(r)*t;l=a.solve_linkage(v[1],v[1]+v[2]);g=gravity(m['rows'],v[1],v[1]+v[2])
            scan.append(dict(closure_mm=l['closure_error'],**g))
    meshes=[]
    for pid in a.PARTS:
        mesh=trimesh.load_mesh(a.OUT/'PRINT_STL'/f'{pid}.stl',process=True)
        meshes.append(dict(id=pid,watertight=bool(mesh.is_watertight),winding=bool(mesh.is_winding_consistent)))
    assert all(r['watertight'] and r['winding'] for r in meshes)
    result=dict(status='OFFLINE SCREEN; NOT PHYSICAL APPROVAL',meshes=meshes,samples=len(scan),max_closure_mm=max(r['closure_mm'] for r in scan),
        minimum_abs_transmission_derivative=min(abs(r['d_gamma_d_beta']) for r in scan),
        generalized_gravity_max={k:max(r[k] for r in scan) for k in ['upper_generalized_kgfcm','crank_generalized_kgfcm']},
        gravity_note='50g fruit +25g allowance; horizontal tool coordinated by wrist. Generalized gravity work includes that constraint, not isolated measured motor torque. No acceleration, friction, electrical sag or continuous-duty validation.',
        shoulder_downstream_g=m['shoulder_downstream_g'],reference_R6_downstream_g=301.2308,
        reduction_pct=100*(1-m['shoulder_downstream_g']/301.2308),frame_totals_g=m['frame_totals_g'],
        warning='Base/yaw structure is heavier; this percentage is distal moving mass, not complete robot weight. Tendon closure/return compliance and grasp must be physically tuned.')
    (a.OUT/'VALIDATION.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in result.items() if k not in ['meshes','frame_totals_g']},indent=2))

if __name__=='__main__':main()
