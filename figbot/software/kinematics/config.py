"""Shared geometry and joint-limit configuration.

Lengths in this module are SI metres.  ``cad.config.parameters`` is the source
of truth when present; millimetre-valued CAD parameters are converted to SI.
The local defaults are deliberately labelled ESTIMATE / UNVERIFIED and keep
the simulation runnable while the mechanical design is being generated.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from math import radians
from types import ModuleType
from typing import Iterable


@dataclass(frozen=True)
class JointLimit:
    lower: float
    upper: float
    max_velocity: float
    max_acceleration: float

    def contains(self, value: float, tolerance: float = 1e-9) -> bool:
        return self.lower - tolerance <= value <= self.upper + tolerance


@dataclass(frozen=True)
class ArmGeometry:
    upper_arm: float
    forearm: float
    tool: float
    base_height: float
    joint_limits: tuple[JointLimit, JointLimit, JointLimit, JointLimit]
    source: str
    verification_status: str

    @property
    def maximum_reach(self) -> float:
        return self.upper_arm + self.forearm + self.tool


_DEFAULTS_MM = {
    "upper_arm": 280.0,
    "forearm": 250.0,
    "tool": 70.0,
    "base_height": 220.0,
}

_PARAMETER_NAMES = {
    "upper_arm": ("ARM_UPPER_LENGTH", "UPPER_ARM_LENGTH"),
    "forearm": ("ARM_FORE_LENGTH", "ARM_FOREARM_LENGTH", "FOREARM_LENGTH"),
    "tool": ("ARM_TOOL_LENGTH", "GRIPPER_TOOL_LENGTH", "WRIST_TOOL_LENGTH"),
    "base_height": ("ARM_BASE_HEIGHT", "SHOULDER_HEIGHT", "BASE_TO_SHOULDER_HEIGHT"),
}


def _as_metres(value: float) -> float:
    value = float(value)
    # CAD convention is millimetres.  Values under ten are accepted as SI to
    # make the adapter tolerant of a future explicitly-SI parameter module.
    return value / 1000.0 if abs(value) > 10.0 else value


def _first_attribute(module: ModuleType, names: Iterable[str], fallback_mm: float) -> tuple[float, bool]:
    for name in names:
        if hasattr(module, name):
            return _as_metres(getattr(module, name)), True
    return fallback_mm / 1000.0, False


def _default_joint_limits() -> tuple[JointLimit, JointLimit, JointLimit, JointLimit]:
    # ESTIMATE / UNVERIFIED: controller and mechanism stops must be reconciled
    # before commanding physical hardware.
    return (
        JointLimit(radians(-165), radians(165), radians(150), radians(300)),
        JointLimit(radians(-105), radians(105), radians(120), radians(240)),
        JointLimit(radians(-150), radians(150), radians(150), radians(300)),
        JointLimit(radians(-135), radians(135), radians(180), radians(360)),
    )


def _joint_limits_from_module(module: ModuleType) -> tuple[JointLimit, JointLimit, JointLimit, JointLimit]:
    limit_degrees = getattr(module, "JOINT_LIMITS_DEG", None)
    speed_degrees = getattr(module, "JOINT_MAX_SPEED_DEG_S", None)
    acceleration_degrees = getattr(module, "JOINT_MAX_ACCEL_DEG_S2", None)
    if not all(isinstance(item, dict) for item in (limit_degrees, speed_degrees, acceleration_degrees)):
        return _default_joint_limits()
    try:
        return tuple(
            JointLimit(
                radians(float(limit_degrees[name][0])),
                radians(float(limit_degrees[name][1])),
                radians(float(speed_degrees[name])),
                radians(float(acceleration_degrees[name])),
            )
            for name in ("J1", "J2", "J3", "J4")
        )  # type: ignore[return-value]
    except (KeyError, TypeError, ValueError):
        return _default_joint_limits()


def load_arm_geometry() -> ArmGeometry:
    """Load CAD geometry if available, otherwise return explicit estimates."""

    try:
        parameters = import_module("cad.config.parameters")
    except (ImportError, ModuleNotFoundError):
        return ArmGeometry(
            **{name: value / 1000.0 for name, value in _DEFAULTS_MM.items()},
            joint_limits=_default_joint_limits(),
            source="software.kinematics fallback estimates",
            verification_status="ESTIMATE / UNVERIFIED",
        )

    values: dict[str, float] = {}
    complete = True
    for key, names in _PARAMETER_NAMES.items():
        values[key], found = _first_attribute(parameters, names, _DEFAULTS_MM[key])
        complete &= found
    status = "CAD PARAMETER SOURCE / PHYSICAL VALIDATION REQUIRED"
    if not complete:
        status += " / PARTIAL ESTIMATE FALLBACK"
    return ArmGeometry(
        **values,
        joint_limits=_joint_limits_from_module(parameters),
        source="cad.config.parameters",
        verification_status=status,
    )


def geometry_variant(upper_arm: float, forearm: float, tool: float, base_height: float = 0.22) -> ArmGeometry:
    """Create a simulation-only geometry variant using SI metre inputs."""

    return ArmGeometry(
        upper_arm=upper_arm,
        forearm=forearm,
        tool=tool,
        base_height=base_height,
        joint_limits=_default_joint_limits(),
        source="simulation geometry variant",
        verification_status="ESTIMATE / SIMULATED / PHYSICAL VALIDATION REQUIRED",
    )
