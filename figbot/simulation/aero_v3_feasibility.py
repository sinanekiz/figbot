"""AERO V3 engineering estimates; no geometry or controller changes.

SI internally. Motor ratings are manufacturer references, not clone measurements.
Camera pitch, fruit CG/radius, acceleration time and friction are scenarios.
"""
from pathlib import Path
import json
import math
import hashlib
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'reports/aero_v3_feasibility'
G = 9.80665
K = G*.01  # N m per kgf cm
L1,L2,H = .300,.220,.404
BASE = np.array([.380,.415,.280])
CAM = np.array([.3675,0.,.230])  # front lens surface; optical centre UNVERIFIED
CG_DROP = .086  # scenario close to two pad centres; actual fruit CG unknown


def ry(t):
    c,s=np.cos(t),np.sin(t)
    return np.array([[c,0,s],[0,1,0],[-s,0,c]])


def rz(t):
    c,s=np.cos(t),np.sin(t)
    return np.array([[c,-s,0],[s,c,0],[0,0,1]])


def ik(r,z):
    d=H-z
    b=math.acos((r*r+d*d-L1*L1-L2*L2)/(2*L1*L2))
    a=math.atan2(d,r)-math.atan2(L2*math.sin(b),L1+L2*math.cos(b))
    return np.array([0.,a,b,-a-b])


def camera_angles(point,pitch=35.):
    dx,dy,dz=np.array(point)-CAM
    p=math.radians(pitch)
    depth=dx*math.cos(p)-dz*math.sin(p)
    down=-dx*math.sin(p)-dz*math.cos(p)
    return math.degrees(math.atan2(dy,depth)),math.degrees(math.atan2(down,depth))


def launch_speed(distance,dz,theta_deg):
    t=math.radians(theta_deg)
    denom=2*math.cos(t)**2*(distance*math.tan(t)-dz)
    if denom<=0:raise ValueError('No positive ballistic solution at this angle')
    return math.sqrt(G*distance*distance/denom)


def ballistic_z(s,v,theta,z0):
    t=math.radians(theta)
    return z0+s*math.tan(t)-G*s*s/(2*v*v*math.cos(t)**2)


def load_bodies():
    import cadquery as cq
    from cad.prototype_arm import build_aero_v3 as a
    from cad.prototype_arm.export_aero_v3 import frame_for
    origins={'yaw':np.zeros(3),'upper':np.array([0,0,.124]),'fore':np.array([L1,0,.124]),'tool':np.array([L1+L2,0,.124])}
    bodies=[]
    for c in a.assembly((0,0,0),grip=5):
        frame=frame_for(c.name)
        if frame=='base' or c.group=='shaft':continue
        if frame=='finger':frame='tool'
        s=c.shape.val();vol=s.Volume()
        if c.group=='servo':mass=.0134 if c.name.startswith(('W1','G1')) else .055
        else:mass=vol*{'printed':1.27e-6,'tube':2.70e-6,'horn':1.15e-6,'hardware':7.85e-6,'pad':.35e-6}.get(c.group,1.27e-6)
        center=np.array(s.Center().toTuple())/1000-origins[frame]
        inertia=np.array(cq.Shape.matrixOfInertia(s))*mass/vol/1e6
        bodies.append((c.name,frame,mass,center,inertia))
    return bodies


def transforms(q):
    yaw,a,b,w=q;R=rz(yaw);shoulder=np.array([0.,0.,.124])
    elbow=shoulder+R@ry(a)@np.array([L1,0,0])
    wrist=elbow+R@ry(a+b)@np.array([L2,0,0])
    return {'yaw':(np.zeros(3),R),'upper':(shoulder,R@ry(a)),
            'fore':(elbow,R@ry(a+b)),'tool':(wrist,R@ry(a+b+w))}


def mass_matrix(q,bodies):
    eps=1e-5;poses=transforms(q)
    pert=[(transforms(q+np.eye(4)[i]*eps),transforms(q-np.eye(4)[i]*eps)) for i in range(4)]
    M=np.zeros((4,4));grav=np.zeros(4)
    for _,frame,m,c,I in bodies:
        o,R=poses[frame]
        J=np.zeros((3,4));Jw=np.zeros((3,4));Jw[:,0]=[0,0,1]
        n={'yaw':1,'upper':2,'fore':3,'tool':4}[frame]
        for i in range(1,n):Jw[:,i]=rz(q[0])@np.array([0,1,0])
        for i,(plus,minus) in enumerate(pert):
            op,Rp=plus[frame];om,Rm=minus[frame]
            J[:,i]=((op+Rp@c)-(om+Rm@c))/(2*eps)
        M+=m*J.T@J+Jw.T@(R@I@R.T)@Jw
        grav+=m*G*J[2,:]
    return M,grav


