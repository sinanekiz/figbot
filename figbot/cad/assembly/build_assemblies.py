"""Build V0/V1 assemblies, named GLB scenes, and review renders."""

from __future__ import annotations

import math
import json
from pathlib import Path

import cadquery as cq
import numpy as np
import trimesh

from cad.config import parameters as p
from cad.parts import BUILDERS
from cad.utils import ROOT, render_preview, shape_mesh


ASSEMBLY_DIR = ROOT / "cad" / "assembly"
RENDER_DIR = ROOT / "renders"
VIEWER_MODEL_DIR = ROOT / "viewer" / "public" / "models"


def _pose(shape: cq.Workplane, translation=(0.0, 0.0, 0.0), rotation_y=0.0, rotation_z=0.0) -> cq.Workplane:
    result = shape
    if rotation_y:
        result = result.rotate((0, 0, 0), (0, 1, 0), rotation_y)
    if rotation_z:
        result = result.rotate((0, 0, 0), (0, 0, 1), rotation_z)
    return result.translate(translation)


def _geared_motor_y(face: float, length: float, shaft_d: float, shaft_l: float) -> cq.Workplane:
    """Controlled purchased-part envelope with an output shaft along +Y."""
    motor = _rounded_vendor_box(face, length * 0.47, face).translate((0, -length * 0.765, 0))
    gearbox = _rounded_vendor_box(face + 3, length * 0.53, face + 3).translate((0, -length * 0.265, 0))
    shaft = cq.Workplane("XZ").circle(shaft_d / 2).extrude(shaft_l).translate((0, 0, 0))
    return motor.union(gearbox).union(shaft)


def _geared_motor_z(face: float, length: float, shaft_d: float, shaft_l: float) -> cq.Workplane:
    """Controlled purchased-part envelope with an output shaft along +Z."""
    motor = _rounded_vendor_box(face, face, length * 0.47).translate((0, 0, length * 0.235))
    gearbox = _rounded_vendor_box(face + 3, face + 3, length * 0.53).translate((0, 0, length * 0.735))
    shaft = cq.Workplane("XY").circle(shaft_d / 2).extrude(shaft_l).translate((0, 0, length))
    return motor.union(gearbox).union(shaft)


def _rounded_vendor_box(x: float, y: float, z: float) -> cq.Workplane:
    shape = cq.Workplane("XY").box(x, y, z)
    try:
        return shape.edges("|Z").fillet(2)
    except Exception:
        return shape


def _camera_module_3_wide() -> cq.Workplane:
    board = cq.Workplane("XY").box(p.CAMERA_BOARD_WIDTH, p.CAMERA_BOARD_HEIGHT, 1.2)
    lens = cq.Workplane("XY").circle(6.95 / 2).extrude(11.2).translate((0, 0, -6.2))
    return board.union(lens)


def _raspberry_pi_5() -> cq.Workplane:
    board = cq.Workplane("XY").box(p.PI5_BOARD_LENGTH, p.PI5_BOARD_WIDTH, 1.6)
    # Connector keep-out proxies make enclosure collisions visible.
    usb = cq.Workplane("XY").box(18, 32, 15).translate((39, 7, 8))
    ethernet = cq.Workplane("XY").box(21, 17, 14).translate((34, -20, 7.5))
    return board.union(usb).union(ethernet)


def v0_joint_pivots() -> dict[str, tuple[float, float, float]]:
    stand_top_z = 9.0
    base_plate_top_z = stand_top_z + p.BASE_PLATE_THICKNESS
    shoulder = (0.0, 0.0, base_plate_top_z + p.SHOULDER_PEDESTAL_HEIGHT)
    upper_angle = 30.0
    fore_angle = -45.0
    elbow = (
        p.ARM_UPPER_LENGTH * math.cos(math.radians(upper_angle)),
        0.0,
        shoulder[2] + p.ARM_UPPER_LENGTH * math.sin(math.radians(upper_angle)),
    )
    wrist = (
        elbow[0] + p.ARM_FORE_LENGTH * math.cos(math.radians(fore_angle)),
        0.0,
        elbow[2] + p.ARM_FORE_LENGTH * math.sin(math.radians(fore_angle)),
    )
    return {"J1": (0.0, 0.0, base_plate_top_z), "J2": shoulder, "J3": elbow, "J4": wrist}


