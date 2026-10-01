"""Short bolted arm: printable engineering prototype, not a load-certified product.

Uses the repository's user-horn contour adapters. No printed servo splines.
Body dimensions are nominal; every mechanical interface needs a first-fit check.
"""
from dataclasses import dataclass
from functools import lru_cache
import math
import cadquery as cq
import numpy as np
from cad.utils import ROOT
from cad.prototype_arm import build_aero_v4 as v4
from cad.prototype_arm import build_aero_v3 as old
from cad.prototype_arm import build_snap03b_mg90 as micro

OUT=ROOT/'cad/prototype_arm/aero_v5'
UPPER,FORE,SHOULDER_Z=180.,140.,124.
ROVER_BASE=np.array([550.,415.,66.])
TOOL=110.
TOOL_X=34.
STATUS='ENGINEERING PRINT PROTOTYPE; FIT AND LOAD VALIDATION REQUIRED'
BLUE=(.14,.37,.43); LIGHT=(.39,.68,.66); METAL=(.67,.70,.72)
DARK=(.13,.15,.18); ORANGE=(.88,.48,.20)
box=old.box
transform=v4.transform


@dataclass
class Item:
    name:str
    shape:cq.Workplane
    frame:str
    part_id:str=''
    group:str='printed'
    color:tuple=BLUE


def loft_sections(sections):
    # x, centre_y, full width, full height. Smooth closed outside section.
    w=cq.Workplane('YZ')
    last=0.
    for x,y,b,h in sections:
        w=w.workplane(offset=x-last).center(y,0).ellipse(b/2,h/2).center(-y,0)
        last=x
    return w.loft(combine=True,ruled=True)


def bore_z(s,x,y,d):
    return s.cut(cq.Workplane('XY').center(x,y).circle(d/2).extrude(200,both=True))


def screw_stations(fore=False):
    return [(72,18),(98,18),(107.5,-23),(107.5,29)] if fore else [(72,-18),(107,-18),(137,-18),(136,-34),(136,34)]


@lru_cache(None)
def link_complete(fore=False):
    span=FORE if fore else UPPER
    offset=18 if fore else -18
    carrier=v4.fore_carrier() if fore else v4.upper_carrier()
    yoke=v4.stator_yoke(fore).translate((span,0,0))
    # Continuous flared connection replaces the weak separate root/beam neck.
    sections=[(48,-4 if not fore else -6,64,26),
              (68,offset,32,30),(span-52,offset,28,30),(span-28,offset,30,26)]
    skin=loft_sections(sections)
    s=carrier.union(skin).union(yoke)
    bridge_x=span-(32.5 if fore else 44.)
    bridge_y0=-32 if fore else -42
    bridge_y1=35.75 if fore else 43
    lower_bridge=box(10,bridge_y1-bridge_y0,8,(bridge_x,(bridge_y0+bridge_y1)/2,-10))
    s=s.union(lower_bridge)
    # Open, inspectable cavity; 2.4mm top/bottom and >=2.4mm lateral walls.
    cavity=loft_sections([(68,offset,22,25.2),(span-53,offset,22,25.2)])
    s=s.cut(cavity)
    for x,y in screw_stations(fore):
        # Flat washer lands; a 30mm sleeve prevents clamping the hollow cavity.
        boss=cq.Workplane('XY').center(x,y).circle(6).extrude(30).translate((0,0,-15))
        s=s.union(boss)
        # Standard 6x1mm aluminium tube: final length measured flush.
        s=bore_z(s,x,y,6.25)
    for side in ([-1,1] if not fore else [1]):
        s=v4.clear_receiver(s,v4.horn_pose(side=side))
    # Clear the original motor body and clamp screw passages after merging shells.
    mt=v4.motor_pose(fore,1,(span,15.75 if fore else 23,0))
    clearance=old.servo_case(fore)
    s=s.cut(transform(clearance,mt))
    for px,py in old.clamp_points(fore):
        hole=cq.Workplane('XY').center(px,py).circle(1.7).extrude(160,both=True)
        s=s.cut(transform(hole,mt))
    # Old loose-beam cross holes now have no purpose; new body uses five shell bolts.
    # Keep the passive M6 access bore unobstructed.
    s=old.hole_y(s,span,0,6.4)
    if fore:
        s=old.hole_y(s,0,0,6.4)
        # Wrist horn capsule passes close to the lower bridge at mid-travel.
        # Local radial relief retains the bolted boss while providing clearance.
        s=s.cut(old.cyl_y(28.5,3.6,(FORE,14.5,0)))
    return s.clean()


