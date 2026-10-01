"""Build the rounded, visually legible MG996R single-arm concept.

The aluminium tubes remain the primary load path.  Thin, hollow fairing modules
give the arm a finished form without replacing those tubes.  Servo models are
assembly-only reference geometry and must never be sent to the printer.
"""

from __future__ import annotations

import csv
import json
import math
import zipfile
from dataclasses import dataclass
from pathlib import Path

import cadquery as cq

from cad.utils import ROOT, export_shape, shape_mesh
from cad.prototype_arm.build_printable_v1 import (
    BODY_CLEARANCE,
    MG90S_BODY,
    MG90S_OPENING,
    MG996R_BODY,
    MG996R_OPENING,
    TUBE_SOCKET,
    horn_fit_coupon,
    mg90s_clamp_bar,
    mg90s_fit_plate,
    mg996r_clamp_bar,
    mg996r_fit_plate,
    tube_fit_coupon,
)


OUT = ROOT / "cad" / "prototype_arm" / "aero_v2"
ASSEMBLY_STEP = ROOT / "cad" / "assembly" / "FIGBOT_MG996R_AERO_V2.step"
ASSEMBLY_GLB = ROOT / "cad" / "assembly" / "FIGBOT_MG996R_AERO_V2.glb"
RENDER_ISO = ROOT / "renders" / "FIGBOT_MG996R_AERO_V2_isometric.png"
RENDER_SIDE = ROOT / "renders" / "FIGBOT_MG996R_AERO_V2_mechanism.png"
RENDER_GRIPPER = ROOT / "renders" / "FIGBOT_MG996R_AERO_V2_gripper_closeup.png"

M3_CLEARANCE = 3.4
M4_CLEARANCE = 4.5
M8_CLEARANCE = 8.4
UPPER_LINK_LENGTH = 300.0
FOREARM_LINK_LENGTH = 220.0
TOOL_LENGTH = 85.0
FAIRING_WALL = 0.8
PETG_DENSITY_G_CM3 = 1.27
GRIPPER_LINK_CENTRE_DISTANCE = math.hypot(15.0, 26.0)
ASSEMBLY_SHOULDER_Z = 146.0
ASSEMBLY_FORE_ANGLE_DEG = -18.0
PALM_WRIST_HOLE = (11.24, 20.68)
PALM_WRIST_SECOND_HOLE = (0.73, 53.02)
FULL_PRINT_STATUS = "HOLD - ASSEMBLY DEFECTS (DEC-039); FIT COUPONS ONLY RECOMMENDED"


@dataclass(frozen=True)
class Component:
    name: str
    shape: cq.Workplane
    group: str
    color: tuple[float, float, float]


PRINT_COLOR = (0.93, 0.42, 0.10)
PRINT_DARK = (0.63, 0.19, 0.06)
ALUMINIUM = (0.70, 0.74, 0.77)
SERVO_BLACK = (0.08, 0.10, 0.12)
SERVO_LABEL = (0.08, 0.31, 0.65)
HORN_COLOR = (0.92, 0.73, 0.12)
PAD_COLOR = (0.20, 0.56, 0.39)
FASTENER = (0.28, 0.31, 0.34)


def _box(x: float, y: float, z: float, at=(0.0, 0.0, 0.0)) -> cq.Workplane:
    return cq.Workplane("XY").box(x, y, z).translate(at)


def _rounded_box(
    x: float,
    y: float,
    z: float,
    radius: float,
    at=(0.0, 0.0, 0.0),
    long_axis: str = "Z",
) -> cq.Workplane:
    shape = _box(x, y, z)
    selector = {"X": "|X", "Y": "|Y", "Z": "|Z"}[long_axis]
    try:
        shape = shape.edges(selector).fillet(radius)
    except Exception:
        # Preserve buildability if OCC rejects an edge set after a future edit.
        pass
    return shape.translate(at)


def _hole_z(shape: cq.Workplane, x: float, y: float, diameter: float, height: float = 80) -> cq.Workplane:
    return shape.cut(cq.Workplane("XY").center(x, y).circle(diameter / 2).extrude(height, both=True))


def _hole_y(shape: cq.Workplane, x: float, z: float, diameter: float, depth: float = 90) -> cq.Workplane:
    return shape.cut(cq.Workplane("XZ").center(x, z).circle(diameter / 2).extrude(depth, both=True))


def _capsule_bar_x(length: float, width: float, height: float, radius: float) -> cq.Workplane:
    return _rounded_box(length, width, height, radius, long_axis="X")


def j1_base_aero() -> cq.Workplane:
    base = _rounded_box(110, 110, 8, 12, at=(0, 0, 4), long_axis="Z")
    base = base.union(cq.Workplane("XY").circle(47).circle(40).extrude(10))
    base = base.cut(_box(MG996R_OPENING[0], MG996R_OPENING[1], 28, (0, 0, 4)))
    for x in (-48, 48):
        for y in (-42, 42):
            base = base.cut(_box(12, 5, 30, (x, y, 4)))
    for x in (-29, 29):
        for y in (-15, 15):
            base = _hole_z(base, x, y, M3_CLEARANCE)
    return base


def yaw_deck_aero() -> cq.Workplane:
    deck = _rounded_box(94, 78, 8, 14, at=(0, 0, 6), long_axis="Z")
    deck = deck.union(cq.Workplane("XY").circle(39.6).circle(34).extrude(2))
    deck = _hole_z(deck, 0, 0, M3_CLEARANCE)
    for angle in (0, 90, 180, 270):
        slot = _box(14, 2.6, 24, (10, 0, 6)).rotate((0, 0, 0), (0, 0, 1), angle)
        deck = deck.cut(slot)
    for x in (-32, 32):
        for y in (-27, 27):
            deck = _hole_z(deck, x, y, M4_CLEARANCE)
    return deck


