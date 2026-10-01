"""LINKA L1.3: proximal-drive linkage arm, DEC-080 J1 cable service windows.

Mechanism reference: MeArm / theGHIZmo EEZYbotARM Mk2. Independently
dimensioned geometry; no downloaded STL is represented as our design.
Only the measured yaw interface and original horn sockets reuse R6 helpers.
All strength, servo calibration, fruit size and tendon compliance need trials.
"""
from functools import lru_cache
import math
import numpy as np
import cadquery as cq
from cad.prototype_arm import build_forma_v6 as h
from cad.utils import ROOT

from scripts.project_paths import CAD as OUT
U,F=150.,120.
Z=110.
C=np.array([-65.,0.,105.])
CRANK,ROD,TAIL=65.,185.,35.
WRIST_Y=-62.
PALM_X=48.
REVISION='LINKA L1.5 / DEC-082'
SCOOP_CLOSED_ANGLE=12.
SCOOP_WALL=1.6
# Closed-pose radial sections: height below pivot, radius, half sector angle.
SCOOP_SECTIONS=[(-14,31,5),(-19,29,58),(-27,25,58),(-35,18,58),(-41.3,5,50)]
# Printable plain sleeves: nominal prototype geometry, not a load approval.
FINGER_BUSH_OD,FINGER_BUSH_ID,FINGER_BUSH_LENGTH=4.8,2.4,6.
FINGER_PIVOT_BORE=5.1
# User-reported on2026-09-14. Position above case bottom remains unmeasured.
BASE_CABLE_BOOT_MEASURED={'width':7.,'height':3.9,'protrusion':5.5}
# Service opening preserved; its nominal clearance is not a printer tolerance.
BASE_CABLE_SLOT_WIDTH=12.
BASE_CABLE_SLOT_TOP=28.
BEARING_BOLT_R=12.5
BEARING_CAP_Y=19.2
ROD_SEAT_Y=-31.
ROD_BUSH_OD,ROD_BUSH_ID,ROD_BUSH_LENGTH=6.,3.3,6.
ROD_PIVOT_BORE,ROD_END_THICK=6.3,5.6
CREAM=(.79,.81,.73); DARK=(.16,.23,.25); GREEN=(.28,.53,.43)
ORANGE=(.87,.51,.25)
Item=h.Item

def angle(p):return math.degrees(math.atan2(-p[2],p[0]))
def armvec(length,theta):return h.ry(theta)@np.array([length,0.,0.])

def solve_linkage(a,b):
    """a=upper absolute pitch, b=fore absolute pitch, degrees (Y rotation).
    Exact circle intersection on the rear/up crank branch. No loose visual rod.
    """
    E=np.array([0.,0.,Z])+armvec(U,a)
    D=E-armvec(TAIL,b)
    v=D-C;d=np.linalg.norm(v)
    k=(d*d+CRANK*CRANK-ROD*ROD)/(2*d*CRANK)
    if abs(k)>1:raise ValueError('Remote elbow linkage cannot reach pose')
    g=angle(v)-math.degrees(math.acos(k))
    # Continuous branch across the audited transfer (avoid atan2 +/-180 jump).
    g=g%360-360
    A=C+armvec(CRANK,g)
    return dict(E=E,D=D,A=A,gamma=g,rod_angle=angle(D-A),closure_error=float(abs(np.linalg.norm(D-A)-ROD)))

def ik(target):
    dx,dy,dz=np.array(target)-np.array([550.,415.,66.+Z])
    # Tool datum at wrist + (PALM_X,0,-45), horizontal tool frame.
    reach=math.sqrt(dx*dx+dy*dy-WRIST_Y*WRIST_Y)
    r=reach-PALM_X;z=dz+45.
    k=(r*r+z*z-U*U-F*F)/(2*U*F)
    if abs(k)>1:raise ValueError('Outside two-link reach')
    b=math.acos(k);a=math.atan2(-z,r)-math.atan2(F*math.sin(b),U+F*math.cos(b))
    q=[math.degrees(math.atan2(dy,dx)-math.atan2(WRIST_Y,reach)),math.degrees(a),math.degrees(b),-math.degrees(a+b)]
    solve_linkage(q[1],q[1]+q[2])
    return q

def frames(q):
    y=h.matrix(h.rz(q[0]));u=y@h.matrix(h.ry(q[1]),(0,0,Z))
    f=u@h.matrix(h.ry(q[2]),(U,0,0));t=f@h.matrix(h.ry(q[3]),(F,WRIST_Y,0))
    l=solve_linkage(q[1],q[1]+q[2])
    return {'base':h.matrix(),'yaw':y,'upper':u,'fore':f,'tool':t,
            'crank':y@h.matrix(h.ry(l['gamma']),C),
            'rod':y@h.matrix(h.ry(l['rod_angle']),l['A'])}

