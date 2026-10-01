"""R5 interface and load-path regressions, not physical strength certification.

The assertions inspect solids and contact paths. They do not infer permissible
payload, fatigue life or a validated fit from digital geometry.
"""
import math

import cadquery as cq
import pytest

from cad.prototype_arm import build_forma_v6 as arm
from cad.prototype_arm import forma_v6_horns as horns


def volume(shape):
    return sum(s.Volume() for s in shape.solids().vals())


def section(shape, x):
    # A finite slice avoids tolerance-sensitive coincident zero-thickness faces.
    return shape.intersect(arm.box(.2, 180, 120, (x, 0, 0)))


def test_retainer_and_base_stay_inside_existing_rounded_footprint():
    footprint = arm.rounded(120, 120, 180, 14, (0, 0, 60))
    for shape in [arm.base(), arm.retainer()]:
        assert volume(shape.cut(footprint)) < 1e-5
    # Preserve the fixed mounting pattern; trimming the outline must not remove
    # any of the four screw lands or expose the mounting screw to the edge.
    for angle in [45, 135, 225, 315]:
        t = math.radians(angle)
        x, y = 65 * math.cos(t), 65 * math.sin(t)
        land = arm.cz(4.8, 62, 2, x, y).cut(arm.cz(1.7, 61, 4, x, y))
        assert volume(land.cut(arm.retainer())) < 1e-5


def test_retainer_roof_is_thicker_without_reducing_running_clearance():
    roof = arm.retainer().intersect(arm.ring(53.2, 54.8, 57, 12))
    bb = roof.val().BoundingBox()
    assert bb.zmin == pytest.approx(61.4, abs=1e-6)
    assert bb.zmax == pytest.approx(66.5, abs=1e-6)
    assert bb.zlen == pytest.approx(5.1, abs=1e-6)
    # The upper lip is continuous around the retained flange before the two
    # assembly halves are cut, not four isolated screw pads.
    assert len(roof.solids().vals()) == 1
    ledge = arm.rotor().intersect(arm.ring(53.2, 54.8, 57, 3.5))
    assert ledge.val().BoundingBox().zmax == pytest.approx(60.4, abs=1e-6)


def test_continuous_yaw_swept_bound_clears_retainer_and_keeps_capture():
    # Two cylindrical envelopes conservatively enclose EVERY angular position
    # of the actual rotor within the retainer's height. Unlike a few rendered
    # poses, this bound checks the full 360 degrees of yaw, including .9mm lift.
    rotor = arm.rotor()
    lower = rotor.intersect(arm.box(200, 200, 9.4, (0, 0, 55.7)))
    upper = rotor.intersect(arm.box(200, 200, 6.1, (0, 0, 63.45)))
    # R5 trims only post corners beyondR57.6; retaining flange remainsR55.
    # The previousR59.9 corner envelope collided with the newR58 relief during
    # uplift. Keep this tighter bound on the ACTUAL material, not on the test.
    assert volume(lower.cut(arm.cz(57.6, 51, 9.4))) < 1e-5
    assert volume(upper.cut(arm.cz(52.6, 60.4, 6.1))) < 1e-5
    swept = arm.cz(57.6, 51, 10.3).union(arm.cz(52.6, 60.4, 7.0))
    assert volume(swept.intersect(arm.retainer())) < 1e-5
    flange = arm.ring(53.2, 54.8, 57.5, 2.5)
    assert volume(flange.cut(rotor)) < 1e-5
    # Clearance is not achieved by deleting the retaining lip: excess uplift
    # still brings the flange into the retaining roof.
    raised = rotor.translate((0, 0, 1.6))
    for side in [-1, 1]:
        assert volume(raised.intersect(arm.retainer_half(side))) > 1