@lru_cache(None)
def shell(fore=False,top=True):
    s=link_complete(fore)
    clip=box(800,300,200,(0,0,100 if top else -100))
    s=s.intersect(clip).clean()
    # Loft/legacy-socket union can leave sub-5mm3 sealed slivers. Fill these in
    # CAD, never by deleting a functional exterior surface from the STL.
    solid=s.solids().val()
    inner=solid.innerShells()
    if inner:
        assert all(abs(cq.Solid.makeSolid(c).Volume())<5 for c in inner)
        s=cq.Workplane(obj=cq.Solid.makeSolid(solid.outerShell())).clean()
    return s


@lru_cache(None)
def tower(side=1):
    s=v4.shoulder_tower()
    # Broader foot-to-motor transitions, with two transverse metal bolts.
    for x in [-38,22]:
        rib=box(12,6,21,(x,39,99))
        s=s.union(rib)
        s=old.hole_y(s,x,85.5,3.4)
    s=s.cut(transform(old.servo_case(),v4.motor_pose(False,1,(0,23,124))))
    s=s.cut(v4.shoulder_deck())
    for sx in [-1,1]:
        px=-.2*old.MG[0]+sx*(old.MG[0]/2+4)
        s=s.cut(transform(old.clamp_bar().translate((px,0,-13.6)),v4.motor_pose(False,1,(0,23,124))))
    for px,py in old.clamp_points():
        s=s.cut(transform(cq.Workplane('XY').center(px,py).circle(1.7).extrude(160,both=True),v4.motor_pose(False,1,(0,23,124))))
    return s if side==1 else s.mirror('XZ')


@lru_cache(None)
def palm():
    # Existing wrist capsule and opposite support retain screwdriver access.
    s=transform(v4.receiver(True),v4.WRIST_HORN)
    s=s.union(old.cyl_y(11,10,(0,-22.6,0)))
    s=s.union(box(10,10,35,(0,-22.6,-17.5)))
    s=s.union(box(30,8,8,(10,-22.6,-30)))
    # Three open radial guide slots. Fingers move through them, not through a floor.
    guide=cq.Workplane('XY').circle(44).extrude(4).translate((0,0,-61))
    for a in [0,120,240]:
        cut=box(36,8.6,10,(30,0,-59)).rotate((0,0,0),(0,0,1),a)
        guide=guide.cut(cut)
    guide=bore_z(guide,0,0,10)
    s=s.union(guide.translate((TOOL_X,0,0)))
    for y in [-49,49]:
        s=s.union(box(12,17,4,(TOOL_X,y-math.copysign(4,y),-59)))
        s=s.union(old.rb(14,10,36,2,(TOOL_X,y,-42)))
        s=s.union(box(10,36,4,(TOOL_X,math.copysign(32,y),-24.25)))
    s=s.union(box(24,23,8,(TOOL_X-7,-32,-30)))
    # G1 output points down; mount and clamps are above the scroll cam.
    g=grip_motor_pose()
    s=s.union(transform(old.mount_plate(True),g))
    s=s.union(box(39,8,8,(16,10,-32)))
    s=s.union(box(8,14,17,(TOOL_X,17,-33)))
    s=s.cut(transform(old.servo_case(True),g))
    s=v4.clear_receiver(s,v4.WRIST_HORN,True)
    s=s.cut(transform(micro.build()[0],v4.WRIST_HORN))
    s=s.cut(cq.Workplane('XY').circle(38.4).extrude(6.2).translate((TOOL_X,0,-54)))
    s=old.hole_y(s,0,0,6.4)
    for px,py in old.clamp_points(True):
        hole=cq.Workplane('XY').center(px,py).circle(1.7).extrude(160,both=True)
        s=s.cut(transform(hole,g))
    for sx in [-1,1]:
        px=-.2*old.MICRO[0]+sx*(old.MICRO[0]/2+4)
        s=s.cut(transform(old.clamp_bar(True).translate((px,0,-13.6)),g))
    return s.clean()


def grip_motor_pose():
    return v4.ry(180,(TOOL_X,0,-42.25))


def transform_matrix_x180(at):
    t=np.diag([1.,-1.,-1.,1.]);t[:3,3]=at;return t


def cam_radius(q):return 26.-.28*q