def plate(poly,y,thick):
    return cq.Workplane('XZ').polyline(poly).close().extrude(thick).translate((0,y+thick/2,0))

def capsule(length,width,y,thick):
    return plate([(0,-width/2),(length,-width/2),(length,width/2),(0,width/2)],y,thick).union(h.cy(width/2,y-thick/2,thick)).union(h.cy(width/2,y-thick/2,thick,x=length))

def bore(s,x,y,z,d,length):return s.cut(h.cy(d/2,y,length,x,z))

@lru_cache(None)
def base():
    """Relieve the middle of both J1 end walls below the insert-bearing seats.

    Keep the old floor, ear seats, screw axes and rolling track. Both short
    ends are relieved because the specimen cable end/vertical datum is unverified.
    This is a cable-level window; installation threads the wire through it.
    """
    s=h.base()
    for x in sorted(set(p[0] for p in h.ear_points(spec=h.YAW_MG))):
        # Rounded roof, floor Z4 retained; full9mm wall thickness is opened.
        w=BASE_CABLE_SLOT_WIDTH
        roof=BASE_CABLE_SLOT_TOP-w/2
        cut=h.box(10,w,roof-4,(x,0,(roof+4)/2))
        crown=h.cz(w/2,-5,10).rotate((0,0,0),(0,1,0),90).translate((x,0,roof))
        s=s.cut(cut.union(crown))
    return s

@lru_cache(None)
def rotor():
    # Matched rolling surface and clearance retained; all upper structure NEW.
    s=h.ring(38,51,52,8).cut(cq.Workplane(obj=cq.Solid.makeTorus(45,4.2,(0,0,49.6))))
    s=s.union(h.cz(46,57.5,4.5)).union(h.ring(50,55,57.5,2.5))
    for a in range(0,360,60):
        t=math.radians(a);s=s.cut(h.cz(7,57,6,30*math.cos(t),30*math.sin(t)))
    s=s.union(h.horn_receiver().translate((0,0,50)))
    # Wide, short integral webs carry the separate bolted motor deck.
    for x in [-28,28]:
        for y in [-15,15]:
            s=s.union(h.rounded(14,14,17.5,3,(x,y,66.25)))
            s=h.insert_hole(s,x,y,75,4.2,5)
    return h.clear_horn_face(s,False,0,(0,0,50))

@lru_cache(None)
def motor_deck():
    # Every factory-ear column has a continuous floor, including J3's outer leg.
    # Preserve Z75..80 and the existing four rotor mounting screw axes.
    s=h.rounded(146,120,5,9,(-39,-6,77.5))
    for x in [-28,28]:
        for y in [-15,15]:s=h.screw_hole(s,x,y,3.3)
    # Open underside; no motor clamps. Factory ears land directly on these seats.
    for side,origin in [(1,(0,27,Z)),(-1,(0,-27,Z)),(-1,tuple(C+[0,-38,0]))]:
        seat=h.side_place(h.mount_region(),side,origin);s=s.union(seat)
        for x,y in h.ear_points():
            p=np.array(origin)+np.array([x,-side*(-16),side*y])
            # Integral column under the factory ear; it is not a triangular gusset.
            x0=p[0]; yy=p[1]
            top=max(80.,p[2]);s=s.union(h.rounded(12,12,top-76+3,2,(x0,yy,(76+top+3)/2)))
        # Actual triangular buttress on the outward side of each column.
        for x0 in sorted(set(origin[0]+p[0] for p in h.ear_points())):
            yy=origin[1]+side*16
            profile=[(yy+side*3,79),(yy+side*11,79),(yy+side*3,97)]
            rib=cq.Workplane('YZ').polyline(profile).close().extrude(12).translate((x0-6,0,0))
            s=s.union(rib)
        s=h.clear_mount(s,False,side,origin)
    # Large windows leave a continuous 7+ mm deck border and screw lands.
    for x,y in [(-63,20),(-10,0),(26,0)]:
        s=s.cut(h.rounded(22,20,10,5,(x,y,77)))
    # Relief for the whole rear crank sweep, not merely the displayed pose.
    s=s.cut(h.cy(CRANK+10,-37.8,15.3,C[0],C[2]))
    return s