def shoulder_pedestal_aero() -> cq.Workplane:
    """One-piece open pedestal with rounded rails and large mass-relief windows."""
    bottom = _rounded_box(82, 72, 7, 9, at=(0, 0, 3.5), long_axis="Z")
    top = _rounded_box(78, 68, 7, 9, at=(0, 0, 87.5), long_axis="Z")
    body = bottom.union(top)
    for y in (-29, 29):
        rail = _rounded_box(66, 10, 78, 4.5, at=(0, y, 46), long_axis="Z")
        rail = rail.cut(_rounded_box(42, 18, 54, 9, at=(0, y, 46), long_axis="Z"))
        body = body.union(rail)
    # Short end ribs prevent the two side frames from racking.
    for x in (-33, 33):
        body = body.union(_rounded_box(10, 62, 12, 4, at=(x, 0, 46), long_axis="X"))
    for x in (-32, 32):
        for y in (-27, 27):
            body = _hole_z(body, x, y, M4_CLEARANCE, 220)
    # Three side holes let a low-cost elastic/spring counterbalance be tuned.
    for z in (24, 42, 60):
        body = _hole_y(body, -28, z, M4_CLEARANCE, 100)
    return body


def shoulder_yoke_aero() -> cq.Workplane:
    yoke = _rounded_box(80, 70, 7, 8, at=(0, 0, 3.5), long_axis="Z")
    for y in (-20, 20):
        cheek = _rounded_box(76, 7, 64, 8, at=(0, y, 37), long_axis="Y")
        cheek = cheek.union(cq.Workplane("XZ").center(0, 37).circle(28).extrude(3.5, both=True).translate((0, y, 0)))
        opening = _box(MG996R_OPENING[0], 18, MG996R_OPENING[1], (0, y, 38))
        cheek = cheek.cut(opening)
        for x in (-31, 31):
            for z in (23, 53):
                cheek = _hole_y(cheek, x, z, M3_CLEARANCE)
        yoke = yoke.union(cheek)
    for x in (-32, 32):
        for y in (-27, 27):
            yoke = _hole_z(yoke, x, y, M4_CLEARANCE)
    return yoke


def _horn_slots_y(shape: cq.Workplane, depth: float = 60) -> cq.Workplane:
    shape = _hole_y(shape, 0, 0, M3_CLEARANCE, depth)
    for angle in (0, 90, 180, 270):
        slot = _box(13, depth, 2.6, (10, 0, 0)).rotate((0, 0, 0), (0, 1, 0), angle)
        shape = shape.cut(slot)
    return shape


def upper_link_hub_aero() -> cq.Workplane:
    hub = cq.Workplane("XZ").circle(21).extrude(15, both=True)
    hub = hub.union(_rounded_box(49, 30, 34, 9, at=(16, 0, 0), long_axis="X"))
    hub = hub.cut(_box(42, TUBE_SOCKET, TUBE_SOCKET, (29, 0, 0)))
    hub = _horn_slots_y(hub)
    for x in (24, 37):
        hub = _hole_z(hub, x, 0, M4_CLEARANCE)
    return hub


def elbow_yoke_aero() -> cq.Workplane:
    root = _rounded_box(47, 36, 34, 7, at=(-20, 0, 0), long_axis="X")
    root = root.cut(_box(42, TUBE_SOCKET, TUBE_SOCKET, (-24, 0, 0)))
    body = root
    for y in (-20, 20):
        cheek = _rounded_box(62, 5.5, 64, 8, at=(0, y, 0), long_axis="Y")
        body = body.union(cheek)
    opening = _box(MG996R_OPENING[0], 18, MG996R_OPENING[1], (0, 20, 0))
    body = body.cut(opening)
    for x in (-31, 31):
        for z in (-15, 15):
            body = _hole_y(body, x, z, M3_CLEARANCE)
    body = _hole_y(body, 0, 0, M8_CLEARANCE)
    for x in (-32, -19):
        body = _hole_z(body, x, 0, M4_CLEARANCE)
    return body


def forearm_link_hub_aero() -> cq.Workplane:
    hub = cq.Workplane("XZ").circle(20.5).extrude(14.8, both=True)
    hub = hub.union(_rounded_box(49, 29.6, 34, 9, at=(16, 0, 0), long_axis="X"))
    hub = hub.cut(_box(42, TUBE_SOCKET, TUBE_SOCKET, (29, 0, 0)))
    hub = _horn_slots_y(hub)
    for x in (24, 37):
        hub = _hole_z(hub, x, 0, M4_CLEARANCE)
    return hub


def wrist_carrier_aero() -> cq.Workplane:
    carrier = _rounded_box(49, 34, 34, 7, at=(-20, 0, 0), long_axis="X")
    carrier = carrier.cut(_box(43, TUBE_SOCKET, TUBE_SOCKET, (-25, 0, 0)))
    spine = _rounded_box(6, 62, 54, 2.5, at=(5, 0, -13), long_axis="X")
    spine = spine.cut(_rounded_box(12, 40, 30, 8, at=(5, 0, -13), long_axis="X"))
    carrier = carrier.union(spine)
    for y in (-23, 23):
        for z in (-31, 3):
            carrier = _hole_y(carrier, 7, z, M4_CLEARANCE)
    for x in (-34, -20):
        carrier = _hole_z(carrier, x, 0, M4_CLEARANCE)
    return carrier


def gripper_palm_aero() -> cq.Workplane:
    palm = _rounded_box(96, 58, 16, 12, at=(0, 0, 0), long_axis="Z")
    # Open underside creates a thin, voluminous shell instead of a solid block.
    palm = palm.cut(_rounded_box(82, 44, 16, 9, at=(0, 0, -5), long_axis="Z"))
    for x in (-32, 32):
        boss = cq.Workplane("XZ").center(x, 0).circle(7).extrude(9, both=True)
        palm = palm.union(boss)
    # Two raised ears join the palm to the lower wrist-carrier pin while leaving
    # the centre open for the horizontal MG90S.
    for y in (-23, 23):
        palm = palm.union(_rounded_box(20, 8, 52, 3, at=(6, y, 30), long_axis="Y"))
    palm = _hole_y(palm, PALM_WRIST_HOLE[0], PALM_WRIST_HOLE[1], M4_CLEARANCE, 90)
    palm = _hole_y(palm, PALM_WRIST_SECOND_HOLE[0], PALM_WRIST_SECOND_HOLE[1], M4_CLEARANCE, 90)
    # MG90S lies on its side: output shaft is parallel to the jaw pivot pins.
    palm = palm.cut(_rounded_box(MG90S_OPENING[0], MG90S_BODY[2] + BODY_CLEARANCE, MG90S_OPENING[1], 2, at=(-4.6, 0, 14), long_axis="Y"))
    for y in (-17, 17):
        palm = _hole_z(palm, -4.6, y, M3_CLEARANCE)
    palm = palm.cut(_rounded_box(42, 32, 11, 8, at=(21, 0, -3), long_axis="Z"))
    for x in (-32, 32):
        palm = _hole_y(palm, x, 0, M3_CLEARANCE)
    for x in (-43, 43):
        for y in (-21, 21):
            palm = _hole_z(palm, x, y, M4_CLEARANCE)
    for x in (-28, 2):
        for y in (-12, 12):
            palm = _hole_z(palm, x, y, 2.8)
    return palm


