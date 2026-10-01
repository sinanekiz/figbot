"""Cable-window geometry; no assertion about an unmeasured physical cable."""
import pytest
import cadquery as cq
from cad.prototype_arm import build_linka_v1 as a

@pytest.fixture(scope='module')
def pair():return a.h.base(),a.base()

def test_old_wall_is_real_and_new_cable_corridor_open(pair):
    old,new=pair
    for x in sorted(set(p[0] for p in a.h.ear_points(spec=a.h.YAW_MG))):
        probe=a.h.box(9,11.8,17.8,(x,0,13))
        assert old.intersect(probe).val().Volume()>1000
        assert new.intersect(probe).val().Volume()<1e-6

def test_slot_preserves_floor_seats_and_track(pair):
    old,new=pair
    removed=old.cut(new)
    assert removed.intersect(a.h.box(200,200,4,(0,0,2))).val().Volume()<1e-6
    assert removed.intersect(a.h.box(200,200,50,(0,0,53))).val().Volume()<1e-6
    assert removed.intersect(a.h.ring(40,80,4,70)).val().Volume()<1e-6
    for x,y in a.h.ear_points(spec=a.h.YAW_MG):
        envelope=a.h.cz(3.1,31.5,8,x,y)
        assert removed.intersect(envelope).val().Volume()<1e-6

def test_no_new_solid_added_and_feet_still_connected(pair):
    old,new=pair
    assert new.cut(old).val().Volume()<1e-6
    assert new.val().isValid() and len(new.val().Solids())==1
    # Nominal side legs remain on each side of the cable opening.
    for x in sorted(set(p[0] for p in a.h.ear_points(spec=a.h.YAW_MG))):
        for y in [-10,10]:
            leg=a.h.box(4,4,22,(x,y,16))
            assert new.intersect(leg).val().Volume()>350

@pytest.mark.parametrize('end',[-1,1])
def test_measured_boot_plus_clearance_fits_source_and_shipped_step(pair,end):
    # Conditional positional range, NOT an assertion of the real boot's datum.
    # Leave0.5mm nominal clearance on each cross-section side and at the tip.
    b=a.BASE_CABLE_BOOT_MEASURED
    assert b=={'width':7.,'height':3.9,'protrusion':5.5}
    face=a.h.YAW_MG['offset']+end*a.h.YAW_MG['length']/2
    length=b['protrusion']+.5
    shipped=cq.importers.importStep(str(a.OUT/'PART_STEP/L1-01-BASE.step'))
    for bottom in [4.5,7.1,12.,17.6]:
        probe=a.h.box(length,b['width']+1,b['height']+1,
                      (face+end*length/2,0,bottom+b['height']/2))
        for s in [pair[1],shipped]:
            assert s.intersect(probe).val().Volume()<1e-6
