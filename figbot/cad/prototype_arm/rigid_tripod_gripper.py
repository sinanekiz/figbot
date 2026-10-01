"""DEC-084: single pinion/rack, three positively driven rigid scoop fingers.

Prototype in millimetres. No tendon, no printed spline, no certified load.
Local Z points toward fruit; local XY is the palm plane.
"""
from functools import lru_cache
import math
import numpy as np
import cadquery as cq
from cad.prototype_arm import build_linka_v1 as a, geared_gripper as gg
from cad.prototype_arm import build_forma_v6 as h

REVISION='UC SERT KEPCE / DEC-084 / PROTOTIP'
PIVOT=28.; CRANK=12.; LINK=24.; SR=8.; OPEN=35.; WALL=1.2
TEETH=28; GEAR_R=gg.M*TEETH/2
PX=-6-GEAR_R; PZ=-28.; MOTOR_Y=-15.; TOOL_X=52.
PITCH=math.pi*gg.M

def state(deg):
    t=math.radians(deg)
    c=np.array([PIVOT-CRANK*math.cos(t),0.,CRANK*math.sin(t)])
    dz=math.sqrt(LINK**2-(c[0]-SR)**2)
    s=np.array([SR,0.,c[2]-dz])
    return dict(crank=c,slider=s,link_angle=math.degrees(math.atan2(-(c[2]-s[2]),c[0]-s[0])),
                gear_deg=-math.degrees((s[2]-state_zero())/GEAR_R))

def state_zero():return -math.sqrt(LINK**2-(PIVOT-CRANK-SR)**2)
def radial(shape,phi):return shape.rotate((0,0,0),(0,0,1),phi)
def motor_place(shape):return shape.rotate((0,0,0),(1,0,0),-90).translate((PX,MOTOR_Y,PZ))
def bore_y(shape,x,z,r,start=-4,length=8):return shape.cut(h.cy(r,start,length,x,z))

def boss_hole(shape,x,z):
    # Same part accepts a3mm insert from either face; installation side is explicit.
    return bore_y(shape,x,z,1.45,-2.85,5.7)

@lru_cache(None)
def scoop():
    wires=[]
    for z,r,half in [(12,28,8),(20,29,55),(32,24,57),(43,15,55),(50,4,45)]:
        t=math.radians(half);ri=r-WALL
        wires.append(cq.Workplane('XY',origin=(0,0,z)).moveTo(r*math.cos(t),-r*math.sin(t))
          .threePointArc((r,0),(r*math.cos(t),r*math.sin(t))).lineTo(ri*math.cos(t),ri*math.sin(t))
          .threePointArc((ri,0),(ri*math.cos(t),-ri*math.sin(t))).close().val())
    return cq.Workplane(obj=cq.Solid.makeLoft(wires,ruled=True))

@lru_cache(None)
def finger():
    # Integral inward crank; filleted/circular roots, thin distal scoop.
    s=a.capsule(CRANK,8,0,5.5).translate((PIVOT-CRANK,0,0))
    stem=a.plate([(24,0),(32,0),(31,14),(26,17),(24,12)],0,5.5)
    s=s.union(stem).union(scoop())
    s=bore_y(s,PIVOT,0,2.55)
    return boss_hole(s,PIVOT-CRANK,0)

def finger_at(deg):return finger().rotate((PIVOT,0,0),(PIVOT,1,0),deg)

@lru_cache(None)
def link():
    s=a.capsule(LINK,7,4.3,2.5)
    for x in [0,LINK]:s=bore_y(s,x,0,2.15,2.8,3.2)
    return s

@lru_cache(None)
def joint_bush():return a.plain_bush(4.,2.3,3.1)