def gripper_servo_saddle() -> cq.Workplane:
    """Removable U strap that clamps the horizontal MG90S into the palm."""
    saddle = _rounded_box(12, 42, 3, 1.3, at=(0, 0, 8), long_axis="Z")
    for y in (-19.5, 19.5):
        saddle = saddle.union(_rounded_box(12, 3, 12, 1.2, at=(0, y, 2.5), long_axis="Y"))
    for y in (-17, 17):
        saddle = _hole_z(saddle, 0, y, M3_CLEARANCE)
    return saddle


def gripper_jaw(left: bool = True) -> cq.Workplane:
    """Curved scoop jaw; print flat and add the soft pad after the fit test."""
    side = -1.0 if left else 1.0
    # Profile coordinates are mirrored about X=0 for a matched jaw pair.
    raw = [
        (25, 7), (39, 7), (39, -7), (33, -11), (32, -28),
        (27, -47), (17, -64), (6, -72), (1, -62), (9, -54),
        (16, -39), (20, -22), (19, -5),
    ]
    points = [(side * x, z) for x, z in raw]
    jaw = cq.Workplane("XZ").polyline(points).close().extrude(6, both=True)
    jaw = _hole_y(jaw, side * 32, 0, M3_CLEARANCE, 30)
    jaw = _hole_y(jaw, side * 22, -12, M3_CLEARANCE, 30)
    return jaw


def gripper_link_aero() -> cq.Workplane:
    link = _capsule_bar_x(GRIPPER_LINK_CENTRE_DISTANCE + 10, 8, 4, 3.5)
    link = _hole_z(link, -GRIPPER_LINK_CENTRE_DISTANCE / 2, 0, M3_CLEARANCE)
    link = _hole_z(link, GRIPPER_LINK_CENTRE_DISTANCE / 2, 0, M3_CLEARANCE)
    return link


def mg90s_side_cradle_coupon() -> cq.Workplane:
    """Small coupon for the horizontal MG90S pocket and saddle screw pitch."""
    coupon = _rounded_box(42, 46, 8, 4, at=(0, 0, 4), long_axis="Z")
    pocket = _rounded_box(
        MG90S_OPENING[0],
        MG90S_BODY[2] + BODY_CLEARANCE,
        8,
        2,
        at=(0, 0, 8),
        long_axis="Z",
    )
    coupon = coupon.cut(pocket)
    for y in (-17, 17):
        coupon = _hole_z(coupon, 0, y, M3_CLEARANCE)
    return coupon


def fairing_module(length: float) -> cq.Workplane:
    """Thin rounded sleeve with two internal collars for a 20 mm tube."""
    outer = _rounded_box(length, 36, 30, 7, long_axis="X")
    cavity = _rounded_box(
        length + 4,
        36 - 2 * FAIRING_WALL,
        30 - 2 * FAIRING_WALL,
        7 - FAIRING_WALL,
        long_axis="X",
    )
    shell = outer.cut(cavity)
    for x in (-length / 2 + 2, length / 2 - 2):
        # The collar overlaps the thin outer shell, making the sleeve one solid.
        collar = _rounded_box(3, 35, 29, 5, at=(x, 0, 0), long_axis="X")
        collar = collar.cut(_box(8, TUBE_SOCKET, TUBE_SOCKET, (x, 0, 0)))
        shell = shell.union(collar)
    return shell


def upper_fairing() -> cq.Workplane:
    return fairing_module(94)


def forearm_fairing() -> cq.Workplane:
    return fairing_module(104)


def counterbalance_tube_anchor() -> cq.Workplane:
    """Slide-on upper-tube ring with an M4 eye for a spring or elastic cord."""
    anchor = _rounded_box(20, 36, 36, 5, long_axis="X")
    anchor = anchor.cut(_box(26, TUBE_SOCKET, TUBE_SOCKET))
    anchor = anchor.union(_rounded_box(20, 10, 20, 3, at=(0, 0, -23), long_axis="X"))
    anchor = _hole_y(anchor, 0, -24, M4_CLEARANCE, 40)
    for x in (-6, 6):
        anchor = _hole_z(anchor, x, 0, M4_CLEARANCE, 60)
    return anchor