@lru_cache(None)
def cam():
    # Local +Z is downward in assembly. Capture user's asymmetric original horn.
    s=cq.Workplane('XY').circle(38).extrude(5)
    s=s.cut(micro.prism(micro.profile().buffer(.25),3.7,1.4))
    s=s.cut(old.rb(28.4,42.4,1.4,3,(0,0,4.3)))
    s=bore_z(s,0,0,8)
    # Archimedean grooves give 14mm radial travel over 50deg servo rotation.
    for a in [0,120,240]:
        pts=[]
        for t in np.linspace(-28,28,57):
            r=26.-.28*t;theta=math.radians(a+t)
            pts.append((r*math.cos(theta),r*math.sin(theta)))
        from shapely.geometry import LineString
        groove=LineString(pts).buffer(1.9,resolution=8)
        s=s.cut(micro.prism(groove,8,-1))
    for x in [-10,10]:s=bore_z(s,x,0,2.3)
    return s.clean()


@lru_cache(None)
def cam_cap():
    s=old.rb(28,42,1.2,3,(0,0,.6))
    s=bore_z(s,0,0,10)
    for x in [-10,10]:s=bore_z(s,x,0,2.3)
    # The recessed retainer must leave every follower groove open too.
    return s.intersect(cam()).clean()


@lru_cache(None)
def finger():
    # Identical radial sliding jaw; layer plane follows finger length.
    s=old.rb(14,12,3.6,2,(0,0,-55))
    s=s.union(old.rb(6,7.6,53,1.5,(5,0,-82)))
    s=s.union(old.rb(12,7.6,17,2,(2,0,-106)))
    s=bore_z(s,0,0,3.3)
    # Keep the follower washer and locknut clear of the tall finger stem.
    s=s.cut(cq.Workplane('XY').circle(2.7).extrude(7).translate((0,0,-63.8)))
    # Tie-through pad attachment; avoid adhesives in the main load path.
    for z in [-102,-109]:
        s=s.cut(cq.Workplane('YZ').center(0,z).circle(1.2).extrude(20,both=True))
    return s.clean()


@lru_cache(None)
def pad():
    # TPU or cut silicone alternative, never rigid PLA on the fruit surface.
    s=old.rb(4,12,19,1.5,(-6,0,-106))
    for z in [-102,-109]:
        s=s.cut(cq.Workplane('YZ').center(0,z).circle(1.2).extrude(20,both=True))
    return s


PARTS={
 'A5-01-BASE':(v4.base,1,'structural'),
 'A5-02-YAW-DECK':(v4.shoulder_deck,1,'structural'),
 'A5-03-THRUST-WASHER':(old.thrust_washer,1,'wear'),
 'A5-04-TOWER-R':(lambda:tower(1),1,'structural'),
 'A5-05-TOWER-L':(lambda:tower(-1),1,'structural'),
 'A5-06-UPPER-TOP':(lambda:shell(False,True),1,'shell'),
 'A5-07-UPPER-BOTTOM':(lambda:shell(False,False),1,'shell'),
 'A5-08-FORE-TOP':(lambda:shell(True,True),1,'shell'),
 'A5-09-FORE-BOTTOM':(lambda:shell(True,False),1,'shell'),
 'A5-10-PALM-GUIDE':(palm,1,'structural'),
 'A5-11-SCROLL-CAM':(cam,1,'precision'),
 'A5-12-CAM-CAP':(cam_cap,1,'precision'),
 'A5-13-FINGER':(finger,3,'finger'),
 'A5-14-PAD':(pad,3,'TPU'),
 'A5-15-MG996-CLAMP':(lambda:old.clamp_bar(False),8,'small'),
 'A5-16-MG90-CLAMP':(lambda:old.clamp_bar(True),4,'small'),
 'S02-BODY':(lambda:v4.large.build()[0],4,'reuse_or_fit'),
 'S02-CAP':(lambda:v4.large.build()[1],8,'reuse_or_fit'),
 'S03B-BODY':(lambda:micro.build()[0],1,'fit_first'),
 'S03B-CAP':(lambda:micro.build()[1],2,'fit_first'),
}


