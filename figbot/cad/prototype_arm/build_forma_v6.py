"""Independent FIGBOT FORMA V6 geometry. No V3/V4/V5 mount imports.

Study/fit prototype: nominal interfaces are NOT measured user hardware.
PB02 45 mm pitch-radius / 24 x 8 mm rolling-element concept is retained.
All new fixed plastic screw joints use heat-set inserts, not printed pins.
"""
from dataclasses import dataclass
from functools import lru_cache
import math
import cadquery as cq
import numpy as np
from cad.utils import ROOT
from cad.prototype_arm import forma_v6_horns as original_horns

OUT=ROOT/'cad/prototype_arm/forma_v6'
UPPER=180.; FORE=140.; SHOULDER_Z=100.
BASE_WORLD=np.array([550.,415.,66.])
PALM_X=38.
FRUIT=np.array([PALM_X,0.,-66.])
BALL_R=4.; RACE_R=45.; BALL_Z=49.8
RETAINER_AXIAL_CLEARANCE=1.0  # DEC-071: physical fit and uplift retention require testing.
REVISION='R6 / DEC-075'
RETAINER_TOP=66.5
WHITE=(.83,.86,.82); TEAL=(.09,.39,.40); GOLD=(.76,.53,.18)
BLACK=(.13,.16,.17); SILVER=(.60,.64,.65); SOFT=(.79,.42,.25)

# Explicit design candidates. Matching the physical ear/horn patterns is open.
# Do not relabel these as measured values: see INTERFACES.json / ASSUMPTIONS.md.
MG={'length':40.7,'width':19.7,'height':42.9,'offset':-10.15,
    'ear_pitch':49.5,'ear_cross':10.,'ear_z':-12.,'insert_d':4.2,'insert_depth':5.}
# DEC-072: only this J1 specimen was measured. Remaining interfaces are candidates.
YAW_MEASUREMENTS={'case_length_mm':39.9,'near_case_face_to_spline_edge_mm':7.3,
                  'spline_outer_diameter_mm':5.7}
YAW_MG={**MG,'length':39.9,'offset':-9.8,'shaft_d':5.7}
# DEC-073: measured body is not an instruction to shrink the known mounting opening.
# Retain the complete pre-DEC-072 aperture in shaft coordinates. Cable boot/plug
# dimensions and insertion path are UNVERIFIED; this is only a body clearance.
YAW_MOUNT={'opening_length':41.5,'opening_width':20.5,'opening_x':-10.15}
MICRO={'length':22.8,'width':12.2,'height':28.5,'offset':-4.8,
       'ear_pitch':28.,'ear_cross':0.,'ear_z':-10.,'insert_d':2.9,'insert_depth':4.}

@dataclass
class Item:
    name:str
    shape:cq.Workplane
    frame:str='base'
    part_id:str=''
    color:tuple=WHITE
    mass_g:float|None=None

def box(x,y,z,c=(0,0,0)):
    return cq.Workplane('XY').box(x,y,z).translate(c)

def rounded(x,y,z,r,c=(0,0,0)):
    r=min(r,min(x,y)/2-.05)
    return cq.Workplane('XY').rect(x,y).extrude(z).edges('|Z').fillet(r).translate((c[0],c[1],c[2]-z/2))

def ring(ri,ro,z,h):
    return cq.Workplane('XY').circle(ro).circle(ri).extrude(h).translate((0,0,z))

def cz(r,z,h,x=0,y=0):
    return cq.Workplane('XY').center(x,y).circle(r).extrude(h).translate((0,0,z))

def cy(r,y,h,x=0,z=0):
    return cz(r,0,h).rotate((0,0,0),(1,0,0),-90).translate((x,y,z))

def screw_hole(s,x,y,d=3.3,z=-100,h=200):
    return s.cut(cz(d/2,z,h,x,y))

def insert_hole(s,x,y,top,d=4.2,depth=5.):
    # Blind pocket with >=1.2 mm bottom in its designed boss.
    return s.cut(cz(d/2,top-depth,depth+.05,x,y))

