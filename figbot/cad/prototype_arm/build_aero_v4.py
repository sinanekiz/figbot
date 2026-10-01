"""AERO V4 pin-and-socket bench arm; preserves the physically tried horn parts.

Printed locking pins substitute optional assembly screws for initial low-load
trials. Original servo centre screws remain mandatory. No strength certification.
"""
from dataclasses import dataclass
from functools import lru_cache
import math
import cadquery as cq
import numpy as np
from cad.utils import ROOT
from cad.prototype_arm import build_aero_v3 as old
from cad.prototype_arm import build_snap02 as large
from cad.prototype_arm import build_snap03_mg90 as small

OUT=ROOT/'cad/prototype_arm/aero_v4'
UPPER=300.; FORE=220.; SHOULDER_Z=124.
BLUE=(.10,.51,.62); LIGHT=(.24,.68,.74); GOLD=(.94,.56,.18)
DARK=(.17,.20,.24); PURPLE=(.56,.40,.71)
box=old.box

def cyl_y(r,h,c=(0,0,0)):return old.cyl_y(r,h,c)
def hole_z(s,x,y,d=3.4):return old.hole(s,x,y,d)
def hole_y(s,x,z,d=3.4):return old.hole_y(s,x,z,d)

def basis(tangent=(1,0,0),normal=(0,1,0),at=(0,0,0)):
    y=np.array(tangent,dtype=float);z=np.array(normal,dtype=float)
    x=np.cross(y,z);assert np.allclose(np.linalg.norm(x),1)
    t=np.eye(4);t[:3,:3]=np.stack([x,y,z],axis=1);t[:3,3]=at
    return t

def transform(s,t):
    # OCC rigid transform, not a geometry-changing affine mesh transform.
    from OCP.gp import gp_Trsf
    g=gp_Trsf();g.SetValues(*[float(x) for x in t[:3].ravel()])
    return s.newObject([s.val().moved(cq.Location(g))])

def ry(q,at=(0,0,0)):
    a=math.radians(q);t=np.eye(4)
    t[:3,:3]=[[math.cos(a),0,math.sin(a)],[0,1,0],[-math.sin(a),0,math.cos(a)]]
    t[:3,3]=at;return t

def rz(q):
    a=math.radians(q);t=np.eye(4)
    t[:3,:3]=[[math.cos(a),-math.sin(a),0],[math.sin(a),math.cos(a),0],[0,0,1]]
    return t

def motor_pose(micro=False,side=1,at=(0,0,0),vertical=False):
    if vertical:t=np.eye(4);t[:3,3]=at;return t
    # Same local servo convention as AERO V3.
    a=math.radians(90*side);t=np.eye(4)
    t[:3,:3]=[[1,0,0],[0,math.cos(a),-math.sin(a)],[0,math.sin(a),math.cos(a)]]
    t[:3,3]=at;return t

def horn_pose(micro=False,side=1,down=False,at=None):
    return basis((0,0,-1) if down else (1,0,0),(0,side,0),
                 at if at is not None else (0,side*(10 if micro else 16),0))

@lru_cache(None)
def receiver(micro=False):
    w,end,thick,top,bottom,holes=(12,44,2.4,4.5,-1.8,[30,38]) if micro else (18,52,3,5.2,-2,[34,44])
    # Open toward the horn; tip stops against the far end wall.
    s=box(w+4.4,end+2.3-23.5,top-bottom,(0,(end+2.3+23.5)/2,(top+bottom)/2))
    s=s.cut(box(w+.4,end+.3-23.3,thick+.4,(0,(end+.3+23.3)/2,thick/2)))
    for y in holes:s=hole_z(s,0,y)
    return s

@lru_cache(None)
def locking_pin(grip=7.4,diam=3.05):
    head=1.6;r=diam/2;barb=r+.325
    s=cq.Workplane('XY').circle(r+1.5).extrude(head)
    s=s.union(cq.Workplane('XY').circle(r).extrude(grip).translate((0,0,head)))
    nose=cq.Workplane('XY').workplane(offset=head+grip).circle(barb).workplane(offset=1.2).circle(r-.25).loft()
    s=s.union(nose)
    start=head+max(1.,grip-11.)
    s=s.cut(box(.8,2*barb+2,head+grip+1.3-start,(0,0,(head+grip+1.3+start)/2)))
    return s

