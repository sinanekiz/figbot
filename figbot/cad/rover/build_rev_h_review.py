"""Rev-H placement study using the actual Aero V2 components, not print geometry.

This is a packaging and discrete-pose review, not a vehicle manufacturing release
or proof of a dynamically safe trajectory. Coordinates are millimetres, +X front.
"""
from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path
import xml.etree.ElementTree as ET

import cadquery as cq
import numpy as np
from cad.prototype_arm import build_aero_v2 as arm
from cad.utils import ROOT, shape_mesh
from cad.rover import rev_h_running_gear as gear

OUT = ROOT / "cad/rover/rev_h_review"
BASE = (380.0, 415.0, 280.0)
BASKET_REAR, BASKET_FRONT = -280.0, 320.0
BASKET_HALF_WIDTH, BASKET_REAR_Z, SLOPE = 330.0, 145.0, 15.0
TARGETS = {"pickup": (650.0, 415.0, 30.0),
           "lift": (680.0, 415.0, 370.0),
           "release": (400.0, 275.0, 440.0)}
STATUS = "PACKAGING STUDY / PHYSICAL VALIDATION REQUIRED"


def floor_z(x):
    return BASKET_REAR_Z + (x - BASKET_REAR) * math.tan(math.radians(SLOPE))


def rotate_y(xz, angle):
    c, s = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    return np.array([xz[0]*c+xz[1]*s, -xz[0]*s+xz[1]*c])


def solve_pose(target, branch=1):
    """IK for the actual fixed-wrist soft-pad midpoint; no joint-limit claim."""
    dx, dy = target[0]-BASE[0], target[1]-BASE[1]
    r = math.hypot(dx, dy)
    down = BASE[2]+arm.ASSEMBLY_SHOULDER_Z-target[2]
    # Reference pad midpoint is wrist + (5, -116) at fore angle -18 deg.
    eff = np.array([arm.FOREARM_LINK_LENGTH, 0.0]) + rotate_y((5, -116), 18)
    length = float(np.linalg.norm(eff))
    offset = math.degrees(math.atan2(-eff[1], eff[0]))
    c = (r*r+down*down-arm.UPPER_LINK_LENGTH**2-length**2)/(2*arm.UPPER_LINK_LENGTH*length)
    if abs(c) > 1:
        raise ValueError("Target outside fixed-wrist geometric reach")
    elbow = branch*math.acos(c)
    upper = math.atan2(down, r)-math.atan2(length*math.sin(elbow), arm.UPPER_LINK_LENGTH+length*math.cos(elbow))
    return (math.degrees(math.atan2(dy, dx)), math.degrees(upper), math.degrees(upper+elbow)-offset)


def pad_position(pose):
    yaw, upper, fore = pose
    eff = np.array([arm.FOREARM_LINK_LENGTH, 0.0])+rotate_y((5,-116),18)
    xz = rotate_y((arm.UPPER_LINK_LENGTH,0),upper)+rotate_y(eff,fore)
    return np.array([BASE[0]+xz[0]*math.cos(math.radians(yaw)),
                     BASE[1]+xz[0]*math.sin(math.radians(yaw)),
                     BASE[2]+arm.ASSEMBLY_SHOULDER_Z+xz[1]])


@lru_cache(None)
def reference_components():
    return arm.assembly_components()