def ear_points(micro=False,spec=None):
    p=spec if spec is not None else (MICRO if micro else MG)
    ys=[0.] if micro else [-p['ear_cross']/2,p['ear_cross']/2]
    return [(p['offset']+side*p['ear_pitch']/2,y) for side in [-1,1] for y in ys]

def body_opening(p):
    if p is YAW_MG:return YAW_MOUNT['opening_length'],YAW_MOUNT['opening_width'],YAW_MOUNT['opening_x']
    return p['length']+.8,p['width']+.8,p['offset']

def mount_region(micro=False,spec=None):
    """Integrated flange seat, with direct insert holes underneath servo ears."""
    p=spec if spec is not None else (MICRO if micro else MG)
    # Keep known J1 envelope; reinforce other seats OUTSIDE the body aperture.
    reinforced=p is not YAW_MG
    top=p['ear_z']; h=p['insert_depth']+(3. if reinforced else 1.5)
    s=rounded(p['ear_pitch']+10,p['width']+(12 if reinforced else 8),h,2,(p['offset'],0,top-h/2))
    length,width,x=body_opening(p)
    s=s.cut(box(length,width,80,(x,0,-15)))
    for x,y in ear_points(micro,spec=p):s=insert_hole(s,x,y,top,p['insert_d'],p['insert_depth'])
    return s

def servo(micro=False,spec=None):
    p=spec if spec is not None else (MICRO if micro else MG)
    s=rounded(p['length'],p['width'],p['height'],1,(p['offset'],0,-p['height']/2))
    ear=rounded(p['ear_pitch']+6,p['width'],2.2,.7,(p['offset'],0,p['ear_z']+1.1))
    for x,y in ear_points(micro,spec=p):ear=screw_hole(ear,x,y,2.2 if micro else 3.3)
    return s.union(ear).union(cz(p.get('shaft_d',5 if micro else 6)/2,0,5))

def horn(micro=False):return original_horns.horn(micro)
def horn_points(micro=False):return original_horns.points(micro)

def side_place(s,side=1,origin=(0,0,0)):
    return s.rotate((0,0,0),(1,0,0),90*side).translate(origin)

def clear_mount(s,micro=False,side=0,origin=(0,0,0),spec=None):
    p=spec if spec is not None else (MICRO if micro else MG)
    place=lambda q:side_place(q,side,origin) if side else q.translate(origin)
    length,width,x=body_opening(p)
    s=s.cut(place(box(length,width,p['height']+1,(x,0,-p['height']/2))))
    for x,y in ear_points(micro,spec=p):
        s=s.cut(place(cz(p['insert_d']/2,p['ear_z']-p['insert_depth'],p['insert_depth']+.05,x,y)))
    # Clear the entire flange, including its screw holes. Subtracting a drilled
    # servo alone leaves isolated plastic plugs inside those holes after web union.
    flange=rounded(p['ear_pitch']+6,p['width'],2.2,.7,(p['offset'],0,p['ear_z']+1.1))
    return s.cut(place(servo(micro,spec=p).union(flange)))

def horn_receiver(micro=False):
    return original_horns.receiver(micro)

def clear_horn_face(s,micro=False,side=0,origin=(0,0,0)):
    """Reopen functional voids AFTER ribs/bridges have been united to a face."""
    place=lambda q:side_place(q,side,origin) if side else q.translate(origin)
    s=s.cut(place(cz(3.5,5.4,20)))
    z=original_horns.cover_top(micro)
    for x,y in horn_points(micro):s=s.cut(place(cz(1.45,z-.05,4.4,x,y)))
    s=s.cut(place(original_horns.pocket_tool(micro)))
    # Keep added webs out of the removable closure and its external screw heads.
    s=s.cut(place(original_horns.closure(micro)))
    for name,shape in original_horns.fastener_heads(micro):s=s.cut(place(shape))
    return s

def passive_receiver(face=-16.5):
    s=cy(12,face,6.5)
    return s.cut(cy(2.1,face-.05,4.55))

