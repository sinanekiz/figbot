from math import pi

from simulation.collision import CollisionChecker
from simulation.pick_test import PickSimulator, generate_targets
from software.kinematics import ArmKinematics
from software.trajectory import plan_joint_trajectory


def test_safe_joint_trajectory_obeys_limits_and_endpoints():
    arm = ArmKinematics()
    start = arm.inverse(0.30, 0.0, 0.36, tool_pitch=-pi / 2)
    goal = arm.inverse(0.34, 0.10, 0.18, tool_pitch=-pi / 2, seed=start.joints)
    assert start.joints is not None and goal.joints is not None
    checker = CollisionChecker(arm)
    trajectory = plan_joint_trajectory(arm, start.joints, goal.joints, collision_fn=checker.collides)
    assert trajectory.valid, trajectory.reason
    assert trajectory.duration > 0.0
    assert trajectory.points[0].joints == start.joints
    assert trajectory.points[-1].joints == goal.joints
    assert all(arm.within_limits(point.joints) for point in trajectory.points)


def test_pick_simulation_is_deterministic_and_records_required_fields():
    arm = ArmKinematics()
    targets_a = generate_targets(count=5)
    targets_b = generate_targets(count=5)
    assert targets_a == targets_b
    results = PickSimulator(arm).run(targets_a)
    assert len(results) == 5
    assert all(result.reachable and result.ik_success for result in results)
    assert all(result.travel_distance is not None and result.travel_distance > 0 for result in results)
    assert all(result.cycle_time is not None and result.cycle_time > 0 for result in results)

