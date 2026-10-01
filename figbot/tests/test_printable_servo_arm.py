from cad.prototype_arm.build_printable_v1 import (
    BODY_CLEARANCE,
    MG90S_BODY,
    MG996R_BODY,
    MG90S_OPENING,
    MG996R_OPENING,
    PARTS,
    TUBE_SOCKET,
    assembly_shape,
)


def test_printable_v1_contains_fit_gate_and_complete_single_arm_part_set():
    fit_parts = {name for name, (_, _, phase) in PARTS.items() if phase == "PRINT FIRST"}
    structural_parts = {name for name, (_, _, phase) in PARTS.items() if phase == "AFTER FIT CHECK"}
    assert fit_parts == {
        "FIT-001-MG996R-PLATE",
        "FIT-002-MG996R-CLAMP",
        "FIT-003-MG90S-PLATE",
        "FIT-004-MG90S-CLAMP",
        "FIT-005-20MM-TUBE",
        "FIT-006-HORN-ADAPTER",
    }
    assert len(structural_parts) == 12


def test_printable_v1_uses_controlled_nominal_servo_envelopes_and_clearance():
    assert MG996R_BODY == (40.7, 19.7, 42.9)
    assert MG90S_BODY == (22.8, 12.2, 28.5)
    assert BODY_CLEARANCE == 0.8
    assert MG996R_OPENING == (41.5, 20.5)
    assert MG90S_OPENING == (23.6, 13.0)
    assert TUBE_SOCKET == 20.5


def test_every_printed_part_is_one_positive_solid_and_fits_common_bed_envelope():
    for part_id, (builder, _, _) in PARTS.items():
        value = builder().val()
        bounds = value.BoundingBox()
        assert len(value.Solids()) == 1, part_id
        assert value.Volume() > 500, part_id
        assert max(bounds.xlen, bounds.ylen, bounds.zlen) <= 120, part_id


def test_dual_shoulder_hubs_fit_inside_yoke_gap():
    upper_bounds = PARTS["PRT-G05-UPPER-LINK-HUB"][0]().val().BoundingBox()
    fore_bounds = PARTS["PRT-G07-FOREARM-LINK-HUB"][0]().val().BoundingBox()
    assert upper_bounds.ylen < 32.0
    assert fore_bounds.ylen < 32.0


def test_printable_v1_assembly_retains_long_reach_packaging():
    bounds = assembly_shape().val().BoundingBox()
    assert bounds.xlen >= 550
    assert bounds.zlen >= 180