@lru_cache(None)
def base():
    s=rounded(120,120,4,14,(0,0,2))
    s=s.union(mount_region(spec=YAW_MG).translate((0,0,50)))
    for x in [YAW_MG['offset']-YAW_MG['ear_pitch']/2,YAW_MG['offset']+YAW_MG['ear_pitch']/2]:
        # The servo body sits between these integral supports, not in a clamp.
        s=s.union(rounded(9,29,28,2,(x,0,18)))
    outer=ring(51,55,4,42)
    for a in range(0,360,60):
        cut=rounded(24,16,25,5,(0,54,21)).rotate((0,0,0),(0,0,1),a)
        outer=outer.cut(cut)
    race=ring(38,55,43,5).cut(cq.Workplane(obj=cq.Solid.makeTorus(45,4.2,(0,0,50))))
    s=s.union(outer).union(race)
    for a in range(0,360,90):
        t=math.radians(a+45);x,y=65*math.cos(t),65*math.sin(t)
        s=s.union(cz(6,4,47,x,y));s=insert_hole(s,x,y,51)
        # Fixed diagonal buttresses join the retainer posts to the bearing wall.
        rib=rounded(18,8,32,3,(58,0,20)).rotate((0,0,0),(0,0,1),a+45)
        s=s.union(rib)
    for x in [-50,50]:
        for y in [-50,50]:s=screw_hole(s,x,y,4.4)
    # The flange clears in its final position but used to clip the inner race
    # edge during insertion. Relieve only the bore above the fixed ear seats;
    # do not touch the ball groove (minimum radius40.8mm) or the blind inserts.
    s=s.cut(rounded(YAW_MG['ear_pitch']+7,YAW_MG['width']+1,16,.7,(YAW_MG['offset'],0,50)))
    return clear_mount(s,False,0,(0,0,50),spec=YAW_MG)

@lru_cache(None)
def rotor():
    s=ring(38,51,52,8).cut(cq.Workplane(obj=cq.Solid.makeTorus(45,4.2,(0,0,49.6))))
    s=s.union(cz(46,57.5,4.5)).union(ring(50,55,57.5,2.5))
    # Lightened web leaving continuous race and central horn interface.
    for a in range(0,360,60):
        t=math.radians(a);s=s.cut(cz(7,57,6,30*math.cos(t),30*math.sin(t)))
    s=screw_hole(s,0,0,7)
    s=s.union(horn_receiver().translate((0,0,50)))
    for side in [-1,1]:
        # Whole ear seat and pillar belong to the turntable, no separate brackets.
        s=s.union(side_place(mount_region(),side,(0,side*24,SHOULDER_Z)))
        for x in [MG['offset']-MG['ear_pitch']/2,MG['offset']+MG['ear_pitch']/2]:
            # Continuous widening toward the rotor, no abrupt collar at midheight.
            s=s.union(tapered_post(x,side))
            profile=[(side*27,60),(side*43,60),(side*43,82),(side*35,82)]
            rib=cq.Workplane('YZ').polyline(profile).close().extrude(6,both=True).translate((x,0,0))
            s=s.union(rib)
        s=s.union(rounded(65,9,9,3,(MG['offset'],side*39,64)))
    # Trim lower pillar corners to clear fixed retainer during full yaw rotation.
    # Wider R5 posts would otherwise leave corner ledges toR59.9 beneath the
    # fixed R58 land. Keep those ledges insideR57.6; functional R55flange stays.
    s=s.cut(ring(57.6,90,57.5,2.9))
    s=s.cut(ring(52.6,90,60.4,RETAINER_TOP+.6-60.4))
    for side in [-1,1]:s=clear_mount(s,False,side,(0,side*24,SHOULDER_Z))
    return clear_horn_face(s,False,0,(0,0,50))

@lru_cache(None)
def retainer():
    # The screw positions remain diagonalR65; cardinal edges no longer overhang.
    s=ring(53,70,60.5,RETAINER_TOP-60.5)
    s=s.intersect(rounded(120,120,80,14,(0,0,40)))
    # Flange top Z60; pillar corner ledges persist to Z60.4 below the notch.
    # Relieve to Z61.4 for 1 mm over those corners and 1.4 mm over the flange.
    # Preserve outer screw-bearing land, roof top and all rotor geometry.
    # R58 leaves a real land at the120mm cardinal sides; R60 is tangent there.
    s=s.cut(cz(58,60.49,60.4+RETAINER_AXIAL_CLEARANCE-60.49))
    for a in range(0,360,90):
        t=math.radians(a+45);x,y=65*math.cos(t),65*math.sin(t)
        s=s.union(cz(5,51,RETAINER_TOP-51,x,y));s=screw_hole(s,x,y,3.3)
    return s

