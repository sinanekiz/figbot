"""AERO V3: supported servo interfaces, offset tubes, downward active wrist.

Digital bench prototype only. Supplied horns, servo calibration, strength and
loaded motion require physical trials. Never export actuator references as prints.
"""
from __future__ import annotations
import csv
import json
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET

import cadquery as cq
import numpy as np
from cad.utils import ROOT, export_shape, shape_mesh
from cad.prototype_arm.build_aero_v2 import _rounded_box as rb, _box as box

OUT=ROOT/'cad/prototype_arm/aero_v3'
UPPER=300.; FORE=220.; SHOULDER_Z=124.
MG=(40.7,19.7,42.9); MICRO=(22.8,12.2,28.5)
BASE=(380.,415.,280.)
ORANGE=(.93,.40,.10); DARK=(.57,.19,.06); METAL=(.65,.69,.73)
BLACK=(.08,.10,.13); GOLD=(.85,.65,.20); GREEN=(.18,.48,.30)
STATUS='DIGITAL BENCH PROTOTYPE; PHYSICAL VALIDATION REQUIRED'

@dataclass(frozen=True)
class Component:
    name:str
    shape:cq.Workplane
    group:str='printed'
    color:tuple=ORANGE
    part_id:str=''

def hole(s,x,y,d=3.4):
    return s.cut(cq.Workplane('XY').center(x,y).circle(d/2).extrude(300,both=True))

def hole_y(s,x,z,d=4.3):
    return s.cut(cq.Workplane('XZ').center(x,z).circle(d/2).extrude(200,both=True))

def cyl_y(r,depth,at=(0,0,0)):
    return cq.Workplane('XZ').circle(r).extrude(depth/2,both=True).translate(at)

def rotate(s,angle,origin=(0,0,0)):
    return s.rotate((0,0,0),(0,1,0),angle).translate(tuple(origin))

def servo_place(s,side=1,origin=(0,0,0)):
    # Local +Z output points inward: +side Y motor -> -side Y shaft.
    return s.rotate((0,0,0),(1,0,0),90*side).translate(origin)

def clamp_points(micro=False):
    x,y,_=MICRO if micro else MG
    return [(-.2*x+sx*(x/2+4),sy*(y/2+5)) for sx in (-1,1) for sy in (-1,1)]

@lru_cache(None)
def servo_case(micro=False):
    x,y,z=MICRO if micro else MG
    case=rb(x,y,z,1.5,(-.2*x,0,-6-z/2))
    flange=rb(x+15 if not micro else x+9,y+1.2,2.4,1.0,(-.2*x,0,-14.8))
    return case.union(flange).union(cq.Workplane('XY').circle(y*.42).extrude(6).translate((0,0,-6)))

@lru_cache(None)
def horn(micro=False):
    r=2.0 if micro else 2.8
    flat=cq.Workplane('XY').circle(10 if not micro else 8).circle(r).extrude(2.5).translate((0,0,3))
    hub=cq.Workplane('XY').circle(r+1.5).circle(r).extrude(4)
    s=flat.union(hub)
    for a in range(0,360,90):
        rr=6 if micro else 8
        s=hole(s,rr*math.cos(math.radians(a)),rr*math.sin(math.radians(a)),2.4)
    return s

@lru_cache(None)
def mount_plate(micro=False):
    x,y,z=MICRO if micro else MG
    s=rb(x+24,y+20,4,3,(-.2*x,0,-18))
    s=s.cut(box(x+.8,y+.8,10,(-.2*x,0,-18)))
    for px,py in clamp_points(micro):s=hole(s,px,py)
    return s

@lru_cache(None)
def clamp_bar(micro=False):
    _,y,_=MICRO if micro else MG
    s=rb(7,y+17,3,1.2,(0,0,1.5))
    for sy in (-1,1):s=hole(s,0,sy*(y/2+5))
    return s

