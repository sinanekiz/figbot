"""Build the P0 Rev-G sloped-front-basket dual-arm rover packaging model.

The vehicle uses the task-specific lightweight MG996R test-arm packaging model
and controlled envelopes for the remaining purchased parts. It is still not
released manufacturing geometry: hubs, knuckles, motor shafts, servo brackets
and horns require measured samples before holes are frozen.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import cadquery as cq
import matplotlib
import numpy as np
import trimesh

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from cad.config import parameters as p
from cad.prototype_arm.build_servo_arm import prototype_arm_shape
from cad.rover.geometry_checks import clearance_report
from cad.utils import ROOT, shape_mesh


ASSEMBLY_DIR = ROOT / "cad" / "assembly"
RENDER_DIR = ROOT / "renders"
VIEWER_MODEL_DIR = ROOT / "viewer" / "public" / "models"
LAYOUT_PATH = ROOT / "cad" / "rover" / "FIGBOT_P0_LAYOUT.json"
PALETTE = {
    "frame": [70, 76, 73, 255],
    "deck": [126, 105, 75, 255],
    "tire": [31, 33, 32, 255],
    "metal": [176, 184, 181, 255],
    "steering": [56, 105, 120, 255],
    "drive": [61, 83, 104, 255],
    "guard": [85, 100, 105, 220],
    "battery": [44, 77, 62, 255],
    "electronics": [45, 98, 119, 255],
    "pcb": [47, 125, 73, 255],
    "power": [104, 68, 132, 255],
    "arm": [216, 139, 43, 255],
    "basket": [151, 78, 57, 255],
    "liner": [224, 191, 143, 255],
    "camera": [38, 48, 54, 255],
    "safety": [198, 50, 42, 255],
}


def _box(x: float, y: float, z: float, at: tuple[float, float, float]) -> cq.Workplane:
    return cq.Workplane("XY").box(x, y, z).translate(at)


def _cylinder_z(diameter: float, height: float, at: tuple[float, float, float]) -> cq.Workplane:
    return cq.Workplane("XY").circle(diameter / 2).extrude(height / 2, both=True).translate(at)


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


def _wheel_shape(x: float, y: float, steer_deg: float, kind: str) -> cq.Workplane:
    radius = p.P0_WHEEL_DIAMETER / 2
    if kind == "tire":
        shape = (
            cq.Workplane("XZ")
            .circle(radius)
            .circle(radius * 0.62)
            .extrude(p.P0_WHEEL_WIDTH / 2, both=True)
        )
    elif kind == "rim":
        shape = cq.Workplane("XZ").circle(radius * 0.61).circle(23).extrude(20, both=True)
    elif kind == "hub":
        shape = cq.Workplane("XZ").circle(31).extrude(p.P0_WHEEL_WIDTH / 2 + 12, both=True)
    else:
        raise ValueError(kind)
    if steer_deg:
        shape = shape.rotate((0, 0, 0), (0, 0, 1), steer_deg)
    return shape.translate((x, y, p.P0_WHEEL_CENTER_Z))


def _basket_crate() -> cq.Workplane:
    length, width, height = p.P0_BASKET_LENGTH, p.P0_BASKET_WIDTH, p.P0_BASKET_HEIGHT
    bottom_z = p.P0_BASKET_BOTTOM_Z
    top_z = bottom_z + height
    slope_rise = length * math.tan(math.radians(p.P0_BASKET_FLOOR_SLOPE_DEG))

    # The front (+X) is high and the rear (-X) is low. The lower rear face
    # remains at P0_BASKET_BOTTOM_Z while the upper surface feeds rearward.
    shape = (
        cq.Workplane("XZ")
        .polyline([
            (-length / 2, bottom_z),
            (length / 2, bottom_z + slope_rise),
            (length / 2, bottom_z + slope_rise + 7),
            (-length / 2, bottom_z + 7),
        ])
        .close()
        .extrude(width / 2, both=True)
    )

    def floor_surface_z(local_x: float) -> float:
        return bottom_z + 7 + (local_x + length / 2) * math.tan(
            math.radians(p.P0_BASKET_FLOOR_SLOPE_DEG)
        )

    for x in (-length / 2 + 8, length / 2 - 8):
        for y in (-width / 2 + 8, width / 2 - 8):
            post_bottom = floor_surface_z(x)
            post_height = top_z - post_bottom
            shape = shape.union(_box(16, 16, post_height, (x, y, post_bottom + post_height / 2)))

    opening = p.P0_BASKET_SIDE_OPENING_LENGTH
    opening_center = p.P0_BASKET_SIDE_OPENING_CENTER_X - p.P0_BASKET_CENTER_X
    opening_min = opening_center - opening / 2
    opening_max = opening_center + opening / 2
    side_segments = ((-length / 2, opening_min), (opening_max, length / 2))
    for z in (top_z - 110, top_z - 70, top_z - 30):
        for y in (-width / 2 + 5, width / 2 - 5):
            for segment_start, segment_end in side_segments:
                segment_length = segment_end - segment_start
                if segment_length > 1:
                    shape = shape.union(
                        _box(segment_length, 10, 12, ((segment_start + segment_end) / 2, y, z))
                    )
        shape = shape.union(_box(10, width, 12, (-length / 2 + 5, 0, z)))
        shape = shape.union(_box(10, width, 12, (length / 2 - 5, 0, z)))

    # Sloped thresholds and opening-edge posts identify the front-side release
    # zones while keeping the passive rearward feed path visible.
    for y in (-width / 2 + 5, width / 2 - 5):
        shape = shape.union(
            _rod_between(
                (opening_min, y, floor_surface_z(opening_min) + 15),
                (opening_max, y, floor_surface_z(opening_max) + 15),
                12,
            )
        )
        for x in (opening_min, opening_max):
            post_bottom = floor_surface_z(x)
            post_height = top_z - post_bottom
            shape = shape.union(_box(16, 16, post_height, (x, y, post_bottom + post_height / 2)))
    return shape.translate((p.P0_BASKET_CENTER_X, p.P0_BASKET_CENTER_Y, 0))


def _basket_liner() -> cq.Workplane:
    """Removable low-friction liner proxy; final food-contact material is TBD."""

    length = p.P0_BASKET_LENGTH - 18
    gradient = math.tan(math.radians(p.P0_BASKET_FLOOR_SLOPE_DEG))
    rear_z = p.P0_BASKET_BOTTOM_Z + 7 + 9 * gradient
    front_z = rear_z + length * gradient
    return (
        cq.Workplane("XZ")
        .polyline([(-length / 2, rear_z), (length / 2, front_z), (length / 2, front_z + 3), (-length / 2, rear_z + 3)])
        .close()
        .extrude((p.P0_BASKET_WIDTH - 24) / 2, both=True)
        .translate((p.P0_BASKET_CENTER_X, p.P0_BASKET_CENTER_Y, 0))
    )


def _prototype_arm(x: float, y: float, yaw_deg: float) -> cq.Workplane:
    return prototype_arm_shape(yaw_deg).translate((x, y, p.P0_ARM_BASE_Z + 6))


def _add_wheel(
    parts: dict[str, tuple[cq.Workplane, str]],
    label: str,
    x: float,
    y: float,
    steer_deg: float,
) -> None:
    parts[f"P0-TIRE-{label}"] = (_wheel_shape(x, y, steer_deg, "tire"), "tire")
    parts[f"P0-RIM-{label}"] = (_wheel_shape(x, y, steer_deg, "rim"), "metal")
    parts[f"P0-HUB-{label}"] = (_wheel_shape(x, y, steer_deg, "hub"), "metal")


def components() -> dict[str, tuple[cq.Workplane, str]]:
    zf = p.P0_FRAME_CENTER_Z
    rail_y = p.P0_CHASSIS_WIDTH / 2 - p.P0_FRAME_PROFILE / 2
    panel_z = p.P0_DECK_TOP_Z - p.P0_DECK_THICKNESS / 2
    left_inner, right_outer = 21.0, 13.5  # representative left turn from Ackermann relation
    wheel_y = p.P0_TRACK / 2
    kingpin_y = wheel_y - 45
    tie_rod_y = kingpin_y - 40
    mast_x, mast_y = p.P0_CAMERA_MAST_X, p.P0_CAMERA_MAST_Y
    bridge_z = p.P0_CAMERA_BRIDGE_Z
    deck_top = p.P0_DECK_TOP_Z

    def basket_support(x: float, y: float) -> cq.Workplane:
        rear_x = p.P0_BASKET_CENTER_X - p.P0_BASKET_LENGTH / 2
        floor_bottom = p.P0_BASKET_BOTTOM_Z + (x - rear_x) * math.tan(math.radians(p.P0_BASKET_FLOOR_SLOPE_DEG))
        return _box(25, 25, floor_bottom - deck_top, (x, y, (floor_bottom + deck_top) / 2))

    parts: dict[str, tuple[cq.Workplane, str]] = {
        "P0-FRM-RAIL-L": (_box(p.P0_CHASSIS_LENGTH, 30, 30, (0, rail_y, zf)), "frame"),
        "P0-FRM-RAIL-R": (_box(p.P0_CHASSIS_LENGTH, 30, 30, (0, -rail_y, zf)), "frame"),
        "P0-FRM-XMEM-F": (_box(30, p.P0_CHASSIS_WIDTH - 60, 30, (270, 0, zf)), "frame"),
        "P0-FRM-XMEM-C": (_box(30, p.P0_CHASSIS_WIDTH - 60, 30, (60, 0, zf)), "frame"),
        "P0-FRM-XMEM-R": (_box(30, p.P0_CHASSIS_WIDTH - 60, 30, (-270, 0, zf)), "frame"),
        "P0-ARM-OUTRIGGER": (_box(150, 660, 30, (p.P0_ARM_BASE_X, 0, zf)), "frame"),
        "P0-DECK-FRONT": (_box(300, 520, p.P0_DECK_THICKNESS, (155, 0, panel_z)), "deck"),
        "P0-DECK-REAR": (_box(300, 520, p.P0_DECK_THICKNESS, (-160, 0, panel_z)), "deck"),
        "P0-FRONT-AXLE-BEAM": (_box(50, kingpin_y * 2, 40, (p.P0_FRONT_AXLE_X, 0, 145)), "frame"),
        "P0-FRONT-BEAM-SUPPORT-L": (_box(50, 35, 50, (p.P0_FRONT_AXLE_X, 250, 118)), "frame"),
        "P0-FRONT-BEAM-SUPPORT-R": (_box(50, 35, 50, (p.P0_FRONT_AXLE_X, -250, 118)), "frame"),
        "P0-KINGPIN-FL": (_cylinder_z(22, 100, (p.P0_FRONT_AXLE_X, kingpin_y, 145)), "steering"),
        "P0-KINGPIN-FR": (_cylinder_z(22, 100, (p.P0_FRONT_AXLE_X, -kingpin_y, 145)), "steering"),
        "P0-KNUCKLE-FL": (_box(62, 55, 74, (p.P0_FRONT_AXLE_X, (wheel_y + kingpin_y) / 2, p.P0_WHEEL_CENTER_Z)), "steering"),
        "P0-KNUCKLE-FR": (_box(62, 55, 74, (p.P0_FRONT_AXLE_X, -(wheel_y + kingpin_y) / 2, p.P0_WHEEL_CENTER_Z)), "steering"),
        "P0-TIE-ROD": (_rod_between((180, -tie_rod_y, 150), (180, tie_rod_y, 150), 12), "steering"),
        "P0-STEER-ARM-L": (_rod_between((180, tie_rod_y, 150), (220, kingpin_y, 150), 12), "steering"),
        "P0-STEER-ARM-R": (_rod_between((180, -tie_rod_y, 150), (220, -kingpin_y, 150), 12), "steering"),
        "P0-ACTUATOR-BODY": (_rod_between((180, -170, 148), (180, 35, 148), 38), "steering"),
        "P0-ACTUATOR-ROD": (_rod_between((180, 35, 148), (180, 135, 150), 16), "metal"),
        "P0-MOTOR-RL": (cq.Workplane("XZ").circle(39).extrude(52, both=True).translate((-175, 170, 150)), "drive"),
        "P0-MOTOR-RR": (cq.Workplane("XZ").circle(39).extrude(52, both=True).translate((-175, -170, 150)), "drive"),
        "P0-GEARBOX-RL": (_box(85, 72, 84, (-210, 170, 150)), "drive"),
        "P0-GEARBOX-RR": (_box(85, 72, 84, (-210, -170, 150)), "drive"),
        "P0-REAR-STUB-AXLE-L": (_rod_between((p.P0_REAR_AXLE_X, 295, p.P0_WHEEL_CENTER_Z), (p.P0_REAR_AXLE_X, wheel_y, p.P0_WHEEL_CENTER_Z), 25), "metal"),
        "P0-REAR-STUB-AXLE-R": (_rod_between((p.P0_REAR_AXLE_X, -295, p.P0_WHEEL_CENTER_Z), (p.P0_REAR_AXLE_X, -wheel_y, p.P0_WHEEL_CENTER_Z), 25), "metal"),
        "P0-REAR-BEARING-L": (_box(55, 28, 62, (p.P0_REAR_AXLE_X, 300, p.P0_WHEEL_CENTER_Z)), "metal"),
        "P0-REAR-BEARING-R": (_box(55, 28, 62, (p.P0_REAR_AXLE_X, -300, p.P0_WHEEL_CENTER_Z)), "metal"),
        "P0-CHAIN-GUARD-L": (_box(200, 14, 82, (-220, 318, 136)), "guard"),
        "P0-CHAIN-GUARD-R": (_box(200, 14, 82, (-220, -318, 136)), "guard"),
        "P0-BATTERY-TRAY": (_box(280, 195, 4, (p.P0_BATTERY_CENTER_X, p.P0_BATTERY_CENTER_Y, deck_top + 2)), "metal"),
        "P0-BATTERY": (_box(*p.P0_BATTERY_ENVELOPE, (p.P0_BATTERY_CENTER_X, p.P0_BATTERY_CENTER_Y, p.P0_BATTERY_CENTER_Z)), "battery"),
        "P0-BATTERY-STRAP-A": (_box(24, 190, 8, (-190, p.P0_BATTERY_CENTER_Y, p.P0_BATTERY_CENTER_Z + 59)), "guard"),
        "P0-BATTERY-STRAP-B": (_box(24, 190, 8, (-60, p.P0_BATTERY_CENTER_Y, p.P0_BATTERY_CENTER_Z + 59)), "guard"),
        "P0-BATTERY-TERMINAL-P": (_cylinder_z(18, 12, (-190, p.P0_BATTERY_CENTER_Y + 40, p.P0_BATTERY_CENTER_Z + 61)), "safety"),
        "P0-BATTERY-TERMINAL-N": (_cylinder_z(18, 12, (-190, p.P0_BATTERY_CENTER_Y - 40, p.P0_BATTERY_CENTER_Z + 61)), "metal"),
        "P0-ELECTRONICS-TRAY": (_box(200, 140, 4, (p.P0_ELECTRONICS_CENTER_X, p.P0_ELECTRONICS_CENTER_Y, deck_top + 2)), "electronics"),
        "P0-ELECTRONICS-RAIL-L": (_box(200, 8, 24, (p.P0_ELECTRONICS_CENTER_X, -161, deck_top + 14)), "electronics"),
        "P0-ELECTRONICS-RAIL-R": (_box(200, 8, 24, (p.P0_ELECTRONICS_CENTER_X, -29, deck_top + 14)), "electronics"),
        "P0-CPU-RPI5": (_box(85, 56, 2, (-178, -128, deck_top + 12)), "pcb"),
        "P0-CPU-HEATSINK": (_box(44, 32, 14, (-178, -128, deck_top + 20)), "metal"),
        "P0-DRIVER-MDDS30": (_box(100, 60, 5, (-75, -128, deck_top + 14)), "pcb"),
        "P0-DRIVER-TERMINALS": (_box(82, 14, 18, (-75, -149, deck_top + 24)), "power"),
        "P0-CTRL-ESP32": (_box(52, 28, 4, (-195, -61, deck_top + 13)), "pcb"),
        "P0-POWER-DCDC": (_box(60, 45, 20, (-128, -61, deck_top + 20)), "power"),
        "P0-SAFETY-CONTACTOR": (_box(42, 45, 46, (-65, -61, deck_top + 29)), "safety"),
        "P0-BASKET": (_basket_crate(), "basket"),
        "P0-BASKET-LINER": (_basket_liner(), "liner"),
        "P0-BASKET-SOFT-REAR-STOP": (
            _box(
                18,
                p.P0_BASKET_WIDTH - 30,
                65,
                (
                    p.P0_BASKET_CENTER_X - p.P0_BASKET_LENGTH / 2 + 14,
                    p.P0_BASKET_CENTER_Y,
                    p.P0_BASKET_BOTTOM_Z + 42,
                ),
            ),
            "liner",
        ),
        "P0-BASKET-POST-RL": (basket_support(-80, 145), "frame"),
        "P0-BASKET-POST-RR": (basket_support(-80, -145), "frame"),
        "P0-BASKET-POST-FL": (basket_support(275, 145), "frame"),
        "P0-BASKET-POST-FR": (basket_support(275, -145), "frame"),
        "P0-ARM-MOUNT-L": (_box(p.P0_ARM_MOUNT_SIZE, p.P0_ARM_MOUNT_SIZE, 6, (p.P0_ARM_BASES[0][0], p.P0_ARM_BASES[0][1], p.P0_DECK_TOP_Z + 3)), "metal"),
        "P0-ARM-MOUNT-R": (_box(p.P0_ARM_MOUNT_SIZE, p.P0_ARM_MOUNT_SIZE, 6, (p.P0_ARM_BASES[1][0], p.P0_ARM_BASES[1][1], p.P0_DECK_TOP_Z + 3)), "metal"),
        "P0-ARM-MG996R-PROTOTYPE-L": (_prototype_arm(*p.P0_ARM_BASES[0], -p.P0_ARM_RENDER_YAW_DEG), "arm"),
        "P0-ARM-MG996R-PROTOTYPE-R": (_prototype_arm(*p.P0_ARM_BASES[1], p.P0_ARM_RENDER_YAW_DEG), "arm"),
        "P0-CAMERA-MAST-L": (_box(p.P0_CAMERA_MAST_SIZE, p.P0_CAMERA_MAST_SIZE, bridge_z - deck_top, (mast_x, mast_y, (bridge_z + deck_top) / 2)), "frame"),
        "P0-CAMERA-MAST-R": (_box(p.P0_CAMERA_MAST_SIZE, p.P0_CAMERA_MAST_SIZE, bridge_z - deck_top, (mast_x, -mast_y, (bridge_z + deck_top) / 2)), "frame"),
        "P0-CAMERA-BRACE-L": (_rod_between((mast_x, mast_y, 380), (-260, mast_y, deck_top), 18), "frame"),
        "P0-CAMERA-BRACE-R": (_rod_between((mast_x, -mast_y, 380), (-260, -mast_y, deck_top), 18), "frame"),
        "P0-CAMERA-BRIDGE": (_box(30, mast_y * 2 + 30, 30, (mast_x, 0, bridge_z)), "frame"),
        "P0-CAMERA-BOOM": (_box(p.P0_CAMERA_CENTER_X - mast_x, 30, 30, ((p.P0_CAMERA_CENTER_X + mast_x) / 2, 0, bridge_z)), "frame"),
        "P0-CAMERA-MODULE": (_box(42, 34, 18, (p.P0_CAMERA_CENTER_X, p.P0_CAMERA_CENTER_Y, p.P0_CAMERA_CENTER_Z)), "camera"),
        "P0-CAMERA-LENS": (_cylinder_z(16, 18, (p.P0_CAMERA_CENTER_X, p.P0_CAMERA_CENTER_Y, p.P0_CAMERA_CENTER_Z - 17)), "camera"),
        "P0-ESTOP-BASE": (_cylinder_z(32, 32, (-270, -172, p.P0_DECK_TOP_Z + 22)), "camera"),
        "P0-ESTOP": (_cylinder_z(44, 22, (-270, -172, p.P0_DECK_TOP_Z + 48)), "safety"),
    }
    _add_wheel(parts, "FL", p.P0_FRONT_AXLE_X, p.P0_TRACK / 2, left_inner)
    _add_wheel(parts, "FR", p.P0_FRONT_AXLE_X, -p.P0_TRACK / 2, right_outer)
    _add_wheel(parts, "RL", p.P0_REAR_AXLE_X, p.P0_TRACK / 2, 0.0)
    _add_wheel(parts, "RR", p.P0_REAR_AXLE_X, -p.P0_TRACK / 2, 0.0)
    return parts


def _compound(parts: dict[str, tuple[cq.Workplane, str]]) -> cq.Compound:
    return cq.Compound.makeCompound([shape.val() for shape, _ in parts.values()])


def _mesh_parts(parts: dict[str, tuple[cq.Workplane, str]]) -> dict[str, tuple[np.ndarray, np.ndarray, str]]:
    meshes: dict[str, tuple[np.ndarray, np.ndarray, str]] = {}
    for name, (shape, group) in parts.items():
        vertices, faces = shape_mesh(shape)
        meshes[name] = (vertices, faces, group)
    return meshes


def _export_glb(meshes: dict[str, tuple[np.ndarray, np.ndarray, str]], path: Path) -> None:
    scene = trimesh.Scene()
    for name, (vertices, faces, group) in meshes.items():
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
        mesh.visual.face_colors = PALETTE[group]
        scene.add_geometry(mesh, node_name=name, geom_name=name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(scene.export(file_type="glb"))


def _render(
    meshes: dict[str, tuple[np.ndarray, np.ndarray, str]],
    path: Path,
    title: str,
    elev: float,
    azim: float,
) -> None:
    fig = plt.figure(figsize=(10.2, 7.2), facecolor="#eef2ed")
    ax = fig.add_subplot(111, projection="3d")
    all_vertices: list[np.ndarray] = []
    for vertices, faces, group in meshes.values():
        all_vertices.append(vertices)
        color = np.asarray(PALETTE[group], dtype=float) / 255.0
        ax.add_collection3d(
            Poly3DCollection(vertices[faces], facecolor=color, edgecolor="#26332b", linewidth=0.045)
        )
    vertices = np.vstack(all_vertices)
    mins, maxs = vertices.min(axis=0), vertices.max(axis=0)
    center = (mins + maxs) / 2
    radius = max(float((maxs - mins).max()) / 2, 1.0)
    ax.set_xlim(center[0] - radius, center[0] + radius)
    ax.set_ylim(center[1] - radius, center[1] + radius)
    ax.set_zlim(0, maxs[2] + 40)
    ax.set_box_aspect((1, 1, 0.78))
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    ax.set_title(title, fontsize=15, weight="bold", color="#193528", pad=12)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=190, bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)


def _rotated_rectangle(cx: float, cy: float, length: float, width: float, angle_deg: float) -> np.ndarray:
    corners = np.asarray(
        [(-length / 2, -width / 2), (length / 2, -width / 2), (length / 2, width / 2), (-length / 2, width / 2)]
    )
    angle = math.radians(angle_deg)
    rotation = np.asarray(((math.cos(angle), -math.sin(angle)), (math.sin(angle), math.cos(angle))))
    return corners @ rotation.T + np.asarray((cx, cy))


def _render_annotated_layout(path: Path, report: dict[str, float]) -> None:
    from matplotlib.patches import Circle, Polygon, Rectangle

    fig, ax = plt.subplots(figsize=(14, 9), facecolor="#eef2ed")
    ax.set_facecolor("#f8faf8")
    ax.add_patch(Rectangle((-p.P0_CHASSIS_LENGTH / 2, -p.P0_CHASSIS_WIDTH / 2), p.P0_CHASSIS_LENGTH, p.P0_CHASSIS_WIDTH, facecolor="#c2ad87", edgecolor="#37423b", linewidth=2))
    for x, y, angle in (
        (p.P0_FRONT_AXLE_X, p.P0_TRACK / 2, 21.0),
        (p.P0_FRONT_AXLE_X, -p.P0_TRACK / 2, 13.5),
        (p.P0_REAR_AXLE_X, p.P0_TRACK / 2, 0.0),
        (p.P0_REAR_AXLE_X, -p.P0_TRACK / 2, 0.0),
    ):
        ax.add_patch(Polygon(_rotated_rectangle(x, y, p.P0_WHEEL_DIAMETER, p.P0_WHEEL_WIDTH, angle), closed=True, facecolor="#222624", edgecolor="#000"))
    sweep_radius = math.hypot(p.P0_WHEEL_DIAMETER / 2, p.P0_WHEEL_WIDTH / 2)
    for y in (-p.P0_TRACK / 2, p.P0_TRACK / 2):
        ax.add_patch(Circle((p.P0_FRONT_AXLE_X, y), sweep_radius, fill=False, edgecolor="#b42318", linestyle="--", linewidth=1.2))
    basket_origin = (p.P0_BASKET_CENTER_X - p.P0_BASKET_LENGTH / 2, p.P0_BASKET_CENTER_Y - p.P0_BASKET_WIDTH / 2)
    ax.add_patch(Rectangle(basket_origin, p.P0_BASKET_LENGTH, p.P0_BASKET_WIDTH, facecolor="#a95643", alpha=0.72, edgecolor="#71372c", linewidth=2))
    opening_x0 = p.P0_BASKET_SIDE_OPENING_CENTER_X - p.P0_BASKET_SIDE_OPENING_LENGTH / 2
    for y in (-p.P0_BASKET_WIDTH / 2, p.P0_BASKET_WIDTH / 2):
        ax.plot([opening_x0, opening_x0 + p.P0_BASKET_SIDE_OPENING_LENGTH], [y, y], color="#f6d1b8", linewidth=7, solid_capstyle="butt")
    battery_origin = (p.P0_BATTERY_CENTER_X - p.P0_BATTERY_ENVELOPE[0] / 2, p.P0_BATTERY_CENTER_Y - p.P0_BATTERY_ENVELOPE[1] / 2)
    electronics_origin = (p.P0_ELECTRONICS_CENTER_X - p.P0_ELECTRONICS_ENVELOPE[0] / 2, p.P0_ELECTRONICS_CENTER_Y - p.P0_ELECTRONICS_ENVELOPE[1] / 2)
    ax.add_patch(Rectangle(battery_origin, p.P0_BATTERY_ENVELOPE[0], p.P0_BATTERY_ENVELOPE[1], fill=False, edgecolor="#144c36", linewidth=2, linestyle="--"))
    ax.add_patch(Rectangle(electronics_origin, p.P0_ELECTRONICS_ENVELOPE[0], p.P0_ELECTRONICS_ENVELOPE[1], facecolor="#2d7891", alpha=0.75, edgecolor="#184b5c"))
    for x, y in p.P0_ARM_BASES:
        ax.add_patch(Circle((x, y), p.P0_ARM_MOUNT_SIZE / 2, facecolor="#d88b2b", edgecolor="#7c5019", linewidth=2))
    for y in (-p.P0_CAMERA_MAST_Y, p.P0_CAMERA_MAST_Y):
        ax.add_patch(Rectangle((p.P0_CAMERA_MAST_X - p.P0_CAMERA_MAST_SIZE / 2, y - p.P0_CAMERA_MAST_SIZE / 2), p.P0_CAMERA_MAST_SIZE, p.P0_CAMERA_MAST_SIZE, facecolor="#4b5550", edgecolor="#202824"))
    ax.plot([p.P0_CAMERA_MAST_X, p.P0_CAMERA_CENTER_X], [0, 0], color="#4b5550", linewidth=8)
    ax.scatter([p.P0_CAMERA_CENTER_X], [0], s=100, c="#1f2b31", zorder=8)
    ax.plot([p.P0_REAR_AXLE_X, p.P0_REAR_AXLE_X], [-p.P0_TRACK / 2, p.P0_TRACK / 2], color="#8c9691", linewidth=5)
    ax.plot([p.P0_FRONT_AXLE_X, p.P0_FRONT_AXLE_X], [-(p.P0_TRACK / 2 - 45), p.P0_TRACK / 2 - 45], color="#53656b", linewidth=8)

    zone_x0, zone_x1 = p.P0_ARM_PICK_X_RANGE
    left_y0, left_y1 = p.P0_LEFT_ARM_PICK_Y_RANGE
    right_y0, right_y1 = p.P0_RIGHT_ARM_PICK_Y_RANGE
    ax.add_patch(Rectangle((zone_x0, left_y0), zone_x1 - zone_x0, left_y1 - left_y0, facecolor="#f2b84b", alpha=0.16, edgecolor="#b57900", linestyle="--"))
    ax.add_patch(Rectangle((zone_x0, right_y0), zone_x1 - zone_x0, right_y1 - right_y0, facecolor="#5f9ed1", alpha=0.16, edgecolor="#28648e", linestyle="--"))
    ax.text(510, 250, "SOL KOL TOPLAMA ŞERİDİ", ha="center", va="center", fontsize=9, weight="bold", color="#805500")
    ax.text(510, -250, "SAĞ KOL TOPLAMA ŞERİDİ", ha="center", va="center", fontsize=9, weight="bold", color="#245b82")
    for target, drop, color in (((500, 220), p.P0_BASKET_DROP_POINTS[0], "#b57900"), ((500, -220), p.P0_BASKET_DROP_POINTS[1], "#28648e")):
        ax.annotate("", xy=(drop[0], drop[1]), xytext=target, arrowprops={"arrowstyle": "->", "lw": 2.5, "color": color, "connectionstyle": "arc3,rad=0.12"})
        ax.scatter([drop[0]], [drop[1]], s=55, c=color, zorder=9)

    ax.annotate(
        "",
        xy=(-55, -42),
        xytext=(260, -42),
        arrowprops={"arrowstyle": "->", "lw": 4, "color": "#f8dfb2"},
    )
    ax.text(102, -42, "ARKAYA PASİF AKIŞ", ha="center", va="center", fontsize=9, weight="bold", color="#6b382c")

    labels = [
        ((100, 35), (120, 82), "ÖN-ORTA SEPET\n400 × 350 mm"),
        ((220, 175), (235, 215), "SOL ÖN-YAN\nBIRAKMA AÇIKLIĞI"),
        ((220, -175), (235, -215), "SAĞ ÖN-YAN\nBIRAKMA AÇIKLIĞI"),
        ((-85, 110), (-110, 105), "24 V AKÜ\n(altta)"),
        ((-85, -100), (-110, -105), "PROGRAMLANABİLİR\nELEKTRONİKLER (altta)"),
        (p.P0_ARM_BASES[0], (p.P0_ARM_BASE_X, 355), "SOL KOL\nsepetin yanında"),
        (p.P0_ARM_BASES[1], (p.P0_ARM_BASE_X, -355), "SAĞ KOL\nsepetin yanında"),
        ((330, 0), (360, -300), "ORTAK ZEMİN KAMERASI\narka köprüden öne bakar"),
    ]
    for target, text_pos, text_value in labels:
        ax.annotate(
            text_value,
            xy=target,
            xytext=text_pos,
            ha="center",
            va="center",
            fontsize=9,
            weight="bold",
            color="#102d20",
            arrowprops={"arrowstyle": "->", "lw": 1.2, "color": "#315c46"},
            bbox={"facecolor": "#f8faf8", "edgecolor": "none", "alpha": 0.86, "pad": 1.5},
        )
    ax.annotate("+X İLERİ", xy=(625, -270), xytext=(500, -270), arrowprops={"arrowstyle": "->", "lw": 2, "color": "#174c31"}, va="center", weight="bold")
    ax.text(
        -350,
        -470,
        f"Tam ±{p.P0_STEER_LIMIT_DEG:.0f}° süpürmede lastik-şasi boşluğu: {report['steered_tyre_to_frame_mm']:.1f} mm\n"
        f"Kol tablası-teker süpürme boşluğu: {report['arm_mount_to_front_wheel_sweep_mm']:.1f} mm | Sepet-kol tablası boşluğu: {report['basket_side_to_arm_mount_mm']:.1f} mm\n"
        f"Sepet önü-şasi önü: {report['basket_front_to_frame_mm']:.1f} mm | Eğim: {p.P0_BASKET_FLOOR_SLOPE_DEG:.1f}° (ESTIMATE, ayarlı {p.P0_BASKET_FLOOR_SLOPE_RANGE_DEG[0]:.0f}–{p.P0_BASKET_FLOOR_SLOPE_RANGE_DEG[1]:.0f}°)\n"
        f"Çerçeve: {p.P0_CHASSIS_LENGTH:.0f}×{p.P0_CHASSIS_WIDTH:.0f} mm | Dış teker genişliği: {p.P0_TRACK + p.P0_WHEEL_WIDTH:.0f} mm",
        fontsize=10,
        color="#23382d",
        bbox={"facecolor": "#e4eee7", "edgecolor": "#7b9283", "boxstyle": "round,pad=0.5"},
    )
    ax.set_xlim(-410, 680)
    ax.set_ylim(-570, 570)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("FIGBOT P0 REV-G | ÖN SEPET, YANLARDA İKİ KOL, ARKAYA EĞİMLİ TABAN", fontsize=16, weight="bold", color="#193528")
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=190, bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)


def _render_basket_slope_section(path: Path) -> None:
    """Render an X-Z section explaining the passive rear-fill concept."""

    from matplotlib.patches import Polygon, Rectangle

    rear_x = p.P0_BASKET_CENTER_X - p.P0_BASKET_LENGTH / 2
    front_x = p.P0_BASKET_CENTER_X + p.P0_BASKET_LENGTH / 2
    rear_z = p.P0_BASKET_BOTTOM_Z + 7
    front_z = p.P0_BASKET_FRONT_FLOOR_Z + 7
    top_z = p.P0_BASKET_BOTTOM_Z + p.P0_BASKET_HEIGHT
    fig, ax = plt.subplots(figsize=(12, 6), facecolor="#eef2ed")
    ax.set_facecolor("#f8faf8")
    ax.add_patch(
        Polygon(
            [(rear_x, rear_z - 7), (front_x, front_z - 7), (front_x, front_z), (rear_x, rear_z)],
            closed=True,
            facecolor="#a95643",
            edgecolor="#71372c",
            linewidth=2,
        )
    )
    ax.add_patch(Rectangle((rear_x, rear_z), 18, 65, facecolor="#e0bf8f", edgecolor="#8a633d"))
    ax.plot([rear_x, rear_x], [rear_z - 7, top_z], color="#71372c", linewidth=7)
    ax.plot([front_x, front_x], [front_z - 7, top_z], color="#71372c", linewidth=7)
    ax.plot([rear_x, front_x], [top_z, top_z], color="#71372c", linewidth=5)
    ax.annotate(
        "",
        xy=(rear_x + 35, rear_z + 24),
        xytext=(front_x - 35, front_z + 24),
        arrowprops={"arrowstyle": "->", "lw": 4, "color": "#d17b24"},
    )
    ax.scatter([front_x - 45], [front_z + 28], s=230, c="#71402b", edgecolors="#432719", zorder=5)
    ax.text(front_x - 50, top_z + 28, "ÖN-YAN BIRAKMA", ha="center", weight="bold", color="#193528")
    ax.text(rear_x + 62, rear_z + 90, "YUMUŞAK ARKA\nDURDURUCU (TBD)", ha="center", weight="bold", color="#60472f")
    ax.text(100, rear_z - 45, f"TABAN EĞİMİ {p.P0_BASKET_FLOOR_SLOPE_DEG:.1f}° — ÖNDEN ARKAYA {front_z - rear_z:.1f} mm DÜŞÜŞ", ha="center", weight="bold", color="#193528")
    ax.text(rear_x + 105, rear_z + 66, "ARKADAN DOLMAYA BAŞLAR", ha="left", va="center", weight="bold", color="#6b382c")
    ax.set_xlim(rear_x - 55, front_x + 55)
    ax.set_ylim(rear_z - 70, top_z + 65)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("FIGBOT P0 REV-G | EĞİMLİ SEPET YAN KESİTİ", fontsize=16, weight="bold", color="#193528")
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=190, bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)


def build_p0_rover() -> Path:
    report = clearance_report()
    for name, value in report.items():
        if value < p.P0_STEER_CLEARANCE_MIN:
            raise ValueError(f"P0 Rev-G clearance failed: {name}={value:.2f} mm")
    parts = components()
    compound = _compound(parts)
    ASSEMBLY_DIR.mkdir(parents=True, exist_ok=True)
    step_path = ASSEMBLY_DIR / "FIGBOT_P0_ROVER.step"
    cq.exporters.export(compound, str(step_path), exportType="STEP")
    meshes = _mesh_parts(parts)
    _export_glb(meshes, VIEWER_MODEL_DIR / "FIGBOT_P0_ROVER.glb")
    for name, elev, azim in (
        ("isometric", 38, -52),
        ("top", 88, -90),
        ("front", 8, 0),
        ("side", 8, -90),
    ):
        _render(meshes, RENDER_DIR / f"FIGBOT_P0_ROVER_{name}.png", f"FIGBOT P0 REV-G | {name}", elev, azim)
    _render_annotated_layout(RENDER_DIR / "FIGBOT_P0_ROVER_layout_annotated.png", report)
    _render_basket_slope_section(RENDER_DIR / "FIGBOT_P0_BASKET_SLOPE_SECTION.png")
    payload = {
        "revision": "G",
        "status": "PACKAGING CONCEPT - PHYSICAL VALIDATION REQUIRED",
        "units": "mm",
        "coordinate_system": "+X forward, +Y left, +Z up",
        "chassis": {"length": p.P0_CHASSIS_LENGTH, "width": p.P0_CHASSIS_WIDTH},
        "wheel": {
            "diameter": p.P0_WHEEL_DIAMETER,
            "actual_model_width": p.P0_WHEEL_WIDTH,
            "wheelbase": p.P0_WHEELBASE,
            "track": p.P0_TRACK,
        },
        "steering": {
            "type": "front Ackermann",
            "limit_deg": p.P0_STEER_LIMIT_DEG,
            "visual_left_turn_deg": {"left": 21, "right": 13.5},
            "actuator_candidate": "24 V / 100 mm / 205 mm closed envelope",
            "clearance_report_mm": report,
        },
        "drive": {"type": "rear 2WD", "motors": "2 x 24 V 250 W candidate"},
        "arms": {
            "count": p.P0_ARM_COUNT,
            "candidate": "task-specific lightweight MG996R F/P test arm",
            "geometry_source": "cad/prototype_arm/build_servo_arm.py",
            "main_actuators_per_arm": "4 x MG996R PWM servo candidate (dual J2 shoulder)",
            "gripper_actuator_per_arm": "1 x MG90S candidate",
            "wrist": "passive parallelogram; no powered J4",
            "bases": [[x, y, p.P0_ARM_BASE_Z] for x, y in p.P0_ARM_BASES],
            "placement": "arms flank the front basket at the same X station",
            "target_partition": "left arm Y>=0; right arm Y<0; overlap requires coordination interlock",
        },
        "basket": {
            "center": [p.P0_BASKET_CENTER_X, p.P0_BASKET_CENTER_Y, p.P0_BASKET_BOTTOM_Z],
            "main_envelope": [p.P0_BASKET_LENGTH, p.P0_BASKET_WIDTH, p.P0_BASKET_HEIGHT],
            "drop_points": [list(point) for point in p.P0_BASKET_DROP_POINTS],
            "side_opening_length": p.P0_BASKET_SIDE_OPENING_LENGTH,
            "side_opening_center_x": p.P0_BASKET_SIDE_OPENING_CENTER_X,
            "floor_slope_deg": p.P0_BASKET_FLOOR_SLOPE_DEG,
            "adjustable_slope_range_deg": list(p.P0_BASKET_FLOOR_SLOPE_RANGE_DEG),
            "rear_floor_z": p.P0_BASKET_BOTTOM_Z,
            "front_floor_z": p.P0_BASKET_FRONT_FLOOR_Z,
            "fill_direction": "front (+X) release to rear (-X) passive feed",
            "liner": "removable low-friction food-contact liner; material TBD",
            "rear_stop": "soft energy-absorbing stop; material and thickness TBD",
            "placement": "front-centre, between the two arm bases",
        },
        "ground_pick_zone": {
            "x": p.P0_GROUND_PICK_X_RANGE,
            "y": p.P0_GROUND_PICK_Y_RANGE,
            "z": p.P0_GROUND_PICK_Z_RANGE,
        },
        "arm_command_pick_lanes": {
            "x": p.P0_ARM_PICK_X_RANGE,
            "left_y": p.P0_LEFT_ARM_PICK_Y_RANGE,
            "right_y": p.P0_RIGHT_ARM_PICK_Y_RANGE,
            "policy": "vehicle repositions detections into one lane before arm motion",
        },
        "interfaces": "TBD until incoming purchased-part measurements",
    }
    LAYOUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return step_path


if __name__ == "__main__":
    print(build_p0_rover())