@lru_cache(None)
def upper_side(side):
    y=side*16.
    # Constant-depth load rails, gradual broad root; no tapered needle fork.
    s=plate([(0,-23),(30,-19),(129,-13),(150,-13),(150,13),(129,13),(30,19),(0,23)],y,5)
    s=s.union(h.cy(24,y-2.5,5)).union(h.cy(16,-18.5 if side<0 else 11.5,7,x=U))
    for x,w in [(47,26),(84,27),(119,18)]:
        cut=h.rounded(w,30,13,4,(x,y,0));s=s.cut(cut)
    s=s.union(h.side_place(h.horn_receiver(),side,(0,side*27,0)))
    # 625 bearing pocket, trial +0.15 mm diameter, retained by separate ring.
    s=bore(s,U,y-6,0,12.4,12)
    s=bore(s,U,14 if side>0 else -20,0,16.15,6)
    for phi in [90,210,330]:
        x=U+BEARING_BOLT_R*math.cos(math.radians(phi));z=BEARING_BOLT_R*math.sin(math.radians(phi))
        s=bore(s,x,15 if side>0 else -18.5,z,2.9,3.5)
    for x in [35,112]:s=bore(s,x,y-5,-10,3.3,10)
    return h.clear_horn_face(s,False,side,(0,side*27,0))

@lru_cache(None)
def upper_tie():
    s=h.rounded(10,27,10,2,(0,0,0))
    for side in [-1,1]:s=bore(s,0,-13.5 if side<0 else 8.5,0,4.2,5)
    return s

@lru_cache(None)
def bearing_cap():
    s=h.cy(16,0,2).cut(h.cy(6.2,0,2))
    for phi in [90,210,330]:
        x=BEARING_BOLT_R*math.cos(math.radians(phi));z=BEARING_BOLT_R*math.sin(math.radians(phi))
        # Integral feet seat on the upper plate, leaving 0.2mm bearing end float.
        s=s.union(h.cy(2.8,-.7,.7,x,z))
        s=bore(s,x,-1,z,2.2,4)
    return s

@lru_cache(None)
def fore_side(side):
    y=side*25.
    start=-TAIL if side==-1 else 0.
    s=plate([(start,-9),(0,-16),(26,-15),(104,-10),(120,-10),(120,10),(104,10),(26,15),(0,16),(start,9)],y,4)
    s=s.union(h.cy(12,y-2,4)).union(h.cy(10,y-2,4,x=F))
    if side==-1:
        s=s.union(h.cy(8,y-2,4,x=-TAIL)).union(h.cy(6,ROD_SEAT_Y,9,x=-TAIL))
        s=bore(s,-TAIL,ROD_SEAT_Y,0,3.3,8)
        s=bore(s,-TAIL,ROD_SEAT_Y,0,4.2,4.5)
    for x,w in [(40,28),(79,25)]:s=s.cut(h.rounded(w,70,12,4,(x,y,0)))
    s=bore(s,0,y-4,0,5.3,16)
    # Both outside faces are flat at +/-27: washers and an accessible M5 locknut.
    s=bore(s,24,y-4,8,3.3,8)
    s=bore(s,106,y-4,3,2.2,8)
    if side==-1:s=h.clear_mount(s,True,1,(F,WRIST_Y,0))
    return s

@lru_cache(None)
def fore_tie():
    s=h.rounded(9,46,9,2)
    for side in [-1,1]:s=bore(s,0,-23 if side<0 else 18,0,4.2,5)
    return s

@lru_cache(None)
def wrist_seat():
    # Removable short transverse bridge; insert bolts outside the servo envelope.
    s=h.rounded(12,80,4,2,(-17,-17,17)).union(h.side_place(h.mount_region(True),1,(0,WRIST_Y,0)))
    s=s.union(h.rounded(7,12,24,1,(-20.5,-48,7)))
    for y in [-19.5,19.5]:
        s=s.union(h.rounded(16,7,26,2,(-14,y,7)))
        s=bore(s,-14,y-4,3,2.9,8)
    return h.clear_mount(s,True,1,(0,WRIST_Y,0))

@lru_cache(None)
def crank():
    y=-27.
    s=capsule(CRANK,14,y,5).union(h.side_place(h.horn_receiver(),-1,(0,-38,0)))
    s=s.cut(h.rounded(22,15,5,2,(34,y,0)))
    s=s.union(h.cy(6,ROD_SEAT_Y,9,x=CRANK))
    s=bore(s,CRANK,ROD_SEAT_Y,0,3.3,8)
    s=bore(s,CRANK,ROD_SEAT_Y,0,4.2,4.5)
    return h.clear_horn_face(s,False,-1,(0,-38,0))

