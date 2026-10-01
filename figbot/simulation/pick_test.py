"""Deterministic virtual pick-cycle simulation for FIGBOT V0."""

from __future__ import annotations

from dataclasses import dataclass
from math import pi
from random import Random

from software.kinematics.model import ArmKinematics, JointState
from software.trajectory.planner import plan_joint_trajectory
from simulation.collision import CollisionChecker


@dataclass(frozen=True)
class Target:
    identifier: str
    x: float
    y: float
    z: float


@dataclass(frozen=True)
class PickResult:
    target: Target
    reachable: bool
    ik_success: bool
    collision: bool
    travel_distance: float | None
    cycle_time: float | None
    status: str
    contacts: tuple[str, ...]


@dataclass(frozen=True)
class CycleConfiguration:
    name: str
    hopper_approach: tuple[float, float, float]
    hopper_drop: tuple[float, float, float]
    approach_height: float = 0.10
    lift_height: float = 0.12
    grip_time: float = 0.35
    release_time: float = 0.20
    perception_overlap_residual: float = 0.10
    speed_scale: float = 0.90


BALANCED_NEAR_FUNNEL = CycleConfiguration(
    name="balanced_near_funnel",
    # The CAD funnel center is (-0.12, 0.25, 0.21) m. The drop point is moved
    # 110 mm toward its inner rim: the exact center exceeds the current J1
    # software limit by about 0.6 degrees.
    hopper_approach=(-0.01, 0.25, 0.36),
    hopper_drop=(-0.01, 0.25, 0.28),
)


def generate_targets(count: int = 100, seed: int = 20260820) -> list[Target]:
    """Generate the repeatable V0 floor test population in metres."""

    rng = Random(seed)
    try:
        from cad.config import parameters

        x_range = tuple(float(value) / 1000.0 for value in parameters.TARGET_ZONE_X_RANGE)
        y_range = tuple(float(value) / 1000.0 for value in parameters.TARGET_ZONE_Y_RANGE)
        nominal_z = float(parameters.TARGET_ZONE_Z) / 1000.0
    except (ImportError, AttributeError, TypeError, ValueError):
        x_range = (0.12, 0.50)
        y_range = (-0.30, 0.30)
        nominal_z = 0.020
    targets: list[Target] = []
    for index in range(count):
        # X/Y are the full CAD target zone. Height variation above its nominal
        # Z plane is an ESTIMATE representing different fruit profiles.
        x = rng.uniform(*x_range)
        y = rng.uniform(*y_range)
        z = rng.uniform(nominal_z, nominal_z + 0.035)
        targets.append(Target(f"T{index + 1:03d}", x, y, z))
    return targets


class PickSimulator:
    def __init__(self, arm: ArmKinematics, configuration: CycleConfiguration = BALANCED_NEAR_FUNNEL) -> None:
        self.arm = arm
        self.configuration = configuration
        self.collision = CollisionChecker(arm)

    def _solve(self, point: tuple[float, float, float], seed: JointState | None = None):
        return self.arm.inverse(*point, tool_pitch=-pi / 2, seed=seed)

    def run_target(self, target: Target) -> PickResult:
        cfg = self.configuration
        pick_point = (target.x, target.y, target.z)
        approach_point = (target.x, target.y, target.z + cfg.approach_height)
        lift_point = (target.x, target.y, target.z + cfg.lift_height)

        # Steady-state closed cycle: the preceding fruit was just released at
        # the hopper. The next target is already available from overlapped
        # perception, so the arm moves directly to its approach pose.
        cycle_start = self._solve(cfg.hopper_drop)
        approach = self._solve(approach_point, cycle_start.joints)
        pick = self._solve(pick_point, approach.joints)
        lift = self._solve(lift_point, pick.joints)
        hopper_approach = self._solve(cfg.hopper_approach, lift.joints)
        hopper_drop = self._solve(cfg.hopper_drop, hopper_approach.joints)
        results = (cycle_start, approach, pick, lift, hopper_approach, hopper_drop)
        if not all(result.success and result.joints is not None for result in results):
            return PickResult(target, False, False, False, None, None, "IK_FAILED", ())

        states = [result.joints for result in results]
        assert all(state is not None for state in states)
        typed_states = [state for state in states if state is not None]
        paths = []
        contacts: set[str] = set()
        for index, (start, goal) in enumerate(zip(typed_states, typed_states[1:])):
            # The initial and final paths intentionally enter/leave the funnel
            # drop volume. Other proxies remain active throughout.
            ignore = frozenset({"funnel"}) if index == 0 or index >= 3 else frozenset()
            path = plan_joint_trajectory(
                self.arm,
                start,
                goal,
                speed_scale=cfg.speed_scale,
                collision_fn=lambda joints, ignored=ignore: self.collision.collides(joints, ignored),
            )
            paths.append(path)
            if not path.valid:
                report = self.collision.check(goal, ignore=ignore)
                contacts.update(report.contacts or (path.reason.lower(),))
                return PickResult(target, True, True, True, None, None, "COLLISION_REJECTED", tuple(sorted(contacts)))

        travel = sum(path.cartesian_distance for path in paths)
        motion_time = sum(path.duration for path in paths)
        cycle_time = motion_time + cfg.grip_time + cfg.release_time + cfg.perception_overlap_residual
        return PickResult(target, True, True, False, travel, cycle_time, "SUCCESS", ())

    def run(self, targets: list[Target]) -> list[PickResult]:
        return [self.run_target(target) for target in targets]