def posed_arm(pose, side=1):
    yaw, upper, fore = pose
    yaw *= side
    shoulder = (0., 0., arm.ASSEMBLY_SHOULDER_Z)
    old_e = np.array([300*math.cos(math.radians(18)),0,shoulder[2]-300*math.sin(math.radians(18))])
    new_e = np.array([300*math.cos(math.radians(upper)),0,shoulder[2]-300*math.sin(math.radians(upper))])
    fixed = {"J1 rounded base", "J1 yaw deck", "open shoulder pedestal", "dual-servo shoulder yoke"}
    upper_names = {"upper hub", "300 mm aluminium upper tube", "adjustable counterbalance tube anchor", "elbow yoke", "J2 horn"}
    result = []
    for item in reference_components():
        name, shape = item.name, item.shape
        # Spring force and routing are not defined; omit the misleading rigid bar.
        if name == "elastic counterbalance reference":
            continue
        if name in fixed or name.startswith(("J1 MG996R", "J2L MG996R", "J2R MG996R")):
            pass
        elif name in upper_names or name.startswith(("upper hollow", "J3 MG996R")):
            shape = shape.rotate(shoulder, (0,1,shoulder[2]), upper-18)
        else:
            shape = shape.rotate(tuple(old_e), tuple(old_e+np.array([0,1,0])), fore+18).translate(tuple(new_e-old_e))
        if name != "J1 rounded base" and not name.startswith("J1 MG996R"):
            shape = shape.rotate((0,0,0),(0,0,1),yaw)
        result.append(arm.Component(name, shape.translate((BASE[0],side*BASE[1],BASE[2])), item.group, item.color))
    return result


def dual_arms(pose):
    return [arm.Component(("L " if side==1 else "R ")+c.name,c.shape,c.group,c.color)
            for side in (1,-1) for c in posed_arm(pose,side)]


def cross_arm_gap(pose):
    left=posed_arm(pose,1);right=posed_arm(pose,-1)
    return min(c.shape.val().BoundingBox().ymin for c in left)-max(c.shape.val().BoundingBox().ymax for c in right)


def intersection_volume(a,b):
    aa,bb=a.BoundingBox(),b.BoundingBox()
    if aa.xmax<bb.xmin or bb.xmax<aa.xmin or aa.ymax<bb.ymin or bb.ymax<aa.ymin or aa.zmax<bb.zmin or bb.zmax<aa.zmin:
        return 0.
    return a.intersect(b).Volume()


def running_gear_review():
    parts=vehicle()
    obstacles=[c for c in parts if c.group in {'basket','equipment','camera'}]
    clashes=[]
    for a in gear.components():
        for b in obstacles:
            volume=intersection_volume(a.shape.val(),b.shape.val())
            if volume>.1:clashes.append([a.name,b.name,round(volume,2)])
    wheel_samples=[]
    for side,label in ((1,'L'),(-1,'R')):
        tire=next(c.shape for c in parts if c.name=='wheel F'+label)
        for angle in (-30,-15,0,15,30):
            shape=tire.rotate((290,side*370,0),(290,side*370,1),angle).val()
            hits=[]
            for other in parts:
                if other.name in {'wheel F'+label,'rim F'+label,'hub F'+label,'wheel bolts F'+label}:
                    continue
                v=intersection_volume(shape,other.shape.val())
                if v>.1:hits.append([other.name,round(v,2)])
            wheel_samples.append({'side':label,'steer_deg':angle,'intersections':hits})
    return {'connections':gear.connection_report(),'gear_vs_basket_equipment_camera':clashes,
            'front_tire_steering_samples':wheel_samples,
            'scope':'Nominal force-path adjacency and tire envelopes only. Steering linkage kinematics, bearing fits, bolts, torque, brakes and structural loads UNVERIFIED.'}


