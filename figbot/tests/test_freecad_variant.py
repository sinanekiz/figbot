import math
import pytest
from cad.freecad.parameters import DEFAULTS,validate
from cad.freecad import variant_worker as v


def test_invalid_dimensions_rejected():
    for change in ({'UpperLength':0},{'BasketSlope':float('nan')},{'ArmBaseZ':float('inf')}):
        with pytest.raises(ValueError):
            validate(DEFAULTS|change)


def test_default_variant_matches_controlled_rover():
    v.configure(DEFAULTS)
    original=v.rover.vehicle()+v.rover.dual_arms(v.rover.solve_pose(v.rover.TARGETS['pickup']))
    generated=v.components('rover',DEFAULTS)
    assert len(original)==len(generated)
    for a,b in zip(original,generated):
        assert a.name==b.name
        assert a.shape.val().Volume()==pytest.approx(b.shape.val().Volume(),abs=.001)
        aa,bb=a.shape.val().BoundingBox(),b.shape.val().BoundingBox()
        for key in ('xmin','xmax','ymin','ymax','zmin','zmax'):
            assert getattr(aa,key)==pytest.approx(getattr(bb,key),abs=1e-5)


def test_changed_lengths_move_joint_and_resize_tubes():
    parts={c.name:c.shape.val() for c in v.components('arm',DEFAULTS|{'UpperLength':310.,'ForeLength':230.})}
    assert parts['300 mm aluminium upper tube'].Volume()==pytest.approx(310*400)
    assert parts['220 mm aluminium forearm tube'].Volume()==pytest.approx(230*400)
    changed=parts['elbow yoke'].Center()
    baseline={c.name:c.shape.val() for c in v.components('arm',DEFAULTS)}
    delta=changed-baseline['elbow yoke'].Center()
    assert delta.x==pytest.approx(10*math.cos(math.radians(18)),abs=1e-4)
    assert delta.z==pytest.approx(-10*math.sin(math.radians(18)),abs=1e-4)
    assert parts['upper hollow fairing 1'].isValid()


def test_basket_slope_changes_front_not_rear():
    v.configure(DEFAULTS|{'BasketSlope':10.})
    assert v.rover.floor_z(-280)==145
    assert v.rover.floor_z(320)==pytest.approx(145+600*math.tan(math.radians(10)))
    v.configure(DEFAULTS)