@lru_cache(None)
def rack_slider():
    # Rack pitch plane X=-6; teeth face -X, guide lands on +X and both Y sides.
    z0=state_zero();s=h.box(8.9375,4,34,(.03125,0,-10))
    s=s.union(h.box(2.5,9,21,(3.25,0,-16.5)))
    # Tooth positions mesh with the pinion's right-hand tooth space at q=0.
    w=PITCH/2-.15;tan=math.tan(gg.ALPHA)
    for k in range(-7,7):
        z=PZ-z0+(k+.5)*PITCH
        if -20<z<4:
            poly=[(-4.4375,z-(w/2+1.5625*tan)),(-7.25,z-(w/2-1.25*tan)),
                  (-7.25,z+(w/2-1.25*tan)),(-4.4375,z+(w/2+1.5625*tan))]
            s=s.union(a.plate(poly,0,4))
    s=s.union(h.cz(5,-3,6))
    for phi in [0,120,240]:
        tab=a.capsule(8,7,0,5.5)
        tab=boss_hole(tab,SR,0)
        s=s.union(radial(tab,phi))
    return s

@lru_cache(None)
def gear_blank():
    rb=GEAR_R*math.cos(gg.ALPHA);rf=GEAR_R-1.25*gg.M;ra=GEAR_R+gg.M
    half=math.pi/(2*TEETH)-gg.BACKLASH/(4*GEAR_R);invp=gg.involute(GEAR_R,rb)
    xy=lambda r,t:(r*math.cos(t),r*math.sin(t));points=[]
    for k in range(TEETH):
        t=2*math.pi*k/TEETH;hb=half+invp;points.append(xy(rf,t-hb))
        for j in range(11):
            r=rb+(ra-rb)*j/10;points.append(xy(r,t-half-invp+gg.involute(r,rb)))
        ha=half+invp-gg.involute(ra,rb)
        for j in range(1,5):points.append(xy(ra,t-ha+2*ha*j/4))
        for j in range(9,-1,-1):
            r=rb+(ra-rb)*j/10;points.append(xy(r,t+half+invp-gg.involute(r,rb)))
        points.append(xy(rf,t+hb))
        for j in range(1,5):points.append(xy(rf,t+hb+(2*math.pi/TEETH-2*hb)*j/5))
    return cq.Workplane('XY').polyline(points).close().extrude(gg.FACE).translate((0,0,gg.GEAR_Z))

@lru_cache(None)
def pinion():
    # Captures the supplied star with existing external closure and centre screw.
    s=gear_blank().union(h.horn_receiver(True)).union(h.cz(7,12.5,4.8))
    return h.clear_horn_face(s,True,0,(0,0,0))