def v0_components() -> dict[str, cq.Workplane]:
    bx, by = 0.0, 0.0
    stand_top_z = 9.0
    base_plate_top_z = stand_top_z + p.BASE_PLATE_THICKNESS
    pedestal_base_z = base_plate_top_z
    pivots = v0_joint_pivots()
    shoulder_z = pivots["J2"][2]
    upper_angle = 30.0
    fore_angle = -45.0
    elbow = pivots["J3"]
    wrist = pivots["J4"]
    return {
        "CHA-001": _pose(BUILDERS["CHA-001"](), (0, 0, 0)),
        "ARM-001": _pose(BUILDERS["ARM-001"](), (bx, by, stand_top_z + p.BASE_PLATE_THICKNESS / 2)),
        "PUR-MOT-J1": _pose(_geared_motor_z(p.NEMA23_FACE, p.J2_GEARED_MOTOR_BODY_LENGTH, p.J2_GEARED_MOTOR_SHAFT_DIAMETER, p.J2_GEARED_MOTOR_SHAFT_LENGTH), (bx, by, base_plate_top_z + p.J2_GEARED_MOTOR_BODY_LENGTH), rotation_y=180),
        "STD-FIXTURE-LEG-1": _pose(_rounded_vendor_box(40, 40, 160), (-400, -300, -80)),
        "STD-FIXTURE-LEG-2": _pose(_rounded_vendor_box(40, 40, 160), (-400, 300, -80)),
        "STD-FIXTURE-LEG-3": _pose(_rounded_vendor_box(40, 40, 160), (400, -300, -80)),
        "STD-FIXTURE-LEG-4": _pose(_rounded_vendor_box(40, 40, 160), (400, 300, -80)),
        "ARM-002": _pose(BUILDERS["ARM-002"](), (bx, by, pedestal_base_z)),
        "PUR-MOT-J2": _pose(_geared_motor_y(p.NEMA23_FACE, p.J2_GEARED_MOTOR_BODY_LENGTH, p.J2_GEARED_MOTOR_SHAFT_DIAMETER, p.J2_GEARED_MOTOR_SHAFT_LENGTH), (bx, by - 70, shoulder_z)),
        "ARM-003": _pose(BUILDERS["ARM-003"](), (bx, by, shoulder_z), rotation_y=-upper_angle),
        "ARM-004": _pose(BUILDERS["ARM-004"](), elbow, rotation_y=-upper_angle),
        "PUR-MOT-J3": _pose(_geared_motor_y(p.NEMA17_FACE, p.DISTAL_GEARED_MOTOR_BODY_LENGTH, p.DISTAL_GEARED_MOTOR_SHAFT_DIAMETER, p.DISTAL_GEARED_MOTOR_SHAFT_LENGTH), (elbow[0], elbow[1] - 50, elbow[2]), rotation_y=-upper_angle),
        "ARM-005": _pose(BUILDERS["ARM-005"](), elbow, rotation_y=-fore_angle),
        "ARM-006": _pose(BUILDERS["ARM-006"](), wrist, rotation_y=-fore_angle),
        "PUR-MOT-J4": _pose(_geared_motor_y(p.NEMA17_FACE, p.DISTAL_GEARED_MOTOR_BODY_LENGTH, p.DISTAL_GEARED_MOTOR_SHAFT_DIAMETER, p.DISTAL_GEARED_MOTOR_SHAFT_LENGTH), (wrist[0], wrist[1] - 50, wrist[2]), rotation_y=-fore_angle),
        "GRP-001": _pose(BUILDERS["GRP-001"](), (wrist[0], wrist[1], wrist[2]-82)),
        "PUR-ACT-G1": _pose(_rounded_vendor_box(20, 34, 26), (wrist[0], wrist[1], wrist[2]-78)),
        "GRP-002-L": _pose(BUILDERS["GRP-002"](), (wrist[0]-25, wrist[1], wrist[2]-112), rotation_z=0),
        "GRP-002-R": _pose(BUILDERS["GRP-002"](), (wrist[0]+25, wrist[1], wrist[2]-112), rotation_z=180),
        "FUN-001": _pose(BUILDERS["FUN-001"](), (p.FUNNEL_CENTER_XYZ[0], p.FUNNEL_CENTER_XYZ[1], p.FUNNEL_CENTER_XYZ[2] + p.FUNNEL_HEIGHT / 2)),
        "FUN-002": _pose(BUILDERS["FUN-002"](), (p.FUNNEL_CENTER_XYZ[0], p.FUNNEL_CENTER_XYZ[1], p.FUNNEL_CENTER_XYZ[2] + p.FUNNEL_HEIGHT / 2 - 3)),
        "FUN-003": _pose(BUILDERS["FUN-003"](), (p.FUNNEL_CENTER_XYZ[0], p.FUNNEL_CENTER_XYZ[1], p.FUNNEL_CENTER_XYZ[2] - p.FUNNEL_HEIGHT / 2), rotation_z=90),
        "VIS-001": _pose(BUILDERS["VIS-001"](), (p.CAMERA_CENTER_XYZ[0] - 290, p.CAMERA_CENTER_XYZ[1], p.CAMERA_CENTER_XYZ[2] - 710)),
        "PUR-CAM-01": _pose(_camera_module_3_wide(), (p.CAMERA_CENTER_XYZ[0], p.CAMERA_CENTER_XYZ[1], p.CAMERA_CENTER_XYZ[2]), rotation_y=180),
        "ELE-001": _pose(BUILDERS["ELE-001"](), (-265, -220, 25)),
        "PUR-CPU-01": _pose(_raspberry_pi_5(), (-265, -220, 35)),
    }


