"""Connected running-gear packaging. All unselected purchased interfaces UNVERIFIED.

Rear: two independent geared DC motors, couplings, double-supported stub shafts.
Front: free-running bearing hubs, kingpins, steering arms, tie rod and actuator.
No torque rating or manufacturer part-number claim is made by these envelopes.
"""
import math
from functools import lru_cache
import cadquery as cq
import numpy as np
from cad.prototype_arm.build_aero_v2 import Component, _box, _rounded_box

METAL=(.64,.69,.73)
FRAME=(.29,.36,.4)
DRIVE=(.16,.38,.52)
STEER=(.85,.54,.18)
WHEEL_RADIUS=127.
REAR_X,FRONT_X,TRACK_HALF,AXIS_Z=-220.,290.,415.,127.
SHAFT_DIAMETER=20. # Provisional mechanical interface, not a selected axle.


def cyl_y(radius,length,at,inner=0):
    w=cq.Workplane("XZ").circle(radius)
    if inner: w=w.circle(inner)
    return w.extrude(length/2,both=True).translate(at)


def rod(a,b,diameter):
    a,b=np.array(a,dtype=float),np.array(b,dtype=float)
    v=b-a;length=float(np.linalg.norm(v));u=v/length
    axis=(-u[1],u[0],0.)
    angle=math.degrees(math.acos(float(np.clip(u[2],-1,1))))
    shape=cq.Workplane("XY").circle(diameter/2).extrude(length)
    if np.linalg.norm(axis)>1e-8:shape=shape.rotate((0,0,0),tuple(axis),angle)
    elif u[2]<0:shape=shape.rotate((0,0,0),(1,0,0),180)
    return shape.translate(tuple(a))


def wheel(x,y,front=False):
    tire=cyl_y(127,60,(x,y,127),80)
    tire=tire.edges().fillet(3)
    rim=cyl_y(83,36,(x,y,127),68)
    for angle in range(0,360,60):
        spoke=_rounded_box(56,16,14,4,at=(50,0,0),long_axis="X")
        rim=rim.union(spoke.rotate((0,0,0),(0,1,0),angle).translate((x,y,127)))
    hub=cyl_y(28,50,(x,y,127),17.5 if front else 10)
    flange=cyl_y(37,8,(x,y,127),17.5 if front else 10)
    hub=hub.union(flange)
    # Four visible wheel bolts, inside hub/spoke load path.
    bolts=[]
    for angle in (45,135,225,315):
        t=math.radians(angle)
        bolts.append(cyl_y(3,26,(x+31*math.cos(t),y,127+31*math.sin(t))))
    return tire,rim,hub,cq.Workplane(obj=cq.Compound.makeCompound([b.val() for b in bolts]))


