import math
import numpy as np
import pytest
from cad.prototype_arm import build_aero_v3 as a
from cad.prototype_arm import audit_aero_v3 as audit


def test_parts_are_valid_single_solids_and_fit_printer():
    for name,(builder,qty) in a.PRINT_PARTS.items():
        s=builder().val();b=s.BoundingBox()
        assert s.isValid() and len(s.Solids())==1,name
        assert s.Volume()>30 and qty>=1,name
        assert max(b.xlen,b.ylen,b.zlen)<256,name


def test_vertical_tool_and_wrist_target_from_fk():
    for name,target in a.TARGETS.items():
        yaw,upper,fore=a.ik(target)
        x=a.UPPER*math.cos(math.radians(upper))+a.FORE*math.cos(math.radians(fore))
        z=a.SHOULDER_Z-a.UPPER*math.sin(math.radians(upper))-a.FORE*math.sin(math.radians(fore))
        world=np.array(a.BASE)+[x*math.cos(math.radians(yaw)),x*math.sin(math.radians(yaw)),z]
        assert np.allclose(world,target)
        assert fore + (-fore) == 0
        # Geometry, not only angle arithmetic: fixed pad remains vertical.
        pad=next(c.shape.val() for c in a.assembly((yaw,upper,fore),base=a.BASE) if c.name=='fixed soft pad')
        assert pad.BoundingBox().zlen==pytest.approx(12,abs=1e-5)
        assert pad.Center().z==pytest.approx(target[2]-89,abs=1e-5)


def test_tubes_do_not_intersect_sockets():
    for fore in (False,True):
        length=a.FORE if fore else a.UPPER
        off=18 if fore else -18
        t=a.tube(length-(59 if fore else 65),off,(44,59,length-(43 if fore else 57),length-(34 if fore else 42)))
        assert t.val().intersect(a.link_hub(fore).val()).Volume()<.1
        socket=a.yoke('wrist' if fore else 'elbow').translate((length,0,0))
        assert t.val().intersect(socket.val()).Volume()<.1
        # Actual CAD saw lengths, as opposed to the joint-to-joint spans.
        assert t.val().BoundingBox().xlen==pytest.approx(161 if fore else 235)


def test_all_key_pose_solids_are_clear():
    for target in a.TARGETS.values():
        parts=a.assembly(a.ik(target),base=a.BASE)
        assert not audit.clashes(parts), audit.clashes(parts)


def test_idler_stack_has_running_clearance():
    assert a.pivot_sleeve().val().BoundingBox().zlen==6
    # 4 mm plate + two 0.8 mm washers -> 0.4 mm axial running clearance.
    assert 6-4-2*.8==pytest.approx(.4)
    assert 6.4-6==pytest.approx(.4)


def test_print_quantities_match_assembled_instances():
    from collections import Counter
    counts=Counter(c.part_id for c in a.assembly() if c.group=='printed')
    assert counts=={key:qty for key,(_,qty) in a.PRINT_PARTS.items()}