def torques(q,dq,ddq,bodies):
    M,grav=mass_matrix(q,bodies);eps=1e-4
    dM=np.array([(mass_matrix(q+np.eye(4)[k]*eps,bodies)[0]-mass_matrix(q-np.eye(4)[k]*eps,bodies)[0])/(2*eps) for k in range(4)])
    C=np.zeros(4)
    for i in range(4):
        for j in range(4):
            for k in range(4):C[i]+=.5*(dM[k,i,j]+dM[j,i,k]-dM[i,j,k])*dq[j]*dq[k]
    return M@ddq+C+grav,grav,M


def with_fruit(bodies,mass):
    return bodies+[('fruit','tool',mass,np.array([0.,0.,-CG_DROP]),np.zeros((3,3)))]


def build():
    OUT.mkdir(exist_ok=True,parents=True)
    bodies=load_bodies();rows=[]
    for r in (.22,.27,.32,.37,.40):
        q=ik(r,.102)
        loads={}
        for m in (0.,.04,.10):
            _,t=mass_matrix(q,with_fruit(bodies,m))
            loads[str(m)]=dict(zip(('yaw','shoulder_total','elbow','wrist'),np.abs(t/K).round(4)))
        rows.append({'r_from_shoulder_m':r,'x_vehicle_m':.380+r,'ahead_of_straight_tire_m':.380+r-(.290+.127),
                     'joint_angles_deg':np.degrees(q).tolist(),'gravity_kgf_cm':loads})
    reach=math.sqrt((L1+L2)**2-(H-.102)**2)
    cameras=[]
    for x,y in ((.600,.415),(.650,.415),(.700,.415),(.650,.500)):
        cameras.append({'target_ground_m':[x,y,0.], 'horizontal_lens_angles_deg':camera_angles((x,y,0),0),
                        'pitch35_lens_angles_deg':camera_angles((x,y,0),35)})
    # Scenario trajectory: from outside front corner, down onto near basket floor.
    start=np.array([.600,.415,.360]);end=np.array([.300,.250,0.])
    end[2]=.145+(.300+.280)*math.tan(math.radians(15))+.006+.020
    delta=end-start;distance=float(np.linalg.norm(delta[:2]));theta=20.
    v=launch_speed(distance,delta[2],theta);flight=distance/(v*math.cos(math.radians(theta)))
    velocity=np.r_[delta[:2]/distance*v*math.cos(math.radians(theta)),v*math.sin(math.radians(theta))]
    q=ik(start[0]-BASE[0],start[2]+CG_DROP)
    # Cartesian Jacobian, dependent wrist keeps fruit directly below wrist.
    eps=1e-5;J=np.zeros((3,3))
    def point(u):
        u=u.copy();u[3]=-u[1]-u[2];o,R=transforms(u)['tool'];return o+R@np.array([0,0,-CG_DROP])
    for i in range(3):J[:,i]=(point(q+np.eye(4)[i]*eps)-point(q-np.eye(4)[i]*eps))/(2*eps)
    dq3=np.linalg.solve(J,velocity);dq=np.r_[dq3,-dq3[1]-dq3[2]]
    dynamic=[]
    for m in (.04,.10):
        for ramp in (.10,.20):
            tau,gravity,M=torques(q,dq,dq/ramp,with_fruit(bodies,m))
            dynamic.append({'fruit_kg':m,'ramp_time_s':ramp,'torque_snapshot_kgf_cm':dict(zip(('yaw','shoulder_total','elbow','wrist'),(tau/K).round(4))),
                            'kinetic_energy_J':float(.5*dq@M@dq)})
    paths=[]
    for s in np.linspace(0,distance,201):
        xy=start[:2]+s/distance*delta[:2]
        paths.append([*xy,ballistic_z(s,v,theta,start[2])])
    apron_s=(start[0]-.415)/(start[0]-end[0])*distance
    apron_z=.145+.600*math.tan(math.radians(15))+.024
    comparative=[{'d_m':d,'rise_m':dz,'angle_deg':20.,'speed_m_s':launch_speed(d,dz,20.)} for d,dz in ((.2,0),(.3,0),(.4,0),(.3,.1))]
    from cad.prototype_arm import build_aero_v3 as cad
    poses=[]
    for name,p in cad.TARGETS.items():
        yaw,a,f=cad.ik(p);poses.append((name,np.array([yaw,a,f-a,-f])))
    limits=np.array([400.,400.,400.,600.]);cycle=[]
    for (n1,p1),(n2,p2) in zip(poses,poses[1:]+poses[:1]):
        times=np.abs(p2-p1)/limits
        cycle.append({'leg':n1+' -> '+n2,'ideal_no_acceleration_s':float(times.max())})
    result={'source_sha256':hashlib.sha256(Path(cad.__file__).read_bytes()).hexdigest(),
      'assumptions':{'dimensions':'AERO V3 unchanged; metres unless stated','camera_candidate':'Pi Camera Module 3 Wide 102H x67V degrees; not a purchased/verified sensor',
       'camera_pitch35':'scenario only; CAD optical axis remains horizontal','fruit':'point CG 86 mm below wrist; landing radius20 mm scenario, not inferred from mass',
       'dynamics':'nominal CAD rigid-body inertia, uniform servo mass distribution, full solid PETG. Missing fasteners/cables, friction, flexibility and motor rotor inertia. Acceleration snapshot, not trajectory peak or control approval.',
       'motor':'TowerPro web main specification 0.19/0.15 s per60deg at4.8/6V; 9.4/11kgfcm STALL; actual clones UNVERIFIED. Same page old table0.17 inconsistent; use main spec. User requested constant loaded speed counterfactual.',
       'throw':'air drag, rotation, gripper impulse excluded; no physical trajectory clearance certification'},
      'reach':{'theoretical_shoulder_radius_m':reach,'theoretical_ahead_of_tire_m':reach-.037,'sampled_rows':rows},
      'camera':cameras,'throw':{'start_cg_m':start.tolist(),'landing_cg_m':end.tolist(),'distance_m':distance,'angle_deg':theta,'speed_m_s':v,'flight_s':flight,
       'velocity_m_s':velocity.tolist(),'pose_degrees':np.degrees(q).tolist(),'required_joint_speed_deg_s':dict(zip(('yaw','shoulder','elbow_relative','wrist_relative'),np.degrees(dq).round(3))),
       'front_apron_sphere_bottom_clearance_m':ballistic_z(apron_s,v,theta,start[2])-.020-apron_z,'dynamic_snapshots':dynamic,'path':paths,'simple_comparisons':comparative},
      'cycle_ideal_lower_bound':cycle,'sources':['https://towerpro.com.tw/product/mg996r/','https://towerpro.com.tw/product/mg90s-3/','https://datasheets.raspberrypi.com/camera/camera-module-3-product-brief.pdf']}
    (OUT/'calculations.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    plot(result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('assumptions','sources')},indent=2)[:15000])
    return result


def plot(d):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, Rectangle
    fig,axes=plt.subplots(2,2,figsize=(14,10),facecolor='#f7f5f0')
    for ax in axes.flat:
        ax.set_facecolor('#f7f5f0');ax.grid(alpha=.18)
    ax=axes[0,0]
    ax.add_patch(Circle((.290,.127),.127,color='#65717b',alpha=.35))
    ax.axhline(0,color='#777777');ax.plot([.380,.380],[.280,.404],color='#65717b',lw=7)
    for r,color,label in ((.27,'#e47723','Mevcut alma pozu'),(.40,'#83aaa5','Uzak erişim örneği')):
        q=ik(r,.102);T=transforms(q);elbow=T['fore'][0];wrist=T['tool'][0]
        ax.plot([.380,.380+elbow[0],.380+wrist[0]],[H,.280+elbow[2],.280+wrist[2]],color=color,lw=4,label=label)
        ax.plot([.380+r,.380+r],[.102,.016],color=color,lw=3)
    ax.scatter([CAM[0]],[CAM[2]],color='#407db0',s=45)
    ax.annotate('Ön lastik sınırı: X=417 mm',(.417,.02),(.23,-.095),fontsize=9,arrowprops={'arrowstyle':'->'})
    ax.annotate('Mevcut hedef: lastikten 233 mm ileride',(.65,.016),(.45,-.155),fontsize=9,arrowprops={'arrowstyle':'->'})
    ax.set(xlim=(.12,.88),ylim=(-.20,.56),xlabel='Araç X (m)',ylabel='Yükseklik (m)',title='1 | Yerden erişim — omuz yüksekliği 404 mm');ax.legend(fontsize=8,loc='upper right')
    ax=axes[0,1]
    xx=np.linspace(.4,.9,180);yy=np.linspace(-.65,.65,200);X,Y=np.meshgrid(xx,yy)
    p=math.radians(35);depth=(X-CAM[0])*math.cos(p)+CAM[2]*math.sin(p)
    down=-(X-CAM[0])*math.sin(p)+CAM[2]*math.cos(p)
    visible=(np.abs(Y)<=depth*math.tan(math.radians(51)))&(np.abs(down)<=depth*math.tan(math.radians(33.5)))
    ax.contourf(X,Y,visible.astype(float),levels=[.5,1.5],colors=['#d4e5ef'])
    for sy in (-1,1):
        ax.add_patch(Rectangle((.163,sy*.415-.03),.254,.06,color='#65717b',alpha=.5))
        ax.plot([.62,.70],[sy*.415]*2,lw=8,color='#df8b43')
        ax.scatter([.65],[sy*.415],color='#b64f18',s=35)
    ax.scatter([CAM[0]],[0],color='#407db0',s=50)
    ax.text(.52,.02,'Mavi: 102° × 67° kamera\n35° aşağı eğim SENARYOSU',fontsize=9)
    ax.set(xlim=(.32,.9),ylim=(-.65,.65),xlabel='Araç X (m)',ylabel='Araç Y (m)',title='2 | Görüş ve toplama şeritleri — engeller hariç')
    ax=axes[1,0];r=d['reach']['sampled_rows']
    for mass,label,col in (('0.0','Yüksüz','#7e858c'),('0.04','40 g incir','#478c83'),('0.1','100 g incir','#d07830')):
        ax.plot([v['ahead_of_straight_tire_m']*100 for v in r],[v['gravity_kgf_cm'][mass]['shoulder_total'] for v in r],'-o',color=col,label=label)
    ax.axhline(22,color='#b44545',ls='--',label='2 × 11 kgf·cm: 6 V STALL referansı')
    ax.text(18.5,20.4,'Sürekli çalışma / hız kapasitesi değildir',color='#a34e4e',fontsize=9)
    ax.set(xlabel='Ön lastikten ileri mesafe (cm)',ylabel='İki omuz motoruna toplam statik tork (kgf·cm)',title='3 | Kolun kendi ağırlığı baskın');ax.legend(fontsize=8,loc='lower right')
    ax=axes[1,1];t=d['throw'];D=t['distance_m'];s=np.linspace(0,D,201)
    z=np.array(t['path'])[:,2];ax.plot(s,z,color='#d07830',lw=3,label='Meyve merkezi, 20° / 2,03 m/s')
    ax.fill_between(s,z-.02,z+.02,color='#d07830',alpha=.13)
    x=.600+(.300-.600)*s/D
    surface=np.where(x>=.320,.145+.600*math.tan(math.radians(15))+.006+(x-.320)*.018/.095,.145+(x+.280)*math.tan(math.radians(15))+.006)
    surface[x>.415]=np.nan
    ax.plot(s,surface,color='#5d9185',lw=4,label='Sepet / ön giriş yüzeyi')
    ax.scatter([0,D],[.360,t['landing_cg_m'][2]],color='#b45220')
    ax.text(.015,.30,'Uçuş: 0,180 s\nÖn girişte nominal alt boşluk: 27 mm\nDinamik motor yeterliliği ONAYLI DEĞİL',fontsize=9)
    ax.set(xlim=(-.01,.365),ylim=(.285,.435),xlabel='Sepete doğru yatay yol (m)',ylabel='Yerden yükseklik (m)',title='4 | Atışın fiziksel yolu mümkün; motor sınırı ayrı');ax.legend(fontsize=8,loc='upper right')
    fig.suptitle('FIGBOT AERO V3 | Erişim, görüş, yük ve atış incelemesi',fontsize=18,y=.99)
    fig.text(.05,.013,'CAD değiştirilmedi. Nominal boyutlar ve açık senaryolar kullanıldı; fiziksel kalibrasyon, meyve hasarı ve gerçek motor performansı doğrulanmadı.',fontsize=9,color='#755a46')
    fig.tight_layout(rect=(0,.035,1,.96))
    fig.savefig(OUT/'engineering_overview.png',dpi=160)
    fig.savefig(OUT/'engineering_overview.svg')
    plt.close(fig)


if __name__=='__main__':build()