PARTS = {
    "FIT-001-MG996R-PLATE": (mg996r_fit_plate, 1, "PRINT FIRST"),
    "FIT-002-MG996R-CLAMP": (mg996r_clamp_bar, 2, "PRINT FIRST"),
    "FIT-003-MG90S-PLATE": (mg90s_fit_plate, 1, "PRINT FIRST"),
    "FIT-004-MG90S-CLAMP": (mg90s_clamp_bar, 2, "PRINT FIRST"),
    "FIT-005-20MM-TUBE": (tube_fit_coupon, 1, "PRINT FIRST"),
    "FIT-006-HORN-ADAPTER": (horn_fit_coupon, 1, "PRINT FIRST"),
    "FIT-007-MG90S-SIDE-CRADLE": (mg90s_side_cradle_coupon, 1, "PRINT FIRST"),
    "PRT-H01-J1-AERO-BASE": (j1_base_aero, 1, "AFTER FIT CHECK"),
    "PRT-H02-ROUNDED-YAW-DECK": (yaw_deck_aero, 1, "AFTER FIT CHECK"),
    "PRT-H03-OPEN-SHOULDER-PEDESTAL": (shoulder_pedestal_aero, 1, "AFTER FIT CHECK"),
    "PRT-H04-DUAL-SERVO-SHOULDER-YOKE": (shoulder_yoke_aero, 1, "AFTER FIT CHECK"),
    "PRT-H05-UPPER-LINK-HUB": (upper_link_hub_aero, 1, "AFTER FIT CHECK"),
    "PRT-H06-ELBOW-YOKE": (elbow_yoke_aero, 1, "AFTER FIT CHECK"),
    "PRT-H07-FOREARM-LINK-HUB": (forearm_link_hub_aero, 1, "AFTER FIT CHECK"),
    "PRT-H08-WRIST-CARRIER": (wrist_carrier_aero, 1, "AFTER FIT CHECK"),
    "PRT-H09-GRIPPER-PALM": (gripper_palm_aero, 1, "AFTER FIT CHECK"),
    "PRT-H10-GRIPPER-JAW-LEFT": (lambda: gripper_jaw(True), 1, "AFTER FIT CHECK"),
    "PRT-H11-GRIPPER-JAW-RIGHT": (lambda: gripper_jaw(False), 1, "AFTER FIT CHECK"),
    "PRT-H12-GRIPPER-LINK": (gripper_link_aero, 2, "AFTER FIT CHECK"),
    "PRT-H13-UPPER-FAIRING-94MM": (upper_fairing, 3, "OPTIONAL COSMETIC"),
    "PRT-H14-FOREARM-FAIRING-104MM": (forearm_fairing, 2, "OPTIONAL COSMETIC"),
    "PRT-H15-MG996R-CLAMP-BAR": (mg996r_clamp_bar, 6, "AFTER FIT CHECK"),
    "PRT-H16-MG90S-SERVO-SADDLE": (gripper_servo_saddle, 1, "AFTER FIT CHECK"),
    "PRT-H17-COUNTERBALANCE-TUBE-ANCHOR": (counterbalance_tube_anchor, 1, "AFTER FIT CHECK"),
}


def _servo_model(body: tuple[float, float, float], micro: bool = False) -> list[tuple[str, cq.Workplane, tuple[float, float, float]]]:
    x, y, z = body
    case = _rounded_box(x, y, z, 2.4 if not micro else 1.7, at=(0, 0, 0), long_axis="Z")
    flange_z = z * 0.22
    flange = _rounded_box(x + (15 if not micro else 9), y + 1.2, 2.4, 2, at=(0, 0, flange_z), long_axis="Z")
    top = cq.Workplane("XY").circle(y * 0.42).extrude(3).translate((x * 0.20, 0, z / 2 + 1.5))
    shaft = cq.Workplane("XY").circle(2.8 if not micro else 2.0).extrude(5).translate((x * 0.20, 0, z / 2 + 3))
    label = _rounded_box(x * 0.62, y + 0.5, z * 0.40, 1, at=(0, 0, -z * 0.05), long_axis="Z")
    return [
        ("case", case.union(flange).union(top), SERVO_BLACK),
        ("label", label, SERVO_LABEL),
        ("shaft", shaft, FASTENER),
    ]


def _horn_disc(radius: float = 18, thickness: float = 3) -> cq.Workplane:
    horn = cq.Workplane("XY").circle(radius).extrude(thickness, both=True)
    horn = horn.cut(cq.Workplane("XY").circle(radius * 0.68).extrude(thickness + 4, both=True))
    for angle in (0, 90, 180, 270):
        horn = horn.union(_rounded_box(radius * 1.25, 4, thickness, 1.7, at=(radius * 0.30, 0, 0), long_axis="X").rotate((0, 0, 0), (0, 0, 1), angle))
    return horn


def _place(shape: cq.Workplane, origin: tuple[float, float, float], y_angle: float = 0) -> cq.Workplane:
    return shape.rotate((0, 0, 0), (0, 1, 0), y_angle).translate(origin)


def _place_servo(
    components: list[Component],
    prefix: str,
    body: tuple[float, float, float],
    origin: tuple[float, float, float],
    rotations: tuple[tuple[tuple[float, float, float], float], ...] = (),
    micro: bool = False,
) -> None:
    for suffix, shape, color in _servo_model(body, micro=micro):
        for axis, angle in rotations:
            shape = shape.rotate((0, 0, 0), axis, angle)
        components.append(Component(f"{prefix}-{suffix}", shape.translate(origin), "servo", color))


def _bar_between_xz(
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    y: float,
    width: float = 5.0,
    depth: float = 4.0,
) -> cq.Workplane:
    """Create a rounded link whose end centres are exact X-Z coordinates."""
    dx, dz = end[0] - start[0], end[1] - start[1]
    length = math.hypot(dx, dz)
    angle_y = -math.degrees(math.atan2(dz, dx))
    link = _rounded_box(length, depth, width, min(width, depth) * 0.45, long_axis="X")
    return link.rotate((0, 0, 0), (0, 1, 0), angle_y).translate(((start[0] + end[0]) / 2, y, (start[1] + end[1]) / 2))