def pin_at(grip,diam,underside,axis=(0,0,-1)):
    n=np.array(axis,dtype=float);tangent=(1,0,0) if abs(n[0])<.5 else (0,1,0)
    return transform(locking_pin(grip,diam),basis(tangent,n,np.array(underside)-1.6*n))

def sleeve_pins(micro=False):
    return [pin_at(6.5 if micro else 7.4,3.05,(0,y,4.5 if micro else 5.2)) for y in ([30,38] if micro else [34,44])]

def clear_receiver(s,t,micro=False):
    w,end,thick,holes=(12,44,2.4,[30,38]) if micro else (18,52,3,[34,44])
    cavity=box(w+.4,end+.3-23.3,thick+.4,(0,(end+.3+23.3)/2,thick/2))
    s=s.cut(transform(cavity,t))
    for y in holes:
        bore=cq.Workplane('XY').center(0,y).circle(1.7).extrude(30,both=True)
        s=s.cut(transform(bore,t))
        bottom=-1.8 if micro else -2
        nutroom=cq.Workplane('XY').center(0,y).circle(3.4).extrude(6).translate((0,0,bottom-6))
        s=s.cut(transform(nutroom,t))
    return s

def clear_port(s,x0,x1,offset,closed_end,holes):
    aa,bb=(x0+2,x1+1) if closed_end=='left' else (x0-1,x1-2)
    s=s.cut(box(bb-aa,20.5,20.5,((aa+bb)/2,offset,0)))
    for x in holes:
        s=hole_z(s,x,offset)
        headroom=cq.Workplane('XY').center(x,offset).circle(3.3).extrude(70).translate((0,0,13))
        s=s.cut(headroom)
    return s

def port(x0,x1,offset,closed_end,holes):
    s=box(x1-x0,26,26,((x0+x1)/2,offset,0))
    # 0.25 mm clearance per side around the nominal20 mm beam.
    a,b=(x0+2,x1+1) if closed_end=='left' else (x0-1,x1-2)
    s=s.cut(box(b-a,20.5,20.5,((a+b)/2,offset,0)))
    for x in holes:s=hole_z(s,x,offset)
    return s

@lru_cache(None)
def base():
    s=old.rb(116,110,6,10,(0,0,3))
    s=s.union(old.mount_plate().translate((0,0,58)))
    for x in [-37,21]:
        for y in [-17,17]:s=s.union(old.rb(8,8,34,2,(x,y,22)))
    ring=cq.Workplane('XY').circle(45).circle(35).extrude(4).translate((0,0,69.7))
    s=s.union(ring)
    for x in [-48,48]:
        for y in [-45,45]:
            s=s.union(old.rb(8,8,64.7,2,(x,y,37.85)))
            theta=math.degrees(math.atan2(y,x))
            bridge=box(30,8,4,(53.8,0,71.7)).rotate((0,0,0),(0,0,1),theta)
            s=s.union(bridge)
    for x,y in old.clamp_points():
        relief=cq.Workplane('XY').center(x,y).circle(3.3).extrude(32).translate((0,0,6))
        s=hole_z(s.cut(relief),x,y)
    for x in [-50,50]:
        for y in [-43,43]:s=hole_z(s,x,y,4.5)
        s=hole_z(s,x,0,4.5)
    return s

YAW_HORN=basis((1,0,0),(0,0,-1),(0,0,65))

@lru_cache(None)
def shoulder_deck():
    s=old.rb(100,96,4,8,(0,0,76.5))
    s=s.cut(cq.Workplane('XY').circle(5).extrude(100))
    pilot=cq.Workplane('XY').circle(34.5).circle(30).extrude(4.5).translate((0,0,70))
    s=s.union(pilot).union(transform(receiver(),YAW_HORN))
    s=s.union(box(6,22.4,8,(26.5,0,70.8)))
    for side in [-1,1]:
        for x in [-38,22]:
            socket=box(14,12,12,(x,side*39,84.5))
            socket=socket.cut(box(8.4,6.4,11,(x,side*39,86)))
            socket=hole_y(socket,x,85.5)
            s=s.union(socket)
    return clear_receiver(s,YAW_HORN)

