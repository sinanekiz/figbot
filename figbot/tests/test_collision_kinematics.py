from math import pi

from simulation.collision import CollisionChecker
from software.kinematics import ArmKinematics, JointState


def test_nominal_observation_pose_clears_all_proxy_objects():
    arm = ArmKinematics()
    result = arm.inverse(0.30, 0.0, 0.36, tool_pitch=-pi / 2)
    assert result.success and result.joints is not None
    report = CollisionChecker(arm).check(result.joints)
    assert not report.collision, report.contacts


def test_ground_penetration_is_rejected():
    arm = ArmKinematics()
    # All angles are within current digital limits, but the folded chain enters
    # the ground. This checks geometry independently from joint-limit checks.
    joints = JointState(0.0, -0.55, -1.60, 0.0)
    assert arm.within_limits(joints)
    report = CollisionChecker(arm).check(joints)
    assert report.collision
    assert "ground" in report.contacts


def test_proxy_set_covers_required_v0_obstacles():
    checker = CollisionChecker(ArmKinematics())
    names = {proxy.name for proxy in checker.boxes} | {proxy.name for proxy in checker.cylinders}
    assert {"base", "chassis", "camera", "funnel"} <= names