@lru_cache(None)
def vehicle():
    result = []
    def add(name, shape, color, group="vehicle"):
        result.append(arm.Component(name, shape, group, color))
    box = arm._box
    grey, blue, green = (.28,.33,.36), (.15,.38,.50), (.20,.43,.32)
    for y in (-285,285):
        add(f"chassis rail {y}", box(650,30,30,(0,y,90)),grey)
    for x in (-310,0,310):
        add(f"chassis crossmember {x}",box(30,600,30,(x,0,90)),grey)
    deck=box(630,570,6,(0,0,108))
    for side in (-1,1):
        deck=deck.cut(box(66,154,20,(-220,side*190,108)))
    add("equipment deck",deck,(.66,.69,.7))
    result.extend(gear.components())
    # The basket is a complete inclined trough: no impossible negative-height posts.
    rear, front = BASKET_REAR, BASKET_FRONT
    z0,z1=floor_z(rear),floor_z(front)
    add("basket floor 15deg",cq.Workplane("XZ").polyline([(rear,z0),(front,z1),(front,z1+6),(rear,z0+6)]).close().extrude(BASKET_HALF_WIDTH,both=True),(.68,.35,.18),"basket")
    for y in (-BASKET_HALF_WIDTH,BASKET_HALF_WIDTH):
        # Lower front lip permits immediate side release; rear retains cargo.
        side=cq.Workplane("XZ").polyline([(rear,z0),(front,z1),(front,z1+35),(rear,z0+180)]).close().extrude(3,both=True).translate((0,y,0))
        add(f"basket side {y}",side,(.83,.49,.25),"basket")
    add("basket padded rear wall",box(6,660,180,(rear,0,z0+90)),(.31,.5,.37),"basket")
    # Broad forward catch apron, sloping back into the main trough.
    add("front catch apron",cq.Workplane("XZ").polyline([(front,z1),(front+95,z1+18),(front+95,z1+24),(front,z1+6)]).close().extrude(330,both=True),(.88,.63,.34),"basket")
    for x in (-240,270):
        h=floor_z(x)-111
        for y in (-250,250):
            add(f"basket support {x} {y}",box(22,22,h,(x,y,111+h/2)),grey)
    add("battery envelope",box(180,100,100,(170,110,161)),green,"equipment")
    add("computer enclosure envelope",box(200,140,60,(30,-100,141)),blue,"equipment")
    add("power electronics envelope",box(140,100,55,(200,-100,138.5)),(.40,.30,.55),"equipment")
    add("front camera riser",box(22,22,130,(300,0,176)),grey)
    add("camera body envelope",box(55,90,40,(330,0,240)),(.10,.16,.20),"camera")
    lens=cq.Workplane("YZ").circle(13).extrude(10).translate((357.5,0,230))
    add("camera lens",lens,(.18,.54,.69),"camera")
    return result


def sweep_review():
    poses=[solve_pose(t) for t in TARGETS.values()]
    samples=[]
    for segment,(a,b) in enumerate(zip(poses,poses[1:])):
        for i in range(9):
            pose=tuple(np.array(a)+(np.array(b)-a)*i/8)
            result=review(pose)
            samples.append({"segment":segment,"fraction":i/8,
                            "lowest_arm_solid_mm":result["lowest_arm_solid_mm"],
                            "intersections":result["obstacle_intersections_mm3"]})
    return samples


def review(pose):
    components = dual_arms(pose)
    collisions=[]
    for component in components:
        for obstacle in vehicle():
            if obstacle.group not in {"wheel","basket","camera","equipment","running gear","drive","steering"}:
                continue
            a,b=component.shape.val(),obstacle.shape.val()
            aa,bb=a.BoundingBox(),b.BoundingBox()
            if aa.xmax<bb.xmin or bb.xmax<aa.xmin or aa.ymax<bb.ymin or bb.ymax<aa.ymin or aa.zmax<bb.zmin or bb.zmax<aa.zmin:
                continue
            volume=a.intersect(b).Volume()
            if volume>0.1:
                collisions.append([component.name,obstacle.name,round(volume,2)])
    return {"pose_degrees_yaw_upper_fore":pose,"pad_midpoint_mm":pad_position(pose).round(2).tolist(),"cross_arm_y_gap_mm":round(cross_arm_gap(pose),2),
            "lowest_arm_solid_mm":round(min(c.shape.val().BoundingBox().zmin for c in components),2),
            "fixed_gripper_tilt_from_reference_deg":round(pose[2]+18,2),"obstacle_intersections_mm3":collisions}