@lru_cache(None)
def components():
    parts=[]
    def add(name,shape,color=METAL,group="running gear"):
        parts.append(Component(name,shape,group,color))
    for side in (-1,1):
        label="L" if side==1 else "R"
        sy=lambda n:side*n
        # Rear bearing shelf touches the original side rail at Y=285.
        add(f"rear bearing outrigger {label}",_box(80,115,30,(-220,sy(327.5),90)),FRAME)
        add(f"rear shelf gusset {label}",cq.Workplane("YZ").polyline([(sy(285),75),(sy(370),75),(sy(285),40)]).close().extrude(4,both=True).translate((-220,0,0)),FRAME)
        # Motor output is collinear with coupling, bearings and wheel centre.
        cradle=_box(62,180,8,(-220,sy(205),103))
        cradle=cradle.cut(cyl_y(25,60,(-220,sy(160),127)))
        cradle=cradle.cut(_rounded_box(50,60,50,5,at=(-220,sy(220),127),long_axis="Y"))
        add(f"rear motor cradle {label}",cradle,FRAME)
        add(f"rear DC motor {label}",cyl_y(25,60,(-220,sy(160),127)),DRIVE,"drive")
        add(f"rear gearbox {label}",_rounded_box(50,60,50,5,at=(-220,sy(220),127),long_axis="Y"),DRIVE,"drive")
        add(f"rear motor retaining strap {label}",cyl_y(28,10,(-220,sy(160),127),25),METAL)
        for yy in (140,180,235):
            add(f"motor mount bolt {label} {yy}",rod((-248,sy(yy),97),(-248,sy(yy),113),5),METAL)
        add(f"rear motor output shaft {label}",cyl_y(6,35,(-220,sy(267.5),127)))
        coupling=cyl_y(17,30,(-220,sy(285),127))
        coupling=coupling.cut(cyl_y(6,16,(-220,sy(277.5),127)))
        coupling=coupling.cut(cyl_y(10,16,(-220,sy(292.5),127)))
        add(f"rear shaft coupling {label}",coupling,STEER)
        axle=cyl_y(10,171,(-220,sy(370.5),127))
        keyway=_box(6,40,6,(-220,sy(415),137))
        add(f"rear supported axle {label}",axle.cut(keyway))
        add(f"rear drive key {label}",_box(6,38,6,(-220,sy(415),137)),STEER)
        for yy in (320,365):
            housing=_rounded_box(60,24,44,5,at=(-220,sy(yy),127),long_axis="Y")
            housing=housing.cut(cyl_y(21,40,(-220,sy(yy),127)))
            housing=housing.union(_box(70,34,6,(-220,sy(yy),108)))
            housing=housing.cut(cyl_y(21,40,(-220,sy(yy),127)))
            for xx in (-247,-193):
                hole=cq.Workplane("XY").center(xx,sy(yy)).circle(3.3).extrude(20).translate((0,0,99))
                housing=housing.cut(hole)
                add(f"bearing mount bolt {label} {yy} {xx}",rod((xx,sy(yy),97),(xx,sy(yy),114),6))
            add(f"rear bearing housing {label} {yy}",housing,FRAME)
            add(f"rear bearing insert {label} {yy}",cyl_y(21,12,(-220,sy(yy),127),10),METAL)
        # Long supports formerly intersected the front tires. Uprights are now
        # behind the tire sweep and cantilever across only above tire top.
        add(f"arm support outrigger {label}",_box(50,100,30,(100,sy(330),90)),FRAME)
        add(f"arm support upright {label}",_box(30,30,158,(100,sy(365),184)),FRAME)
        add(f"arm top longitudinal rail {label}",_box(330,30,12,(250,sy(365),269)),FRAME)
        add(f"arm mount {label}",_box(180,140,6,(350,sy(405),277)),FRAME)
        add(f"arm mount cross tie {label}",_box(40,100,8,(380,sy(380),270)),FRAME)
        # Two small triangular webs connect the upper rail to the upright.
        for yy in (sy(356),sy(374)):
            web=cq.Workplane("XZ").polyline([(85,260),(175,260),(85,205)]).close().extrude(3,both=True).translate((0,yy,0))
            add(f"arm support gusset {label} {yy}",web,FRAME)
        # Front wheel/kingpin: upper bridge avoids the rotating tire envelope.
        kp=(290,sy(370),127)
        stem=rod((290,sy(370),161),(290,sy(370),266),20)
        stem=stem.cut(rod((290,sy(370),150),(290,sy(370),176),16))
        add(f"front kingpin support stem {label}",stem,FRAME)
        add(f"front fixed carrier {label}",_box(26,18,76,(290,sy(350),127)),FRAME)
        for zz in (98,156):
            lug=cq.Workplane("XY").circle(16).circle(8).extrude(10,both=True).translate((290,sy(370),zz))
            lug=lug.union(_box(26,22,12,(290,sy(360),zz)))
            lug=lug.cut(cq.Workplane("XY").center(290,sy(370)).circle(8).extrude(25,both=True).translate((0,0,zz)))
            add(f"front kingpin bearing carrier {label} {zz}",lug,FRAME)
        add(f"front kingpin {label}",rod((290,sy(370),85),(290,sy(370),171),16),STEER)
        knuckle=_rounded_box(30,30,38,4,at=kp,long_axis="Z")
        knuckle=knuckle.cut(rod((290,sy(370),95),(290,sy(370),160),16))
        add(f"front steering knuckle {label}",knuckle,STEER)
        add(f"front spindle {label}",cyl_y(10,76,(290,sy(418),127)),METAL)
        for yy in (400,430):
            add(f"front hub bearing {label} {yy}",cyl_y(17.5,10,(290,sy(yy),127),10),METAL)
        tie_y=370-70*370/510
        end=(220,sy(tie_y),240)
        add(f"front steering arm {label}",rod((275,sy(370),140),end,14),STEER)
        add(f"front tie rod ball {label}",cq.Workplane("XY").sphere(11).translate(end),STEER)
        for x,front in ((-220,False),(290,True)):
            tag=("F" if front else "R")+label
            tire,rim,hub,bolts=wheel(x,sy(415),front)
            if not front:hub=hub.cut(_box(6,40,6,(x,sy(415),137)))
            add(f"wheel {tag}",tire,(.10,.13,.15),"wheel")
            add(f"rim {tag}",rim,(.72,.77,.79))
            add(f"hub {tag}",hub,METAL)
            add(f"wheel bolts {tag}",bolts,STEER)
            add(f"axle washer {tag}",cyl_y(16,3,(x,sy(441.5),127),10))
            nut=cq.Workplane("XZ").polygon(6,29).extrude(6,both=True).translate((x,sy(449),127))
            nut=nut.cut(cyl_y(10,20,(x,sy(449),127)))
            add(f"axle nut {tag}",nut,STEER)
    add("front upper bridge",_box(40,780,10,(290,0,268)),FRAME)
    tie_y=370-70*370/510
    add("front steering tie rod",rod((220,-tie_y,240),(220,tie_y,240),12),METAL,"steering")
    start=np.array([300.,-175.,240.]);end=np.array([220.,tie_y,240.])
    split=start+(end-start)*.52
    add("steering actuator body envelope",rod(tuple(start),tuple(split),32),DRIVE,"steering")
    add("steering actuator pushrod",rod(tuple(split),tuple(end),12),METAL,"steering")
    add("steering actuator fixed bracket",_box(30,20,129,(300,-175,175.5)),FRAME)
    add("steering actuator pivot pin",rod((300,-175,226),(300,-175,256),8),STEER)
    return parts