@lru_cache(None)
def shoulder_tower():
    # Right tower; opposite side mirrored across XZ, not rotated around Z.
    s=transform(old.mount_plate(),motor_pose(False,1,(0,23,124)))
    s=s.union(box(70,10,4,(-8,39,92.5)))
    for x in [-38,22]:
        s=s.union(box(6,4,15,(x,39,101.5)))
        peg=box(8,6,9.8,(x,39,85.6));peg=hole_y(peg,x,85.5)
        s=s.union(peg)
    return s

@lru_cache(None)
def upper_carrier():
    s=transform(receiver(),horn_pose(side=-1)).union(transform(receiver(),horn_pose(side=1)))
    s=s.union(box(10,39.2,18,(52,0,0)))
    s=s.union(box(15,26,18,(60.5,-18,0)))
    s=s.union(port(60,92,-18,'left',[75,85]))
    for side in [-1,1]:s=clear_receiver(s,horn_pose(side=side))
    return clear_port(s,60,92,-18,'left',[75,85])

@lru_cache(None)
def fore_carrier():
    s=transform(receiver(),horn_pose())
    s=s.union(cyl_y(11,10,(0,-32.6,0)))
    s=s.union(box(51,10,16,(25.5,-32.6,0)))
    s=s.union(box(10,54.6,18,(52,-7.3,0)))
    s=s.union(box(15,26,18,(60.5,18,0)))
    s=s.union(port(60,92,18,'left',[75,85]))
    s=clear_receiver(s,horn_pose())
    s=clear_port(s,60,92,18,'left',[75,85])
    return hole_y(s,0,0,6.4)

@lru_cache(None)
def stator_yoke(micro=False):
    origin=15.75 if micro else 23
    passive=-30 if micro else -40
    x,y,_=old.MICRO if micro else old.MG
    s=transform(old.mount_plate(micro),motor_pose(micro,1,(0,origin,0)))
    p=old.rb(x+24,4,y+20,3,(-.2*x,passive,0),long_axis='Y')
    s=s.union(hole_y(p,0,0,6.4))
    bridge=-32.5 if micro else -44
    outer=origin+20
    s=s.union(box(10,outer-passive+2,8,(bridge,(outer+passive-2)/2,10)))
    if micro:return clear_port(s.union(port(-55,-27,18,'right',[-47,-37])),-55,-27,18,'right',[-47,-37])
    return clear_port(s.union(port(-65,-31,-18,'right',[-53,-43])),-65,-31,-18,'right',[-53,-43])

@lru_cache(None)
def beam(fore=False):
    # Local X0 corresponds to assembled X62.2; all four pin stations reinforced.
    length=128.6 if fore else 204.6
    holes=[12.8,22.8,110.8,120.8] if fore else [12.8,22.8,184.8,194.8]
    s=cq.Workplane('YZ').rect(20,20).rect(16,16).extrude(length)
    for x in holes:
        boss=cq.Workplane('XY').center(x,0).circle(3.4).extrude(20).translate((0,0,-10))
        s=s.union(boss);s=hole_z(s,x,0)
    return s

WRIST_HORN=horn_pose(True,down=True)
GRIP_HORN=horn_pose(True,down=True)