@lru_cache(None)
def local_items():
    out=[]
    def add(name,s,frame,pid='',group='printed',color=BLUE):
        out.append(Item(name,s,frame,pid,group,color))
    def part(pid,frame,at=(0,0,0)):
        add(pid,PARTS[pid][0]().translate(at),frame,pid)
    # All load-bearing assembly pins are replaced by metal hardware in the BOM.
    def motor(name,ismicro,t,frame):
        add(name+' case',transform(old.servo_case(ismicro),t),frame,group='servo',color=DARK)
        x,y,_=old.MICRO if ismicro else old.MG
        pid='A5-16-MG90-CLAMP' if ismicro else 'A5-15-MG996-CLAMP'
        for side in [-1,1]:
            px=-.2*x+side*(x/2+4)
            add(name+f' clamp {side}',transform(old.clamp_bar(ismicro).translate((px,0,-13.6)),t),frame,pid,color=LIGHT)
    def coupling(name,ismicro,t,frame):
        mod=micro if ismicro else v4.large
        b,c=mod.build()
        add(name+' adapter',transform(b,t),frame,'S03B-BODY' if ismicro else 'S02-BODY',group='reused',color=LIGHT)
        for k,lid in enumerate(mod.caps_pose(c)):
            add(name+f' lid {k}',transform(lid,t),frame,'S03B-CAP' if ismicro else 'S02-CAP',group='reused',color=LIGHT)
        add(name+' horn',transform(mod.horn_envelope(),t),frame,group='horn',color=DARK)
    part('A5-01-BASE','base');part('A5-03-THRUST-WASHER','base',(0,0,73.7))
    part('A5-02-YAW-DECK','yaw')
    motor('J1',False,v4.motor_pose(at=(0,0,58),vertical=True),'base')
    coupling('J1',False,v4.YAW_HORN,'yaw')
    for side in [-1,1]:
        part('A5-04-TOWER-R' if side==1 else 'A5-05-TOWER-L','yaw')
        motor('J2 '+str(side),False,v4.motor_pose(False,side,(0,side*23,124)),'yaw')
        coupling('J2 '+str(side),False,v4.horn_pose(side=side),'upper')
    for pid in ['A5-06-UPPER-TOP','A5-07-UPPER-BOTTOM']:part(pid,'upper')
    motor('J3',False,v4.motor_pose(False,1,(UPPER,23,0)),'upper')
    coupling('J3',False,v4.horn_pose(),'fore')
    for pid in ['A5-08-FORE-TOP','A5-09-FORE-BOTTOM']:part(pid,'fore')
    for fore in [False,True]:
        frame='fore' if fore else 'upper'
        for k,(x,y) in enumerate(screw_stations(fore)):
            sleeve=cq.Workplane('XY').center(x,y).circle(3).circle(2).extrude(30).translate((0,0,-15))
            add(f'{frame} compression sleeve {k}',sleeve,frame,group='metal',color=METAL)
            shaft=cq.Workplane('XY').center(x,y).circle(1.5).extrude(40).translate((0,0,-24.5))
            head=cq.Workplane('XY').center(x,y).circle(2.8).extrude(3).translate((0,0,15.5))
            add(f'{frame} M3x40 bolt {k}',shaft.union(head),frame,group='metal',color=METAL)
            for z in [-15.5,15]:
                washer=cq.Workplane('XY').center(x,y).circle(3.5).circle(1.6).extrude(.5).translate((0,0,z))
                add(f'{frame} washer {k} {z}',washer,frame,group='metal',color=METAL)
            nut=cq.Workplane('XY').center(x,y).polygon(6,6.35).circle(1.5).extrude(4).translate((0,0,-19.5))
            add(f'{frame} M3 nut {k}',nut,frame,group='metal',color=METAL)
    motor('W1',True,v4.motor_pose(True,1,(FORE,15.75,0)),'fore')
    coupling('W1',True,v4.WRIST_HORN,'tool')
    part('A5-10-PALM-GUIDE','tool')
    motor('G1',True,grip_motor_pose(),'tool')
    tc=transform_matrix_x180((0,0,-48))
    add('G1 cam',transform(cam(),tc),'cam','A5-11-SCROLL-CAM',color=ORANGE)
    add('G1 cam cap',transform(cam_cap().translate((0,0,3.8)),tc),'cam','A5-12-CAM-CAP',color=LIGHT)
    add('G1 original horn',transform(micro.horn_envelope(),tc),'cam',group='horn',color=DARK)
    # Retainer screw envelopes include heads and nuts, not just clearance holes.
    for x in [-10,10]:
        shaft=cq.Workplane('XY').center(x,0).circle(1).extrude(10).translate((0,0,-4.5))
        head=cq.Workplane('XY').center(x,0).circle(1.9).extrude(2).translate((0,0,5.5))
        nut=cq.Workplane('XY').center(x,0).polygon(6,4.62).circle(1).extrude(2.5).translate((0,0,-3))
        for label,s in [('screw',shaft.union(head)),('nut',nut)]:
            add(f'cam retainer {x} {label}',transform(s,tc),'cam',group='metal',color=METAL)
        for z in [-.5,5]:
            washer=cq.Workplane('XY').center(x,0).circle(2.5).circle(1.05).extrude(.5).translate((0,0,z))
            add(f'cam retainer {x} washer {z}',transform(washer,tc),'cam',group='metal',color=METAL)
    for k in range(3):
        part('A5-13-FINGER',f'finger{k}')
        add(f'pad {k}',pad(),f'finger{k}','A5-14-PAD','soft',(.40,.45,.42))
        follower=cq.Workplane('XY').circle(1.5).circle(1.05).extrude(9.2).translate((0,0,-57))
        add(f'cam follower sleeve {k}',follower,f'finger{k}',group='metal',color=METAL)
        shaft=cq.Workplane('XY').circle(1).extrude(16).translate((0,0,-47.3-16))
        head=cq.Workplane('XY').circle(1.9).extrude(2).translate((0,0,-47.3))
        nut=cq.Workplane('XY').polygon(6,4.62).circle(1).extrude(2.5).translate((0,0,-60))
        add(f'cam follower M2 screw {k}',shaft.union(head),f'finger{k}',group='metal',color=METAL)
        add(f'cam follower M2 nut {k}',nut,f'finger{k}',group='metal',color=METAL)
        for z in [-57.5,-47.8]:
            washer=cq.Workplane('XY').circle(2.5).circle(1.05).extrude(.5).translate((0,0,z))
            add(f'cam follower washer {k} {z}',washer,f'finger{k}',group='metal',color=METAL)
    return out