def assembly_components() -> list[Component]:
    """Return a color-coded, bent working pose that exposes all mechanisms."""
    result: list[Component] = []
    shoulder = (0.0, 0.0, ASSEMBLY_SHOULDER_Z)
    upper_angle = 18.0  # CadQuery +Y rotation slopes +X downward.
    elbow = (
        shoulder[0] + UPPER_LINK_LENGTH * math.cos(math.radians(upper_angle)),
        0.0,
        shoulder[2] - UPPER_LINK_LENGTH * math.sin(math.radians(upper_angle)),
    )
    fore_angle = ASSEMBLY_FORE_ANGLE_DEG
    wrist = (
        elbow[0] + FOREARM_LINK_LENGTH * math.cos(math.radians(fore_angle)),
        0.0,
        elbow[2] - FOREARM_LINK_LENGTH * math.sin(math.radians(fore_angle)),
    )

    def add(name: str, shape: cq.Workplane, group: str = "printed", color=PRINT_COLOR) -> None:
        result.append(Component(name, shape, group, color))

    add("J1 rounded base", j1_base_aero())
    add("J1 yaw deck", yaw_deck_aero().translate((0, 0, 10)))
    add("open shoulder pedestal", shoulder_pedestal_aero().translate((0, 0, 18)))
    add("dual-servo shoulder yoke", shoulder_yoke_aero().translate((0, 0, 108)))
    add("upper hub", _place(upper_link_hub_aero(), shoulder, upper_angle), color=PRINT_DARK)

    upper_tube = _box(UPPER_LINK_LENGTH, 20, 20, (UPPER_LINK_LENGTH / 2, 0, 0))
    add("300 mm aluminium upper tube", _place(upper_tube, shoulder, upper_angle), "aluminium", ALUMINIUM)
    for i, local_x in enumerate((52, 150, 248), 1):
        add(f"upper hollow fairing {i}", _place(upper_fairing().translate((local_x, 0, 0)), shoulder, upper_angle))
    counterbalance_local_x = 90.0
    add(
        "adjustable counterbalance tube anchor",
        _place(counterbalance_tube_anchor().translate((counterbalance_local_x, 0, 0)), shoulder, upper_angle),
        color=PRINT_DARK,
    )

    add("elbow yoke", _place(elbow_yoke_aero(), elbow, upper_angle), color=PRINT_DARK)
    add("forearm hub", _place(forearm_link_hub_aero(), elbow, fore_angle), color=PRINT_DARK)
    fore_tube = _box(FOREARM_LINK_LENGTH, 20, 20, (FOREARM_LINK_LENGTH / 2, 0, 0))
    add("220 mm aluminium forearm tube", _place(fore_tube, elbow, fore_angle), "aluminium", ALUMINIUM)
    for i, local_x in enumerate((55, 165), 1):
        add(f"forearm hollow fairing {i}", _place(forearm_fairing().translate((local_x, 0, 0)), elbow, fore_angle))
    add("wrist carrier", _place(wrist_carrier_aero(), wrist, fore_angle), color=PRINT_DARK)

    palm_origin = (wrist[0] + 5, 0, wrist[2] - 48)
    add("rounded gripper palm", gripper_palm_aero().translate(palm_origin))
    # Jaw profiles and palm use the same pivot coordinates by construction.
    add("left curved jaw", gripper_jaw(True).translate(palm_origin), color=PRINT_DARK)
    add("right curved jaw", gripper_jaw(False).translate(palm_origin), color=PRINT_DARK)

    # Soft replaceable pads are assembly-only visual references.
    for sx in (-1, 1):
        pad = _rounded_box(18, 14, 5, 2.2, at=(palm_origin[0] + sx * 9, 0, palm_origin[2] - 68), long_axis="Y")
        add(f"soft pad {'L' if sx < 0 else 'R'}", pad, "soft pad", PAD_COLOR)

    # Servo bodies are explicit reference models, never printable parts.
    mg996r_proxy_shaft_x = MG996R_BODY[0] * 0.20
    _place_servo(result, "J1 MG996R", MG996R_BODY, (-mg996r_proxy_shaft_x, 0, 42))
    _place_servo(result, "J2L MG996R", MG996R_BODY, (-mg996r_proxy_shaft_x, 43, shoulder[2]), (((1, 0, 0), 90),))
    _place_servo(result, "J2R MG996R", MG996R_BODY, (-mg996r_proxy_shaft_x, -43, shoulder[2]), (((1, 0, 0), -90),))
    _place_servo(result, "J3 MG996R", MG996R_BODY, (elbow[0] - mg996r_proxy_shaft_x, 43, elbow[2]), (((1, 0, 0), 90),))
    # Rotate MG90S so its shaft and both jaw pivots share the Y axis.
    servo_origin = (palm_origin[0] - MG90S_BODY[0] * 0.20, 0, palm_origin[2] + 14)
    _place_servo(result, "G1 MG90S", MG90S_BODY, servo_origin, (((1, 0, 0), 90),), micro=True)
    add("MG90S retaining saddle", gripper_servo_saddle().translate(servo_origin), color=PRINT_DARK)
    for y in (-17, 17):
        screw = cq.Workplane("XY").center(servo_origin[0], y).circle(1.45).extrude(15).translate((0, 0, palm_origin[2] + 2))
        add(f"MG90S saddle screw {'front' if y < 0 else 'rear'}", screw, "fastener", FASTENER)

    # Yellow output horns and links make the power path legible.
    add("J2 horn", _place(_horn_disc(), shoulder, upper_angle).rotate(shoulder, (shoulder[0], shoulder[1] + 1, shoulder[2]), 90), "drive", HORN_COLOR)
    add("J3 horn", _place(_horn_disc(), elbow, fore_angle).rotate(elbow, (elbow[0], elbow[1] + 1, elbow[2]), 90), "drive", HORN_COLOR)
    horn_center = (palm_origin[0], palm_origin[2] + 14)
    horn = _horn_disc(radius=11, thickness=2.5).rotate((0, 0, 0), (1, 0, 0), 90).translate((horn_center[0], -17, horn_center[1]))
    add("gripper servo horn", horn, "drive", HORN_COLOR)
    for sx in (-1, 1):
        horn_pin = (horn_center[0] + sx * 7, horn_center[1])
        jaw_pin = (palm_origin[0] + sx * 22, palm_origin[2] - 12)
        link = _bar_between_xz(horn_pin, jaw_pin, y=-10, width=5, depth=4)
        add(f"gripper linkage {'L' if sx < 0 else 'R'}", link, "drive", HORN_COLOR)
        pin = cq.Workplane("XZ").center(jaw_pin[0], jaw_pin[1]).circle(1.5).extrude(8, both=True)
        add(f"jaw drive pin {'L' if sx < 0 else 'R'}", pin, "fastener", FASTENER)
    for sx in (-1, 1):
        pivot_x = palm_origin[0] + sx * 32
        pin = cq.Workplane("XZ").center(pivot_x, palm_origin[2]).circle(1.5).extrude(9, both=True)
        add(f"jaw pivot pin {'L' if sx < 0 else 'R'}", pin, "fastener", FASTENER)
    for label, wrist_pin_local in (("lower", (7.0, -31.0)), ("upper", (7.0, 3.0))):
        wrist_pin_world = (
            wrist[0] + wrist_pin_local[0] * math.cos(math.radians(fore_angle)) + wrist_pin_local[1] * math.sin(math.radians(fore_angle)),
            wrist[2] - wrist_pin_local[0] * math.sin(math.radians(fore_angle)) + wrist_pin_local[1] * math.cos(math.radians(fore_angle)),
        )
        wrist_pin = cq.Workplane("XZ").center(*wrist_pin_world).circle(2.0).extrude(34, both=True)
        add(f"wrist-to-palm {label} pin", wrist_pin, "fastener", FASTENER)

    # Visual reference for a cheap adjustable elastic/spring counterbalance.
    base_anchor = (-28.0, 18.0 + 42.0)
    anchor_x = shoulder[0] + counterbalance_local_x * math.cos(math.radians(upper_angle)) + (-24.0) * math.sin(math.radians(upper_angle))
    anchor_z = shoulder[2] - counterbalance_local_x * math.sin(math.radians(upper_angle)) + (-24.0) * math.cos(math.radians(upper_angle))
    add("elastic counterbalance reference", _bar_between_xz(base_anchor, (anchor_x, anchor_z), y=-24, width=4, depth=4), "counterbalance", PAD_COLOR)
    return result


