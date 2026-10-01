"""DEC-083 two-jaw feasibility CAD. Review geometry, NOT released print parts.

Independent involute geometry, KHK standard spur-gear equations. No copied STL.
Stock MG90S and source horn socket retained; supports are explicit candidates.
"""
from functools import lru_cache
import math
import cadquery as cq
from cad.prototype_arm import build_linka_v1 as a
from cad.prototype_arm import build_forma_v6 as h

REVISION='DISLI TUTUCU / DEC-083 / INCELEME'
M=1.25;N=28;ALPHA=math.radians(20);R=M*N/2
BACKLASH=.30;FACE=4.;GEAR_Z=13.3;CX=25.;CY=R
OPEN=24.;BOWL_X=67.;WALL=1.8
WRIST_MOUNT_Y=4.  # Stage offset gives the servo a straight insertion path.
POSTS=[(2,-40),(49,-40),(2,40),(49,40)]

def involute(r,rb):
    u=math.sqrt(max(0,(r/rb)**2-1));return u-math.atan(u)

@lru_cache(None)
def gear():
    rb=R*math.cos(ALPHA);rf=R-1.25*M;ra=R+M
    half=math.pi/(2*N)-BACKLASH/(4*R);invp=involute(R,rb)
    def xy(r,t):return (r*math.cos(t),r*math.sin(t))
    points=[]
    for k in range(N):
        t=2*math.pi*k/N;hb=half+invp
        points.append(xy(rf,t-hb))
        for j in range(11):
            r=rb+(ra-rb)*j/10;points.append(xy(r,t-half-invp+involute(r,rb)))
        ha=half+invp-involute(ra,rb)
        for j in range(1,5):points.append(xy(ra,t-ha+2*ha*j/4))
        for j in range(9,-1,-1):
            r=rb+(ra-rb)*j/10;points.append(xy(r,t+half+invp-involute(r,rb)))
        points.append(xy(rf,t+hb))
        for j in range(1,5):points.append(xy(rf,t+hb+(2*math.pi/N-2*hb)*j/5))
    return cq.Workplane('XY').polyline(points).close().extrude(FACE).translate((0,0,GEAR_Z))

def half_bowl(inset=0,wall=WALL):
    wires=[]
    for z,r in [(16,24),(8,23),(0,18),(-7,9),(-9,3)]:
        ro=r-inset;ri=ro-wall
        w=(cq.Workplane('XY',origin=(BOWL_X,0,z)).moveTo(ro,0)
           .threePointArc((0,ro),(-ro,0)).lineTo(-ri,0)
           .threePointArc((0,ri),(ri,0)).close().val())
        wires.append(w)
    s=cq.Workplane(obj=cq.Solid.makeLoft(wires,ruled=True))
    return s.intersect(h.box(140,50,70,(BOWL_X,25.65,5)))

@lru_cache(None)
def jaw(right=True):
    # Global closed-pose coordinates. Horn below tooth face; service access above.
    phase=180/N if right else 0
    s=gear().rotate((0,0,0),(0,0,1),phase).translate((CX,CY,0))
    s=s.union(h.rounded(32,7,4,2,(45,20,15.3))).union(half_bowl())
    if right:
        s=s.union(h.cz(6,9.3,9.4,CX,CY)).cut(h.cz(3.2,8,13,CX,CY))
    else:
        s=s.mirror('XZ')
        s=s.union(h.horn_receiver(True).translate((CX,-CY,0)))
        s=s.union(h.cz(7,12.5,4,CX,-CY))
        s=s.union(h.cz(5,16,6,CX,-CY))
        s=s.cut(h.cz(3.5,5,19,CX,-CY))
        s=h.clear_horn_face(s,True,0,(CX,-CY,0))
    return s

@lru_cache(None)
def lower_frame():
    # Open frame. Integral factory-ear seats; no box around servo or closed roof.
    s=h.side_place(h.horn_receiver(True),1,(0,WRIST_MOUNT_Y,0))
    for y in [-40,40]:s=s.union(h.rounded(60,5,3,2,(25,y,-16)))
    for x in [0,49]:s=s.union(h.rounded(5,80,3,2,(x,0,-16)))
    s=s.union(h.rounded(12,24,3,2,(1,-12,-16)))
    s=s.union(h.mount_region(True).translate((CX,-CY,0)))
    # Servo mounting ears connect to side rails through two short horizontal webs.
    for x,y in h.ear_points(True):
        s=s.union(h.rounded(5.5,24,3,2,(CX+x,-29,-16)))
    for x,y in POSTS:
        s=s.union(h.rounded(5.5,5.5,37,1.5,(x,y,.5)))
        s=h.insert_hole(s,x,y,19,2.9,4)
    # Driven-axis support rises from the lower cross rail, not from the servo.
    s=s.union(h.rounded(28,7,3,2,(38,CY,-16)))
    s=s.union(h.cz(4.5,-17.5,26.5,CX,CY))
    s=s.cut(h.cz(2.75,-17.6,19,CX,CY))
    s=h.insert_hole(s,CX,CY,9,2.9,4)
    s=h.clear_mount(s,True,0,(CX,-CY,0))
    return h.clear_horn_face(s,True,1,(0,WRIST_MOUNT_Y,0))