def connection_pairs():
    """Geometric adjacency checks for the declared force path; not strength tests."""
    pairs=[]
    for label in ("L","R"):
        pairs += [(f"rear DC motor {label}",f"rear gearbox {label}"),
                  (f"rear gearbox {label}",f"rear motor output shaft {label}"),
                  (f"rear motor output shaft {label}",f"rear shaft coupling {label}"),
                  (f"rear shaft coupling {label}",f"rear supported axle {label}"),
                  (f"rear supported axle {label}",f"hub R{label}"),
                  (f"hub R{label}",f"rim R{label}"),(f"rim R{label}",f"wheel R{label}"),
                  (f"front upper bridge",f"front kingpin support stem {label}"),
                  (f"front kingpin support stem {label}",f"front kingpin bearing carrier {label} 156"),
                  (f"front kingpin {label}",f"front steering knuckle {label}"),
                  (f"front steering knuckle {label}",f"front spindle {label}"),
                  (f"front spindle {label}",f"front hub bearing {label} 400"),
                  (f"front hub bearing {label} 400",f"hub F{label}"),
                  (f"hub F{label}",f"rim F{label}"),(f"rim F{label}",f"wheel F{label}"),
                  (f"front steering arm {label}",f"front steering knuckle {label}"),
                  (f"front steering arm {label}","front steering tie rod"),
                  (f"arm support outrigger {label}",f"arm support upright {label}"),
                  (f"arm support upright {label}",f"arm top longitudinal rail {label}"),
                  (f"arm top longitudinal rail {label}",f"arm mount {label}")]
        for yy in (320,365):
            pairs += [(f"rear supported axle {label}",f"rear bearing insert {label} {yy}"),
                      (f"rear bearing insert {label} {yy}",f"rear bearing housing {label} {yy}"),
                      (f"rear bearing housing {label} {yy}",f"rear bearing outrigger {label}")]
    return pairs+[("steering actuator body envelope","steering actuator fixed bracket"),
                  ("steering actuator body envelope","steering actuator pushrod"),
                  ("steering actuator pushrod","front tie rod ball L")]


def connection_report():
    items={c.name:c.shape.val() for c in components()}
    return [{"a":a,"b":b,"gap_mm":round(items[a].distance(items[b]),4)} for a,b in connection_pairs()]