def assembly_shape() -> cq.Workplane:
    return cq.Workplane(obj=cq.Compound.makeCompound([item.shape.val() for item in assembly_components()]))


def assembly_model() -> cq.Assembly:
    assembly = cq.Assembly(name="FIGBOT_MG996R_AERO_V2")
    for item in assembly_components():
        assembly.add(item.shape, name=item.name, color=cq.Color(*item.color))
    return assembly


def _render_colored(path: Path, side: bool = False, gripper_closeup: bool = False) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    components = assembly_components()
    if gripper_closeup:
        components = [item for item in components if item.shape.val().BoundingBox().xmax > 440]
    fig = plt.figure(figsize=(12.5, 7.2), facecolor="#f5f3ee")
    ax = fig.add_subplot(111, projection="3d")
    all_xyz = []
    for item in components:
        xyz, faces = shape_mesh(item.shape)
        all_xyz.append(xyz)
        transparent_shell = gripper_closeup and item.name in {"rounded gripper palm", "wrist carrier"}
        alpha = 0.24 if transparent_shell else 1.0
        edge = "#d26b32" if transparent_shell else item.color
        mesh = Poly3DCollection(xyz[faces], facecolor=item.color, edgecolor=edge, linewidth=0.08 if transparent_shell else 0.01, alpha=alpha)
        ax.add_collection3d(mesh)
    import numpy as np

    vertices = np.vstack(all_xyz)
    mins, maxs = vertices.min(axis=0), vertices.max(axis=0)
    centre = (mins + maxs) / 2
    spans = maxs - mins
    margin = 0.07
    ax.set_xlim(mins[0] - spans[0] * margin, maxs[0] + spans[0] * margin)
    ax.set_ylim(mins[1] - max(spans[1], 30) * margin, maxs[1] + max(spans[1], 30) * margin)
    ax.set_zlim(mins[2] - spans[2] * margin, maxs[2] + spans[2] * margin)
    ax.set_box_aspect((max(spans[0], 1), max(spans[1], 1), max(spans[2], 1)))
    ax.set_axis_off()
    ax.view_init(elev=14 if gripper_closeup else (7 if side else 22), azim=-64 if gripper_closeup else (-90 if side else -58))
    ax.set_title(
        "FIGBOT AERO V2 | kıskaç mekanizması yakın görünüm" if gripper_closeup else
        ("FIGBOT AERO V2 | çalışma pozu ve gerçekçi motor yerleşimi" if not side
        else "FIGBOT AERO V2 | hareket zinciri: servo → horn/link → iki kavisli çene"),
        fontsize=15,
        weight="bold",
        color="#263238",
        pad=10,
    )
    legend = [
        Patch(facecolor=PRINT_COLOR, label="Hafif baskı kabuğu / taşıyıcı"),
        Patch(facecolor=ALUMINIUM, label="20×20 mm alüminyum ana taşıyıcı"),
        Patch(facecolor=SERVO_BLACK, label="Motor (montaj referansı)"),
        Patch(facecolor=HORN_COLOR, label="Horn ve hareket bağlantısı"),
        Patch(facecolor=PAD_COLOR, label="Değiştirilebilir yumuşak temas pedi"),
    ]
    ax.legend(handles=legend, loc="lower center", bbox_to_anchor=(0.5, -0.02), ncol=3, frameon=False, fontsize=9)
    if side and not gripper_closeup:
        labels = [
            (0.10, 0.73, "J2: çift MG996R omuz"),
            (0.47, 0.63, "J3: MG996R dirsek"),
            (0.78, 0.54, "G1: MG90S kıskaç servosu"),
            (0.86, 0.30, "Kavisli çeneler + yumuşak ped"),
        ]
        for x, y, label in labels:
            fig.text(x, y, label, fontsize=10, color="#263238", bbox=dict(boxstyle="round,pad=0.35", fc="white", ec="#d26b32", alpha=0.94))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=190, bbox_inches="tight", pad_inches=0.16)
    plt.close(fig)


def _layout_shape(part_ids: list[str], columns: int = 4, gap: float = 18) -> cq.Workplane:
    placed: list[cq.Shape] = []
    x_cursor = y_cursor = row_depth = 0.0
    for index, part_id in enumerate(part_ids):
        shape = PARTS[part_id][0]()
        bounds = shape.val().BoundingBox()
        if index and index % columns == 0:
            x_cursor = 0.0
            y_cursor += row_depth + gap
            row_depth = 0.0
        placed.append(shape.translate((x_cursor - bounds.xmin, y_cursor - bounds.ymin, -bounds.zmin)).val())
        x_cursor += bounds.xlen + gap
        row_depth = max(row_depth, bounds.ylen)
    return cq.Workplane(obj=cq.Compound.makeCompound(placed))


