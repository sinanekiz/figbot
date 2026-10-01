"""Geometry and mechanism regression; not a physical strength certificate."""
import math
import json
import numpy as np
import pytest
from cad.prototype_arm import build_linka_v1 as a
from scripts.arm_engineering_review import TARGETS

def test_all_task_points_close_linkage():
    qs=[a.ik(t) for t in TARGETS.values()]
    for q in qs:
        fs=a.frames(q)
        fruit=fs['tool']@np.array([a.PALM_X,0,-45,1])
        target=list(TARGETS.values())[qs.index(q)]
        assert np.linalg.norm(fruit[:3]+[550,415,66]-target)<1e-6
    for left,right in zip(qs,qs[1:]):
        for t in np.linspace(0,1,41):
            q=(1-t)*np.array(left)+t*np.array(right)
            l=a.solve_linkage(q[1],q[1]+q[2])
            assert l['closure_error']<1e-8
            assert abs(np.linalg.norm(l['A']-a.C)-a.CRANK)<1e-8

def test_remote_motor_is_not_distal():
    entries=a.local_items()
    remote=next(i for i in entries if i.name=='J3 REMOTE servo')
    assert remote.frame=='yaw'
    assert len([i for i in entries if i.name.endswith('servo')])==6
    assert not [i for i in entries if i.name.endswith('servo') and i.frame=='upper']

@pytest.mark.parametrize('pid',list(a.PARTS))
def test_parts_connected_and_valid(pid):
    s=a.PARTS[pid][0]().val()
    assert s.isValid()
    assert len(s.Solids())==1
    assert s.Volume()>0

def test_tie_insert_pockets_both_sides():
    s=a.upper_tie()
    for y in [-11,11]:
        assert s.intersect(a.h.cy(1.9,y-.2,.4)).val().Volume()<1e-6

def test_original_yaw_aperture_unchanged():
    assert a.h.body_opening(a.h.YAW_MG)==(41.5,20.5,-10.15)
    assert a.rotor().intersect(a.h.cz(3.4,56,7)).val().Volume()<.01

def test_changed_spans_and_non_cosmetic_topology():
    assert (a.U,a.F)==(150,120)
    assert 'L1-15-COUPLER' in a.PARTS
    assert 'L1-14-DRIVE-CRANK' in a.PARTS
    assert a.PARTS['L1-10-FORE-L'][0]().val().BoundingBox().xmin< -a.TAIL

def test_reference_export_status():
    p=a.OUT/'RELEASE_STATUS.json'
    if p.exists():assert json.loads(p.read_text())['manufacturing_approved'] is False

def test_closing_and_return_tendons_have_opposite_moments():
    for theta in np.linspace(-15,12,20):
        for eye,anchor,sign in [([4,0,-12],[-10,0,-6],1),([4,0,-8],[-.5,0,7],-1)]:
            r=a.h.ry(theta)@eye;force=np.array(anchor)-r
            moment=np.cross(r,force/np.linalg.norm(force))[1]
            assert moment*sign>0

def test_spool_and_stator_clear_palm():
    items=a.local_items();p=next(i.shape for i in items if i.name=='L1-16-PALM')
    for name in ['L1-19 spool','G1 servo']:
        s=next(i.shape for i in items if i.name==name)
        assert p.intersect(s).val().Volume()<.01

def test_fingers_clear_palm_in_command_candidate_range():
    for angle in [-15,0,12]:
        items=a.local_items(angle);p=next(i.shape for i in items if i.name=='L1-16-PALM')
        for i in items:
            if i.name.startswith('L1-17'):assert p.intersect(i.shape).val().Volume()<.01

def test_critical_clearances_along_transfer():
    items={i.name:i for i in a.local_items()}
    pairs=[('L1-06-DECK','L1-14-DRIVE-CRANK'),('L1-10-FORE-L','L1-16-PALM'),('L1-13 wrist','L1-16-PALM'),('W1 servo','L1-16-PALM')]
    qs=[a.ik(t) for t in TARGETS.values()]
    for left,right in zip(qs,qs[1:]):
        for t in np.linspace(0,1,9):
            fs=a.frames(np.array(left)*(1-t)+np.array(right)*t)
            for an,bn in pairs:
                aa,bb=items[an],items[bn]
                s=a.h.move(bb.shape,np.linalg.inv(fs[aa.frame])@fs[bb.frame])
                assert aa.shape.intersect(s).val().Volume()<.1,(an,bn,t)