@lru_cache(None)
def rod():
    s=capsule(ROD,10,-34,4)
    # Two rails and short cross webs, lying flat when printed.
    for x in [27,59,91,123,155]:s=s.cut(h.rounded(24,12,4.2,1.5,(x,-34,0)))
    for x in [0,ROD]:
        s=s.union(h.cy(7,-34-ROD_END_THICK/2,ROD_END_THICK,x))
        s=bore(s,x,-38,0,ROD_PIVOT_BORE,8)
    return s

@lru_cache(None)
def rod_bush():
    return plain_bush(ROD_BUSH_OD,ROD_BUSH_ID,ROD_BUSH_LENGTH)

@lru_cache(None)
def palm():
    # Short open tripod, not the previous long solid palm/cylinder.
    s=h.side_place(h.horn_receiver(True),1,(0,0,0))
    s=s.union(h.rounded(60,8,5,2,(24,-14,-1.5)))
    s=s.union(h.rounded(15,22,5,3,(PALM_X-1,-5,-1.5)))
    hub=h.cz(12,-4,4,PALM_X,0)
    for phi in [0,120,240]:
        ray=h.rounded(27,8,4,3,(15,0,-2)).rotate((0,0,0),(0,0,1),phi).translate((PALM_X,0,0))
        hub=hub.union(ray)
        return_eye=h.cz(.6,-4.2,4.4,27.5,0).rotate((0,0,0),(0,0,1),phi).translate((PALM_X,0,0))
        hub=hub.cut(return_eye)
        guide=h.rounded(6,5,17,1.5,(18,0,-8.5))
        guide=bore(guide,18,-4,-15,1.6,8)
        hub=hub.union(guide.rotate((0,0,0),(0,0,1),phi).translate((PALM_X,0,0)))
        for yy in [-5,5]:
            lug=h.rounded(10,4,12,2,(28,yy,-6))
            lug=bore(lug,28,yy-3,-9,2.2 if yy<0 else 2.9,6)
            hub=hub.union(lug.rotate((0,0,0),(0,0,1),phi).translate((PALM_X,0,0)))
    s=s.union(hub)
    s=s.union(h.rounded(8,58,4,2,(PALM_X,0,-2)))
    s=s.cut(h.cz(7,-6,18,PALM_X,0))
    # G1 inverted, its case stays above the fingers. Integral factory-ear mounts.
    place=lambda v:v.rotate((0,0,0),(1,0,0),180).translate((PALM_X,0,16))
    s=s.union(place(h.mount_region(True)))
    s=s.union(h.rounded(32,64,4,3,(PALM_X-4.8,0,30)))
    for y in [-26,26]:s=s.union(h.rounded(6,6,33,2,(PALM_X,y,12.5)))
    # Clear nominal stator and flange, retain open access to original ears.
    s=s.cut(place(h.servo(True)))
    for x,y in h.ear_points(True):s=s.cut(place(h.cz(1.45,-14,4.1,x,y)))
    s=s.cut(h.cy(20.5,9,10.5))
    # Full rotating envelope of captured original star, not just the spool drum.
    s=s.cut(h.cz(22.5,2.5,11,PALM_X,0))
    s=h.clear_horn_face(s,True,1,(0,0,0))
    # The centre-screw access cut severs a 7 mm3 hole plug; it is waste, not a part.
    return cq.Workplane(obj=max(s.val().Solids(),key=lambda v:v.Volume()))

@lru_cache(None)
def finger():
    # Factory pivot/cord interfaces unchanged. Broad thin spoon starts below them.
    s=plate([(-5,4),(5,4),(8,-9),(7,-19),(-1,-19),(0,-15),(-2,-7)],0,5.5)
    s=s.union(scoop_shell(0,SCOOP_WALL))
    s=bore(s,0,-4,0,FINGER_PIVOT_BORE,8)
    # Closing and return eyes below pivot, with separate guide directions.
    s=bore(s,4,-4,-12,1.4,8)
    s=bore(s,4,-4,-8,1.6,8)
    return s

@lru_cache(None)
def pad():
    # Conformal thin TPU contact liner. Not a PLA part or the former flat pad.
    return scoop_shell(SCOOP_WALL+.05,1.,liner=True).cut(finger())


def scoop_shell(inset,thickness,liner=False):
    """Three116-degree spoons nearly close a cup at12deg; openings remain explicit."""
    wires=[]
    sections=SCOOP_SECTIONS[1:] if liner else SCOOP_SECTIONS
    for z,r,half in sections:
        ro=r-inset;ri=ro-thickness;phi=math.radians(half-(2 if liner else 0))
        c,t=math.cos(phi),math.sin(phi)
        w=(cq.Workplane('XY',origin=(0,0,z)).moveTo(ro*c,-ro*t)
           .threePointArc((ro,0),(ro*c,ro*t)).lineTo(ri*c,ri*t)
           .threePointArc((ri,0),(ri*c,-ri*t)).close().val())
        wires.append(w)
    s=cq.Workplane(obj=cq.Solid.makeLoft(wires,ruled=True))
    s=s.translate((-28,0,0)).rotate((0,0,0),(0,1,0),-SCOOP_CLOSED_ANGLE)
    # User requested exactly10mm more projection from old -35mm finger tip.
    floor=-44.5 if liner else -45.
    return s.intersect(h.box(200,200,100,(0,0,floor+50)))

