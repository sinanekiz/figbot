"""Forward and analytic inverse kinematics for a yaw + 3-pitch arm."""

from __future__ import annotations

from dataclasses import dataclass
from math import acos, atan2, cos, hypot, pi, sin, sqrt
from typing import Iterable, Sequence

from .config import ArmGeometry, load_arm_geometry


@dataclass(frozen=True)
class JointState:
    j1: float
    j2: float
    j3: float
    j4: float

    def as_tuple(self) -> tuple[float, float, float, float]:
        return (self.j1, self.j2, self.j3, self.j4)


@dataclass(frozen=True)
class Pose:
    x: float
    y: float
    z: float
    tool_pitch: float

    def position_error(self, other: "Pose") -> float:
        return sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2 + (self.z - other.z) ** 2)


@dataclass(frozen=True)
class IKResult:
    success: bool
    joints: JointState | None
    position_error: float
    reason: str
    branch: str = ""


def _angle_distance(a: float, b: float) -> float:
    return abs((a - b + pi) % (2 * pi) - pi)


class ArmKinematics:
    """Kinematics using radians and metres.

    J1 yaws about +Z. J2/J3/J4 pitch in a radial vertical plane. A zero
    pitch chain points horizontally away from the base.
    """

    def __init__(self, geometry: ArmGeometry | None = None) -> None:
        self.geometry = geometry or load_arm_geometry()

    def within_limits(self, joints: JointState) -> bool:
        return all(limit.contains(value) for limit, value in zip(self.geometry.joint_limits, joints.as_tuple()))

    def forward(self, joints: JointState) -> Pose:
        q1, q2, q3, q4 = joints.as_tuple()
        a23 = q2 + q3
        pitch = a23 + q4
        radial = (
            self.geometry.upper_arm * cos(q2)
            + self.geometry.forearm * cos(a23)
            + self.geometry.tool * cos(pitch)
        )
        z = (
            self.geometry.base_height
            + self.geometry.upper_arm * sin(q2)
            + self.geometry.forearm * sin(a23)
            + self.geometry.tool * sin(pitch)
        )
        return Pose(radial * cos(q1), radial * sin(q1), z, pitch)

    def link_points(self, joints: JointState) -> tuple[tuple[float, float, float], ...]:
        """Return base, shoulder, elbow, wrist and tool-tip points."""

        q1, q2, q3, q4 = joints.as_tuple()
        direction = (cos(q1), sin(q1))
        shoulder = (0.0, 0.0, self.geometry.base_height)
        r1 = self.geometry.upper_arm * cos(q2)
        z1 = self.geometry.base_height + self.geometry.upper_arm * sin(q2)
        elbow = (r1 * direction[0], r1 * direction[1], z1)
        a23 = q2 + q3
        r2 = r1 + self.geometry.forearm * cos(a23)
        z2 = z1 + self.geometry.forearm * sin(a23)
        wrist = (r2 * direction[0], r2 * direction[1], z2)
        pitch = a23 + q4
        r3 = r2 + self.geometry.tool * cos(pitch)
        z3 = z2 + self.geometry.tool * sin(pitch)
        tool = (r3 * direction[0], r3 * direction[1], z3)
        return ((0.0, 0.0, 0.0), shoulder, elbow, wrist, tool)

    def inverse(
        self,
        x: float,
        y: float,
        z: float,
        tool_pitch: float | None = None,
        seed: JointState | None = None,
        tolerance: float = 1e-6,
    ) -> IKResult:
        """Solve position and tool pitch, trying both elbow branches.

        When ``tool_pitch`` is omitted, a small deterministic orientation set
        is searched, preferring a downward gripper appropriate for ground
        pickup. The best valid solution is selected by seed distance.
        """

        radial = hypot(x, y)
        q1 = atan2(y, x)
        if not self.geometry.joint_limits[0].contains(q1):
            return IKResult(False, None, float("inf"), "J1_LIMIT")

        pitches: Sequence[float]
        if tool_pitch is None:
            pitches = (-pi / 2, -pi / 3, -pi / 4, 0.0, pi / 4)
        else:
            pitches = (tool_pitch,)

        candidates: list[tuple[float, JointState, float, str]] = []
        seed_values = seed.as_tuple() if seed else (q1, 0.0, 0.0, -pi / 2)
        l1, l2, l3 = self.geometry.upper_arm, self.geometry.forearm, self.geometry.tool

        for pitch in pitches:
            wrist_r = radial - l3 * cos(pitch)
            wrist_z = z - self.geometry.base_height - l3 * sin(pitch)
            cosine_elbow = (wrist_r * wrist_r + wrist_z * wrist_z - l1 * l1 - l2 * l2) / (2 * l1 * l2)
            if cosine_elbow < -1.0 - tolerance or cosine_elbow > 1.0 + tolerance:
                continue
            cosine_elbow = max(-1.0, min(1.0, cosine_elbow))
            elbow_magnitude = acos(cosine_elbow)
            for q3, branch in ((elbow_magnitude, "elbow_up"), (-elbow_magnitude, "elbow_down")):
                q2 = atan2(wrist_z, wrist_r) - atan2(l2 * sin(q3), l1 + l2 * cos(q3))
                q4 = pitch - q2 - q3
                joints = JointState(q1, q2, q3, q4)
                if not self.within_limits(joints):
                    continue
                pose = self.forward(joints)
                error = sqrt((pose.x - x) ** 2 + (pose.y - y) ** 2 + (pose.z - z) ** 2)
                distance = sum(_angle_distance(a, b) for a, b in zip(joints.as_tuple(), seed_values))
                candidates.append((distance, joints, error, branch))

        if not candidates:
            return IKResult(False, None, float("inf"), "OUT_OF_REACH_OR_JOINT_LIMIT")
        _, best, error, branch = min(candidates, key=lambda item: (item[0], item[2]))
        return IKResult(error <= tolerance, best, error, "OK" if error <= tolerance else "NUMERICAL_ERROR", branch)

    def reachable(self, point: Iterable[float], tool_pitch: float | None = None) -> bool:
        x, y, z = point
        return self.inverse(float(x), float(y), float(z), tool_pitch=tool_pitch).success