@pytest.mark.parametrize('make,span', [(arm.upper, arm.UPPER), (arm.fore, arm.FORE)])
def test_reinforcement_is_local_and_midspan_remains_hollow(make, span):
    shape = make()
    middle = section(shape, span / 2)
    root = section(shape, 35)
    middle_area, root_area = volume(middle) / .2, volume(root) / .2
    assert 90 < middle_area < 225
    assert root_area > 1.8 * middle_area
    assert root_area > 300
    # A real open internal passage must remain; an indiscriminately solid beam
    # could otherwise meet section-area/valid-solid tests at excessive mass.
    core = arm.box(20, 12, 12, (span / 2, 0, 0))
    assert volume(shape.intersect(core)) < 1e-5
    bottom = arm.box(2, 4, .3, (span / 2, 0, -12.5 if span == arm.FORE else -15.5))
    assert volume(bottom.cut(shape)) < 1e-5


@pytest.mark.parametrize('make,span', [(arm.upper, arm.UPPER), (arm.fore, arm.FORE)])
def test_distal_fork_has_real_lower_load_path_and_wider_motor_seat(make, span):
    shape = make()
    sliced = section(shape, span - 10)
    passive = sliced.intersect(arm.box(1, 40, 50, (span - 10, -30, -10)))
    assert len(passive.solids().vals()) == 1
    bb = passive.val().BoundingBox()
    # Previous 4x12mm web had48mm². Check the actual strengthened rounded
    # section, not merely its nominal bounding box or a changed parameter.
    assert bb.ylen >= 5.99 and bb.zlen >= 15.99
    assert volume(passive) / .2 > 80
    positive = sliced.intersect(arm.box(1, 50, 35, (span - 10, 35, 17.5)))
    assert len(positive.solids().vals()) == 1
    assert positive.val().BoundingBox().zlen >= 5.59
    assert volume(positive) / .2 > 38
    # Added web/seat unions must not refill the motor body or factory flange.
    micro = span == arm.FORE
    motor = arm.side_place(arm.servo(micro), 1, (span, 20 if micro else 24, 0))
    assert volume(shape.intersect(motor)) < 1e-5


def test_elbow_moving_mass_budget_is_not_traded_away_for_reinforcement():
    from cad.prototype_arm.validate_forma_v6 import gravity
    report = gravity((0, 0, 0, 0))
    assert report['modeled_mass_g']['elbow'] < 150


@pytest.mark.parametrize('micro', [False, True])
def test_original_horn_reference_and_centre_screw_access(micro):
    horn, receiver = horns.horn(micro), horns.receiver(micro)
    assert len(horn.solids().vals()) == len(receiver.solids().vals()) == 1
    assert horn.val().isValid() and receiver.val().isValid()
    assert volume(horn.intersect(receiver)) < 1e-5
    # Seven-millimetre access opens through the receiving floor. The original
    # central fastener is separately present, not hidden inside printed plastic.
    tool = arm.cz(3.5, horns.MATING_Z, 5.5)
    assert volume(tool.intersect(receiver)) < 1e-5
    centres = [(name, s) for name, s in horns.hardware(micro) if 'centre screw' in name]
    assert {name for name, _ in centres} == {'original centre screw head', 'original centre screw shank'}
    for _, shape in centres:
        assert volume(shape.intersect(receiver)) < 1e-5
    for name, shape in horns.hardware(micro):
        assert volume(shape.intersect(horn)) < 1e-5, name
    for name, shape in horns.fastener_heads(micro):
        assert volume(shape.intersect(receiver)) < 1e-5, name


def test_large_star_is_keyed_and_external_screws_avoid_factory_holes():
    original_holes = horns.source_holes(False)
    points = horns.points(False)
    assert len(original_holes) == 6 and len(points) == 2
    for x, y in points:
        assert all(math.hypot(x-hx,y-hy)>5 for hx,hy,r in original_holes)
        receiver = horns.receiver(False).val()
        assert not receiver.isInside(cq.Vector(x, y, 8))
        assert receiver.isInside(cq.Vector(x, y, 12.5))
    for angle in [-3,3]:
        assert volume(horns.horn(False).rotate((0,0,0),(0,0,1),angle).intersect(horns.receiver(False)))>1