@lru_cache(None)
def spool():
    s=h.horn_receiver(True)
    # Radius 5 working drum. Three separate lanes, elastic links downstream.
    s=s.union(h.cz(5,12.5,8.5))
    for z in [13,15.5,18,20.5]:s=s.union(h.cz(6.5,z,.7))
    for phi in [0,120,240]:
        t=math.radians(phi);s=h.screw_hole(s,4*math.cos(t),4*math.sin(t),1.2,13,8.5)
    return s


def plain_bush(od,id_,length):
    """Z-axis upright printing; no flange or unverified interference fit."""
    return h.cz(od/2,0,length).cut(h.cz(id_/2,-.1,length+.2))


@lru_cache(None)
def elbow_bush_long():return plain_bush(8,5.3,28)


@lru_cache(None)
def elbow_bush_short():return plain_bush(8,5.3,4)


@lru_cache(None)
def finger_bush():return plain_bush(FINGER_BUSH_OD,FINGER_BUSH_ID,FINGER_BUSH_LENGTH)

PARTS={
 'L1-01-BASE':(base,1,'base'), 'L1-02-ROTOR':(rotor,1,'yaw'),
 'L1-03-RETAINER-L':(lambda:h.retainer_half(-1),1,'base'),
 'L1-04-RETAINER-R':(lambda:h.retainer_half(1),1,'base'),
 'L1-05-CAGE':(h.cage,1,'base'),'L1-06-DECK':(motor_deck,1,'yaw'),
 'L1-07-UPPER-L':(lambda:upper_side(-1),1,'upper'),
 'L1-08-UPPER-R':(lambda:upper_side(1),1,'upper'),
 'L1-09-UPPER-TIE':(upper_tie,2,'upper'),
 'L1-10-FORE-L':(lambda:fore_side(-1),1,'fore'),
 'L1-11-FORE-R':(lambda:fore_side(1),1,'fore'),
 'L1-12-FORE-TIE':(fore_tie,1,'fore'),
 'L1-13-WRIST-SEAT':(wrist_seat,1,'fore'),
 'L1-14-DRIVE-CRANK':(crank,1,'crank'),
 'L1-15-COUPLER':(rod,1,'rod'),
 'L1-16-PALM':(palm,1,'tool'),'L1-17-FINGER':(finger,3,'finger'),
 'L1-18-PAD':(pad,3,'finger'),'L1-19-SPOOL':(spool,1,'tool'),
 'L1-20-MG-COVER':(lambda:h.original_horns.closure(False),4,'hardware'),
 'L1-21-MICRO-COVER':(lambda:h.original_horns.closure(True),2,'hardware'),
 'L1-22-BEARING-CAP':(bearing_cap,2,'upper'),
 'L1-23-ELBOW-BUSH-LONG':(elbow_bush_long,1,'bush'),
 'L1-24-ELBOW-BUSH-SHORT':(elbow_bush_short,2,'bush'),
 'L1-25-FINGER-BUSH':(finger_bush,3,'bush'),
 'L1-26-ROD-BUSH':(rod_bush,2,'bush'),
}

def cord(p,q,r=.45):
    v=np.array(q)-p
    return cq.Workplane(obj=cq.Solid.makeCylinder(r,float(np.linalg.norm(v)),cq.Vector(*p),cq.Vector(*v)))

def washer_y(od,id,y,t,x=0,z=0):
    return h.cy(od/2,y,t,x,z).cut(h.cy(id/2,y,t,x,z))

def hexnut_y(af,id,y,t):
    s=cq.Workplane('XY').polygon(6,af/math.cos(math.pi/6)).extrude(t).cut(h.cz(id/2,-.1,t+.2))
    return s.rotate((0,0,0),(1,0,0),-90).translate((0,y,0))

def rod_shoulder_screw(x):
    # DEC-085: standard M3x10, 0.5mm M3 washer, 6mm printed sleeve.
    # Under-head Y=-37.5; tip=-27.5, nominal insert engagement3.5mm.
    return h.cy(2.75,-40.5,3,x).union(h.cy(1.5,-37.5,10,x))