@lru_cache(None)
def palm():
    s=transform(receiver(True),WRIST_HORN)
    s=s.union(cyl_y(11,10,(0,-22.6,0)))
    s=s.union(box(10,10,35,(0,-22.6,-17.5)))
    s=s.union(box(12,24.6,10,(0,-12.3,-32)))
    s=s.union(old.rb(85,4,49,3,(7.5,-2,-51.5),long_axis='Y'))
    for x in [-6.2,6.2]:s=s.union(box(4,10,15,(x,4,-36)))
    # Fixed finger and MG90 stator are carried by the same continuous palm.
    outline=[(-35,-34),(-25,-34),(-25,-98),(-19,-122),(-19,-134),(-27,-134),(-35,-100)]
    f=cq.Workplane('XZ').polyline(outline).close().extrude(4,both=True).translate((0,10,0))
    s=s.union(f).union(box(12,16,16,(-30,4,-43)))
    s=s.union(transform(old.mount_plate(True),motor_pose(True,1,(30,15.75,-66))))
    # The whole proven capsule rotates, not only the little finger: keep stator
    # supports outside its swept rectangle and bridge back at the motor flange.
    s=s.union(box(14,4,10,(55,-2,-66)))
    s=s.union(box(10,4,10,(1,31.75,-66)))
    s=s.union(box(16,4,10,(54,31.75,-66)))
    for x in [-2,60]:s=s.union(box(4,34,10,(x,16,-66)))
    return hole_y(hole_y(s,0,0,6.4),30,-66,8)

@lru_cache(None)
def moving_finger():
    s=transform(receiver(True),GRIP_HORN)
    outline=[(-7,-43),(7,-43),(7,-51),(-4,-66),(-6,-68),(-12,-68),(-14,-61),(-3,-48)]
    f=cq.Workplane('XZ').polyline(outline).close().extrude(4,both=True).translate((0,10,0))
    return clear_receiver(s.union(f),GRIP_HORN,True)

PARTS={
 'A4-01-BASE':(base,1),
 'A4-02-SHOULDER-DECK':(shoulder_deck,1),
 'A4-03-YAW-WASHER':(old.thrust_washer,1),
 'A4-04-UPPER-CARRIER':(upper_carrier,1),
 'A4-05-UPPER-BEAM':(lambda:beam(False),1),
 'A4-06-ELBOW-YOKE':(lambda:stator_yoke(False),1),
 'A4-07-FORE-CARRIER':(fore_carrier,1),
 'A4-08-FORE-BEAM':(lambda:beam(True),1),
 'A4-09-WRIST-YOKE':(lambda:stator_yoke(True),1),
 'A4-10-PALM-FIXED-FINGER':(palm,1),
 'A4-11-MOVING-FINGER':(moving_finger,1),
 'A4-12-MG996-CLAMP':(lambda:old.clamp_bar(False),8),
 'A4-13-MG90-CLAMP':(lambda:old.clamp_bar(True),4),
 'A4-14-SHOULDER-TOWER-R':(shoulder_tower,1),
 'A4-15-SHOULDER-TOWER-L':(lambda:shoulder_tower().mirror('XZ'),1),
 'A4-P1-COUPLER-LARGE':(lambda:locking_pin(7.4),8),
 'A4-P2-COUPLER-MICRO':(lambda:locking_pin(6.5),4),
 'A4-P3-MOTOR-CLAMP':(lambda:locking_pin(9.6),24),
 'A4-P4-BEAM-LOCK':(lambda:locking_pin(26.2),8),
 'A4-P5-PIVOT-AXLE':(lambda:locking_pin(14.6,6),2),
 'A4-P6-TOWER-LOCK':(lambda:locking_pin(12.2),4),
}

@dataclass
class Item:
    name:str
    shape:cq.Workplane
    frame:str
    part_id:str=''
    group:str='printed'
    color:tuple=BLUE

