"""Build the Rev-G low-cost MG996R prototype arm.

The geometry is a controlled packaging model for the first fast collection test.
It is not a production-strength release.  Servo tabs, supplied brackets, horn
stack-up and spline position must be measured on the delivered samples before
printing or machining the final adapters.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import cadquery as cq
import numpy as np

from cad.config import parameters as p
from cad.utils import ROOT, render_preview


ASSEMBLY_DIR = ROOT / "cad" / "assembly"
RENDER_DIR = ROOT / "renders"
MODEL_PATH = ASSEMBLY_DIR / "FIGBOT_MG996R_TEST_ARM.step"
CONTRACT_PATH = ROOT / "cad" / "prototype_arm" / "FIGBOT_MG996R_TEST_ARM.json"


def _rounded_box(x: float, y: float, z: float, radius: float = 2.0) -> cq.Workplane:
    shape = cq.Workplane("XY").box(x, y, z)
    try:
        return shape.edges("|Z").fillet(radius)
    except Exception:
        return shape


def _box_between(
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    width: float,
    height: float,
) -> cq.Workplane:
    """Rectangular member with its long axis between two points."""

    vector = np.asarray(end, dtype=float) - np.asarray(start, dtype=float)
    length = float(np.linalg.norm(vector))
    yaw = math.degrees(math.atan2(vector[1], vector[0]))
    pitch = -math.degrees(math.atan2(vector[2], math.hypot(vector[0], vector[1])))
    member = cq.Workplane("XY").box(length, width, height).translate((length / 2, 0, 0))
    member = member.rotate((0, 0, 0), (0, 1, 0), pitch)
    member = member.rotate((0, 0, 0), (0, 0, 1), yaw)
    return member.translate(start)


def _rod_between(
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    diameter: float,
) -> cq.Workplane:
    vector = np.asarray(end, dtype=float) - np.asarray(start, dtype=float)
    length = float(np.linalg.norm(vector))
    unit = vector / length
    axis = (-float(unit[1]), float(unit[0]), 0.0)
    angle = math.degrees(math.acos(max(-1.0, min(1.0, float(unit[2])))))
    rod = cq.Workplane("XY").circle(diameter / 2).extrude(length)
    if math.hypot(axis[0], axis[1]) > 1e-9:
        rod = rod.rotate((0, 0, 0), axis, angle)
    elif unit[2] < 0:
        rod = rod.rotate((0, 0, 0), (1, 0, 0), 180)
    return rod.translate(start)


def _servo_envelope_y(at: tuple[float, float, float]) -> cq.Workplane:
    """MG996R controlled body envelope with output axis along Y."""

    body = _rounded_box(p.TEST_ARM_SERVO_LENGTH, p.TEST_ARM_SERVO_WIDTH, p.TEST_ARM_SERVO_HEIGHT, 2)
    axis = cq.Workplane("XZ").circle(p.TEST_ARM_SERVO_SPLINE_DIAMETER / 2).extrude(10, both=True)
    return body.union(axis).translate(at)


def _servo_envelope_z(at: tuple[float, float, float]) -> cq.Workplane:
    body = _rounded_box(p.TEST_ARM_SERVO_LENGTH, p.TEST_ARM_SERVO_WIDTH, p.TEST_ARM_SERVO_HEIGHT, 2)
    axis = cq.Workplane("XY").circle(p.TEST_ARM_SERVO_SPLINE_DIAMETER / 2).extrude(10, both=True)
    return body.union(axis).translate(at)


def prototype_arm_components() -> dict[str, cq.Workplane]:
    """Return one arm in the local base frame in a representative ground pose."""

    shoulder = (0.0, 0.0, p.TEST_ARM_SHOULDER_HEIGHT)
    upper_angle = math.radians(p.TEST_ARM_RENDER_UPPER_DEG)
    fore_angle = math.radians(p.TEST_ARM_RENDER_FORE_DEG)
    elbow = (
        p.ARM_UPPER_LENGTH * math.cos(upper_angle),
        0.0,
        shoulder[2] + p.ARM_UPPER_LENGTH * math.sin(upper_angle),
    )
    wrist = (
        elbow[0] + p.ARM_FORE_LENGTH * math.cos(fore_angle),
        0.0,
        elbow[2] + p.ARM_FORE_LENGTH * math.sin(fore_angle),
    )
    tool_tip = (wrist[0], wrist[1], wrist[2] - p.ARM_TOOL_LENGTH)

    base_plate = _rounded_box(110, 100, 8, 6).translate((0, 0, 4))
    # Slots retain adjustment until the delivered servo/bracket stack is measured.
    for x in (-38, 38):
        for y in (-32, 32):
            slot = cq.Workplane("XY").center(x, y).rect(12, 5).extrude(16, both=True)
            base_plate = base_plate.cut(slot)

    tower = (
        _rounded_box(68, 8, p.TEST_ARM_SHOULDER_HEIGHT - 30, 3)
        .translate((0, -34, (p.TEST_ARM_SHOULDER_HEIGHT - 30) / 2 + 18))
        .union(
            _rounded_box(68, 8, p.TEST_ARM_SHOULDER_HEIGHT - 30, 3).translate(
                (0, 34, (p.TEST_ARM_SHOULDER_HEIGHT - 30) / 2 + 18)
            )
        )
        .union(_rounded_box(68, 76, 8, 3).translate((0, 0, 24)))
    )

    elbow_block = _rounded_box(62, 44, 54, 5).translate(elbow)
    wrist_block = _rounded_box(52, 38, 48, 5).translate(wrist)
    gripper_body = _rounded_box(58, 48, 24, 5).translate((wrist[0], 0, wrist[2] - 48))
    finger_left = _rounded_box(12, 12, 62, 4).translate((wrist[0], 24, tool_tip[2] + 31))
    finger_right = _rounded_box(12, 12, 62, 4).translate((wrist[0], -24, tool_tip[2] + 31))

    # A second light rod keeps the gripper approximately vertical and removes
    # the moving wrist motor from the V0 arm.
    upper_parallel_start = (0.0, 0.0, shoulder[2] + 28)
    upper_parallel_end = (elbow[0], 0.0, elbow[2] + 28)
    fore_parallel_start = upper_parallel_end
    fore_parallel_end = (wrist[0], 0.0, wrist[2] + 28)

    return {
        "ARM-G01-BASE-ADAPTER": base_plate,
        "ARM-G02-SHOULDER-TOWER": tower,
        "PUR-MG996R-J1": _servo_envelope_z((0, 0, 52)),
        # Two mirrored MG996R units share J2. Their horns must be aligned and
        # driven from the same command; the counterbalance carries most of the
        # static gravity load. Final coupling geometry waits for sample measurements.
        "PUR-MG996R-J2-A": _servo_envelope_y((shoulder[0], -24.0, shoulder[2])),
        "PUR-MG996R-J2-B": _servo_envelope_y((shoulder[0], 24.0, shoulder[2])),
        "ARM-G03-UPPER-TUBE": _box_between(shoulder, elbow, p.TEST_ARM_LINK_SIZE, p.TEST_ARM_LINK_SIZE),
        "ARM-G04-UPPER-PARALLEL-ROD": _rod_between(upper_parallel_start, upper_parallel_end, 6),
        "ARM-G05-ELBOW-CARRIER": elbow_block,
        "PUR-MG996R-J3": _servo_envelope_y(elbow),
        "ARM-G06-FORE-TUBE": _box_between(elbow, wrist, p.TEST_ARM_LINK_SIZE, p.TEST_ARM_LINK_SIZE),
        "ARM-G07-FORE-PARALLEL-ROD": _rod_between(fore_parallel_start, fore_parallel_end, 6),
        "ARM-G08-WRIST-CARRIER": wrist_block,
        "ARM-G09-SHOULDER-COUNTERBALANCE": _rod_between(
            (-22.0, 0.0, 74.0),
            (
                shoulder[0] + 0.48 * (elbow[0] - shoulder[0]),
                0.0,
                shoulder[2] + 0.48 * (elbow[2] - shoulder[2]),
            ),
            9,
        ),
        "GRP-G01-BODY": gripper_body,
        "PUR-MG90S-G1": _rounded_box(23, 12, 29, 2).translate((wrist[0], 0, wrist[2] - 47)),
        "GRP-G02-FINGER-L": finger_left,
        "GRP-G03-FINGER-R": finger_right,
    }


def prototype_arm_shape(yaw_deg: float = 0.0) -> cq.Workplane:
    compound = cq.Compound.makeCompound([shape.val() for shape in prototype_arm_components().values()])
    wrapped = cq.Workplane(obj=compound)
    if yaw_deg:
        wrapped = wrapped.rotate((0, 0, 0), (0, 0, 1), yaw_deg)
    return wrapped


def build_servo_arm() -> Path:
    ASSEMBLY_DIR.mkdir(parents=True, exist_ok=True)
    RENDER_DIR.mkdir(parents=True, exist_ok=True)
    arm = prototype_arm_shape()
    cq.exporters.export(arm, str(MODEL_PATH), exportType="STEP")
    render_preview(
        arm,
        RENDER_DIR / "FIGBOT_MG996R_TEST_ARM_isometric.png",
        "FIGBOT REV-G | MG996R F/P test arm",
        elev=18,
        azim=-55,
    )
    contract = {
        "revision": "G",
        "status": "DIGITAL PROTOTYPE / PHYSICAL VALIDATION REQUIRED",
        "actuation": {
            "J1": "one MG996R PWM servo candidate",
            "J2": "two mechanically coupled MG996R PWM servo candidates plus adjustable counterbalance",
            "J3": "one MG996R PWM servo candidate",
            "G1": "MG90S micro servo candidate",
            "wrist_orientation": "passive parallelogram; no J4 motor",
        },
        "geometry_mm": {
            "upper_link": p.ARM_UPPER_LENGTH,
            "fore_link": p.ARM_FORE_LENGTH,
            "tool_offset": p.ARM_TOOL_LENGTH,
            "nominal_reach": p.ARM_UPPER_LENGTH + p.ARM_FORE_LENGTH + p.ARM_TOOL_LENGTH,
            "shoulder_height_above_mount": p.TEST_ARM_SHOULDER_HEIGHT,
            "main_link_section": [p.TEST_ARM_LINK_SIZE, p.TEST_ARM_LINK_SIZE, p.TEST_ARM_LINK_WALL],
        },
        "servo_interface": {
            "body_envelope": [p.TEST_ARM_SERVO_LENGTH, p.TEST_ARM_SERVO_WIDTH, p.TEST_ARM_SERVO_HEIGHT],
            "spline": "Futaba-compatible; exact tooth count and fit require delivered-sample inspection",
            "spline_major_diameter_mm": p.TEST_ARM_SERVO_SPLINE_DIAMETER,
            "mounting_tabs_horn_and_brackets": "UNVERIFIED - MEASURE DELIVERED SAMPLE BEFORE FINAL PRINT",
            "dual_J2_alignment": "PHYSICAL VALIDATION REQUIRED - match horn zero, linkage stiffness, current and temperature",
        },
        "throughput_contract": {
            "vehicle_target_per_min": 30,
            "arms": 2,
            "target_per_arm_per_min": 15,
            "maximum_average_cycle_s_per_arm": 4.0,
            "validation": "UNVERIFIED - TIMED PHYSICAL TEST REQUIRED",
        },
    }
    CONTRACT_PATH.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
    return MODEL_PATH


if __name__ == "__main__":
    print(build_servo_arm())
