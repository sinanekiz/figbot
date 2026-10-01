import math

from software.rover.ackermann import command_from_twist


def test_straight_command_has_equal_rear_speed():
    command = command_from_twist(0.4, 0.0)
    assert not command.stopped
    assert command.front_left_rad == 0
    assert command.front_right_rad == 0
    assert command.rear_left_rad_s == command.rear_right_rad_s


def test_left_turn_uses_larger_inner_angle_and_faster_outer_wheel():
    command = command_from_twist(0.4, 0.4)
    assert 0 < command.front_right_rad < command.front_left_rad
    assert command.rear_right_rad_s > command.rear_left_rad_s > 0


def test_right_turn_is_symmetric():
    left = command_from_twist(0.4, 0.4)
    right = command_from_twist(0.4, -0.4)
    assert math.isclose(left.front_left_rad, -right.front_right_rad)
    assert math.isclose(left.front_right_rad, -right.front_left_rad)
    assert math.isclose(left.rear_left_rad_s, right.rear_right_rad_s)


def test_steering_limit_is_enforced():
    command = command_from_twist(0.2, 0.5)
    assert not command.stopped
    assert max(abs(command.front_left_rad), abs(command.front_right_rad)) <= math.radians(30) + 1e-12


def test_pivot_and_bad_geometry_fail_safe():
    assert command_from_twist(0.0, 1.0).stopped
    assert command_from_twist(0.2, 0.1, wheelbase_m=-1).stopped
    assert command_from_twist(float("nan"), 0.0).stopped
