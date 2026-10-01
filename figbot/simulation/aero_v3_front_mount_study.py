"""Placement alternatives only; does not modify CAD or print dimensions."""
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from cad.prototype_arm import build_aero_v3 as arm
from simulation import aero_v3_feasibility as physics

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/aero_v3_front_mount'
CASES=[('Mevcut',380,280),('14 cm önde, aynı yükseklik',520,280),
       ('14 cm önde, 8 cm aşağıda',520,200),('14 cm önde, 12 cm aşağıda',520,160)]


def joint_state(target,base):
    yaw,upper,fore=arm.ik(target,base=base)
    return np.array([yaw,upper,fore-upper,-fore])


def build():
    OUT.mkdir(parents=True,exist_ok=True)
    model=ET.parse(ROOT/'cad/prototype_arm/aero_v3/urdf/AERO_V3_REVIEW.urdf').getroot()
    limits={name:tuple(math.degrees(float(model.find(f"joint[@name='{name}']/limit").attrib[k])) for k in ('lower','upper')) for name in ('J1','J2','J3','W1')}
    bodies=physics.load_bodies();rows=[]
    for name,x,z in CASES:
        base=(x,415,z);q=joint_state((650,415,102),base)
        loads={}
        for mass in (.04,.1):
            _,tau=physics.mass_matrix(np.radians(q),physics.with_fruit(bodies,mass))
            loads[str(mass)]=dict(zip(('yaw','shoulder_total','elbow','wrist'),np.abs(tau/physics.K).tolist()))
        old_release=joint_state((400,275,460),base)
        violations=[n for n,v in zip(limits,q) if not limits[n][0]<=v<=limits[n][1]]
        rows.append({'name':name,'base_mm':base,'shoulder_height_mm':z+arm.SHOULDER_Z,'pickup_joint_degrees':q.tolist(),
           'pickup_limit_violations':violations,'gravity_kgf_cm':loads,'old_release_yaw_deg':old_release[0],
           'theoretical_ground_radius_mm':math.sqrt((arm.UPPER+arm.FORE)**2-(z+arm.SHOULDER_Z-102)**2)})
    data={'unchanged_CAD':True,'reference_target_wrist_mm':[650,415,102],'joint_limits_deg':limits,'cases':rows,
      'candidate_new_release':{'target_wrist_mm':[540,275,460],'base_mm':[520,415,280],
       'joint_degrees':joint_state((540,275,460),(520,415,280)).tolist(),
       'note':'Requires new catch apron; existing apron ends at X415. New support, basket, trajectories and camera are NOT designed or approved.'},
      'scope':'Same arm and same fruit location, ideal rigid-body static gravity only. Lowering does not shorten links. Pose limits are CAD review limits, not measured servo calibration. No bracket strength, stability, tyre steering sweep or continuous path approval.'}
    (OUT/'comparison.json').write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')
    draw(data)
    return data


def draw(data):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle,Rectangle
    fig,axes=plt.subplots(1,3,figsize=(15,6),facecolor='#f7f5ef')
    for ax,row in zip(axes,[data['cases'][0],data['cases'][1],data['cases'][3]]):
        ax.set_facecolor('#f7f5ef');ax.add_patch(Circle((290,127),127,color='#6d7780',alpha=.3))
        x,_,z=row['base_mm'];q=np.radians(row['pickup_joint_degrees']);a=q[1];b=q[2]
        ex=x+300*math.cos(a);ez=z+124-300*math.sin(a)
        ax.add_patch(Rectangle((x-58,z),116,74,color='#6d7780',alpha=.7))
        ax.plot([x,x],[z+74,z+124],color='#69727b',lw=5)
        ax.plot([x,ex,650],[z+124,ez,102],color='#dc752b',lw=5)
        ax.plot([650,650],[102,16],color='#dc752b',lw=4)
        ax.scatter([650],[16],s=35,color='#643b28')
        ax.plot([320,415],[312,330],color='#5a9288',lw=4)
        ax.axhline(0,color='#777777');ax.axvline(417,color='#8f969c',ls=':')
        torque=row['gravity_kgf_cm']['0.1']
        ax.text(150,-65,f"100 g: omuz {torque['shoulder_total']:.2f} / dirsek {torque['elbow']:.2f} kgf·cm",fontsize=9)
        if row['pickup_limit_violations']:ax.text(150,-110,'Bilek model açı sınırının dışında',color='#b7453e',fontsize=9)
        elif x>380:ax.text(150,-110,'Yeni taşıyıcı ve sepet girişi gerekiyor',color='#986231',fontsize=9)
        ax.set(xlim=(130,850),ylim=(-145,485),title=row['name'],xlabel='Araç X (mm)',ylabel='Yerden yükseklik (mm)')
        ax.set_aspect('equal');ax.grid(alpha=.16)
    fig.suptitle('Aynı incir, aynı kol: montaj konumunun etkisi',fontsize=18)
    fig.text(.05,.045,'Gri kutu: kol tabanı. Yeşil çizgi: mevcut sepet girişi. Öndeki tabanlar yalnız yerleşim adayıdır; şasi bağlantıları tasarlanmadı.',fontsize=10)
    fig.tight_layout(rect=(0,.09,1,.94));fig.savefig(OUT/'placement_comparison.png',dpi=150);plt.close(fig)


if __name__=='__main__':
    print(json.dumps(build(),indent=2,ensure_ascii=False))