def test_micro_star_factory_holes_remain_undrilled_with_external_retention():
    horn, receiver = horns.horn(True), horns.receiver(True)
    for x, y, radius in horns.source_holes(True):
        assert .49 < radius < .51
        hole = arm.cz(.48, 5.9, 1.5, x, y)
        assert volume(horn.intersect(hole)) < 1e-5
        # Material at .7mm radius proves that the original1mm hole was NOT
        # silently enlarged to accept an M2 shank.
        annulus = arm.ring(.6, .8, 5.9, 1.5).translate((x, y, 0))
        assert volume(annulus.cut(horn)) < 1e-5
    hardware = horns.hardware(True)
    for name, part in hardware:
        if 'mounting shank' in name or 'retaining washer' in name:
            assert volume(part.intersect(horn)) < 1e-5
    assert not any('washer' in name for name,_ in hardware)
    # Axial withdrawal must encounter the enclosure cover; angular movement must
    # encounter the shaped wall. These are contact checks, not strength claims.
    withdrawn = horn.translate((0, 0, -.25))
    assert volume(withdrawn.intersect(horns.closure(True))) > 1
    for angle in [-3, 3]:
        rotated = horn.rotate((0, 0, 0), (0, 0, 1), angle)
        assert volume(rotated.intersect(receiver)) > 1


@pytest.mark.parametrize('make,micro,side,origin,back_top', [
    (arm.rotor, False, 0, (0, 0, 50), 13.0),
    (arm.upper, False, -1, (0, -24, 0), 13.0),
    (arm.upper, False, 1, (0, 24, 0), 13.0),
    (arm.fore, False, 1, (0, 24, 0), 13.0),
    (arm.palm, True, 1, (0, 20, 0), 13.0),
    (arm.spool, True, 0, (0, 0, -7.5), 13.0),
])
def test_finished_parts_keep_horn_pilots_open_and_blind_backwalls(
        make, micro, side, origin, back_top):
    # Checking an isolated receiver missed a genuine regression: subsequently
    # united root webs refilled the +X holes. Probe FINAL PRINTED PART solids.
    shape = make()
    place = (lambda s: arm.side_place(s, side, origin)) if side else (lambda s: s.translate(origin))
    entry = horns.cover_top(micro)
    for x, y in horns.points(micro):
        pilot = place(arm.cz(1.3, entry + .1, 3.8, x, y))
        assert volume(pilot.intersect(shape)) < 1e-5
        # Keep the full intended blind floor behind the4mm insert, not merely
        # an infinitesimal residual face which would pass a point test.
        back_start = entry + 4.35
        back = place(arm.cz(1.3, back_start + .1, back_top - back_start - .2, x, y))
        assert volume(back.cut(shape)) < 1e-5
    tool = place(arm.cz(3.49, 7.5, 5.5))
    assert volume(tool.intersect(shape)) < 1e-5


def test_spool_cord_routes_do_not_cross_insert_bosses_or_horn_hardware():
    spool = arm.spool()
    transform = lambda s: s.translate((0, 0, -7.5))
    obstacles = [transform(s) for _, s in horns.hardware(True)] + [transform(horns.horn(True))]
    for x, y in horns.points(True):
        # This outer envelope includes the physical brass insert, the plastic
        # blind floor and its remaining supporting boss.
        obstacles.append(transform(arm.cz(3.2, 5.85, 7.15, x, y)))
    for angle in [30, 150, 270]:
        t = math.radians(angle)
        cord = arm.cz(.55, 5.5, 10, 10.4 * math.cos(t), 10.4 * math.sin(t))
        assert volume(cord.intersect(spool)) < 1e-5
        assert all(volume(cord.intersect(obstacle)) < 1e-5 for obstacle in obstacles)
    # All three winding lanes remain genuinely open above the backing plate.
    for low, high in [(6.7, 9.1), (9.6, 11.7), (12.2, 14.3)]:
        lane = arm.ring(9.51, 11.49, low + .01, high - low - .02)
        assert volume(lane.intersect(spool)) < 1e-5
        assert all(volume(lane.intersect(obstacle)) < 1e-5 for obstacle in obstacles)
