from cad.config import parameters as p
from cad.prototype_arm.build_servo_arm import prototype_arm_components, prototype_arm_shape
from cad.rover.build_p0_rover import components as rover_components


def test_rev_g_test_arm_uses_four_main_servos_and_one_light_gripper_servo():
    components = prototype_arm_components()
    assert {name for name in components if name.startswith("PUR-MG996R-")} == {
        "PUR-MG996R-J1",
        "PUR-MG996R-J2-A",
        "PUR-MG996R-J2-B",
        "PUR-MG996R-J3",
    }
    assert "PUR-MG90S-G1" in components
    assert any("COUNTERBALANCE" in name for name in components)
    assert any("PARALLEL" in name for name in components)


def test_rev_g_test_arm_retains_controlled_605_mm_nominal_reach():
    assert p.ARM_UPPER_LENGTH + p.ARM_FORE_LENGTH + p.ARM_TOOL_LENGTH == 605.0
    box = prototype_arm_shape().val().BoundingBox()
    assert box.xlen > 400.0
    assert box.zlen > 200.0


def test_mg996r_packaging_interface_is_explicit():
    assert (p.TEST_ARM_SERVO_LENGTH, p.TEST_ARM_SERVO_WIDTH, p.TEST_ARM_SERVO_HEIGHT) == (40.7, 19.7, 42.9)
    assert p.TEST_ARM_SERVO_SPLINE_DIAMETER == 6.0


def test_rev_g_command_lanes_are_outside_basket_sides_and_ahead_of_front_wheels():
    basket_side = p.P0_BASKET_WIDTH / 2
    assert p.P0_LEFT_ARM_PICK_Y_RANGE[0] > basket_side
    assert p.P0_RIGHT_ARM_PICK_Y_RANGE[1] < -basket_side
    assert p.P0_ARM_PICK_X_RANGE[0] > p.P0_FRONT_AXLE_X + p.P0_WHEEL_DIAMETER / 2


def test_representative_ground_pose_does_not_intersect_basket():
    components = rover_components()
    basket = components["P0-BASKET"][0]
    for name in ("P0-ARM-MG996R-PROTOTYPE-L", "P0-ARM-MG996R-PROTOTYPE-R"):
        assert components[name][0].intersect(basket).val().Volume() < 1e-6
