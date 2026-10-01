"""Captive-socket and gradual-transition regressions; not strength certification."""
import pytest
from cad.prototype_arm import build_forma_v6 as a
from cad.prototype_arm import forma_v6_horns as h
from cad.prototype_arm.validate_forma_v6 import volume_overlap


@pytest.mark.parametrize('micro',[False,True])
def test_socket_enclosure_captures_horn_without_using_tiny_holes(micro):
    horn,seat,lid=h.horn(micro),h.receiver(micro),h.closure(micro)
    assert lid.val().isValid() and len(lid.solids().vals())==1
    assert volume_overlap(lid,horn)<1e-6 and volume_overlap(lid,seat)<1e-6
    assert volume_overlap(horn.translate((0,0,-.3)),lid)>1
    # Blocking extraction must not rely on the unmodeled tooth engagement.
    assert volume_overlap(horn.translate((0,0,.3)),seat)>1
    for name,bolt in h.hardware(micro):
        assert volume_overlap(bolt,horn)<1e-5,name
        assert volume_overlap(bolt,lid)<1e-5,name
    for x,y,r in h.source_holes(micro):
        probe=a.cz(r*.9,h.MATING_Z-1.5,1.4,x,y)
        assert volume_overlap(probe,horn)<1e-5
    # Receiver floor leaves access for the original centre screw and tool.
    assert volume_overlap(a.cz(3.49,7.5,5.5),seat)<1e-5


def test_closures_follow_outputs_and_are_counted_as_printed_mass():
    rows=[i for i in a.local_items() if 'SOCKET-COVER' in i.part_id]
    assert len(rows)==6
    assert [r.frame for r in rows]==['yaw','upper','upper','fore','tool','tool']
    assert all(r.mass_g is None for r in rows)


@pytest.mark.parametrize('make,span',[(a.upper,a.UPPER),(a.fore,a.FORE)])
def test_root_transition_has_no_old_abrupt_section_drop(make,span):
    shape=make()
    areas=[]
    for x in [48,50,52,54,56,58,60]:
        cut=shape.intersect(a.box(.2,100,100,(x,0,0)))
        areas.append(sum(s.Volume() for s in cut.solids().vals())/.2)
    # Two-millimetre sampling across the former abrupt X52 termination.
    assert max(abs(v-u) for u,v in zip(areas,areas[1:]))<45
    assert len(shape.solids().vals())==1 and shape.val().isValid()


def test_hardware_no_longer_requires_star_holes_or_special_rim_washers():
    from scripts.build_forma_v6_hardware import ROWS
    assert not any('wide washer' in r[0] or 'M2x5 screw'==r[0] for r in ROWS)
    assert next(r[1] for r in ROWS if r[0]=='M2x6 screw')==16
