"""Synchronized, limit-aware smooth joint interpolation.

The planner is intentionally simple for V0: it produces a cubic smooth-step
trajectory in joint space and verifies sampled joint limits. Collision checks
are supplied by the simulation layer rather than hidden in this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil, sqrt
from typing import Callable

from software.kinematics.config import JointLimit
from software.kinematics.model import ArmKinematics, JointState


@dataclass(frozen=True)
class TrajectoryPoint:
    time_from_start: float
    joints: JointState


@dataclass(frozen=True)
class JointTrajectory:
    points: tuple[TrajectoryPoint, ...]
    duration: float
    cartesian_distance: float
    valid: bool
    reason: str


def _minimum_cubic_duration(distance: float, limit: JointLimit) -> float:
    if distance <= 1e-12:
        return 0.0
    # For s(u)=3u^2-2u^3: max(ds/du)=1.5 and max|d2s/du2|=6.
    velocity_time = 1.5 * distance / limit.max_velocity
    acceleration_time = sqrt(6.0 * distance / limit.max_acceleration)
    return max(velocity_time, acceleration_time)


def _interpolate(start: JointState, goal: JointState, fraction: float) -> JointState:
    smooth = 3.0 * fraction * fraction - 2.0 * fraction * fraction * fraction
    return JointState(*(a + (b - a) * smooth for a, b in zip(start.as_tuple(), goal.as_tuple())))


def plan_joint_trajectory(
    arm: ArmKinematics,
    start: JointState,
    goal: JointState,
    sample_period: float = 0.02,
    speed_scale: float = 0.8,
    collision_fn: Callable[[JointState], bool] | None = None,
) -> JointTrajectory:
    """Plan and validate one synchronized point-to-point move.

    ``speed_scale`` is capped at one. The 0.8 default leaves modelling margin;
    it is an ESTIMATE and must not be used as a physical controller guarantee.
    """

    if not 0.0 < speed_scale <= 1.0:
        raise ValueError("speed_scale must be in (0, 1]")
    if sample_period <= 0.0:
        raise ValueError("sample_period must be positive")
    if not arm.within_limits(start) or not arm.within_limits(goal):
        return JointTrajectory((), 0.0, 0.0, False, "JOINT_LIMIT")

    distances = [abs(b - a) for a, b in zip(start.as_tuple(), goal.as_tuple())]
    duration = max(
        (_minimum_cubic_duration(distance, limit) for distance, limit in zip(distances, arm.geometry.joint_limits)),
        default=0.0,
    ) / speed_scale
    duration = max(duration, sample_period)
    steps = max(1, int(ceil(duration / sample_period)))
    points: list[TrajectoryPoint] = []
    cartesian_distance = 0.0
    previous_pose = arm.forward(start)
    for index in range(steps + 1):
        fraction = index / steps
        joints = _interpolate(start, goal, fraction)
        if not arm.within_limits(joints):
            return JointTrajectory(tuple(points), duration, cartesian_distance, False, "JOINT_LIMIT")
        if collision_fn is not None and collision_fn(joints):
            return JointTrajectory(tuple(points), duration, cartesian_distance, False, "COLLISION")
        time_from_start = duration * fraction
        points.append(TrajectoryPoint(time_from_start, joints))
        pose = arm.forward(joints)
        cartesian_distance += pose.position_error(previous_pose)
        previous_pose = pose
    return JointTrajectory(tuple(points), duration, cartesian_distance, True, "OK")

