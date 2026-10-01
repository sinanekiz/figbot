"""Existing rover CONTEXT only. No old arm geometry is reused in FORMA V6.

The proposed plate-to-rover truss interface needs fabrication validation. The
generated plate is an insert receiver; rods below it are contextual envelopes.
"""
from functools import lru_cache
from cad.prototype_arm import build_forma_v6 as a
from cad.rover import build_rev_i_direct_basket as context
from cad.rover import rev_h_running_gear as gear

@lru_cache(None)
def vehicle():
    items=[]
    for p in context.vehicle():
        if p.name.startswith(('front arm carrier','front mounting plate')):continue
        items.append(a.Item(p.name,p.shape,'vehicle',color=p.color))
    for side in [-1,1]:
        for k,(p,q) in enumerate([
            ((300,side*280,90),(550,side*280,47)),
            ((500,side*280,66),(550,side*415,47)),
            ((310,side*285,90),(500,side*280,140)),
            ((500,side*280,140),(500,side*330,47)),
            ((500,side*330,47),(550,side*415,47))]):
            items.append(a.Item(f'carrier envelope {side} {k}',gear.rod(p,q,18),'vehicle',color=a.SILVER))
        plate=a.vehicle_plate().translate((550,side*415,66))
        items.append(a.Item(f'F6-16 receiver {side}',plate,'vehicle','F6-16-ROVER-PLATE',a.TEAL))
    return items

def scene(q):return vehicle()+a.assembly(q,rover=True)