def retainer_half(side):
    left=retainer().intersect(box(100,180,100,(-50.2,0,50)))
    return left if side==-1 else left.rotate((0,0,0),(0,0,1),180)

@lru_cache(None)
def cage():
    s=ring(40.3,49.7,48.4,2.8)
    for a in range(24):
        t=math.tau*a/24;s=screw_hole(s,45*math.cos(t),45*math.sin(t),8.35)
    return s

def beam_skin(length,width,height,wall,start=0):
    # Constant oval shell: smooth exterior, hollow inside, no decorative heavy cover.
    out=cq.Workplane('YZ').ellipse(width/2,height/2).extrude(length).translate((start,0,0))
    inside=cq.Workplane('YZ').ellipse(width/2-wall,height/2-wall).extrude(length+2).translate((start-1,0,0))
    return out.cut(inside)


def capsule_loft(sections):
    """Smooth rounded YZ sections: (x, y, z, width, height)."""
    w=cq.Workplane('YZ');last=0
    for x,y,z,width,height in sections:
        r=width/2;straight=height/2-r
        w=w.workplane(offset=x-last).center(y,z).moveTo(-r,-straight).lineTo(-r,straight)
        w=w.threePointArc((0,height/2),(r,straight)).lineTo(r,-straight)
        w=w.threePointArc((0,-height/2),(-r,-straight)).close().center(-y,-z)
        last=x
    return w.loft(ruled=False)


def tapered_post(x,side):
    w=cq.Workplane('XY');last=0
    for z,wx,wy in [(60,16,13),(67,16,13),(77,14,11),(90,12,9),(101,12,9)]:
        w=w.workplane(offset=z-last).center(x,side*39).rect(wx,wy).center(-x,-side*39)
        last=z
    return w.loft(ruled=True)

def bridge_profile(span,micro=False):
    """A continuous thin-wall beam with integral motor-ear end and output fork."""
    main_start=18.; main_end=span-(26 if micro else 41)
    width=26. if micro else 33.;height=26. if micro else 32.;wall=1.8 if micro else 2.
    s=beam_skin(main_end-main_start,width,height,wall,main_start)
    # Accessible longitudinal opening; insertion and cable service do not need covers.
    window=rounded(main_end-main_start-18,width-9,20,4,((main_start+main_end)/2,0,height/2+5))
    s=s.cut(window)
    for side in [-1,1]:
        if micro and side==-1:s=s.union(passive_receiver())
        else:s=s.union(side_place(horn_receiver(),side,(0,side*24,0)))
        # Gradually blend the 28mm-deep receiver web into the hollow shell.
        end_y=side*(width/2-wall/2-.25)
        sections=[]
        for x,t in [(2,0),(24,0),(36,.15),(48,.4),(60,.7),(72,.95),(80,1)]:
            u=t*t*(3-2*t)
            sections.append((x,side*13.5*(1-u)+end_y*u,-2,6*(1-u)+.8*u,28*(1-u)+3*u))
        s=s.union(capsule_loft(sections))
    seat_origin=(span,20 if micro else 24,0)
    s=s.union(side_place(mount_region(micro),1,seat_origin))
    p=MICRO if micro else MG
    end_x0=span+p['offset']-p['ear_pitch']/2
    yseat=(20 if micro else 24)-p['ear_z']+3
    # End webs stay behind the rotating horn plane; forward motion clearance audited.
    for side in [-1,1]:
        yend=yseat if side==1 else -26
        z=-10 if micro else -12
        xstart=main_end-44; xend=end_x0+6
        sections=[]
        for t in [0,.125,.25,.5,.75,.875,1]:
            smooth=t*t*(3-2*t)
            sections.append((xstart+(xend-xstart)*t,
                side*(width/2-wall/2-.25)*(1-smooth)+yend*smooth,
                -2*(1-smooth)+z*smooth,.8+5.2*smooth,3+13*smooth))
        sections.append((span+12,yend,z,6,16))
        s=s.union(capsule_loft(sections))
    # Passive side shaft runs on a replaceable bushing, with M3 insert retention.
    boss=cy(9,-28,7,span,0).cut(cy(3.1,-29,9,span,0))
    s=s.union(boss)
    s=clear_mount(s,micro,1,seat_origin).cut(cy(3.1,-29,9,span,0))
    for side in [-1,1]:
        if not (micro and side==-1):s=clear_horn_face(s,False,side,(0,side*24,0))
    return s