@lru_cache(None)
def upper_bridge():
    s=h.rounded(14,80,3,2,(CX,0,20.5))
    for y in [-40,40]:s=s.union(h.rounded(54,6,3,2,(25.5,y,20.5)))
    for x,y in POSTS:s=s.cut(h.cz(1.1,18,5,x,y))
    s=s.cut(h.cz(5.2,18,5,CX,-CY)).cut(h.cz(1.1,18,5,CX,CY))
    return s

def liner():return half_bowl(WALL+.1,.8)

def move(s,side,angle):
    return s.rotate((CX,side*CY,0),(CX,side*CY,1),side*angle)

def items(angle=0,exploded=False):
    out=[h.Item('FRAME',lower_frame(),'tool','GG-FRAME',a.CREAM),
         h.Item('BRIDGE',upper_bridge().translate((0,0,30 if exploded else 0)),'tool','GG-BRIDGE',a.GREEN)]
    for side,right in [(-1,False),(1,True)]:
        out.append(h.Item('JAW '+str(side),move(jaw(right),side,angle),'tool','GG-JAW-'+str(side),a.CREAM))
        # Three independently replaceable patches: two on one side, one opposite.
        soft=(liner() if right else liner().mirror('XZ')).cut(jaw(right))
        if right:
            for k,(x,w) in enumerate([(62,25),(90,25)]):
                patch=soft.intersect(h.box(w,60,40,(x,0,5)))
                out.append(h.Item('PAD right '+str(k),move(patch,side,angle),'tool','GG-PAD-R'+str(k),a.ORANGE))
        else:out.append(h.Item('PAD left',move(soft,side,angle),'tool','GG-PAD-L',a.ORANGE))
    servo=h.servo(True).translate((CX,-CY,0))
    out.append(h.Item('G1 servo',servo,'tool',color=h.BLACK,mass_g=13.4))
    for name,s in [('original horn',h.horn(True)),('star closure',h.original_horns.closure(True))]+list(h.original_horns.hardware(True)):
        placed=s.translate((CX,-CY,0));density=.00124 if name in ['original horn','star closure'] else .00785
        out.append(h.Item('G1 '+name,move(placed,-1,angle),'tool',color=h.SILVER,mass_g=s.val().Volume()*density))
    # Fixed sleeve through driven gear, retained by screw into lower support.
    sleeve=h.cz(3,9,10,CX,CY).cut(h.cz(1.15,8,12,CX,CY))
    out.append(h.Item('DRIVEN SLEEVE',sleeve,'tool','GG-SLEEVE',a.GREEN))
    for name,x,y,z,length in [('axle',CX,CY,22,16)]+[('cover',x,y,22,6) for x,y in POSTS]:
        bolt=h.cz(1,z-length,length,x,y).union(h.cz(1.8,z,1.5,x,y))
        out.append(h.Item('M2 '+name,bolt,'tool',color=h.SILVER,mass_g=.3))
        iz=5 if name=='axle' else 15
        insert=h.cz(1.6,iz,4,x,y).cut(h.cz(1,iz-.1,4.2,x,y))
        out.append(h.Item('INSERT '+name,insert,'tool',color=h.GOLD,mass_g=insert.val().Volume()*.0085))
    for x,y in h.ear_points(True):
        x+=CX;y-=CY
        bolt=h.cz(1,-13.5,6,x,y).union(h.cz(1.8,-7.5,1.5,x,y))
        washer=h.cz(2.5,-7.8,.3,x,y).cut(h.cz(1.1,-7.9,.5,x,y))
        ins=h.cz(1.6,-14,4,x,y).cut(h.cz(1,-14.1,4.2,x,y))
        for label,s,d in [('ear screw',bolt,.00785),('ear washer',washer,.00785),('ear insert',ins,.0085)]:
            out.append(h.Item(label,s,'tool',color=h.SILVER,mass_g=s.val().Volume()*d))
    return out
