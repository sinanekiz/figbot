"""Workspace sampling and geometry comparison helpers."""

from __future__ import annotations

from dataclasses import dataclass
from math import pi
from random import Random
from typing import Iterable

from .model import ArmKinematics, JointState


@dataclass(frozen=True)
class WorkspaceStats:
    samples: int
    reachable: int
    reach_fraction: float
    max_reachable_radius: float


def evaluate_box(
    arm: ArmKinematics,
    x_range: tuple[float, float],
    y_range: tuple[float, float],
    z_range: tuple[float, float],
    samples: int = 2000,
    seed: int = 42,
) -> WorkspaceStats:
    rng = Random(seed)
    reachable = 0
    max_radius = 0.0
    for _ in range(samples):
        x = rng.uniform(*x_range)
        y = rng.uniform(*y_range)
        z = rng.uniform(*z_range)
        result = arm.inverse(x, y, z)
        if result.success:
            reachable += 1
            max_radius = max(max_radius, (x * x + y * y) ** 0.5)
    return WorkspaceStats(samples, reachable, reachable / samples if samples else 0.0, max_radius)


def sample_reachability_cloud(
    arm: ArmKinematics,
    angular_steps: tuple[int, int, int, int] = (13, 9, 9, 7),
) -> list[tuple[float, float, float]]:
    """Generate a dependency-free 3D reachability point cloud."""

    values: list[list[float]] = []
    for limit, count in zip(arm.geometry.joint_limits, angular_steps):
        values.append([limit.lower + (limit.upper - limit.lower) * i / (count - 1) for i in range(count)])
    points: list[tuple[float, float, float]] = []
    # Reduce redundant J4 samples while preserving the full envelope.
    for j1 in values[0]:
        for j2 in values[1]:
            for j3 in values[2]:
                for j4 in values[3]:
                    pose = arm.forward(JointState(j1, j2, j3, j4))
                    if pose.z >= 0.0:
                        points.append((pose.x, pose.y, pose.z))
    return points