@lru_cache(None)
def upper():return bridge_profile(UPPER)

@lru_cache(None)
def fore():return bridge_profile(FORE,True)

@lru_cache(None)
def palm():
    # Small open triangular palm with 3 identical finger pivots; tendon actuation.
    s=cz(25,-3,3,PALM_X).cut(cz(9,-4,5,PALM_X))
    grip_origin=(PALM_X,0,31)
    s=s.union(mount_region(True).translate(grip_origin))
    for x,y in ear_points(True):
        s=s.union(rounded(6,10,19,1,(PALM_X+x,y,7)))
    for side in [-1,1]:
        if side==-1:s=s.union(passive_receiver(-12.5))
        else:s=s.union(side_place(horn_receiver(True),side,(0,side*20,0)))
        s=s.union(rounded(PALM_X+4,4,12,2,(PALM_X/2,side*10,-5)))
    for a in [0,120,240]:
        ear=rounded(9,16,10,2,(23,0,-5))
        ear=ear.cut(box(12,4.8,12,(23,0,-5)))
        ear=ear.cut(cy(1.1,-8,16,23,-5))
        # M2 insert only in one ear; a 3 mm smooth sleeve is the bearing surface.
        ear=ear.cut(cy(1.45,2.4,4,23,-5))
        ear=ear.cut(cz(.75,-11,12,26,5.2))
        guide=rounded(4,4,35,1,(24,-6,16.5)).union(cz(3,33,3,24,-6))
        guide=guide.cut(cz(.85,32,5,24,-6))
        ear=ear.union(guide)
        s=s.union(ear.rotate((0,0,0),(0,0,1),a).translate((PALM_X,0,0)))
    for a in [0,120,240]:
        slot=box(21,4.8,16,(22.5,0,-5)).rotate((0,0,0),(0,0,1),a).translate((PALM_X,0,0))
        s=s.cut(slot)
    return clear_horn_face(clear_mount(s,True,0,grip_origin),True,1,(0,20,0))

def cord_segment(p,q,r=.45):
    p=np.array(p);q=np.array(q);v=q-p
    return cq.Workplane(obj=cq.Solid.makeCylinder(r,float(np.linalg.norm(v)),cq.Vector(*p),cq.Vector(*v)))

@lru_cache(None)
def finger():
    # Side-profile, printed flat. Neutral near-closed pad radius 20 mm.
    profile=[(-5,1),(5,1),(6,-15),(4,-33),(-1,-51),(-7,-53),(-10,-48),(-3,-30),(-2,-12)]
    s=cq.Workplane('XZ').polyline(profile).close().extrude(2,both=True)
    s=s.union(cy(5,-2,4)).cut(cy(1.6,-3,6))
    # Inner tendon arm and two cord holes, not screw bearing bores.
    s=s.union(box(8,4,5,(-6,0,-3))).cut(cy(.8,-3,6,-8,-3))
    s=s.cut(cy(.8,-3,6,3,-10))
    s=s.cut(cy(1.45,-2.05,3.7,-5,-46))
    return s

@lru_cache(None)
def spool():
    # Keep tiny factory horn holes intact. Keyed backing + rim washers lie
    # BELOW all three cord lanes, never in a winding path.
    s=horn_receiver(True).translate((0,0,-7.5))
    s=s.union(cz(11.5,5.5,1.2)).union(cz(9.5,6.7,7.6)).union(cz(11.5,14.3,1.2))
    for z in [9.1,11.7]:s=s.union(cz(11.5,z,.5))
    s=screw_hole(s,0,0,7)
    for a in [30,150,270]:
        t=math.radians(a);s=screw_hole(s,10.4*math.cos(t),10.4*math.sin(t),1.2,z=5.5,h=11)
    return s