@lru_cache(None)
def yaw_base():
    s=rb(116,110,6,10,(0,0,3))
    s=s.union(mount_plate().translate((0,0,65)))
    for x in (-37,21):
        for y in (-17,17):s=s.union(rb(8,8,41,2,(x,y,25.5)))
    # Plain thrust bearing with replaceable printed washer and radial pilot.
    ring=cq.Workplane('XY').circle(45).circle(35).extrude(4).translate((0,0,69.7))
    s=s.union(ring)
    for x,y in ((43.5,0),(-43.5,0),(0,43.5),(0,-43.5)):
        s=s.union(rb(9,9,64.7,2,(x,y,37.85)))
    for x in (-50,50):
        for y in (-43,43):s=hole(s,x,y,4.5)
    return s

@lru_cache(None)
def thrust_washer():
    return cq.Workplane('XY').circle(44.7).circle(35.3).extrude(.8)

@lru_cache(None)
def yaw_deck():
    s=rb(94,86,6,12,(0,0,77.5))
    s=s.union(cq.Workplane('XY').circle(18).extrude(4).translate((0,0,70.5)))
    s=s.union(cq.Workplane('XY').circle(34.5).circle(30).extrude(4.5).translate((0,0,70)))
    s=hole(s,0,0,6.5)
    for a in range(0,360,90):
        x,y=8*math.cos(math.radians(a)),8*math.sin(math.radians(a))
        s=hole(s,x,y,2.4)
        s=s.cut(cq.Workplane('XY').center(x,y).circle(2.5).extrude(4).translate((0,0,77.5)))
    for x in (-20,20):
        for y in (-14,14):s=hole(s,x,y,4.5)
    return s

def adapter(s,half,micro=False):
    # Adapter faces are normal to Y, exactly touching supplied horn flat faces.
    rr=6 if micro else 8
    for a in range(0,360,90):
        s=hole_y(s,rr*math.cos(math.radians(a)),rr*math.sin(math.radians(a)),2.4)
    return hole_y(s,0,0,6.5 if not micro else 5)

def socket(s,offset,start,end,holes):
    s=s.cut(box(end-start,20.5,20.5,((start+end)/2,offset,0)))
    for x in holes:s=hole(s,x,offset,4.5)
    return s

@lru_cache(None)
def link_hub(fore=False):
    offset=18 if fore else -18
    # Two light end discs with a central torsion sleeve, not a solid block.
    s=cyl_y(21,4,(0,-14,0)).union(cyl_y(21,4,(0,14,0)))
    s=s.union(cyl_y(16,24).cut(cyl_y(11,30)))
    s=s.union(rb(38,27,27,4,(53,offset,0),long_axis='X'))
    s=s.union(box(32,26,18,(26,13 if fore else -13,0)))
    s=socket(s,offset,31,76,(44,59))
    s=adapter(s,16)
    if fore:
        # Opposite side supported by M4 shoulder-bolt style shank/bushing.
        s=s.union(cyl_y(6,20.3,(0,-26.15,0)))
        s=hole_y(s,0,0,4.3)
        s=nut_trap(s,-36.3)
    return s

@lru_cache(None)
def yoke(kind='shoulder'):
    micro=kind=='wrist'
    origin=17.5 if micro else 21.5
    x,y,_=MICRO if micro else MG
    p=servo_place(mount_plate(micro),1,(0,origin,0))
    if kind=='shoulder':
        p=p.union(servo_place(mount_plate(),-1,(0,-origin,0)))
        base=rb(86,83,6,6,(-5,0,80.5-SHOULDER_Z+3))
        for bx in (-20,20):
            for by in (-14,14):base=hole(base,bx,by,4.5)
        for bx in (-35,25):
            for by in (-39.5,39.5):
                p=p.union(rb(7,4,28,1.5,(bx,by,-28)))
        p=p.union(base)
    else:
        half=origin+18
        passive=rb(x+24,4,y+20,3,(-.2*x,-half,0),long_axis='Y')
        passive=hole_y(passive,0,0,6.4)
        p=p.union(passive)
        offset=18 if micro else -18
        rear=(-50,-26) if micro else (-70,-30)
        p=p.union(rb(rear[1]-rear[0],27,27,4,((rear[0]+rear[1])/2,offset,0),long_axis='X'))
        bridge_x=-31 if micro else -44
        if micro:
            p=p.union(box(10,2*half+4,26,(bridge_x,0,0)))
        else:
            # Folded forearm passes BELOW this cross bridge, in the +18 mm lane.
            p=p.union(box(10,27,8,(bridge_x,offset,15)))
            p=p.union(box(10,2*half+4,8,(bridge_x,0,20)))
        # Bridge touches rear edges of the plate without crossing motor cavity.
        p=socket(p,offset,rear[0]-5,rear[1]-1,(-43,-34) if micro else (-57,-42))
    return p

