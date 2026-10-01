from math import pi

import pytest

from software.kinematics import ArmKinematics, JointState


@pytest.mark.parametrize(
    "target",
    [
        (0.30, 0.00, 0.035),
        (0.38, 0.16, 0.045),
        (0.42, -0.12, 0.050),
        (0.22, 0.20, 0.125),
    ],
)
def test_inverse_solution_round_trips_through_forward_kinematics(target):
    arm = ArmKinematics()
    result = arm.inverse(*target, tool_pitch=-pi / 2)
    assert result.success, result.reason
    assert result.joints is not None
    assert arm.within_limits(result.joints)
    pose = arm.forward(result.joints)
    assert pose.position_error(type(pose)(*target, -pi / 2)) < 1e-6
    assert abs(pose.tool_pitch + pi / 2) < 1e-9


def test_seed_selects_a_nearby_valid_branch_without_changing_target():
    arm = ArmKinematics()
    seed = JointState(0.0, 0.5, -1.2, -0.8)
    result = arm.inverse(0.32, 0.0, 0.04, tool_pitch=-pi / 2, seed=seed)
    assert result.success
    assert result.joints is not None
    assert arm.forward(result.joints).position_error(type(arm.forward(result.joints))(0.32, 0.0, 0.04, -pi / 2)) < 1e-6


def test_unreachable_target_fails_explicitly():
    result = ArmKinematics().inverse(1.5, 0.0, 0.0, tool_pitch=-pi / 2)
    assert not result.success
    assert result.joints is None
    assert result.reason == "OUT_OF_REACH_OR_JOINT_LIMIT"


def test_j1_limit_is_enforced():
    result = ArmKinematics().inverse(-0.30, 0.0, 0.10)
    assert not result.success
    assert result.reason == "J1_LIMIT"

