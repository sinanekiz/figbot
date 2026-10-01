from cad.prototype_arm.build_aero_v2 import (
    FAIRING_WALL,
    FOREARM_LINK_LENGTH,
    GRIPPER_LINK_CENTRE_DISTANCE,
    MG90S_BODY,
    PARTS,
    TOOL_LENGTH,
    UPPER_LINK_LENGTH,
    assembly_components,
    assembly_shape,
)


def test_aero_v2_retains_the_controlled_reach_dimensions():
    assert UPPER_LINK_LENGTH == 300.0
    assert FOREARM_LINK_LENGTH == 220.0
    assert TOOL_LENGTH == 85.0
    assert FAIRING_WALL == 0.8
    assert round(GRIPPER_LINK_CENTRE_DISTANCE, 3) == 30.017


def test_aero_v2_print_parts_are_closed_positive_solids_on_common_bed():
    for part_id, (builder, _, _) in PARTS.items():
        value = builder().val()
        bounds = value.BoundingBox()
        assert len(value.Solids()) == 1, part_id
        assert value.Volume() > 450, part_id
        assert max(bounds.xlen, bounds.ylen, bounds.zlen) <= 120, part_id


def test_gripper_has_distinct_mirrored_curved_jaws_and_links():
    left = PARTS["PRT-H10-GRIPPER-JAW-LEFT"][0]().val().BoundingBox()
    right = PARTS["PRT-H11-GRIPPER-JAW-RIGHT"][0]().val().BoundingBox()
    assert left.xlen == right.xlen
    assert left.zlen >= 75
    assert PARTS["PRT-H12-GRIPPER-LINK"][1] == 2
    link = PARTS["PRT-H12-GRIPPER-LINK"][0]().val().BoundingBox()
    assert 39 < link.xlen < 41


def test_servo_reference_models_are_visible_but_not_print_parts():
    component_names = {component.name for component in assembly_components()}
    assert "J1 MG996R-case" in component_names
    assert "J2L MG996R-case" in component_names
    assert "J2R MG996R-case" in component_names
    assert "J3 MG996R-case" in component_names
    assert "G1 MG90S-case" in component_names
    assert "MG90S retaining saddle" in component_names
    assert not any("SERVO-BODY" in part_id for part_id in PARTS)


def test_gripper_servo_has_a_printable_retaining_saddle():
    assert "PRT-H16-MG90S-SERVO-SADDLE" in PARTS
    saddle = PARTS["PRT-H16-MG90S-SERVO-SADDLE"][0]().val()
    assert len(saddle.Solids()) == 1
    assert saddle.BoundingBox().ylen >= MG90S_BODY[2]


def test_gripper_servo_shaft_physically_meets_the_horn_reference():
    components = {component.name: component.shape.val() for component in assembly_components()}
    overlap = components["G1 MG90S-shaft"].intersect(components["gripper servo horn"]).Volume()
    assert overlap > 1.0
    assert "wrist-to-palm lower pin" in components
    assert "wrist-to-palm upper pin" in components


def test_counterbalance_has_printed_anchor_and_visible_elastic_reference():
    assert "PRT-H17-COUNTERBALANCE-TUBE-ANCHOR" in PARTS
    component_names = {component.name for component in assembly_components()}
    assert "adjustable counterbalance tube anchor" in component_names
    assert "elastic counterbalance reference" in component_names


def test_mg996r_reference_shafts_meet_joint_horns():
    components = {component.name: component.shape.val() for component in assembly_components()}
    for shaft_name, horn_name in (
        ("J2L MG996R-shaft", "J2 horn"),
        ("J2R MG996R-shaft", "J2 horn"),
        ("J3 MG996R-shaft", "J3 horn"),
    ):
        assert components[shaft_name].distance(components[horn_name]) == 0.0


def test_optional_hollow_fairings_remain_a_small_mass_addition():
    density = 1.27
    mass = 0.0
    for _, (builder, qty, phase) in PARTS.items():
        if phase == "OPTIONAL COSMETIC":
            mass += builder().val().Volume() / 1000 * density * qty
    assert mass < 90


def test_aero_v2_assembly_is_a_long_reach_working_pose():
    bounds = assembly_shape().val().BoundingBox()
    assert bounds.xlen > 520
    assert bounds.zlen > 170