@lru_cache(None)
def wrist_rotor():
    # Separate drive plate allows horn screws to be installed from behind.
    # Internal cavity keeps their heads clear once the palm is attached.
    s=cyl_y(18,16).cut(cyl_y(11,12,(0,2,0)))
    s=s.union(cyl_y(6,24.3,(0,-20.15,0)))
    # Back spine and fixed jaw are kept clear of the moving jaw plane.
    spine=rb(82,4,34,3,(0,5,-27),long_axis='Y')
    s=s.union(spine).union(box(18,12,13,(0,2,-12)))
    fixed=cq.Workplane('XZ').polyline([(-37,-21),(-27,-21),(-27,-54),(-21,-83),(-21,-95),(-28,-95),(-36,-57)]).close().extrude(5,both=True)
    s=s.union(fixed).union(box(16,10,9,(-29,6,-25)))
    # G1 mount is behind the palm; no jaw/plate overlap.
    grip_mount=servo_place(mount_plate(True),1,(20,14.5,-40))
    s=s.union(grip_mount)
    for px in (-9,39):
        s=s.union(box(6,29.5,8,(px,20.25,-40)))
    s=s.cut(cyl_y(12,24,(20,10,-40)))
    s=hole_y(s,0,0,4.3)
    for x in (-14,14):s=hole_y(s,x,0,3.4)
    return nut_trap(s,-32.3)

def wrist_drive_plate():
    s=adapter(cyl_y(18,4,(0,10,0)),12,True)
    for x in (-14,14):s=hole_y(s,x,0,3.4)
    return s

def nut_trap(s,face_y):
    # Side-load M4 hex nut; 0.2 mm nominal radial clearance. Accessible from +X.
    cavity=cq.Workplane('XZ').polygon(6,8.5).extrude(1.8,both=True).translate((0,face_y+4.3,0))
    access=box(10,3.6,7.5,(5,face_y+4.3,0))
    return s.cut(cavity.union(access))

def pivot_sleeve():
    return cq.Workplane('XY').circle(3).circle(2.15).extrude(6)

def pivot_washer():
    return cq.Workplane('XY').circle(5).circle(3.2).extrude(.8)

@lru_cache(None)
def moving_jaw():
    # Local pivot origin. Gentle concavity, one direct driven moving finger.
    profile=[(-9,2),(8,5),(11,-17),(16,-29),(16,-50),(12,-55),(8,-52),(8,-34),(1,-21),(-6,-12)]
    s=cq.Workplane('XZ').polyline(profile).close().extrude(2.5,both=True)
    s=s.union(cyl_y(10,4,(0,7,0)))
    s=s.union(cyl_y(10,2.5,(0,3.75,0)))
    # Active face Y=9 mates with horn at Y=9..11.5.
    s=adapter(s,9,True)
    return s

def tube(length,offset,holes):
    s=cq.Workplane('YZ').rect(20,20).rect(17,17).extrude(length)
    s=s.translate((32,offset,0))
    for x in holes:s=hole(s,x,offset,4.5)
    return s