@lru_cache(None)
def pad():
    s=rounded(11,6,14,3,(-5,-5,-45))
    return s.cut(cy(1.1,-9,10,-5,-46))

@lru_cache(None)
def bushing(length=11.5):return cy(3,-28,length).cut(cy(1.65,-29,length+2))

@lru_cache(None)
def fit_coupon():
    s=mount_region().translate((10.15,0,18.5))
    # Integrated labelled dimension sample; ear spacing is provisional49.5 x10.
    return s

@lru_cache(None)
def yaw_fit_coupon():
    # Separate specimen coupon; preserve other motors' unmeasured nominal coupon.
    return mount_region(spec=YAW_MG).translate((-YAW_MG['offset'],0,18.5))

@lru_cache(None)
def micro_fit_coupon():
    return mount_region(True).translate((4.8,0,15.5))

@lru_cache(None)
def insert_coupon():
    # Six trial pilots; row centres 10/25 mm, left to right increasing size.
    s=rounded(50,35,7,3,(25,17.5,3.5))
    for y,ds,depth in [(10,[4.0,4.2,4.4],5),(25,[2.8,2.9,3.0],4)]:
        for x,d in zip([10,25,40],ds):s=insert_hole(s,x,y,7,d,depth)
    # One corner notch identifies the M3 row without ambiguous text scale.
    return s.cut(box(3,3,10,(0,0,4)))

@lru_cache(None)
def vehicle_plate():
    # Proposed receiver on rover, NOT a servo mounting adapter. Four M4 inserts.
    s=rounded(132,142,10,7,(0,0,-5))
    for x in [-50,50]:
        for y in [-50,50]:s=insert_hole(s,x,y,0,5.6,6)
    return s

PARTS={
 'F6-01-BASE':(base,1,'base'),'F6-02-ROTOR':(rotor,1,'yaw'),
 'F6-03A-RETAINER':(lambda:retainer_half(-1),1,'base'),
 'F6-03B-RETAINER':(lambda:retainer_half(1),1,'base'),'F6-04-CAGE':(cage,1,'base'),
 'F6-05-UPPER':(upper,1,'upper'),'F6-06-FORE':(fore,1,'fore'),
 'F6-07-PALM':(palm,1,'tool'),'F6-08-FINGER':(finger,3,'finger'),
 'F6-09-SPOOL':(spool,1,'tool'),'F6-10-SOFT-PAD':(pad,3,'finger'),
 'F6-12-EAR-FIT':(fit_coupon,1,'fit'),
 'F6-13-BALL-8MM':(lambda:cq.Workplane('XY').sphere(4),24,'base'),
 'F6-14-MICRO-FIT':(micro_fit_coupon,1,'fit'),
 'F6-15-INSERT-FIT':(insert_coupon,1,'fit'),
 'F6-16-ROVER-PLATE':(vehicle_plate,1,'integration'),
 'F6-17-YAW-FIT':(yaw_fit_coupon,1,'fit'),
 'F6-18-LARGE-HORN-FIT':(lambda:horn_receiver(False),1,'fit'),
 'F6-19-MICRO-HORN-FIT':(lambda:horn_receiver(True),1,'fit'),
 'F6-20-LARGE-SOCKET-COVER':(lambda:original_horns.closure(False),4,'closure'),
 'F6-21-MICRO-SOCKET-COVER':(lambda:original_horns.closure(True),2,'closure'),
}

def rz(d):
    t=math.radians(d);c,s=math.cos(t),math.sin(t)
    return np.array([[c,-s,0],[s,c,0],[0,0,1.]])
def ry(d):
    t=math.radians(d);c,s=math.cos(t),math.sin(t)
    return np.array([[c,0,s],[0,1.,0],[-s,0,c]])
def matrix(r=np.eye(3),p=(0,0,0)):
    t=np.eye(4);t[:3,:3]=r;t[:3,3]=p;return t
def move(s,t):
    from OCP.gp import gp_Trsf
    g=gp_Trsf();g.SetValues(*[float(x) for x in t[:3].ravel()])
    return cq.Workplane(obj=s.val().moved(cq.Location(g)))
