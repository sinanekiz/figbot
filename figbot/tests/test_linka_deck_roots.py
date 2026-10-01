"""A one-solid deck can still have unsupported feet: audit the actual root section."""
import numpy as np
import pytest
from cad.prototype_arm import build_linka_v1 as a

@pytest.fixture(scope='module')
def deck():return a.motor_deck()

def test_each_column_has_a_substantial_direct_floor_contact(deck):
    low=deck.intersect(a.h.box(400,300,.1,(0,0,75.9)))
    for name,side,origin in [('J2A',1,(0,27,a.Z)),('J2B',-1,(0,-27,a.Z)),('J3',-1,tuple(a.C+[0,-38,0]))]:
        for x in sorted(set(p[0] for p in a.h.ear_points())):
            foot=a.h.rounded(12,12,.1,2,(x+origin[0],origin[1]+side*16,75.9))
            ratio=low.intersect(foot).val().Volume()/foot.val().Volume()
            assert ratio>.90,(name,x,ratio) # CAD support ratio, not a strength threshold.

def test_outward_triangles_are_material_beyond_old_columns(deck):
    for side,origin in [(1,(0,27,a.Z)),(-1,(0,-27,a.Z)),(-1,tuple(a.C+[0,-38,0]))]:
        for x in sorted(set(p[0] for p in a.h.ear_points())):
            sample=a.h.box(2,1,1,(origin[0]+x,origin[1]+side*23.5,84))
            assert deck.intersect(sample).val().Volume()>1.9

def test_rotor_screws_and_height_are_preserved(deck):
    for x in [-28,28]:
        for y in [-15,15]:
            assert deck.intersect(a.h.cz(1.6,74.9,5.2,x,y)).val().Volume()<1e-5
            land=a.h.cz(4,75,5,x,y).cut(a.h.cz(1.7,75,5,x,y))
            assert deck.intersect(land).val().Volume()>.99*land.val().Volume()
    assert deck.val().BoundingBox().zmin==pytest.approx(75)

def test_new_floor_stays_above_the_rotating_retainer(deck):
    # Both retainer halves' top is66.5; floor starts75, independent of yaw.
    assert deck.val().BoundingBox().zmin-a.h.RETAINER_TOP>=8.5-1e-6