PRINT_PARTS={
 'V3-01-YAW-BASE':(yaw_base,1),
 'V3-02-YAW-DECK':(yaw_deck,1),
 'V3-03-THRUST-WASHER':(thrust_washer,1),
 'V3-04-SHOULDER-YOKE':(lambda:yoke('shoulder'),1),
 'V3-05-UPPER-HUB':(lambda:link_hub(False),1),
 'V3-06-ELBOW-YOKE':(lambda:yoke('elbow'),1),
 'V3-07-FORE-HUB':(lambda:link_hub(True),1),
 'V3-08-WRIST-YOKE':(lambda:yoke('wrist'),1),
 'V3-09-WRIST-PALM-FIXED-JAW':(wrist_rotor,1),
 'V3-10-MOVING-JAW':(moving_jaw,1),
 'V3-11-MG996R-CLAMP':(lambda:clamp_bar(False),8),
 'V3-12-MG90S-CLAMP':(lambda:clamp_bar(True),4),
 'V3-13-IDLER-SLEEVE':(pivot_sleeve,2),
 'V3-14-IDLER-THRUST-WASHER':(pivot_washer,4),
 'V3-15-WRIST-DRIVE-PLATE':(wrist_drive_plate,1),
}

def ik(target,base=BASE):
    dx,dy=target[0]-base[0],target[1]-base[1]
    r=math.hypot(dx,dy);down=base[2]+SHOULDER_Z-target[2]
    c=(r*r+down*down-UPPER**2-FORE**2)/(2*UPPER*FORE)
    if abs(c)>1:raise ValueError('Wrist target outside reach')
    beta=math.acos(c)
    alpha=math.atan2(down,r)-math.atan2(FORE*math.sin(beta),UPPER+FORE*math.cos(beta))
    return math.degrees(math.atan2(dy,dx)),math.degrees(alpha),math.degrees(alpha+beta)

TARGETS={'pickup':(650.,415.,102.),'lift':(650.,415.,450.),'release':(400.,275.,460.)}