def frames(q=(0,-35,85,-50),rover=False):
    base=matrix(p=BASE_WORLD if rover else (0,0,0))
    yaw=base@matrix(rz(q[0]));upper=yaw@matrix(ry(q[1]),(0,0,SHOULDER_Z))
    fore=upper@matrix(ry(q[2]),(UPPER,0,0));tool=fore@matrix(ry(q[3]),(FORE,0,0))
    return dict(base=base,yaw=yaw,upper=upper,fore=fore,tool=tool)

@lru_cache(None)
def local_items():
    out=[]
    for pid in list(PARTS)[:8]:
        fn,n,frame=PARTS[pid];out.append(Item(pid,fn(),frame,pid,TEAL if frame=='base' else WHITE))
    out.append(Item('F6-09-SPOOL',spool().translate((PALM_X,0,38.5)),'tool','F6-09-SPOOL',GOLD))
    for a in [0,120,240]:
        for pid,fn,col in [('F6-08-FINGER',finger,WHITE),('F6-10-SOFT-PAD',pad,SOFT)]:
            s=fn().translate((23,0,-5)).rotate((0,0,0),(0,0,1),a).translate((PALM_X,0,0))
            out.append(Item(pid+str(a),s,'tool',pid,col))
        r=rz(a)
        pts=[np.array([PALM_X,0,0])+r@np.array(p) for p in [(9.5,0,46.4+a/120*2.6),(24,-6,35),(15,0,-8)]]
        for k in range(2):out.append(Item(f'cord path {a} {k}',cord_segment(pts[k],pts[k+1]),'tool',color=TEAL,mass_g=.1))
    placements=[('J1',False,'base',0,(0,0,50)),('J2A',False,'yaw',1,(0,24,100)),
      ('J2B',False,'yaw',-1,(0,-24,100)),('J3',False,'upper',1,(180,24,0)),
      ('W1',True,'fore',1,(140,20,0)),('G1',True,'tool',0,(PALM_X,0,31))]
    for name,micro,frame,side,origin in placements:
        fn=lambda s: side_place(s,side,origin) if side else s.translate(origin)
        p=YAW_MG if name=='J1' else (MICRO if micro else MG)
        out.append(Item(name+' servo',fn(servo(micro,spec=p)),frame,color=BLACK,mass_g=13.4 if micro else 55.))
        for k,(x,y) in enumerate(ear_points(micro,spec=p)):
            # Simplified press-fit insert envelope; no thread modeled. Deliberate
            # brass/plastic interference is excluded from rigid collision screening.
            ins=cz(1.6 if micro else 2.3,p['ear_z']-p['insert_depth'],p['insert_depth'],x,y)
            ins=ins.cut(cz(1 if micro else 1.5,p['ear_z']-8,10,x,y))
            out.append(Item(f'insert {name} ear{k}',fn(ins),frame,color=GOLD,mass_g=.18 if micro else .35))
            head_z=p['ear_z']+2.2+(.5 if micro else 1)
            length=6 if micro else 8
            bolt=cz(1 if micro else 1.5,head_z-length,length,x,y).union(cz(1.8 if micro else 2.7,head_z,1.5 if micro else 2.5,x,y))
            out.append(Item(f'fastener {name} ear{k}',fn(bolt),frame,color=SILVER,mass_g=.22 if micro else .7))
        # Output horns follow moving downstream frame, not stator (zero-pose placements below).
    horns=[('J1','yaw',False,0,(0,0,50)),('J2A','upper',False,1,(0,24,0)),
        ('J2B','upper',False,-1,(0,-24,0)),('J3','fore',False,1,(0,24,0)),
        ('W1','tool',True,1,(0,20,0)),('G1','tool',True,0,(PALM_X,0,31))]
    for name,frame,micro,side,origin in horns:
        s=side_place(horn(micro),side,origin) if side else horn(micro).translate(origin)
        out.append(Item(name+' original horn envelope',s,frame,color=BLACK,mass_g=1 if micro else 2))
        fn=lambda s:side_place(s,side,origin) if side else s.translate(origin)
        pid='F6-21-MICRO-SOCKET-COVER' if micro else 'F6-20-LARGE-SOCKET-COVER'
        out.append(Item(pid+' '+name,fn(original_horns.closure(micro)),frame,pid,WHITE))
        for label,bolt in original_horns.hardware(micro):
            if 'insert' in label:continue  # Insert envelope is added once below.
            out.append(Item(f'fastener {name} {label}',fn(bolt),frame,color=SILVER,mass_g=bolt.val().Volume()*.00785))
        for k,(x,y) in enumerate(horn_points(micro)):
            z=original_horns.cover_top(micro)
            ins=cz(1.6,z,4,x,y).cut(cz(1,z-.5,5,x,y))
            out.append(Item(f'insert {name} horn{k}',fn(ins),frame,color=GOLD,mass_g=.18))
    # Retainer is installed as two radial halves, after the rotor is seated.
    for a in range(0,360,90):
        t=math.radians(a+45);x,y=65*math.cos(t),65*math.sin(t)
        ins=cz(2.3,46,5,x,y).cut(cz(1.5,45,7,x,y))
        out.append(Item(f'insert bearing {a}',ins,color=GOLD,mass_g=.35))
    for a in range(24):
        t=math.tau*a/24;s=cq.Workplane('XY').sphere(4).translate((45*math.cos(t),45*math.sin(t),BALL_Z))
        out.append(Item(f'PB02 ball {a}',s,color=SILVER,mass_g=4/3*math.pi*4**3*.00124))
    for frame,x in [('upper',180),('fore',140)]:
        l=11.5 if frame=='upper' else 15.5
        # Smooth metal sleeve (stock tube), not a threaded/printed axle.
        sleeve=bushing(l).translate((x,0,0))
        out.append(Item('metal pivot sleeve '+frame,sleeve,frame,color=GOLD,mass_g=sleeve.val().Volume()*.0085))
    return out