def build() -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    fit_dir = OUT / "fit_check_first"
    fit_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    printed_mass_g = 0.0
    optional_mass_g = 0.0
    for part_id, (builder, qty, phase) in PARTS.items():
        shape = builder()
        export_shape(shape, OUT, part_id, ("step", "stl"))
        if phase == "PRINT FIRST":
            export_shape(shape, fit_dir, part_id, ("stl",))
        bounds = shape.val().BoundingBox()
        mass_g = shape.val().Volume() / 1000 * PETG_DENSITY_G_CM3 * qty
        if phase == "OPTIONAL COSMETIC":
            optional_mass_g += mass_g
        else:
            printed_mass_g += mass_g
        rows.append([
            part_id, qty, phase, round(bounds.xlen, 2), round(bounds.ylen, 2), round(bounds.zlen, 2),
            round(shape.val().Volume() / 1000, 2), round(mass_g, 1), "PETG prototype", "PHYSICAL VALIDATION REQUIRED",
        ])
    with (OUT / "PRINT_MANIFEST.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(["part_id", "quantity", "phase", "x_mm", "y_mm", "z_mm", "volume_cm3_each", "estimated_mass_g_total", "material", "status"])
        writer.writerows(rows)
    with (OUT / "FULL_PRINT_ORDER.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(["part_id", "print_quantity", "material", "release"])
        for part_id, (_, qty, phase) in PARTS.items():
            if phase == "AFTER FIT CHECK":
                writer.writerow([part_id, qty, "PETG", FULL_PRINT_STATUS])

    contract = {
        "revision": "AERO-V2",
        "status": FULL_PRINT_STATUS,
        "servo_nominal_mm": {"MG996R": MG996R_BODY, "MG90S": MG90S_BODY},
        "clearance_mm": {"servo_body_total": BODY_CLEARANCE, "20mm_tube_socket": TUBE_SOCKET},
        "critical_dimensions_retained_mm": {
            "upper_link": UPPER_LINK_LENGTH,
            "forearm_link": FOREARM_LINK_LENGTH,
            "tool": TOOL_LENGTH,
        },
        "materials": {
            "primary_load_path": "20 x 20 x 1.5 mm light-alloy tube",
            "printed_parts": "PETG candidate",
            "jaw_pads": "soft silicone/foam candidate; food contact TBD",
        },
        "mass_estimate_g": {
            "required_printed_parts_including_fit_coupons": round(printed_mass_g, 1),
            "all_optional_hollow_fairings": round(optional_mass_g, 1),
            "basis": "CAD solid volume x 1.27 g/cm3; slicer output and hardware excluded",
        },
        "gripper_motion": "central MG90S horn drives two short links; links rotate mirrored curved jaws around palm pivots",
        "gripper_connection_map": [
            "wrist carrier to palm: two aligned M4 pins create a fixed-angle first-test wrist",
            "MG90S to palm: horizontal cradle plus removable two-screw printed saddle",
            "MG90S shaft to horn: supplied horn/spline and centre screw; fit unverified",
            "horn to jaws: two short links with M3-class pivot pins",
            "jaws to palm: two aligned M3-class pivot pins",
        ],
        "assembly_reference_models": "servo bodies, labels, shafts, horns, aluminium tubes and soft pads appear in STEP/GLB but are excluded from printable ZIP",
        "print_release": {
            "released_now": "FIT COUPONS for isolated dimensional checks only",
            "gripper_subassembly": FULL_PRINT_STATUS,
            "full_arm": FULL_PRINT_STATUS,
            "open_items": ["J1 mounting/shaft gap", "jaw-palm interference", "J2/J3 horn interface", "tube end insertion", "gripper linkage/spacer stack", "final fastener lengths"],
        },
    }
    (OUT / "AERO_V2.json").write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")

    readme = (
        "# FIGBOT MG996R AERO V2\n\n"
        "**DEC-039: HOLD FULL ARM AND GRIPPER PRINT.** The 2026-09-05 audit found actual assembly defects, not merely unverified physical performance. See FINAL_PRINT_AUDIT.json and SON_BASKI_KONTROLU.md. Older release wording and downloaded archives are superseded.\n\n"
        "Rounded single-arm digital prototype. The 300 and 220 mm aluminium tubes remain the primary load path. "
            "PRT-H13/H14 are optional 0.8 mm nominal (two 0.4 mm perimeters) hollow fairing sleeves and may be omitted for the lightest timing test.\n\n"
        "## Gripper\n\n"
        "The MG90S reference model sits in the rounded palm. A central horn and two short links rotate the mirrored curved jaws. "
        "The servo lies horizontally in a cradle and is held by PRT-H16, a removable two-screw saddle. "
        "Green pads in the assembly are soft-contact references and are not included as printable solids.\n\n"
        "## Print gate\n\n"
        "FIT-001 through FIT-007 are isolated dimensional trials. The DEC-036 nominal clone dimension assumption is retained, but full-set readiness is corrected by DEC-039 after assembly defects were identified. Do not print any servo, horn, tube, fastener or green pad geometry visible in the assembly. "
        "All fits, jaw motion, stiffness, mass, life and 4-second collection-cycle performance require physical validation.\n"
    )
    (OUT / "README.md").write_text(readme, encoding="utf-8")
    (fit_dir / "README.txt").write_text("FIT-001 through FIT-007: isolated dimensional trials only. Full arm/gripper set is on HOLD under DEC-039 because of assembly defects. Nominal servo dimensions remain accepted. Coupons do not prove mounting strength or full assembly fit. Import in mm at 100% scale and slice for your actual printer.\n", encoding="utf-8")
    (OUT / "PRINT_READINESS.md").write_text(
        "# AERO V2 print readiness\n\n"
        "**HOLD FULL ARM AND GRIPPER PRINT — DEC-039, 2026-09-05.**\n\n"
        "The full-set filename is retained for traceability, not approval. J1 drive/mount geometry, jaw-palm interference, horn interfaces and tube end insertion need correction. "
        "Only isolated FIT-001 through FIT-007 dimensional trials are recommended now. This is not a new motor-measurement permission gate: user-authorized nominal clone body dimensions remain accepted.\n\n"
        "See FINAL_PRINT_AUDIT.json and SON_BASKI_KONTROLU.md. Mesh validity alone does not prove assembly or motion. Final screws, spacers, support hardware, printer profile and physical performance remain unresolved.\n",
        encoding="utf-8",
    )
    hardware_rows = [
        ["MG996R supplied horns", 4, "delivered with servos", "FIT-006 validation required"],
        ["MG90S supplied horn", 1, "delivered with servo", "spline and centre screw unverified"],
        ["M3 bolts, washers and locknuts", "TBD", "length after fit measurement", "servo clamps, jaws and links"],
        ["M4 bolts, washers and locknuts", "TBD", "length after stack measurement", "tube clamps and wrist pivot"],
        ["M8 shoulder/elbow support hardware", "TBD", "length after stack measurement", "bearing/bushing stack unverified"],
        ["20 x 20 x 1.5 mm light-alloy tube", 2, "CUT LENGTH TBD; pivot spans 300 mm + 220 mm", "DEC-039: resolve socket insertion before cutting"],
        ["soft jaw pads", 2, "material and thickness TBD", "food contact and marking unverified"],
        ["M4 wrist bolts/pins", 2, "length after printed stack measurement", "fixed-angle wrist"],
        ["elastic cord or extension spring", 1, "force/length tuned on bench", "anchors included; PHYSICAL VALIDATION REQUIRED"],
    ]
    with (OUT / "HARDWARE_REQUIRED.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(["item", "quantity", "size_or_length", "status"])
        writer.writerows(hardware_rows)

    model = assembly_model()
    ASSEMBLY_STEP.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(ASSEMBLY_STEP), exportType="STEP", mode="default")
    model.save(str(ASSEMBLY_GLB), exportType="GLTF", tolerance=0.20, angularTolerance=0.12)
    _render_colored(RENDER_ISO)
    _render_colored(RENDER_SIDE, side=True)
    _render_colored(RENDER_GRIPPER, gripper_closeup=True)

    fit_ids = [key for key, (_, _, phase) in PARTS.items() if phase == "PRINT FIRST"]
    with (fit_dir / "FIT_PRINT_ORDER.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(["part_id", "print_quantity", "purpose"])
        for part_id in fit_ids:
            writer.writerow([part_id, PARTS[part_id][1], "ISOLATED DIMENSIONAL TRIAL ONLY"])
    with zipfile.ZipFile(OUT / "FIGBOT_MG996R_AERO_V2_FIT_CHECK_FIRST.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        archive.write(fit_dir / "README.txt", "README.txt")
        archive.write(fit_dir / "FIT_PRINT_ORDER.csv", "FIT_PRINT_ORDER.csv")
        if (OUT / "SON_BASKI_KONTROLU.md").exists():
            archive.write(OUT / "SON_BASKI_KONTROLU.md", "SON_BASKI_KONTROLU.md")
        for part_id in fit_ids:
            archive.write(fit_dir / f"{part_id}.stl", f"{part_id}.stl")
    stage2_ids = [
        "PRT-H09-GRIPPER-PALM",
        "PRT-H10-GRIPPER-JAW-LEFT",
        "PRT-H11-GRIPPER-JAW-RIGHT",
        "PRT-H12-GRIPPER-LINK",
        "PRT-H16-MG90S-SERVO-SADDLE",
    ]
    with zipfile.ZipFile(OUT / "FIGBOT_MG996R_AERO_V2_GRIPPER_ONLY_STL.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        archive.write(OUT / "PRINT_READINESS.md", "PRINT_READINESS.md")
        if (OUT / "SON_BASKI_KONTROLU.md").exists():
            archive.write(OUT / "SON_BASKI_KONTROLU.md", "SON_BASKI_KONTROLU.md")
        for part_id in stage2_ids:
            archive.write(OUT / f"{part_id}.stl", f"{part_id}.stl")
    required_ids = [key for key, (_, _, phase) in PARTS.items() if phase == "AFTER FIT CHECK"]
    optional_ids = [key for key, (_, _, phase) in PARTS.items() if phase == "OPTIONAL COSMETIC"]
    full_zip = OUT / "FIGBOT_MG996R_AERO_V2_FULL_BENCH_PROTOTYPE_STL.zip"
    with zipfile.ZipFile(full_zip, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.write(OUT / "README.md", "README.md")
        archive.write(OUT / "PRINT_READINESS.md", "PRINT_READINESS.md")
        archive.write(OUT / "HARDWARE_REQUIRED.csv", "HARDWARE_REQUIRED.csv")
        archive.write(OUT / "FULL_PRINT_ORDER.csv", "FULL_PRINT_ORDER.csv")
        archive.write(OUT / "PRINT_MANIFEST.csv", "PRINT_MANIFEST.csv")
        archive.write(OUT / "AERO_V2.json", "AERO_V2.json")
        for report_name in ("FINAL_PRINT_AUDIT.json", "SON_BASKI_KONTROLU.md"):
            if (OUT / report_name).exists():
                archive.write(OUT / report_name, report_name)
        for part_id in required_ids:
            archive.write(OUT / f"{part_id}.stl", f"{part_id}.stl")
    with zipfile.ZipFile(OUT / "FIGBOT_MG996R_AERO_V2_OPTIONAL_FAIRINGS_STL.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        archive.write(OUT / "PRINT_READINESS.md", "PRINT_READINESS.md")
        for part_id in optional_ids:
            archive.write(OUT / f"{part_id}.stl", f"{part_id}.stl")
    (OUT / "FIGBOT_MG996R_AERO_V2_ALL_PRINTABLE_STL.zip").unlink(missing_ok=True)
    (OUT / "FIGBOT_MG996R_AERO_V2_ALL_STL_ENGINEERING_PREVIEW_NOT_RELEASED.zip").unlink(missing_ok=True)
    (OUT / "FIGBOT_MG996R_AERO_V2_GRIPPER_STAGE2_WAIT_FOR_FIT.zip").unlink(missing_ok=True)
    return OUT


if __name__ == "__main__":
    print(build())
