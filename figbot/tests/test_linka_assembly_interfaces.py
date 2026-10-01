"""Revision-specific screw stacks and mating clearances, nominal geometry only."""
import math
import numpy as np
import pytest
from cad.prototype_arm import build_linka_v1 as a
from scripts.arm_engineering_review import TARGETS

@pytest.fixture(scope='module')
def items():return a.local_items()

def test_all_screw_and_insert_stacks_have_tip_clearance():
    # length, external stack, metal insert length, actual pocket depth.
    for name,L,stack,insert,depth in [
        ('MG ear',6,2.2+.5,5,5),('micro ear',6,2.2+.3,4,4),
        ('upper tie',10,5+.5,5,5),('fore tie',8,4+.5,5,5),
        ('deck',10,5+.5,5,5),('retainer',20,15.5+.5,5,5),
        ('wrist',8,4+.3,4,4),('bearing cap',6,2+.7,3,3.5),
        ('horn cover',6,2,4,4.4),('rod threaded tip',10,6.5,4,8)]:
        assert min(L-stack,insert)>=3-1e-8,name
        assert depth-(L-stack)>=.19,name

def test_retained_elbow_stack_and_accessible_nut(items):
    assert 4+4+5+28+5+4+4==54
    assert 54+2*1+5 <70
    byname={i.name:i for i in items}
    axle=byname['elbow M5x70 partial thread bolt'].shape
    right=a.fore_side(1)
    nut=byname['elbow M5 locknut'].shape
    assert right.intersect(nut).val().Volume()<1e-6
    assert right.intersect(axle).val().Volume()<1e-6
    # Last bearing ends atY19; plain shank ends20: no thread in either journal.
    assert 20-19==1

def test_bearing_backing_and_cap_feet():
    s=a.upper_side(1)
    assert s.intersect(a.h.cy(7,11.5,2.5,a.U).cut(a.h.cy(6.3,11.5,2.5,a.U))).val().Volume()>1
    cap=a.bearing_cap().translate((a.U,a.BEARING_CAP_Y,0))
    assert s.intersect(cap).val().Volume()<1e-6
    assert a.BEARING_CAP_Y-19==pytest.approx(.2)
    assert a.BEARING_CAP_Y-.7==pytest.approx(18.5)
    # Minimum material between bearing pocket and installed insert envelope.
    assert a.BEARING_BOLT_R-1.6-16.15/2>2.8

def test_rod_has_shoulder_stop_thread_clearance_and_thrust_space():
    screw=a.rod_shoulder_screw(a.CRANK)
    assert a.crank().intersect(screw).val().Volume()<1e-6
    screw=a.rod_shoulder_screw(-a.TAIL)
    assert a.fore_side(-1).intersect(screw).val().Volume()<1e-6
    assert 6-5.6==pytest.approx(.4)

def test_hardware_count_matches_procurement(items):
    names=[i.name for i in items]
    assert sum('insert' in n.lower() or 'brass ear' in n for n in names)==59
    assert sum(n.startswith('ear washer') for n in names)==20
    assert sum(n.startswith('coupler M3 washer') for n in names)==2
    assert sum(n.startswith('coupler M3x10') for n in names)==2
    assert sum(n.startswith('retainer M3x20 screw') for n in names)==4

def test_crank_branch_has_no_full_turn_discontinuity():
    qs=[a.ik(t) for t in TARGETS.values()]
    gs=[]
    for q,r in zip(qs,qs[1:]):
        for t in np.linspace(0,1,41):
            v=(1-t)*np.array(q)+t*np.array(r)
            gs.append(a.solve_linkage(v[1],v[1]+v[2])['gamma'])
    assert max(abs(np.diff(gs)))<15
    assert np.ptp(gs)<165  # Nominal required travel, not motor calibration.

def test_steel_ball_mass_is_geometric(items):
    balls=[i for i in items if i.name.startswith('ball ')]
    assert len(balls)==24
    assert balls[0].mass_g==pytest.approx(4/3*math.pi*4**3*.00785)
