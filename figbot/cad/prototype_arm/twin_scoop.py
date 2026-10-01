"""DEC-086 two integral gear/scoop jaws, reinforced frame. Trial dimensions."""
from functools import lru_cache
from cad.prototype_arm import geared_gripper as old,build_linka_v1 as a,build_forma_v6 as h
import cadquery as cq

REVISION='DEC-086 / IKI KEPCE / FIZIKSEL DOGRULAMA GEREKLI'
OPEN=24.; WALL=2.6; OFFSET=32.

@lru_cache(None)
def frame():
    s=old.lower_frame()
    # Broad windowed side walls connect the old isolated posts to both decks.
    for y in [-42.5,42.5]:
        wall=h.rounded(55,6,37,2,(25.5,y,.5))
        wall=wall.cut(h.rounded(33,9,21,3,(25.5,y,.5)))
        s=s.union(wall)
    # Reinforce the wrist load route and passive-axis pedestal.
    s=s.union(h.rounded(25,26,4,3,(8,-10,-15.5)))
    s=s.union(h.cz(5,0,11,old.CX,old.CY))
    s=h.insert_hole(s,old.CX,old.CY,11,2.9,4)
    for x,y in old.POSTS:s=h.insert_hole(s,x,y,19,2.9,4)
    s=h.clear_mount(s,True,0,(old.CX,-old.CY,0))
    # Keep the wrist spline datum but move the broad jaw chassis ahead of the fork.
    socket=h.side_place(h.horn_receiver(True),1,(0,old.WRIST_MOUNT_Y,0))
    s=s.cut(socket).translate((OFFSET,0,0))
    for yy in [-8]:
        web=a.plate([(-4,-12),(OFFSET+8,-18),(OFFSET+8,-12),(10,9),(-4,9)],yy,12)
        s=s.union(web)
    s=s.union(socket)
    s=h.clear_mount(s,True,0,(old.CX+OFFSET,-old.CY,0))
    return h.clear_horn_face(s,True,1,(0,old.WRIST_MOUNT_Y,0))

@lru_cache(None)
def bridge():return old.upper_bridge()

@lru_cache(None)
def jaw(right=True):
    # Circumferential rim, broad root and short webs distribute scoop bending.
    phase=180/old.N if right else 0
    s=old.gear().rotate((0,0,0),(0,0,1),phase).translate((old.CX,old.CY,0))
    s=s.union(h.rounded(34,10,6,3,(44,20,15.3)))
    s=s.union(old.half_bowl(wall=WALL))
    rim=old.half_bowl(inset=-.8,wall=3.4).intersect(h.box(65,60,2.4,(old.BOWL_X,20,14.8)))
    s=s.union(rim)
    # Two local gussets; avoid extending ribs into the fruit cavity.
    for x in [48,56]:
        rib=h.rounded(6,7,10,2,(x,17,11.5))
        # only the outboard surface: no abrupt pressure point inside bowl
        rib=rib.cut(h.cz(21,-15,40,old.BOWL_X,0))
        s=s.union(rib)
    if right:
        s=s.union(h.cz(6,11.3,7.4,old.CX,old.CY)).cut(h.cz(3.2,8,13,old.CX,old.CY))
    else:
        s=s.mirror('XZ')
        s=s.union(h.horn_receiver(True).translate((old.CX,-old.CY,0)))
        s=s.union(h.cz(7,12.5,4,old.CX,-old.CY)).union(h.cz(5,16,6,old.CX,-old.CY))
        s=s.cut(h.cz(3.5,5,19,old.CX,-old.CY))
        s=h.clear_horn_face(s,True,0,(old.CX,-old.CY,0))
    return s

@lru_cache(None)
def bush():return a.plain_bush(6,2.4,8)

PARTS={'TS-FRAME':(frame,1),'TS-BRIDGE':(bridge,1),'TS-JAW-DRIVE':(lambda:jaw(False),1),'TS-JAW-PASSIVE':(lambda:jaw(True),1),'TS-BUSH':(bush,1)}

def items(angle=0,exploded=False):
    out=[]
    for i in old.items(angle,exploded):
        if i.name.startswith('PAD'):continue
        if i.name=='FRAME':s,pid=frame(),'TS-FRAME'
        elif i.name=='BRIDGE':s,pid=bridge().translate((0,0,30 if exploded else 0)),'TS-BRIDGE'
        elif i.name=='JAW -1':s,pid=old.move(jaw(False),-1,angle),'TS-JAW-DRIVE'
        elif i.name=='JAW 1':s,pid=old.move(jaw(True),1,angle),'TS-JAW-PASSIVE'
        elif i.name=='DRIVEN SLEEVE':s,pid=bush().translate((old.CX,old.CY,11)),'TS-BUSH'
        elif i.name=='M2 axle':s,pid=h.cz(1,8,14,old.CX,old.CY).union(h.cz(1.8,22,1.5,old.CX,old.CY)),''
        elif i.name=='INSERT axle':s,pid=h.cz(1.6,7,4,old.CX,old.CY).cut(h.cz(1,6.9,4.2,old.CX,old.CY)),''
        else:s,pid=i.shape,i.part_id
        if i.name!='FRAME':s=s.translate((OFFSET,0,0))
        out.append(h.Item(i.name,s,'tool',pid,i.color,None if pid else i.mass_g))
    return out

def tool_items(angle=0):
    return [h.Item(i.name,i.shape.translate((0,-old.WRIST_MOUNT_Y,0)),i.frame,i.part_id,i.color,i.mass_g) for i in items(angle)]