@lru_cache(None)
def frame():
    # Open triangular perimeter: no central palm plate crossing the moving links.
    vertices=[(34*math.cos(math.radians(p)),34*math.sin(math.radians(p))) for p in [0,120,240]]
    s=None
    for k,(x,y) in enumerate(vertices):
        xx,yy=vertices[(k+1)%3];length=math.hypot(xx-x,yy-y)
        bar=h.rounded(length+5,5,3,2,(0,0,-6)).rotate((0,0,0),(0,0,1),math.degrees(math.atan2(yy-y,xx-x))).translate(((x+xx)/2,(y+yy)/2,0))
        s=bar if s is None else s.union(bar)
    for phi in [0,120,240]:
        ray=h.rounded(10,12,3,2,(PIVOT,0,-6))
        for y in [-5,5]:
            lug=h.rounded(10,4,12,2,(PIVOT,y,-2))
            lug=bore_y(lug,PIVOT,0,1.1 if y<0 else 1.45,y-2.1,4.2)
            ray=ray.union(lug)
        s=s.union(radial(ray,phi))
    # Fixed guide backplate and two replaceable retainers. No metal guide shaft.
    s=s.union(h.rounded(4,14,16,1,(8,0,-36)))
    s=s.union(h.rounded(4,5,36,1,(16,-10,-25)))
    s=s.union(h.rounded(13,14,4,1,(11.5,-5,-41)))
    # Pinion motor uses factory ears; open rear/side for body and cable.
    mount=motor_place(h.mount_region(True))
    s=s.union(mount)
    for x,y in h.ear_points(True):
        x+=PX
        s=s.union(h.rounded(6,8,4,1.5,(x,-25,-28)))
        s=s.union(h.rounded(6,5,22,1.5,(x,-25,-18)))
    s=s.union(h.rounded(35,7,3,2,(-28,-24,-6)))
    # Recut actual motor mounting blind holes after joining webs.
    for x,y in h.ear_points(True):s=s.cut(motor_place(h.cz(1.45,-14.2,4.3,x,y)))
    # Four captive insert seats for guide retainers (screw axis X).
    for z in [-36,-30]:
        for y in [-6,6]:
            boss=h.box(4,5,5,(8,y,z));s=s.union(boss)
            hole=h.cz(1.45,0,4.2).rotate((0,0,0),(0,1,0),90).translate((6,y,z))
            s=s.cut(hole)
    # Source wrist horn receiver remains at its existing tool-frame datum.
    wrist=h.side_place(h.horn_receiver(True),1,(0,0,0)).translate((-TOOL_X,0,0)).rotate((0,0,0),(1,0,0),180)
    s=s.union(wrist).union(h.rounded(36,6,4,2,(-26,6,-5)))
    s=s.union(h.rounded(8,14,4,2,(-10,3,-5)))
    # Open central moving-envelope, preserving outboard guide surfaces.
    s=s.cut(h.box(12,8.8,37,(-.5,0,-25.5)))
    s=s.cut(h.box(14,9.6,19,(-2.2,0,-35.5)))
    s=s.cut(guide_cap()).cut(guide_cap().mirror('XZ'))
    # Swept circular star clearance; access is open from +Y after guide removal.
    s=s.cut(motor_place(h.cz(22,3.4,9.9)))
    s=s.cut(motor_place(h.servo(True)))
    p=h.MICRO
    s=s.cut(motor_place(h.box(p['ear_pitch']+7,p['width']+.6,100,(p['offset'],0,p['ear_z']+50))))
    # Recut through screw access after subtracting caps: hole cores are waste.
    for z in [-36,-30]:
        for y in [-6,6]:
            hole=h.cz(1.45,3,7.2).rotate((0,0,0),(0,1,0),90).translate((0,y,z))
            s=s.cut(hole)
    world=s.rotate((0,0,0),(1,0,0),180).translate((TOOL_X,0,0))
    world=h.clear_horn_face(world,True,1,(0,0,0))
    s=world.translate((-TOOL_X,0,0)).rotate((0,0,0),(1,0,0),180)
    return s

@lru_cache(None)
def guide_cap():
    # Two caps withdraw sideways after removing screws; captured rack guide wings.
    s=h.box(6,6,12,(3,5.5,-33))
    s=s.cut(h.box(3.1,3,13,(3.25,3.3,-33)))
    for z in [-36,-30]:
        hole=h.cz(1.1,-1,8).rotate((0,0,0),(0,1,0),90).translate((0,6,z))
        head=h.cz(2.,-1,4).rotate((0,0,0),(0,1,0),90).translate((0,6,z))
        s=s.cut(hole).cut(head)
    return s

def joint_hardware(x,z):
    bush=joint_bush().rotate((0,0,0),(1,0,0),-90).translate((x,2.75,z))
    screw=h.cy(1,-2.15,8,x,z).union(h.cy(1.8,5.85,1.5,x,z))
    ins=h.cy(1.6,-.25,3,x,z).cut(h.cy(1,-.35,3.2,x,z))
    return bush,screw,ins

