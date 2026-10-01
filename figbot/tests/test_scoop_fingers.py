"""DEC-082 geometry checks. No physical grip or strength certification."""
import hashlib,itertools,json
from functools import lru_cache
import cadquery as cq
import pytest
from cad.prototype_arm import build_linka_v1 as a
from scripts.project_paths import ROOT,CAD

@lru_cache(None)
def part(pid):
    return cq.importers.importStep(str(CAD/'PART_STEP'/f'{pid}.step')).val()

def test_length_root_and_new_liner():
    f=part('L1-17-FINGER');p=part('L1-18-PAD');b=f.BoundingBox()
    assert f.isValid() and p.isValid()
    assert len(f.Solids())==len(p.Solids())==1
    assert (b.zmin,b.zmax)==pytest.approx((-45,4),abs=1e-5)
    assert b.ylen==pytest.approx(49.18679,abs=1e-4)
    assert a.SCOOP_WALL==1.6
    assert f.intersect(p).Volume()<1e-6
    assert f.intersect(a.h.box(18,20,6,(0,0,0)).val()).BoundingBox().ylen==pytest.approx(5.5)
    for x,z,d in [(0,0,5.1),(4,-12,1.4),(4,-8,1.6)]:
        assert f.intersect(a.h.cy(d/2-.001,-4,8,x=x,z=z).val()).Volume()<1e-6
    assert p.Volume()<900

@pytest.mark.parametrize('grip',[-15,-10,0,6,12])
def test_sampled_scoops_and_liners_clear(grip):
    items=a.local_items(grip)
    moving=[i for i in items if i.part_id in {'L1-17-FINGER','L1-18-PAD'}]
    fixed=[i for i in items if i.frame=='tool' and i not in moving and not any(w in i.name for w in ['cord','elastic'])]
    for x,y in itertools.combinations(moving,2):
        assert x.shape.val().intersect(y.shape.val()).Volume()<1e-5,(grip,x.name,y.name)
    for x in moving:
        for y in fixed:
            assert x.shape.val().intersect(y.shape.val()).Volume()<1e-5,(grip,x.name,y.name)
    fingers=[i for i in moving if i.part_id=='L1-17-FINGER']
    assert min(x.shape.val().distance(y.shape.val()) for x,y in itertools.combinations(fingers,2))>1.1

def test_only_two_printed_types_change_from_l14():
    old=json.loads((ROOT/'reports/scoop_fingers/before_hashes.json').read_text())
    changed={name for name,h in old.items() if hashlib.sha256((CAD/'PRINT_STL'/name).read_bytes()).hexdigest()!=h}
    assert changed=={'L1-17-FINGER.stl','L1-18-PAD.stl'}
    for ext in ['glb','step']:
        assert (CAD/f'LINKA_L1_GRIPPER_CLOSED.{ext}').stat().st_size>1000

def test_liner_bom_no_old_flat_pad_purchase():
    from scripts.build_linka_shopping import index
    p=index['PADS']
    assert p['required']==3 and p['url'] is None and p['buy_quantity'] is None
    assert 'TPU' in p['part'] and p['order_hold']