def render(components, path, side=False):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    fig=plt.figure(figsize=(13,8),facecolor="#f5f3ee")
    ax=fig.add_subplot(111,projection="3d")
    clouds=[]
    for item in components:
        xyz,faces=shape_mesh(item.shape)
        clouds.append(xyz)
        ax.add_collection3d(Poly3DCollection(xyz[faces],facecolor=item.color,edgecolor=item.color,linewidth=.025))
    bounds=np.vstack(clouds)
    low,high=bounds.min(axis=0),bounds.max(axis=0)
    span=high-low
    ax.set(xlim=(low[0]-30,high[0]+30),ylim=(low[1]-30,high[1]+30),zlim=(0,high[2]+30))
    ax.set_box_aspect((span[0]+60,span[1]+60,high[2]+30));ax.set_axis_off()
    ax.view_init(elev=5 if side else 23,azim=90 if side else 48)
    ax.set_title("FIGBOT Rev-H | Çift kol + bağlı yürüyen aksam + 15° sepet",fontsize=16,pad=10)
    fig.text(.08,.06,"Ön: +X  •  Çift kol yerleşimi  •  Renkli motorlar baskı parçası değildir",fontsize=11)
    fig.text(.08,.03,"Yerleşim çalışması: gerçek yük, kavrama, atış ve hareket sınırları henüz doğrulanmadı.",fontsize=10,color="#8a432b")
    fig.savefig(path,dpi=150,bbox_inches="tight");plt.close(fig)


def section_render():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon, Rectangle, Circle
    fig,ax=plt.subplots(figsize=(13,7),facecolor="#f5f3ee")
    ax.set_facecolor("#f5f3ee")
    for x in (-220,290):
        ax.add_patch(Circle((x,127),127,color="#3d464a",alpha=.25))
    ax.add_patch(Rectangle((-325,75),650,36,color="#626f76"))
    for name,x,z,w,h,color in [("Batarya",170,161,180,100,"#397b57"),("Beyin",30,141,200,60,"#377da0")]:
        # Deliberately offset labels, boxes remain at true X-Z projected coordinates.
        ax.add_patch(Rectangle((x-w/2,z-h/2),w,h,facecolor=color,alpha=.55))
        ax.annotate(name,(x,z),(x-100,-55 if name=="Batarya" else -90),arrowprops={"arrowstyle":"->"},fontsize=11)
    ax.plot([BASKET_REAR,BASKET_FRONT],[floor_z(BASKET_REAR),floor_z(BASKET_FRONT)],color="#d6803e",lw=8)
    ax.plot([BASKET_FRONT,BASKET_FRONT+95],[floor_z(BASKET_FRONT),floor_z(BASKET_FRONT)+18],color="#dca455",lw=8)
    ax.plot([BASKET_REAR,BASKET_REAR],[145,325],color="#397b57",lw=6)
    ax.annotate("Arkaya akış • 15°",(-100,floor_z(-100)),(40,330),arrowprops={"arrowstyle":"->","color":"#a45725"},fontsize=12,color="#a45725")
    for key,color in [("pickup","#e36622"),("release","#386da7")]:
        pose=solve_pose(TARGETS[key]);yaw,upper,fore=pose
        sh=np.array([BASE[0],BASE[2]+arm.ASSEMBLY_SHOULDER_Z])
        elbow=sh+np.array([300*math.cos(math.radians(upper))*math.cos(math.radians(yaw)),-300*math.sin(math.radians(upper))])
        wrist=elbow+np.array([220*math.cos(math.radians(fore))*math.cos(math.radians(yaw)),-220*math.sin(math.radians(fore))])
        tip=np.array([TARGETS[key][0],TARGETS[key][2]])
        ax.plot(*np.array([sh,elbow,wrist,tip]).T,"o-",color=color,lw=5,label="Yerden alma" if key=="pickup" else "Yan girişe bırakma")
    ax.add_patch(Rectangle((325,274),110,6,color="#626f76"))
    ax.annotate("Kol tabanı: 280 mm\nTeker üstünden +26 mm",(380,280),(460,290),arrowprops={"arrowstyle":"->"},fontsize=11)
    ax.scatter([330],[240],s=170,marker="s",color="#184d63")
    ax.annotate("Ön-alt kamera",(330,240),(490,360),arrowprops={"arrowstyle":"->"},fontsize=11)
    ax.plot([330,650],[240,30],"--",color="#3b97b7",lw=1,label="Hedef görüş hattı (şematik)")
    ax.axhline(0,color="#9da39d",lw=1)
    ax.text(-300,590,"ARKA",fontsize=13,weight="bold");ax.text(620,590,"ÖN",fontsize=13,weight="bold")
    ax.set_aspect("equal");ax.set_xlim(-390,850);ax.set_ylim(-120,820)
    ax.set_xlabel("Boyuna konum (mm)");ax.set_ylabel("Yerden yükseklik (mm)")
    ax.set_title("Rev-H • Yan kesit ve iki çalışma pozu",fontsize=17,pad=15)
    ax.legend(loc="upper left",frameon=False)
    fig.text(.12,.015,"Yan görünüm bir izdüşümdür; kol sepetin yanında. Atış yolu ve kamera görüş alanı henüz doğrulanmadı.",fontsize=10)
    fig.savefig(OUT/"layout_section.png",dpi=160,bbox_inches="tight");plt.close(fig)