def assembly(pose=(0.,18.,95.),grip=5.,base=(0.,0.,0.)):
    yaw,upper,fore=pose
    shoulder=np.array((0.,0.,SHOULDER_Z))
    elbow=shoulder+np.array((UPPER*math.cos(math.radians(upper)),0.,-UPPER*math.sin(math.radians(upper))))
    wrist=elbow+np.array((FORE*math.cos(math.radians(fore)),0.,-FORE*math.sin(math.radians(fore))))
    result=[]
    def add(name,s,group='printed',color=ORANGE,part_id='',angle=0.,at=(0,0,0),stationary=False):
        shape=rotate(s,angle,at)
        if not stationary:shape=shape.rotate((0,0,0),(0,0,1),yaw)
        result.append(Component(name,shape.translate(base),group,color,part_id))
    def actuator(name,micro,side,origin,angle=0.,at=(0,0,0),stationary=False,vertical=False,drive=None):
        place=(lambda s:s.translate(origin)) if vertical else (lambda s:servo_place(s,side,origin))
        add(name+' case',place(servo_case(micro)),'servo',BLACK,angle=angle,at=at,stationary=stationary)
        shaft=cq.Workplane('XY').circle(2.0 if micro else 2.8).extrude(5)
        add(name+' shaft',place(shaft),'shaft',METAL,angle=angle,at=at,stationary=stationary)
        add(name+' supplied horn',place(horn(micro)),'horn',GOLD,angle=angle if drive is None else drive,at=at,stationary=stationary and not vertical)
        x,_,_=MICRO if micro else MG
        for sx in (-1,1):
            clamp=clamp_bar(micro).translate((-.2*x+sx*(x/2+4),0,-13.6))
            add(name+f' clamp {sx}',place(clamp),'printed',DARK,'V3-12-MG90S-CLAMP' if micro else 'V3-11-MG996R-CLAMP',angle,at,stationary)
    def idler(name,outer_y,angle,at):
        # Sleeve clamps to rotating hub; its OD journals in the fixed 6.4 bore.
        s=pivot_sleeve().rotate((0,0,0),(1,0,0),-90).translate((0,outer_y-.8,0))
        add(name+' sleeve',s,part_id='V3-13-IDLER-SLEEVE',angle=angle,at=at)
        for i,y in enumerate((outer_y-.8,outer_y+4)):
            w=pivot_washer().rotate((0,0,0),(1,0,0),-90).translate((0,y,0))
            add(name+f' thrust washer {i}',w,part_id='V3-14-IDLER-THRUST-WASHER',angle=angle,at=at)
        shaft=cyl_y(2,12,(0,outer_y+5.2,0))
        head=cyl_y(3.5,2.8,(0,outer_y-2.2,0))
        add(name+' M4x12 axle bolt',shaft.union(head),'hardware',METAL,angle=angle,at=at)
        nut=cq.Workplane('XZ').polygon(6,8.08).circle(2.1).extrude(1.6,both=True).translate((0,outer_y+9.5,0))
        add(name+' M4 captive nut',nut,'hardware',METAL,angle=angle,at=at)
    add('yaw base',yaw_base(),part_id='V3-01-YAW-BASE',stationary=True)
    add('yaw thrust washer',thrust_washer().translate((0,0,73.7)),part_id='V3-03-THRUST-WASHER',stationary=True)
    add('yaw deck',yaw_deck(),part_id='V3-02-YAW-DECK')
    actuator('J1',False,1,(0,0,65),stationary=True,vertical=True)
    add('shoulder yoke',yoke('shoulder'),part_id='V3-04-SHOULDER-YOKE',at=shoulder)
    for side in (-1,1):actuator('J2 '+str(side),False,side,(0,side*21.5,0),at=shoulder,drive=upper)
    add('upper hub',link_hub(),part_id='V3-05-UPPER-HUB',angle=upper,at=shoulder)
    add('upper hollow tube',tube(UPPER-65,-18,(44,59,UPPER-57,UPPER-42)),'tube',METAL,angle=upper,at=shoulder)
    add('elbow yoke',yoke('elbow'),part_id='V3-06-ELBOW-YOKE',angle=upper,at=elbow)
    actuator('J3',False,1,(0,21.5,0),angle=upper,at=elbow,drive=fore)
    add('fore hub',link_hub(True),part_id='V3-07-FORE-HUB',angle=fore,at=elbow)
    idler('J3',-41.5,fore,elbow)
    add('fore hollow tube',tube(FORE-59,18,(44,59,FORE-43,FORE-34)),'tube',METAL,angle=fore,at=elbow)
    add('wrist yoke',yoke('wrist'),part_id='V3-08-WRIST-YOKE',angle=fore,at=wrist)
    actuator('W1',True,1,(0,17.5,0),angle=fore,at=wrist,drive=0.)
    # Wrist relative pitch is -fore. Palm orientation remains world-downward.
    add('wrist palm fixed jaw',wrist_rotor(),part_id='V3-09-WRIST-PALM-FIXED-JAW',at=wrist)
    add('wrist drive plate',wrist_drive_plate(),part_id='V3-15-WRIST-DRIVE-PLATE',at=wrist)
    for x in (-14,14):
        bolt=cyl_y(1.5,30,(x,-2.5,0)).union(cyl_y(2.8,3,(x,14,0)))
        add('wrist M3x30 joining bolt '+str(x),bolt,'hardware',METAL,at=wrist)
        for y in (-8.25,12.25):
            washer=cyl_y(3.5,.5,(x,y,0)).cut(cyl_y(1.6,2,(x,y,0)))
            add('wrist M3 washer '+str((x,y)),washer,'hardware',METAL,at=wrist)
        nut=cq.Workplane('XZ').polygon(6,6.35).circle(1.6).extrude(2,both=True).translate((x,-10.5,0))
        add('wrist M3 locking nut '+str(x),nut,'hardware',METAL,at=wrist)
    idler('W1',-37.5,0.,wrist)
    actuator('G1',True,1,(0,14.5,0),at=wrist+np.array((20,0,-40)),drive=grip)
    add('moving jaw',moving_jaw(),part_id='V3-10-MOVING-JAW',angle=grip,at=wrist+np.array((20,0,-40)))
    add('fixed soft pad',box(3,12,12,(-19.5,0,-89)),'pad',GREEN,at=wrist)
    add('moving soft pad',box(3,12,12,(6.5,0,-43)),'pad',GREEN,angle=grip,at=wrist+np.array((20,0,-40)))
    return result

if __name__=='__main__':
    print('Geometry module; use cad.prototype_arm.export_aero_v3 to build audited outputs.')
