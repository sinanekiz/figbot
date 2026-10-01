"""Regression checks for the reported rotation and impossible-cover failures."""
import numpy as np
import cadquery as cq
from cad.prototype_arm import build_snap02 as s

def v(a,b):return a.intersect(b).val().Volume()

def test_star_is_not_round_and_both_torque_directions_hit_a_wall():
    body,_=s.build();horn=s.horn_envelope();p=s.profile()
    assert p.area/p.convex_hull.area<.85
    assert v(body,horn)<1e-6
    for angle in [-3,3]:assert v(body,horn.rotate((0,0,0),(0,0,1),angle))>1

def test_actual_hub_can_be_installed_and_each_cap_can_pass_it():
    body,cap=s.build();horn=s.horn_envelope()
    for z in np.linspace(0,15,16):assert v(body,horn.translate((0,0,float(z))))<1e-6
    for d in np.linspace(0,46,47):
        caps=s.caps_pose(cap,float(d))
        for c in caps:assert v(c,horn)<1e-6
        assert v(caps[0],caps[1])<1e-6

def test_positive_axial_retention_of_star_and_covers():
    body,cap=s.build();horn=s.horn_envelope();caps=s.caps_pose(cap)
    for c in caps:
        assert v(c,body)<1e-6
        assert v(c.translate((0,0,.5)),body)>1
    assert sum(v(c,horn.translate((0,0,.5))) for c in caps)>1
    for c in s.caps_pose(cap,1):assert v(c,body)>0

def test_prints_are_single_solids_and_torque_output_is_integral():
    body,cap=s.build()
    for part in [body,cap]:
        assert part.val().isValid() and len(part.solids().vals())==1
        assert abs(part.val().BoundingBox().zmin)<1e-6
    assert body.val().BoundingBox().ymax>50
    # Continuous material across tongue/body junction, without a floating arm.
    probe=s.box(10,3,1,(0,22,1))
    assert abs(v(body,probe)-30)<1e-5

def test_centre_screwdriver_path_and_print_stays_below_horn_end():
    body,cap=s.build()
    tool=cq.Workplane('XY').circle(3.8).extrude(15).translate((0,0,-5))
    assert v(tool,body)<1e-6
    for c in s.caps_pose(cap):assert v(tool,c)<1e-6
    assert body.val().BoundingBox().zmax<s.FLOOR+5

def test_complete_geometry_audit():
    audit=s.audit_geometry()
    assert audit['references']['four_arm']['valid']
    assert audit['references']['six_arm']['watertight']
    assert audit['checks']['insertion']['rigid_plate_overlap_mm3']<1e-6