def _compound(components: dict[str, cq.Workplane]) -> cq.Compound:
    return cq.Compound.makeCompound([shape.val() for shape in components.values()])


def _export_glb(components: dict[str, cq.Workplane], path: Path) -> None:
    scene = trimesh.Scene()
    palette = {
        "ARM": [218, 146, 54, 255], "GRP": [63, 129, 91, 255], "FUN": [161, 86, 65, 215],
        "CHA": [164, 139, 103, 255], "VIS": [75, 86, 80, 255], "ELE": [75, 110, 126, 255],
        "PUR": [54, 72, 92, 255],
    }
    for name, shape in components.items():
        vertices, faces = shape_mesh(shape)
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
        key = name.split("-")[0]
        mesh.visual.face_colors = palette.get(key, [190, 190, 190, 255])
        scene.add_geometry(mesh, node_name=name, geom_name=name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(scene.export(file_type="glb"))


def _render_views(compound: cq.Compound, prefix: str) -> None:
    views = {
        "front": (0, -90), "rear": (0, 90), "left": (0, 180), "right": (0, 0),
        "top": (90, -90), "bottom": (-90, -90), "isometric": (25, -48),
    }
    for name, (elev, azim) in views.items():
        render_preview(compound, RENDER_DIR / f"{prefix}_{name}.png", f"{prefix.upper()} | {name}", elev=elev, azim=azim)


def _render_exploded(components: dict[str, cq.Workplane]) -> None:
    arm_order = ["ARM-001", "ARM-002", "ARM-003", "ARM-004", "ARM-005", "ARM-006", "GRP-001", "GRP-002-L", "GRP-002-R"]
    exploded: list[cq.Shape] = []
    for index, name in enumerate(arm_order):
        exploded.append(components[name].translate((index * 18, 0, index * 28)).val())
    render_preview(cq.Compound.makeCompound(exploded), RENDER_DIR / "FIGBOT_V0_exploded.png", "FIGBOT V0 | exploded arm")


def build_assemblies() -> tuple[Path, Path]:
    ASSEMBLY_DIR.mkdir(parents=True, exist_ok=True)
    RENDER_DIR.mkdir(parents=True, exist_ok=True)
    components = v0_components()
    v0 = _compound(components)
    v0_step = ASSEMBLY_DIR / "FIGBOT_V0_ASSEMBLY.step"
    cq.exporters.export(v0, str(v0_step), exportType="STEP")
    _export_glb(components, VIEWER_MODEL_DIR / "FIGBOT_V0_ASSEMBLY.glb")
    rig_payload = {"units": "mm", "home_pose_deg": {"J1": 0, "J2": 30, "J3": -75, "J4": 0}, "pivots": v0_joint_pivots()}
    (VIEWER_MODEL_DIR / "FIGBOT_V0_KINEMATICS.json").write_text(json.dumps(rig_payload, indent=2) + "\n", encoding="utf-8")
    (VIEWER_MODEL_DIR / "FIGBOT_V1_KINEMATICS.json").write_text(json.dumps(rig_payload, indent=2) + "\n", encoding="utf-8")
    (ROOT / "viewer" / "src" / "generatedKinematics.json").write_text(
        json.dumps(rig_payload, indent=2) + "\n", encoding="utf-8"
    )
    _render_views(v0, "FIGBOT_V0")
    _render_exploded(components)

    # Mechanical-only custom arm subassembly for supplier DFM/RFQ. Purchased
    # motor and gripper-actuator envelopes are retained so the supplier sees
    # the complete packaging claim without the V0 test stand, funnel, camera,
    # or electronics.
    custom_arm_components = {
        key: value
        for key, value in components.items()
        if key.startswith(("ARM", "GRP", "PUR-MOT", "PUR-ACT"))
    }
    arm_only = _compound(custom_arm_components)
    custom_arm_step = ASSEMBLY_DIR / "FIGBOT_CUSTOM_ARM_ASSEMBLY.step"
    cq.exporters.export(arm_only, str(custom_arm_step), exportType="STEP")
    _export_glb(custom_arm_components, VIEWER_MODEL_DIR / "FIGBOT_CUSTOM_ARM_ASSEMBLY.glb")
    funnel_only = _compound({k:v for k,v in components.items() if k.startswith("FUN")})
    gripper_only = _compound({k:v for k,v in components.items() if k.startswith("GRP")})
    render_preview(arm_only, RENDER_DIR / "FIGBOT_arm_detail.png", "FIGBOT V0 | arm detail", elev=18, azim=-55)
    render_preview(gripper_only, RENDER_DIR / "FIGBOT_gripper_detail.png", "FIGBOT V0 | gripper detail", elev=20, azim=-45)
    render_preview(funnel_only, RENDER_DIR / "FIGBOT_funnel_detail.png", "FIGBOT V0 | funnel detail", elev=28, azim=-45)

    # V1 is a packaging concept only: V0 on a simple manually pushed chassis proxy.
    v1_components = dict(components)
    v1_components["CHA-V1-FRAME-PROXY"] = cq.Workplane("XY").box(p.CHASSIS_LENGTH, p.CHASSIS_WIDTH, 45).translate((0,0,-70))
    for index, (x, y) in enumerate(((-330,-280),(-330,280),(330,-280),(330,280))):
        wheel = cq.Workplane("YZ").circle(95).extrude(38, both=True).translate((x,y,-115))
        v1_components[f"PUR-WHEEL-{index+1}-PROXY"] = wheel
    v1_components["PUR-CRATE-PROXY"] = cq.Workplane("XY").box(430, 330, 260).translate((180,0,80))
    v1 = _compound(v1_components)
    v1_step = ASSEMBLY_DIR / "FIGBOT_V1_ASSEMBLY.step"
    cq.exporters.export(v1, str(v1_step), exportType="STEP")
    _export_glb(v1_components, VIEWER_MODEL_DIR / "FIGBOT_V1_ASSEMBLY.glb")
    render_preview(v1, RENDER_DIR / "FIGBOT_V1_isometric.png", "FIGBOT V1 | packaging concept", elev=22, azim=-48)
    return v0_step, v1_step


if __name__ == "__main__":
    build_assemblies()