def frames(q=(0,-35,75,-40,0)):
    yaw,shoulder,elbow,wrist,grip=q
    f={'base':np.eye(4),'yaw':v4.rz(yaw)}
    f['upper']=f['yaw']@v4.ry(shoulder,(0,0,SHOULDER_Z))
    f['fore']=f['upper']@v4.ry(elbow,(UPPER,0,0))
    f['tool']=f['fore']@v4.ry(wrist,(FORE,0,0))
    origin=np.eye(4);origin[0,3]=TOOL_X
    f['cam']=f['tool']@origin@v4.rz(grip)
    for k in range(3):
        shift=np.eye(4);shift[0,3]=cam_radius(grip)
        f[f'finger{k}']=f['tool']@origin@v4.rz(k*120)@shift
    return f


def assembly(q=(0,-35,75,-40,0),rover=False):
    fs=frames(q);out=[]
    for i in local_items():
        s=transform(i.shape,fs[i.frame])
        if rover:s=s.translate(tuple(ROVER_BASE))
        out.append(Item(i.name,s,i.frame,i.part_id,i.group,i.color))
    return out


def solve(target):
    sh=ROVER_BASE+np.array([0,0,SHOULDER_Z])
    dx,dy=target[0]-sh[0],target[1]-sh[1]
    r=math.hypot(dx,dy)-TOOL_X;down=sh[2]-target[2]-TOOL
    c=(r*r+down*down-UPPER**2-FORE**2)/(2*UPPER*FORE)
    if abs(c)>1:raise ValueError('Target outside arm reach')
    e=math.acos(c);u=math.atan2(down,r)-math.atan2(FORE*math.sin(e),UPPER+FORE*math.cos(e))
    return (math.degrees(math.atan2(dy,dx)),math.degrees(u),math.degrees(e),-math.degrees(u+e),0.)


def print_pose(pid,s):
    # Outer shells face down, open interiors face up; no enclosed support cavity.
    if pid in ['A5-06-UPPER-TOP','A5-08-FORE-TOP']:
        s=s.rotate((0,0,0),(1,0,0),180)
    elif pid in ['A5-04-TOWER-R','A5-05-TOWER-L','A5-13-FINGER','A5-14-PAD']:
        s=s.rotate((0,0,0),(1,0,0),90)
    elif pid=='A5-02-YAW-DECK':s=s.rotate((0,0,0),(0,1,0),90)
    b=s.val().BoundingBox()
    return s.translate((-b.xmin,-b.ymin,-b.zmin))


if __name__=='__main__':
    for pid,(fn,qty,kind) in PARTS.items():
        s=fn();b=print_pose(pid,s).val().BoundingBox()
        print(pid,'solids',len(s.solids().vals()),'valid',s.val().isValid(),
              'mm',tuple(round(x,1) for x in [b.xlen,b.ylen,b.zlen]),flush=True)
