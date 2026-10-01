"""Deterministic Ackermann steering conversion for the P0 rover.

The module deliberately rejects pivot-in-place requests: the selected front-steer
geometry cannot rotate like a differential-drive robot.
"""

from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class RoverCommand:
    front_left_rad: float
    front_right_rad: float
    rear_left_rad_s: float
    rear_right_rad_s: float
    stopped: bool
    reason: str = ""


def stopped_command(reason: str) -> RoverCommand:
    return RoverCommand(0.0, 0.0, 0.0, 0.0, True, reason)


def command_from_twist(
    speed_m_s: float,
    yaw_rate_rad_s: float,
    *,
    wheelbase_m: float = 0.430,
    track_m: float = 0.670,
    wheel_radius_m: float = 0.127,
    max_steer_deg: float = 30.0,
) -> RoverCommand:
    values = (speed_m_s, yaw_rate_rad_s, wheelbase_m, track_m, wheel_radius_m, max_steer_deg)
    if not all(math.isfinite(value) for value in values):
        return stopped_command("non-finite input")
    if wheelbase_m <= 0 or track_m <= 0 or wheel_radius_m <= 0 or not 0 < max_steer_deg < 90:
        return stopped_command("invalid geometry")
    if abs(speed_m_s) < 1e-4:
        return stopped_command("front-steer platform cannot pivot in place")
    if abs(yaw_rate_rad_s) < 1e-5:
        omega = speed_m_s / wheel_radius_m
        return RoverCommand(0.0, 0.0, omega, omega, False)

    radius = speed_m_s / yaw_rate_rad_s
    if abs(radius) <= track_m / 2:
        return stopped_command("requested turn radius is inside rear axle")

    turn_sign = 1.0 if radius > 0 else -1.0
    center_radius = abs(radius)
    inner = math.atan(wheelbase_m / (center_radius - track_m / 2))
    outer = math.atan(wheelbase_m / (center_radius + track_m / 2))
    limit = math.radians(max_steer_deg)
    scale = min(1.0, limit / max(inner, outer))
    inner *= scale
    outer *= scale

    if turn_sign > 0:  # left turn: left wheel is inner
        front_left, front_right = inner, outer
        rear_left_linear = speed_m_s * (center_radius - track_m / 2) / center_radius
        rear_right_linear = speed_m_s * (center_radius + track_m / 2) / center_radius
    else:
        front_left, front_right = -outer, -inner
        rear_left_linear = speed_m_s * (center_radius + track_m / 2) / center_radius
        rear_right_linear = speed_m_s * (center_radius - track_m / 2) / center_radius

    return RoverCommand(
        front_left,
        front_right,
        rear_left_linear / wheel_radius_m,
        rear_right_linear / wheel_radius_m,
        False,
    )
