"""DEC-086 circular J1 retaining cup; existing horn datum remains unchanged."""
from functools import lru_cache
from cad.prototype_arm import build_linka_v1 as a,build_forma_v6 as h

PID='J1-CAPTURE-CUP'
@lru_cache(None)
def cup():
    top=h.original_horns.cover_top(False)
    s=h.cz(25,top-4,4).cut(h.cz(6.3,top-4.1,4.2))
    s=s.union(h.ring(23.1,25,top,2))
    for x,y in h.horn_points(False):s=s.cut(h.cz(1.1,top-4.1,6.2,x,y))
    return s

def apply(local):
    """Only J1 cap and its two screw shafts/heads change. No servo offset."""
    out=[];top=h.original_horns.cover_top(False)
    for i in local:
        if i.name=='L1-20-MG-COVER J1':
            out.append(a.Item(PID,cup().translate((0,0,50)),i.frame,PID,a.GREEN));continue
        if i.name.startswith('J1 horn mounting head'):
            i=a.Item(i.name,i.shape.translate((0,0,-2)),i.frame,i.part_id,i.color,i.mass_g)
        elif i.name.startswith('J1 horn mounting shank'):
            k=int(i.name[-1]);x,y=h.horn_points(False)[k]
            i=a.Item(i.name,h.cz(1,top-4+50,8,x,y),i.frame,i.part_id,i.color,.3)
        out.append(i)
    return out