def items(deg=0,exploded=False):
    q=state(deg);out=[]
    def add(name,s,pid='',color=a.CREAM,mass=None):out.append(h.Item(name,s,'tool',pid,color,mass))
    add('RT frame',frame(),'RT-FRAME')
    for side in [-1,1]:
        cap=guide_cap() if side>0 else guide_cap().mirror('XZ')
        add('RT guide '+str(side),cap.translate((0,side*15 if exploded else 0,0)),'RT-GUIDE',a.GREEN)
    add('RT rack',rack_slider().translate((0,0,q['slider'][2])),'RT-RACK',a.GREEN)
    add('RT pinion',motor_place(pinion().rotate((0,0,0),(0,0,1),q['gear_deg'])),'RT-PINION',a.GREEN)
    add('G1 servo',motor_place(h.servo(True)),color=h.BLACK,mass=13.4)
    for name,s in [('original horn',h.horn(True)),('star cover',h.original_horns.closure(True))]+list(h.original_horns.hardware(True)):
        add('G1 '+name,motor_place(s.rotate((0,0,0),(0,0,1),q['gear_deg'])),color=h.SILVER,
            mass=s.val().Volume()*(.00124 if name in ['original horn','star cover'] else .00785))
    for phi in [0,120,240]:
        put=lambda s:radial(s,phi)
        side=lambda s:s.mirror('XZ') if phi==120 else s
        add('RT finger '+str(phi),put(finger_at(deg)),'RT-FINGER')
        ls=link().rotate((0,0,0),(0,1,0),q['link_angle']).translate(tuple(q['slider']))
        add('RT link '+str(phi),put(side(ls)),'RT-LINK',a.GREEN)
        for tag,p in [('slider',q['slider']),('finger',q['crank'])]:
            for label,s,col in zip(['bush','M2x8','M2L3'],joint_hardware(p[0],p[2]),[a.GREEN,h.SILVER,h.GOLD]):
                add(f'{tag} {label} {phi}',put(side(s)),'RT-JOINT-BUSH' if label=='bush' else '',col,
                    None if label=='bush' else .3 if label=='M2x8' else .14)
        oldb=a.finger_bush().rotate((0,0,0),(1,0,0),-90).translate((PIVOT,-3,0))
        add('RT pivot bush '+str(phi),put(oldb),'L1-25-FINGER-BUSH',a.GREEN)
        bolt=h.cy(1,-7,14,PIVOT,0).union(h.cy(2,-8.5,1.5,PIVOT,0))
        add('RT M2x14 '+str(phi),put(bolt),color=h.SILVER,mass=.8)
        ins=h.cy(1.6,3.5,3,PIVOT,0).cut(h.cy(1,3.4,3.2,PIVOT,0))
        add('RT pivot insert '+str(phi),put(ins),color=h.GOLD,mass=.14)
    for z in [-36,-30]:
        for y in [-6,6]:
            tr=lambda s:s.rotate((0,0,0),(0,1,0),90).translate((0,y,z))
            bolt=h.cz(1,3,6).union(h.cz(1.8,1.5,1.5))
            ins=h.cz(1.6,6,4).cut(h.cz(1,5.9,4.2))
            add('guide M2x6',tr(bolt),color=h.SILVER,mass=.25)
            add('guide M2L4',tr(ins),color=h.GOLD,mass=.2)
    for x,y in h.ear_points(True):
        bolt=h.cz(1,-13.5,6,x,y).union(h.cz(1.8,-7.5,1.5,x,y))
        ins=h.cz(1.6,-14,4,x,y).cut(h.cz(1,-14.1,4.2,x,y))
        washer=h.cz(2.5,-7.8,.3,x,y).cut(h.cz(1.1,-7.9,.5,x,y))
        for label,s,m in [('ear M2x6',bolt,.25),('ear M2L4',ins,.2),('ear washer',washer,.04)]:
            add('G1 '+label,motor_place(s),color=h.SILVER,mass=m)
    return out

def tool_items(deg=0):
    return [h.Item(i.name,i.shape.rotate((0,0,0),(1,0,0),180).translate((TOOL_X,0,0)),i.frame,i.part_id,i.color,i.mass_g) for i in items(deg)]
