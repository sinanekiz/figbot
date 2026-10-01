import numpy as np
import cadquery as cq
from cad.prototype_arm import build_snap01 as old
from cad.prototype_arm import build_snap01b as new

def hub(diameter):
    return cq.Workplane('XY').circle(diameter/2).extrude(12).translate((0,0,old.DECK))

def test_reproduces_reported_insertion_failure():
    _,lid=old.build()
    assert lid.translate((0,-10,old.LID_Z)).intersect(hub(10)).val().Volume()>1
    assert lid.translate((0,0,old.LID_Z)).intersect(hub(10)).val().Volume()<1e-6

def test_new_lid_clears_hub_through_insertion_not_only_at_endpoint():
    _,lid=new.build()
    for d in [8,10,12,13.5]:
        for y in np.linspace(-38,0,39):
            assert lid.translate((0,float(y),old.LID_Z)).intersect(hub(d)).val().Volume()<1e-6

def test_reuses_body_and_keeps_one_solid_and_retention():
    body,lid=new.build();prior,_=old.build()
    assert body.cut(prior).val().Volume()<1e-6 and prior.cut(body).val().Volume()<1e-6
    assert lid.val().isValid() and len(lid.solids().vals())==1
    assert body.intersect(lid.translate((0,0,old.LID_Z))).val().Volume()<1e-6
    assert body.intersect(lid.translate((0,-1,old.LID_Z))).val().Volume()>1
    assert body.intersect(lid.translate((0,0,old.LID_Z+.6))).val().Volume()>1