@lru_cache(None)
def local_items():
    a=[]
    def add(name,s,frame,pid='',group='printed',color=BLUE):a.append(Item(name,s,frame,pid,group,color))
    def part(pid,frame,at=(0,0,0)):
        add(pid,PARTS[pid][0]().translate(at),frame,pid)
    def motor(name,micro,t,frame):
        add(name+' case',transform(old.servo_case(micro),t),frame,group='servo',color=DARK)
        x,y,_=old.MICRO if micro else old.MG
        pid='A4-13-MG90-CLAMP' if micro else 'A4-12-MG996-CLAMP'
        for side in [-1,1]:
            px=-.2*x+side*(x/2+4)
            add(name+' clamp '+str(side),transform(old.clamp_bar(micro).translate((px,0,-13.6)),t),frame,pid,color=LIGHT)
            for sy in [-1,1]:
                s=pin_at(9.6,3.05,(px,sy*(y/2+5),-10.6))
                add(name+f' clamp pin {side} {sy}',transform(s,t),frame,'A4-P3-MOTOR-CLAMP',color=GOLD)
    def coupling(name,micro,t,frame):
        mod=small if micro else large;b,c=mod.build()
        add(name+' fitted body',transform(b,t),frame,'S03_01_MG90_GOVDE' if micro else 'S02_01_YILDIZ_GOVDE',color=LIGHT)
        for i,lid in enumerate(mod.caps_pose(c)):
            add(name+' cover '+str(i),transform(lid,t),frame,'S03_02_MG90_KAPAK' if micro else 'S02_02_YARIM_KAPAK',color=PURPLE)
        add(name+' original horn',transform(mod.horn_envelope(),t),frame,group='horn',color=DARK)
        for i,p in enumerate(sleeve_pins(micro)):
            add(name+' sleeve pin '+str(i),transform(p,t),frame,'A4-P2-COUPLER-MICRO' if micro else 'A4-P1-COUPLER-LARGE',color=GOLD)
    part('A4-01-BASE','base');part('A4-03-YAW-WASHER','base',(0,0,73.7))
    motor('J1',False,motor_pose(at=(0,0,58),vertical=True),'base')
    part('A4-02-SHOULDER-DECK','yaw');coupling('J1',False,YAW_HORN,'yaw')
    part('A4-14-SHOULDER-TOWER-R','yaw');part('A4-15-SHOULDER-TOWER-L','yaw')
    for side in [-1,1]:
        for x in [-38,22]:
            add(f'tower pin {side} {x}',pin_at(12.2,3.05,(x,side*45,85.5),(0,-side,0)),
                'yaw','A4-P6-TOWER-LOCK',color=GOLD)
    for side in [-1,1]:
        motor('J2 '+str(side),False,motor_pose(False,side,(0,side*23,124)),'yaw')
        coupling('J2 '+str(side),False,horn_pose(side=side),'upper')
    part('A4-04-UPPER-CARRIER','upper');part('A4-05-UPPER-BEAM','upper',(62.2,-18,0))
    part('A4-06-ELBOW-YOKE','upper',(300,0,0))
    motor('J3',False,motor_pose(False,1,(300,23,0)),'upper')
    part('A4-07-FORE-CARRIER','fore');coupling('J3',False,horn_pose(),'fore')
    part('A4-08-FORE-BEAM','fore',(62.2,18,0));part('A4-09-WRIST-YOKE','fore',(220,0,0))
    motor('W1',True,motor_pose(True,1,(220,15.75,0)),'fore')
    part('A4-10-PALM-FIXED-FINGER','tool');coupling('W1',True,WRIST_HORN,'tool')
    motor('G1',True,motor_pose(True,1,(30,15.75,-66)),'tool')
    part('A4-11-MOVING-FINGER','finger');coupling('G1',True,GRIP_HORN,'finger')
    for frame,xs,y in [('upper',[75,85,247,257],-18),('fore',[75,85,173,183],18)]:
        for x in xs:add(frame+' beam pin '+str(x),pin_at(26.2,3.05,(x,y,13)),frame,'A4-P4-BEAM-LOCK',color=GOLD)
    for frame,y in [('fore',-42),('tool',-32)]:
        add(frame+' passive axle',pin_at(14.6,6,(0,y,0),(0,1,0)),frame,'A4-P5-PIVOT-AXLE',color=GOLD)
    return a

def frames(q=(0,-35,75,-40,0)):
    yaw,shoulder,elbow,wrist,grip=q
    f={'base':np.eye(4),'yaw':rz(yaw)}
    f['upper']=f['yaw']@ry(shoulder,(0,0,SHOULDER_Z))
    f['fore']=f['upper']@ry(elbow,(UPPER,0,0))
    f['tool']=f['fore']@ry(wrist,(FORE,0,0))
    f['finger']=f['tool']@ry(grip,(30,0,-66))
    return f

def assembly(q=(0,-35,75,-40,0)):
    fs=frames(q)
    return [Item(x.name,transform(x.shape,fs[x.frame]),x.frame,x.part_id,x.group,x.color) for x in local_items()]
