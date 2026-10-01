"""Rev-I direct side-basket spatial study; not manufacturing or control geometry.

Separate branch: shorter hollow links, purchased-motor envelopes and nominal
joint supports. No implicit edit to Rev-H or physically tried V4 interfaces.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import xml.etree.ElementTree as ET

import cadquery as cq
import numpy as np
from cad.utils import ROOT, shape_mesh
from cad.prototype_arm import build_aero_v3 as reference
from cad.rover import rev_h_running_gear as gear
from cad.rover import build_rev_h_review as previous

OUT = ROOT / "cad/rover/rev_i_direct_basket"
SHOULDER = np.array([550., 415., 160.])
UPPER, FORE, TOOL = 180., 140., 60.
FRUIT_RADIUS = 20.  # Unmeasured illustrative fruit envelope.
TARGETS = {
    "pickup": (700., 415., 20.),
    "lift": (690., 415., 175.),
    "clear": (690., 415., 330.),
    "turn": (560., 265., 330.),
    "release": (480., 285., 335.),
}
BLUE, LIGHT = (.12, .48, .58), (.27, .66, .69)
METAL, BLACK, GOLD = (.66, .7, .73), (.12, .15, .18), (.90, .58, .21)
STATUS = "SPATIAL DESIGN STUDY / NOT FOR PRINT / PHYSICAL VALIDATION REQUIRED"
box = reference.box


@dataclass
class Item:
    name: str
    shape: cq.Workplane
    group: str
    color: tuple
    frame: str = "vehicle"
    mass_g: float | None = None


def ry(a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rz(a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def solve(target):
    """Downward tool held vertical; elbow-up IK branch, CAD degrees only."""
    dx, dy = target[0]-SHOULDER[0], target[1]-SHOULDER[1]
    radial = math.hypot(dx, dy)
    down = SHOULDER[2] - (target[2]+TOOL)
    cosine = (radial**2+down**2-UPPER**2-FORE**2)/(2*UPPER*FORE)
    if abs(cosine) > 1+1e-9:
        raise ValueError("Target outside proposed arm reach")
    elbow = math.acos(float(np.clip(cosine, -1, 1)))
    upper = math.atan2(down, radial)-math.atan2(FORE*math.sin(elbow), UPPER+FORE*math.cos(elbow))
    return np.array([math.degrees(math.atan2(dy, dx)), math.degrees(upper),
                     math.degrees(elbow), -math.degrees(upper+elbow)])


def joints(q, side=1):
    yaw, upper, elbow, wrist_angle = q
    sh = SHOULDER.copy()
    rotation = rz(yaw)
    e = sh + rotation @ ry(upper) @ np.array([UPPER, 0., 0.])
    w = e + rotation @ ry(upper+elbow) @ np.array([FORE, 0., 0.])
    fruit = w + rotation @ ry(upper+elbow+wrist_angle) @ np.array([0., 0., -TOOL])
    return [p*np.array([1, side, 1]) for p in (sh, e, w, fruit)]


def floor_z(x):
    return 145. + (x+280.)*140./600.


def wing_z(x):
    return 285. + (x-320.)*20./190.


def slab(points, y0, y1):
    # XZ workplane extrusion points toward -Y; centre and both=True avoid ambiguity.
    return cq.Workplane("XZ").polyline(points).close().extrude((y1-y0)/2, both=True).translate((0,(y0+y1)/2,0))


def surface(x0, x1, z0, z1, y0, y1, thickness=5.):
    return slab([(x0,z0-thickness),(x1,z1-thickness),(x1,z1),(x0,z0)],y0,y1)


@lru_cache(None)
def vehicle():
    result = []
    skip = ("arm support", "arm top", "arm mount")
    for p in previous.vehicle():
        if p.group in {"basket", "camera"} or p.name.startswith(skip+("basket support",)) or p.name=="front camera riser":
            continue
        result.append(Item(p.name,p.shape,p.group,p.color))
    def add(name, shape, group="basket", color=(.84,.55,.29)):
        result.append(Item(name,shape,group,color))
    add("main basket floor",surface(-280,320,145,285,-330,330))
    add("main basket rear wall",box(6,660,95,(-277,0,192.5)))
    # The wings begin directly above the tire and join a full-width front bridge.
    add("front basket bridge",surface(320,510,285,305,-330,330))
    for side in (-1,1):
        y0,y1=sorted([side*330,side*470])
        add(f"over-wheel entry rear {side}",surface(250,320,floor_z(250),285,y0,y1))
        add(f"over-wheel entry front {side}",surface(320,510,285,305,y0,y1))
        add(f"rear basket side {side}",slab([(-280,145),(250,floor_z(250)),(250,floor_z(250)+45),(-280,240)],side*330-3,side*330+3))
        add(f"outer entry rail {side}",slab([(250,floor_z(250)),(510,305),(510,325),(250,floor_z(250)+20)],side*470-3,side*470+3))
        # Gate is open at the front; gripper deposits above the floor, no throw.
        add(f"entry front lip {side}",box(4,140,8,(508,side*400,309)))
        for x in (-240,270):
            top=floor_z(x)-5
            add(f"basket post {x} {side}",box(20,20,top-111,(x,side*250,(top+111)/2)),"support",METAL)
        # Chassis-fixed, triangulated support routed inboard of steering tires.
        for a,b in [((300,side*280,90),(550,side*280,60)),
                    ((500,side*280,66),(550,side*415,60)),
                    ((310,side*285,90),(500,side*280,140)),
                    ((500,side*280,140),(550,side*415,60))]:
            add(f"front arm carrier {side} {len(result)}",gear.rod(a,b,18),"support",METAL)
        add(f"front mounting plate {side}",box(104,142,6,(550,side*415,63)),"support",METAL)
        # Small independent fixed work-camera envelope, ahead of the basket edge.
        add(f"work camera {side}",box(26,34,22,(520,side*320,239)),"camera",BLACK)
        add(f"camera support {side}",gear.rod((505,side*280,145),(520,side*320,224),8),"support",METAL)
    return result


def ellipse_tube(length, width=24., height=30., wall=1.6):
    return cq.Workplane("YZ").ellipse(width/2,height/2).ellipse(width/2-wall,height/2-wall).extrude(length)


@lru_cache(None)
def local_arm():
    """Shaft-centred design envelopes. Coupling details deliberately not released."""
    result=[]
    def add(name,s,frame,group="proposed print",color=BLUE,mass=None):
        if mass is None and group=="proposed print":mass=s.val().Volume()*1.24/1000
        result.append(Item(name,s,group,color,frame,mass))
    # Local frame origin is the shoulder; base stays at fixed yaw.
    add("yaw servo MG996R",reference.servo_case().translate((0,0,-44)),"base","servo",BLACK,55.)
    add("yaw support cage",cq.Workplane("XY").circle(48).circle(40).extrude(49).translate((0,0,-94)),"base")
    add("yaw bearing reference",cq.Workplane("XY").circle(48).circle(40).extrude(4).translate((0,0,-45)),"base","hardware",METAL,18.)
    add("yaw horn reference",reference.horn().translate((0,0,-44)),"yaw","hardware",GOLD,3.)
    add("yaw deck",cq.Workplane("XY").circle(42).extrude(6).translate((0,0,-41)),"yaw")
    for side in (-1,1):
        # Motor bodies face inward toward the common pitch axis.
        add(f"shoulder MG996R {side}",reference.servo_place(reference.servo_case(),side,(0,side*17,0)),"yaw","servo",BLACK,55.)
        tower=box(44,8,48,(-15,side*34,-23))
        tower=tower.cut(reference.cyl_y(5,90,(0,0,0)))
        tower=tower.cut(reference.servo_place(reference.servo_case(),side,(0,side*17,0)))
        add(f"shoulder support {side}",tower,"yaw")
        add(f"shoulder reinforced cheek {side}",box(45,6,30,(12,side*13,0)),"upper")
        add(f"shoulder metal pivot {side}",reference.cyl_y(3,12,(0,side*14,0)),"upper","hardware",METAL,2.)
    add("upper hollow oval beam",ellipse_tube(UPPER-55).translate((30,0,0)),"upper")
    add("elbow saddle",box(33,40,24,(-8,0,0)),"elbow_upper")
    add("elbow MG996R",reference.servo_place(reference.servo_case(),1,(0,20,0)),"elbow_upper","servo",BLACK,55.)
    add("elbow opposite bearing",reference.cyl_y(10,8,(0,-20,0)).cut(reference.cyl_y(3,10,(0,-20,0))),"elbow_upper","hardware",METAL,5.)
    add("fore root collar",box(30,28,28,(15,0,0)),"fore")
    add("fore hollow oval beam",ellipse_tube(FORE-55,21,25,1.4).translate((30,0,0)),"fore")
    add("wrist saddle",box(25,32,22,(-8,0,0)),"wrist_fore")
    add("wrist MG90S",reference.servo_place(reference.servo_case(True),1,(0,17,0)),"wrist_fore","servo",BLACK,13.4)
    add("gripper MG90S",reference.servo_case(True).translate((0,0,-8)),"tool","servo",BLACK,13.4)
    add("gripper palm ring",cq.Workplane("XY").circle(33).circle(23).extrude(6).translate((0,0,-29)),"tool",color=LIGHT)
    for i in range(3):
        a=math.radians(i*120)
        p=(30*math.cos(a),30*math.sin(a),-27)
        b=(27*math.cos(a),27*math.sin(a),-TOOL)
        add(f"finger linkage envelope {i}",gear.rod(p,b,5),"tool",color=LIGHT)
        add(f"soft finger pad {i}",cq.Workplane("XY").sphere(7).translate(b),"tool","pad",(.33,.4,.36),1.5)
    return result


def arm_parts(q,side=1):
    yaw,upper,elbow,wrist=q
    sh,e,w,_=joints(q)
    # Geometry is transformed as rigid solids, not stretched from the old arm.
    frames={"base":(0,sh,False),"yaw":(0,sh,True),"upper":(upper,sh,True),
            "elbow_upper":(upper,e,True),"fore":(upper+elbow,e,True),
            "wrist_fore":(upper+elbow,w,True),"tool":(upper+elbow+wrist,w,True)}
    result=[]
    for item in local_arm():
        pitch,at,turn=frames[item.frame]
        s=item.shape.rotate((0,0,0),(0,1,0),pitch)
        if turn:s=s.rotate((0,0,0),(0,0,1),yaw)
        s=s.translate(tuple(at))
        if side<0:s=s.mirror("XZ")
        result.append(Item(f"{'L' if side>0 else 'R'} {item.name}",s,item.group,item.color,item.frame,item.mass_g))
    return result


def sampled_path(steps=8):
    poses=[solve(t) for t in TARGETS.values()]
    for index,(a,b) in enumerate(zip(poses,poses[1:])):
        for j in range(steps+1):
            yield index,j/steps,a+(b-a)*j/steps


def gravity(q,payload_g=100.):
    """Illustrative rigid static moment; print volume and nominal servo masses."""
    sh,e,w,fruit=joints(q)
    axis=rz(q[0]) @ np.array([0.,1.,0.])
    vals={"shoulder":0.,"elbow":0.,"wrist":0.}
    distal={"fore","wrist_fore","tool"}
    for item in arm_parts(q):
        if item.frame in {"base","yaw"}:continue
        c=item.shape.val().Center();p=np.array([c.x,c.y,c.z]);kg=(item.mass_g or 0)/1000
        vals["shoulder"]+=float(np.dot(np.cross((p-sh)/10,[0,0,-kg]),axis))
        if item.frame in distal:vals["elbow"]+=float(np.dot(np.cross((p-e)/10,[0,0,-kg]),axis))
        if item.frame=="tool":vals["wrist"]+=float(np.dot(np.cross((p-w)/10,[0,0,-kg]),axis))
    for name,origin in [("shoulder",sh),("elbow",e),("wrist",w)]:
        vals[name]+=float(np.dot(np.cross((fruit-origin)/10,[0,0,-payload_g/1000]),axis))
    return {name:round(abs(value),4) for name,value in vals.items()}


def overlaps(a,b):
    return previous.intersection_volume(a,b)


def audit_path(steps=8):
    # Left half only; all moving geometry, obstacles and steering samples mirror.
    obstacles=[p for p in vehicle() if p.shape.val().BoundingBox().ymax>=180]
    report=[]
    for segment,fraction,q in sampled_path(steps):
        parts=arm_parts(q)
        moving=[p for p in parts if p.frame not in {"base","yaw"}]
        collisions=[]
        for p in moving:
            for o in obstacles:
                v=overlaps(p.shape.val(),o.shape.val())
                if v>.1:collisions.append([p.name,o.name,round(v,2)])
        fruit=joints(q)[3]
        sphere=cq.Workplane("XY").sphere(FRUIT_RADIUS).translate(tuple(fruit)).val()
        for o in obstacles:
            v=overlaps(sphere,o.shape.val())
            if v>.1:collisions.append(["fruit envelope",o.name,round(v,2)])
        report.append({"segment":segment,"fraction":fraction,"q_deg":q.tolist(),
                       "fruit_mm":fruit.tolist(),"collisions_mm3":collisions,
                       "min_moving_z_mm":min(p.shape.val().BoundingBox().zmin for p in moving),
                       "fruit_bottom_z_mm":fruit[2]-FRUIT_RADIUS,"gravity_100g_kgfcm":gravity(q)})
    return report


def steering_audit():
    p=next(p for p in vehicle() if p.name=="wheel FL")
    new=[o for o in vehicle() if o.group in {"basket","support","camera"}]
    # Fixed arm bodies also matter even when arm is not moving.
    new += [o for o in arm_parts(solve(TARGETS["pickup"])) if o.frame in {"base","yaw"}]
    rows=[]
    for angle in range(-30,31,5):
        s=p.shape.rotate((290,370,0),(290,370,1),angle).val()
        hits=[]
        for o in new:
            v=overlaps(s,o.shape.val())
            if v>.1:hits.append([o.name,round(v,2)])
        rows.append({"steer_deg":angle,"collisions_mm3":hits,
                     "min_new_geometry_gap_mm":min(s.distance(o.shape.val()) for o in new)})
    return rows


def export_urdf():
    folder=OUT/"urdf";folder.mkdir(exist_ok=True)
    robot=ET.Element("robot",name="figbot_rev_i_geometry_review_not_control")
    def link(name,shapes):
        node=ET.SubElement(robot,"link",name=name)
        compound=cq.Compound.makeCompound([s.val() for s in shapes])
        cq.exporters.export(compound,str(folder/f"{name}.stl"),tolerance=.4)
        visual=ET.SubElement(node,"visual");geom=ET.SubElement(visual,"geometry")
        ET.SubElement(geom,"mesh",filename=f"{name}.stl",scale="0.001 0.001 0.001")
    link("vehicle",[p.shape for p in vehicle()])
    # Fixed inspection pose avoids claiming physical joint calibrations or inertia.
    for side in (-1,1):
        name="left_arm" if side==1 else "right_arm"
        link(name,[p.shape for p in arm_parts(solve(TARGETS["pickup"]),side)])
        j=ET.SubElement(robot,"joint",name=f"{name}_inspection",type="fixed")
        ET.SubElement(j,"parent",link="vehicle");ET.SubElement(j,"child",link=name)
    ET.ElementTree(robot).write(folder/"REV_I_INSPECTION.urdf",encoding="utf-8",xml_declaration=True)


def render(parts,path,title,side=False):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    fig=plt.figure(figsize=(14,8),facecolor="#f5f3ee")
    ax=fig.add_axes((.035,.10,.93,.78))
    ax.set_facecolor("#f5f3ee")
    az,el=math.radians(48),math.radians(25)
    eye=np.array([math.cos(el)*math.cos(az),math.cos(el)*math.sin(az),math.sin(el)])
    right=np.array([-math.sin(az),math.cos(az),0.])
    up=np.cross(eye,right)
    basis=np.stack([right,up,eye],axis=1)
    polygons=[];depths=[];colors=[]
    for item in parts:
        v,f=shape_mesh(item.shape)
        projected=v@basis;tri=v[f]
        normals=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
        norms=np.maximum(np.linalg.norm(normals,axis=1),1e-9)
        shade=.64+.36*np.abs((normals/norms[:,None])@np.array([.3,.4,.866]))
        projected_faces=projected[f]
        polygons.extend(projected_faces[:,:,:2]);depths.extend(projected_faces[:,:,2].mean(axis=1))
        colors.extend(np.clip(shade[:,None]*np.array(item.color),0,1))
    order=np.argsort(depths)
    polys=np.asarray(polygons)[order]
    ax.add_collection(PolyCollection(polys,facecolors=np.asarray(colors)[order],edgecolors='none',rasterized=True))
    low=polys.min(axis=(0,1));high=polys.max(axis=(0,1));margin=(high-low)*.04
    ax.set(xlim=(low[0]-margin[0],high[0]+margin[0]),ylim=(low[1]-margin[1],high[1]+margin[1]))
    ax.set_aspect('equal');ax.set_axis_off()
    fig.suptitle(title,fontsize=20,y=.95)
    fig.text(.08,.045,"Mevcut motorlar • Teker önünde kısa kol • Teker üstünde yan sepet girişi",fontsize=12)
    fig.text(.08,.02,"CAD yerleşim incelemesi; baskı paketi ve doğrulanmış taşıma kapasitesi değildir.",fontsize=10,color="#8a432b")
    fig.savefig(path,dpi=160,bbox_inches="tight");plt.close(fig)


def section():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle,Rectangle
    fig,axes=plt.subplots(1,2,figsize=(15,7),facecolor="#f5f3ee")
    ax=axes[0];ax.set_facecolor("#f5f3ee")
    for x in (-220,290):ax.add_patch(Circle((x,127),127,color="#6a7479",alpha=.3))
    ax.plot([-280,320,510],[145,285,305],color="#bf7835",lw=6)
    ax.annotate("Teker üstünden başlayan\nyan giriş: 305 mm",(480,302),(130,470),arrowprops={"arrowstyle":"->"},fontsize=11)
    for name,color in [("pickup","#267c8c"),("release","#d47726")]:
        points=np.array(joints(solve(TARGETS[name])))
        ax.plot(points[:,0],points[:,2],"o-",color=color,lw=3,label="Yerden al" if name=="pickup" else "Yan sepete bırak")
    ax.annotate("Omuz: 160 mm\nTekerin önünde",(550,160),(440,-80),arrowprops={"arrowstyle":"->"},fontsize=11)
    ax.axhline(0,color="#999");ax.set(xlim=(-350,800),ylim=(-110,570),title="YAN GÖRÜNÜM — mm")
    ax.set_aspect("equal");ax.legend(frameon=False)
    ax=axes[1];ax.set_facecolor("#f5f3ee")
    for side in (-1,1):
        ax.add_patch(Rectangle((163,side*415-30),254,60,color="#6a7479",alpha=.4))
        ax.add_patch(Rectangle((250,side*400-70),260,140,color="#dfb77d",alpha=.6))
        for name,color in [("pickup","#267c8c"),("release","#d47726")]:
            points=np.array(joints(solve(TARGETS[name]),side))
            ax.plot(points[:,0],points[:,1],"o-",color=color,lw=3)
    ax.add_patch(Rectangle((-280,-330),790,660,color="#dfb77d",alpha=.3))
    ax.text(-150,0,"ORTAK SEPET",fontsize=12,weight="bold")
    ax.annotate("Sağa-sola dönen taban",(550,415),(540,560),arrowprops={"arrowstyle":"->"},fontsize=11)
    ax.set(xlim=(-350,800),ylim=(-620,620),title="ÜST GÖRÜNÜM — mm");ax.set_aspect("equal")
    for ax in axes:ax.grid(alpha=.15)
    fig.suptitle("Rev-I | Bant olmadan, kısa yoldan sepete",fontsize=20)
    fig.text(.06,.02,"180 + 140 mm kol boyları öneridir. Renkler iki ayrı pozu gösterir; hareket ve mukavemet fiziksel olarak doğrulanmadı.",fontsize=10)
    fig.tight_layout(rect=(0,.05,1,.95));fig.savefig(OUT/"layout_section.png",dpi=160);plt.close(fig)


def build():
    OUT.mkdir(parents=True,exist_ok=True)
    path=audit_path();steer=steering_audit()
    report={"status":STATUS,"shoulder_mm":SHOULDER.tolist(),"links_mm":[UPPER,FORE],
            "tool_offset_mm":TOOL,"arm_count":2,"motors_per_arm":{"MG996R":4,"MG90S":2},
            "targets_mm":TARGETS,"poses":{n:solve(t).tolist() for n,t in TARGETS.items()},
            "sampled_path":path,"steering_samples":steer,
            "max_sampled_static_100g_kgfcm":{j:max(r["gravity_100g_kgfcm"][j] for r in path) for j in ("shoulder","elbow","wrist")},
            "proposed_print_mass_g_per_arm":sum(p.mass_g for p in local_arm() if p.group=="proposed print"),
            "limits":"No physical servo-angle registration, continuous sweep, self-collision, cables, grasp transmission, strength, thermal or dynamic validation. Nominal servo masses and CAD print volumes; unmodelled bolts/wiring/links remain TBD."}
    (OUT/"REVIEW.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    for name in ("pickup","release"):
        q=solve(TARGETS[name]);parts=vehicle()+arm_parts(q)+arm_parts(q,-1)
        for side in (-1,1):
            fruit=joints(q,side)[3]
            parts.append(Item(f"fruit {side}",cq.Workplane("XY").sphere(FRUIT_RADIUS).translate(tuple(fruit)),"fruit",(.39,.26,.34)))
        model=cq.Assembly(name=f"FIGBOT_REV_I_{name}")
        for i,p in enumerate(parts):model.add(p.shape,name=f"part_{i}",color=cq.Color(*p.color))
        model.save(str(OUT/f"{name}.step"),exportType="STEP")
        model.save(str(OUT/f"{name}.glb"),exportType="GLTF",tolerance=.4,angularTolerance=.15)
        render(parts,OUT/f"{name}.png",f"FIGBOT Rev-I | {'Yerden alma' if name=='pickup' else 'Yan sepete bırakma'}")
    export_urdf();section()
    print(json.dumps({"path_collisions":sum(bool(r['collisions_mm3']) for r in path),
                      "steer_collisions":sum(bool(r['collisions_mm3']) for r in steer),
                      "max_static":report['max_sampled_static_100g_kgfcm']},indent=2))
    return report


if __name__=="__main__":build()