def assembly(q=(0,-35,85,-50),rover=False,grip=0.):
    fs=frames(q,rover)
    out=[]
    for i in local_items():
        s=i.shape
        if i.part_id in ['F6-08-FINGER','F6-10-SOFT-PAD']:
            phi=int(i.name[len(i.part_id):]);fn=finger if i.part_id=='F6-08-FINGER' else pad
            s=fn().rotate((0,0,0),(0,1,0),grip).translate((23,0,-5)).rotate((0,0,0),(0,0,1),phi).translate((PALM_X,0,0))
        out.append(Item(i.name,move(s,fs[i.frame]),i.frame,i.part_id,i.color,i.mass_g))
    return out

def solve(point):
    v=np.array(point)-BASE_WORLD-np.array([0,0,SHOULDER_Z])
    yaw=math.degrees(math.atan2(v[1],v[0]));x=math.hypot(v[0],v[1])-FRUIT[0];z=v[2]-FRUIT[2]
    c=(x*x+z*z-UPPER**2-FORE**2)/(2*UPPER*FORE)
    if abs(c)>1:raise ValueError('Target outside reach')
    e=math.acos(c);s=math.atan2(-z,x)-math.atan2(FORE*math.sin(e),UPPER+FORE*math.cos(e))
    return (yaw,math.degrees(s),math.degrees(e),-math.degrees(s+e))

def print_pose(pid,s):
    if pid in ['F6-02-ROTOR','F6-18-LARGE-HORN-FIT','F6-19-MICRO-HORN-FIT'] or pid.startswith('F6-03'):s=s.rotate((0,0,0),(1,0,0),180)
    if pid in ['F6-05-UPPER','F6-06-FORE','F6-08-FINGER','F6-10-SOFT-PAD','F6-11-BUSHING']:
        s=s.rotate((0,0,0),(1,0,0),90)
    b=s.val().BoundingBox();return s.translate((-b.xmin,-b.ymin,-b.zmin))

if __name__=='__main__':
    for pid,(fn,n,f) in PARTS.items():
        s=fn();b=s.val().BoundingBox()
        print(pid,'valid',s.val().isValid(),'solids',len(s.solids().vals()),'g',round(s.val().Volume()*.00124,2),'box',[round(v,1) for v in [b.xlen,b.ylen,b.zlen]],flush=True)