def local_items(grip=-15):
    out=[]
    for pid in ['L1-01-BASE','L1-02-ROTOR','L1-03-RETAINER-L','L1-04-RETAINER-R','L1-05-CAGE','L1-06-DECK','L1-07-UPPER-L','L1-08-UPPER-R','L1-10-FORE-L','L1-11-FORE-R','L1-14-DRIVE-CRANK','L1-15-COUPLER','L1-16-PALM']:
        fn,n,frame=PARTS[pid]
        color=CREAM if frame in ['upper','fore','tool'] else DARK
        if frame in ['crank','rod']:color=GREEN
        out.append(Item(pid,fn(),frame,pid,color))
    for x in [35,112]:out.append(Item('L1-09 tie '+str(x),upper_tie().translate((x,0,-10)),'upper','L1-09-UPPER-TIE',GREEN))
    for x in [24]:out.append(Item('L1-12 tie '+str(x),fore_tie().translate((x,0,8)),'fore','L1-12-FORE-TIE',GREEN))
    out.append(Item('L1-13 wrist',wrist_seat().translate((F,0,0)),'fore','L1-13-WRIST-SEAT',GREEN))
    invert=lambda s:s.rotate((0,0,0),(1,0,0),180).translate((PALM_X,0,16))
    out.append(Item('L1-19 spool',invert(spool()),'tool','L1-19-SPOOL',GREEN))
    for phi in [0,120,240]:
        put=lambda s:s.rotate((0,0,0),(0,1,0),grip).translate((28,0,-9)).rotate((0,0,0),(0,0,1),phi).translate((PALM_X,0,0))
        out.append(Item('L1-17 finger '+str(phi),put(finger()),'tool','L1-17-FINGER',CREAM))
        out.append(Item('L1-18 pad '+str(phi),put(pad()),'tool','L1-18-PAD',ORANGE))
        # Tendon and individual elastic section, not a claimed force sensor.
        p=np.array([PALM_X,0.,0.])+h.rz(phi)@np.array([6.,0.,0.])
        q=np.array([PALM_X,0.,0.])+h.rz(phi)@np.array([18.,0.,-15.])
        end=np.array([PALM_X,0.,0.])+h.rz(phi)@(h.ry(grip)@np.array([4.,0.,-12.])+[28,0,-9])
        out.append(Item('closing cord '+str(phi),cord(p,q),'tool',color=DARK,mass_g=.1))
        out.append(Item('elastic equalizing link '+str(phi),cord(q,end,.9),'tool',color=ORANGE,mass_g=.2))
        anchor=np.array([PALM_X,0.,0.])+h.rz(phi)@np.array([27.5,0.,-2.])
        eye=np.array([PALM_X,0.,0.])+h.rz(phi)@(h.ry(grip)@np.array([4.,0.,-8.])+[28,0,-9])
        out.append(Item('return elastic '+str(phi),cord(anchor,eye,.65),'tool',color=GREEN,mass_g=.15))
        pivot=h.cy(1.,-7,14,28,-9).union(h.cy(2.,-8.5,1.5,28,-9))
        sleeve=finger_bush().rotate((0,0,0),(1,0,0),-90).translate((28,-3,-9))
        out.append(Item('printed finger bush '+str(phi),sleeve.rotate((0,0,0),(0,0,1),phi).translate((PALM_X,0,0)),'tool','L1-25-FINGER-BUSH',GREEN))
        out.append(Item('finger pivot M2 '+str(phi),pivot.rotate((0,0,0),(0,0,1),phi).translate((PALM_X,0,0)),'tool',color=h.SILVER,mass_g=.8))
        ins=washer_y(3.2,2,3,3,28,-9).rotate((0,0,0),(0,0,1),phi).translate((PALM_X,0,0))
        out.append(Item('finger M2L3 insert '+str(phi),ins,'tool',color=h.GOLD,mass_g=.14))
    placements=[('J1',False,'base',0,(0,0,50)),('J2A',False,'yaw',1,(0,27,Z)),('J2B',False,'yaw',-1,(0,-27,Z)),('J3 REMOTE',False,'yaw',-1,tuple(C+[0,-38,0])),('W1',True,'fore',1,(F,WRIST_Y,0)),('G1',True,'tool',2,(PALM_X,0,16))]
    for name,micro,frame,side,p in placements:
        put=lambda s:invert(s) if side==2 else h.side_place(s,side,p) if side else s.translate(p)
        spec=h.YAW_MG if name=='J1' else None
        out.append(Item(name+' servo',put(h.servo(micro,spec)) ,frame,color=h.BLACK,mass_g=13.4 if micro else 55.))
        for x,y in h.ear_points(micro,spec):
            spec2=spec or (h.MICRO if micro else h.MG);z=spec2['ear_z']
            ins=h.cz(1.5 if micro else 2.1,z-spec2['insert_depth'],spec2['insert_depth'],x,y)
            out.append(Item('brass ear '+name,put(ins),frame,color=h.GOLD,mass_g=.2 if micro else .4))
            length=6;wt=.3 if micro else .5;head=z+2.2+wt
            wash=h.cz(2.5 if micro else 3.5,z+2.2,wt,x,y).cut(h.cz(1.1 if micro else 1.6,z+2.2,wt,x,y))
            out.append(Item('ear washer '+name,put(wash),frame,color=h.SILVER,mass_g=.04 if micro else .12))
            bolt=h.cz(1 if micro else 1.5,head-length,length,x,y).union(h.cz(1.8 if micro else 2.7,head,1.5 if micro else 2.5,x,y))
            out.append(Item('ear screw '+name,put(bolt),frame,color=h.SILVER,mass_g=.25 if micro else .7))
    horns=[('J1','yaw',False,0,(0,0,50)),('J2A','upper',False,1,(0,27,0)),('J2B','upper',False,-1,(0,-27,0)),('J3','crank',False,-1,(0,-38,0)),('W1','tool',True,1,(0,0,0)),('G1','tool',True,2,(PALM_X,0,16))]
    for name,frame,micro,side,p in horns:
        put=lambda s:invert(s) if side==2 else h.side_place(s,side,p) if side else s.translate(p)
        out.append(Item(name+' original horn',put(h.horn(micro)),frame,color=h.BLACK,mass_g=1 if micro else 2))
        pid='L1-21-MICRO-COVER' if micro else 'L1-20-MG-COVER'
        out.append(Item(pid+' '+name,put(h.original_horns.closure(micro)),frame,pid,GREEN))
        for name2,s in h.original_horns.hardware(micro):out.append(Item(name+' '+name2,put(s),frame,color=h.SILVER,mass_g=s.val().Volume()*.00785))
    for side in [-1,1]:
        by=14 if side>0 else -19
        bearing=h.cy(8,by,5,U).cut(h.cy(2.5,by,5,U))
        out.append(Item('625 bearing '+str(side),bearing,'upper',color=h.SILVER,mass_g=4.8))
        cap=bearing_cap().translate((U,BEARING_CAP_Y,0))
        if side<0:cap=cap.mirror('XZ')
        out.append(Item('L1-22 bearing cap '+str(side),cap,'upper','L1-22-BEARING-CAP',GREEN))
        for phi in [90,210,330]:
            x=U+BEARING_BOLT_R*math.cos(math.radians(phi));z=BEARING_BOLT_R*math.sin(math.radians(phi))
            bolt=h.cy(1,BEARING_CAP_Y-4,6,x,z).union(h.cy(1.8,BEARING_CAP_Y+2,1.5,x,z))
            if side<0:bolt=bolt.mirror('XZ')
            out.append(Item('bearing cap screw',bolt,'upper',color=h.SILVER,mass_g=.25))
            ins=washer_y(3.2,2,15.5,3,x,z)
            if side<0:ins=ins.mirror('XZ')
            out.append(Item('bearing M2L3 insert '+str((side,phi)),ins,'upper',color=h.GOLD,mass_g=.14))
    for frame,xs,y,z in [('upper',[35,112],18.5,-10),('fore',[24],27,8),('fore',[106],27,3)]:
        for x in xs:
            for side in [-1,1]:
                r=1 if x==106 else 1.5;length=10 if frame=='upper' else 8;wt=.3 if x==106 else .5
                head=y+wt
                bolt=h.cy(r,head-length,length,x,z).union(h.cy(r*1.8,head,2,x,z))
                wash=washer_y(5 if x==106 else 7,2.2 if x==106 else 3.2,y,wt,x,z)
                if side<0:bolt=bolt.mirror('XZ');wash=wash.mirror('XZ')
                out.append(Item('tie screw '+frame+str(x)+str(side),bolt,frame,color=h.SILVER,mass_g=.3 if x==106 else .7))
                out.append(Item('tie washer '+frame+str(x)+str(side),wash,frame,color=h.SILVER,mass_g=.04 if x==106 else .12))
                start=19 if x==106 else 18 if frame=='fore' else 8.5
                ins=washer_y(3.2 if x==106 else 4.5,2 if x==106 else 3,start,4 if x==106 else 5,x,z)
                if side<0:ins=ins.mirror('XZ')
                out.append(Item('tie insert '+frame+str(x)+str(side),ins,frame,color=h.GOLD,mass_g=.2 if x==106 else .4))
    for x in [-28,28]:
        for y in [-15,15]:
            out.append(Item('deck screw',h.cz(1.5,70.5,10,x,y).union(h.cz(2.7,80.5,2.5,x,y)),'yaw',color=h.SILVER,mass_g=.7))
            out.append(Item('deck washer',h.cz(3.5,80,.5,x,y).cut(h.cz(1.6,80,.5,x,y)),'yaw',color=h.SILVER,mass_g=.12))
            out.append(Item('deck M3L5 insert',h.cz(2.25,70,5,x,y).cut(h.cz(1.5,70,5,x,y)),'yaw',color=h.GOLD,mass_g=.4))
    for angle in range(0,360,90):
        t=math.radians(angle+45);x,y=65*math.cos(t),65*math.sin(t)
        out.append(Item('retainer M3x20 screw '+str(angle),h.cz(1.5,47,20,x,y).union(h.cz(2.7,67,3,x,y)),color=h.SILVER,mass_g=1.2))
        out.append(Item('retainer washer '+str(angle),h.cz(3.5,66.5,.5,x,y).cut(h.cz(1.6,66.5,.5,x,y)),color=h.SILVER,mass_g=.12))
        out.append(Item('retainer M3L5 insert '+str(angle),h.cz(2.25,46,5,x,y).cut(h.cz(1.5,46,5,x,y)),color=h.GOLD,mass_g=.4))
    # M5x70 partial-thread bolt: require measured smooth bearing land >=47mm.
    # 54mm clamped stack + two1mm washers; nut outside the right plate.
    axle=h.cy(2.5,-28,48).union(h.cy(2.4,20,22)).union(h.cy(4.25,-33,5))
    out.append(Item('elbow M5x70 partial thread bolt',axle,'fore',color=h.SILVER,mass_g=12))
    for y in [-28,27]:out.append(Item('elbow M5 washer '+str(y),washer_y(10,5.3,y,1),'fore',color=h.SILVER,mass_g=.44))
    out.append(Item('elbow M5 locknut',hexnut_y(8,5,28,5),'fore',color=h.SILVER,mass_g=1.5))
    for y,length in [(-23,4),(-14,28),(19,4)]:
        pid='L1-23-ELBOW-BUSH-LONG' if length==28 else 'L1-24-ELBOW-BUSH-SHORT'
        tube=PARTS[pid][0]().rotate((0,0,0),(1,0,0),-90).translate((0,y,0))
        out.append(Item('printed elbow compression sleeve '+str(y),tube,'fore',pid,GREEN))
    for x in [0,ROD]:
        out.append(Item('coupler M3x10 '+str(x),rod_shoulder_screw(x),'rod',color=h.SILVER,mass_g=.7))
        out.append(Item('coupler M3 washer '+str(x),washer_y(7,3.2,-37.5,.5,x),'rod',color=h.SILVER,mass_g=.12))
        out.append(Item('coupler printed bush '+str(x),rod_bush().rotate((0,0,0),(1,0,0),-90).translate((x,-37,0)),'rod','L1-26-ROD-BUSH',GREEN))
    for frame,x in [('crank',CRANK),('fore',-TAIL)]:
        out.append(Item('rod fixed M3L4 insert '+frame,washer_y(4.5,3,ROD_SEAT_Y,4,x),frame,color=h.GOLD,mass_g=.3))
    for a in range(24):
        t=math.tau*a/24
        out.append(Item('ball '+str(a),cq.Workplane('XY').sphere(4).translate((45*math.cos(t),45*math.sin(t),49.8)),color=h.SILVER,mass_g=4/3*math.pi*4**3*.00785))
    return out

def assembly(q=(0,-60,95,-35),grip=-15,rover=False):
    fs=frames(q);out=[]
    for i in local_items(grip):
        s=h.move(i.shape,fs[i.frame])
        if rover:s=s.translate((550,415,66))
        out.append(Item(i.name,s,i.frame,i.part_id,i.color,i.mass_g))
    return out

def print_pose(pid,s):
    if 'BUSH' not in pid and pid!='L1-17-FINGER' and any(t in pid for t in ['UPPER','FORE','COUPLER','CRANK','FINGER','BEARING-CAP']):s=s.rotate((0,0,0),(1,0,0),90)
    b=s.val().BoundingBox()
    return s.translate((-b.xmin,-b.ymin,-b.zmin))

if __name__=='__main__':
    for pid,(fn,n,f) in PARTS.items():
        s=fn();print(pid,'solids',len(s.val().Solids()),'valid',s.val().isValid(),'mass',round(s.val().Volume()*.00124,2),flush=True)