def build():
    OUT.mkdir(parents=True,exist_ok=True)
    reports={}
    for name,target in TARGETS.items():
        pose=solve_pose(target)
        reports[name]=review(pose)
        components=vehicle()+dual_arms(pose)
        model=cq.Assembly(name=f"FIGBOT_REV_H_{name}")
        for i,c in enumerate(components):
            model.add(c.shape,name=f"part_{i}_{c.name}",color=cq.Color(*c.color))
        model.save(str(OUT/f"{name}.glb"),exportType="GLTF",tolerance=.3,angularTolerance=.15)
        if name=="pickup":
            model.save(str(OUT/"FIGBOT_REV_H_REVIEW.step"),exportType="STEP")
            # A fixed inspection URDF, explicitly not a control/simulation model.
            mesh=cq.Compound.makeCompound([c.shape.val() for c in components])
            cq.exporters.export(mesh,str(OUT/"review_scene.stl"),tolerance=.3)
            robot=ET.Element("robot",name="figbot_rev_h_fixed_inspection_only")
            link=ET.SubElement(robot,"link",name="review_scene")
            visual=ET.SubElement(link,"visual");geometry=ET.SubElement(visual,"geometry")
            ET.SubElement(geometry,"mesh",filename="review_scene.stl",scale="0.001 0.001 0.001")
            ET.ElementTree(robot).write(OUT/"review_fixed.urdf",encoding="utf-8",xml_declaration=True)
        render(components,OUT/f"{name}.png")
    section_render()
    running_report=running_gear_review()
    (OUT/'RUNNING_GEAR_REVIEW.json').write_text(json.dumps(running_report,indent=2),encoding='utf-8')
    report={"status":STATUS,"arm_base_mm":BASE,"wheel_top_mm":254,"base_above_wheel_mm":BASE[2]-254,
            "arm_count":2,"running_gear_connections":gear.connection_report(),"basket_slope_deg":SLOPE,"basket_front_floor_mm":floor_z(BASKET_FRONT),
            "basket_rear_floor_mm":BASKET_REAR_Z,"poses":reports,"sampled_path":sweep_review(),
            "scope":"Two arms; three poses and 18 joint-interpolated samples against wheel, basket, camera, equipment and running-gear solids. Cross-arm separation checked separately. No continuous sweep, self-collision, steering, compliance, cables, jaw actuation or dynamic validation.",
            "release":"DEC-039: Aero V2 full arm/gripper print on HOLD due to internal assembly defects. Rev-H vehicle/support geometry is packaging only, not printable or manufacture-ready."}
    (OUT/"REVIEW.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2),flush=True)
    return report


if __name__=="__main__":
    build()
