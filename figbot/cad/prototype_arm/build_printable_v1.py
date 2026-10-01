"""Generate the first printable MG996R/MG90S arm interface pack.

This is a low-cost bench prototype.  It deliberately clamps the servo flanges
with separate bars so the design does not depend on clone-specific tab holes.
The supplied servo horns remain part of the load path; horn fit and every
printed structural part require physical validation before fast motion.
"""

from __future__ import annotations

import csv
import json
import zipfile
from pathlib import Path

import cadquery as cq

from cad.utils import ROOT, export_shape, render_preview


OUT = ROOT / "cad" / "prototype_arm" / "printable_v1"
ASSEMBLY_OUT = ROOT / "cad" / "assembly" / "FIGBOT_MG996R_PRINTABLE_V1.step"
RENDER_OUT = ROOT / "renders" / "FIGBOT_MG996R_PRINTABLE_V1_isometric.png"

# Manufacturer nominal body envelopes.  Delivered clone variation is unknown.
MG996R_BODY = (40.7, 19.7, 42.9)
MG90S_BODY = (22.8, 12.2, 28.5)
BODY_CLEARANCE = 0.8
MG996R_OPENING = (MG996R_BODY[0] + BODY_CLEARANCE, MG996R_BODY[1] + BODY_CLEARANCE)
MG90S_OPENING = (MG90S_BODY[0] + BODY_CLEARANCE, MG90S_BODY[1] + BODY_CLEARANCE)
TUBE_NOMINAL = 20.0
TUBE_SOCKET = 20.5
M3_CLEARANCE = 3.4
M4_CLEARANCE = 4.5
M8_CLEARANCE = 8.4


def _box(x: float, y: float, z: float, at=(0.0, 0.0, 0.0)) -> cq.Workplane:
    return cq.Workplane("XY").box(x, y, z).translate(at)


def _hole_z(shape: cq.Workplane, x: float, y: float, diameter: float, height: float = 30) -> cq.Workplane:
    tool = cq.Workplane("XY").center(x, y).circle(diameter / 2).extrude(height, both=True)
    return shape.cut(tool)


def _hole_y(shape: cq.Workplane, x: float, z: float, diameter: float, depth: float = 60) -> cq.Workplane:
    tool = cq.Workplane("XZ").center(x, z).circle(diameter / 2).extrude(depth, both=True)
    return shape.cut(tool)


def _slot_z(shape: cq.Workplane, x: float, y: float, sx: float, sy: float, height: float = 30) -> cq.Workplane:
    return shape.cut(_box(sx, sy, height, (x, y, 0)))


def _servo_plate(
    body_opening: tuple[float, float],
    size: tuple[float, float, float],
    clamp_half_spacing: float,
) -> cq.Workplane:
    x, y, z = size
    plate = _box(x, y, z, (0, 0, z / 2))
    plate = plate.cut(_box(body_opening[0], body_opening[1], z + 4, (0, 0, z / 2)))
    hole_x = x / 2 - 6
    hole_y = clamp_half_spacing
    for px in (-hole_x, hole_x):
        for py in (-hole_y, hole_y):
            plate = _hole_z(plate, px, py, M3_CLEARANCE)
    return plate


def mg996r_fit_plate() -> cq.Workplane:
    return _servo_plate(MG996R_OPENING, (70, 42, 4), 15)


def mg996r_clamp_bar() -> cq.Workplane:
    bar = _box(12, 36, 4, (0, 0, 2))
    for y in (-15, 15):
        bar = _hole_z(bar, 0, y, M3_CLEARANCE)
    return bar


def mg90s_fit_plate() -> cq.Workplane:
    return _servo_plate(MG90S_OPENING, (48, 32, 3), 12)


def mg90s_clamp_bar() -> cq.Workplane:
    bar = _box(9, 28, 3, (0, 0, 1.5))
    for y in (-12, 12):
        bar = _hole_z(bar, 0, y, 2.8)
    return bar


def tube_fit_coupon() -> cq.Workplane:
    body = _box(34, 34, 26, (0, 0, 13))
    body = body.cut(_box(TUBE_SOCKET, TUBE_SOCKET, 32, (0, 0, 16)))
    body = body.cut(_box(2.0, 17, 18, (0, 8.5, 22)))
    for x in (-11, 11):
        body = _hole_z(body, x, 12, M4_CLEARANCE)
    return body


def horn_fit_coupon() -> cq.Workplane:
    disc = cq.Workplane("XY").circle(20).extrude(5)
    disc = _hole_z(disc, 0, 0, M3_CLEARANCE)
    # Four radial slots accept common cross/round supplied horns without
    # pretending that clone horn-hole positions are controlled.
    for angle in (0, 90, 180, 270):
        slot = _box(13, 2.6, 12, (10, 0, 0)).rotate((0, 0, 0), (0, 0, 1), angle)
        disc = disc.cut(slot)
    return disc


def j1_base() -> cq.Workplane:
    base = _box(110, 110, 8, (0, 0, 4))
    base = base.union(cq.Workplane("XY").circle(47).circle(40).extrude(10))
    base = base.cut(_box(MG996R_OPENING[0], MG996R_OPENING[1], 24, (0, 0, 4)))
    for x in (-48, 48):
        for y in (-42, 42):
            base = _slot_z(base, x, y, 12, 5)
    for x in (-29, 29):
        for y in (-15, 15):
            base = _hole_z(base, x, y, M3_CLEARANCE)
    return base


def yaw_deck() -> cq.Workplane:
    deck = _box(96, 82, 8, (0, 0, 6))
    # Printed annular sliding surface transfers arm bending into the fixed base.
    deck = deck.union(cq.Workplane("XY").circle(39.6).circle(34).extrude(2))
    deck = _hole_z(deck, 0, 0, M3_CLEARANCE)
    for angle in (0, 90, 180, 270):
        slot = _box(14, 2.6, 20, (10, 0, 6)).rotate((0, 0, 0), (0, 0, 1), angle)
        deck = deck.cut(slot)
    for x in (-32, 32):
        for y in (-27, 27):
            deck = _hole_z(deck, x, y, M4_CLEARANCE)
    return deck


def shoulder_riser() -> cq.Workplane:
    bottom = _box(80, 70, 6, (0, 0, 3))
    top = _box(80, 70, 6, (0, 0, 87))
    riser = bottom.union(top)
    for x in (-35, 35):
        for y in (-30, 30):
            riser = riser.union(_box(10, 10, 78, (x, y, 45)))
    for x in (-32, 32):
        for y in (-27, 27):
            riser = _hole_z(riser, x, y, M4_CLEARANCE, 220)
    return riser


def _side_servo_opening(shape: cq.Workplane, side_y: float, axis_z: float) -> cq.Workplane:
    opening = _box(MG996R_OPENING[0], 18, MG996R_OPENING[1], (0, side_y, axis_z))
    shape = shape.cut(opening)
    for x in (-31, 31):
        for z in (axis_z - 15, axis_z + 15):
            shape = _hole_y(shape, x, z, M3_CLEARANCE)
    return shape


def shoulder_yoke() -> cq.Workplane:
    yoke = _box(80, 70, 6, (0, 0, 3))
    for y in (-19, 19):
        yoke = yoke.union(_box(74, 6, 64, (0, y, 38)))
        yoke = _side_servo_opening(yoke, y, 38)
    for x in (-32, 32):
        for y in (-27, 27):
            yoke = _hole_z(yoke, x, y, M4_CLEARANCE)
    return yoke


def _horn_slots_y(shape: cq.Workplane, y_depth: float = 50) -> cq.Workplane:
    shape = _hole_y(shape, 0, 0, M3_CLEARANCE, y_depth)
    for angle in (0, 90, 180, 270):
        slot = _box(13, y_depth, 2.6, (10, 0, 0)).rotate((0, 0, 0), (0, 1, 0), angle)
        shape = shape.cut(slot)
    return shape


def upper_link_hub() -> cq.Workplane:
    hub = _box(46, 29.4, 32, (15, 0, 0))
    hub = hub.union(cq.Workplane("XZ").circle(19).extrude(29.4 / 2, both=True))
    hub = hub.cut(_box(39, TUBE_SOCKET, TUBE_SOCKET, (27, 0, 0)))
    hub = _horn_slots_y(hub)
    for x in (23, 35):
        hub = _hole_z(hub, x, 0, M4_CLEARANCE)
    return hub


def elbow_yoke() -> cq.Workplane:
    root = _box(46, 34, 34, (-20, 0, 0))
    root = root.cut(_box(39, TUBE_SOCKET, TUBE_SOCKET, (-23, 0, 0)))
    yoke = root
    for y in (-19, 19):
        yoke = yoke.union(_box(62, 6, 64, (0, y, 0)))
    yoke = _side_servo_opening(yoke, 19, 0)
    yoke = _hole_y(yoke, 0, 0, M8_CLEARANCE)
    for x in (-31, 31):
        yoke = _hole_y(yoke, x, 0, M4_CLEARANCE)
    for x in (-32, -19):
        yoke = _hole_z(yoke, x, 0, M4_CLEARANCE)
    return yoke


def forearm_link_hub() -> cq.Workplane:
    hub = _box(46, 29.0, 32, (15, 0, 0))
    hub = hub.union(cq.Workplane("XZ").circle(19).extrude(29.0 / 2, both=True))
    hub = hub.cut(_box(39, TUBE_SOCKET, TUBE_SOCKET, (27, 0, 0)))
    hub = _horn_slots_y(hub)
    for x in (23, 35):
        hub = _hole_z(hub, x, 0, M4_CLEARANCE)
    return hub


def wrist_carrier() -> cq.Workplane:
    carrier = _box(46, 34, 34, (-20, 0, 0))
    carrier = carrier.cut(_box(39, TUBE_SOCKET, TUBE_SOCKET, (-23, 0, 0)))
    carrier = carrier.union(_box(6, 64, 54, (6, 0, -10)))
    for y in (-22, 22):
        for z in (-25, 5):
            carrier = _hole_y(carrier, 6, z, M4_CLEARANCE)
    carrier = _hole_y(carrier, -8, 19, M4_CLEARANCE)
    for x in (-32, -19):
        carrier = _hole_z(carrier, x, 0, M4_CLEARANCE)
    return carrier


def gripper_palm() -> cq.Workplane:
    palm = _box(74, 66, 6, (0, 0, 3))
    palm = palm.cut(_box(MG90S_OPENING[0], MG90S_OPENING[1], 20, (-14, 0, 3)))
    for x in (-34, 34):
        for y in (-24, 24):
            palm = _hole_z(palm, x, y, M4_CLEARANCE)
    for x in (-32, 18):
        for y in (-22, 22):
            palm = _hole_z(palm, x, y, M3_CLEARANCE)
    for x in (-34, 6):
        for y in (-12, 12):
            palm = _hole_z(palm, x, y, 2.8)
    return palm


def gripper_finger() -> cq.Workplane:
    # Print on its broad side.  Add 2-3 mm silicone/foam to the inner pad.
    finger = _box(70, 12, 8, (28, 0, 49))
    finger = finger.union(_box(16, 12, 58, (55, 0, 25)))
    finger = _hole_z(finger, 0, 0, M3_CLEARANCE, 120)
    finger = _hole_z(finger, 14, 0, M3_CLEARANCE, 120)
    return finger


def gripper_link() -> cq.Workplane:
    link = _box(48, 8, 3, (0, 0, 1.5))
    link = _hole_z(link, -19, 0, M3_CLEARANCE)
    link = _hole_z(link, 19, 0, M3_CLEARANCE)
    return link


PARTS = {
    "FIT-001-MG996R-PLATE": (mg996r_fit_plate, 1, "PRINT FIRST"),
    "FIT-002-MG996R-CLAMP": (mg996r_clamp_bar, 2, "PRINT FIRST"),
    "FIT-003-MG90S-PLATE": (mg90s_fit_plate, 1, "PRINT FIRST"),
    "FIT-004-MG90S-CLAMP": (mg90s_clamp_bar, 2, "PRINT FIRST"),
    "FIT-005-20MM-TUBE": (tube_fit_coupon, 1, "PRINT FIRST"),
    "FIT-006-HORN-ADAPTER": (horn_fit_coupon, 1, "PRINT FIRST"),
    "PRT-G01-J1-BASE": (j1_base, 1, "AFTER FIT CHECK"),
    "PRT-G02-YAW-DECK": (yaw_deck, 1, "AFTER FIT CHECK"),
    "PRT-G03-SHOULDER-RISER": (shoulder_riser, 1, "AFTER FIT CHECK"),
    "PRT-G04-DUAL-SHOULDER-YOKE": (shoulder_yoke, 1, "AFTER FIT CHECK"),
    "PRT-G05-UPPER-LINK-HUB": (upper_link_hub, 1, "AFTER FIT CHECK"),
    "PRT-G06-ELBOW-YOKE": (elbow_yoke, 1, "AFTER FIT CHECK"),
    "PRT-G07-FOREARM-LINK-HUB": (forearm_link_hub, 1, "AFTER FIT CHECK"),
    "PRT-G08-WRIST-CARRIER": (wrist_carrier, 1, "AFTER FIT CHECK"),
    "PRT-G09-GRIPPER-PALM": (gripper_palm, 1, "AFTER FIT CHECK"),
    "PRT-G10-GRIPPER-FINGER": (gripper_finger, 2, "AFTER FIT CHECK"),
    "PRT-G11-GRIPPER-LINK": (gripper_link, 2, "AFTER FIT CHECK"),
    "PRT-G12-MG996R-CLAMP-BAR": (mg996r_clamp_bar, 6, "AFTER FIT CHECK"),
}


def _servo_envelope(body: tuple[float, float, float]) -> cq.Workplane:
    return _box(*body, (0, 0, body[2] / 2))


def assembly_shape() -> cq.Workplane:
    shapes: list[cq.Shape] = []
    shapes.append(j1_base().val())
    shapes.append(yaw_deck().translate((0, 0, 10)).val())
    shapes.append(shoulder_riser().translate((0, 0, 18)).val())
    shapes.append(shoulder_yoke().translate((0, 0, 108)).val())
    shoulder_z = 146.0
    shapes.append(upper_link_hub().translate((0, 0, shoulder_z)).val())
    shapes.append(_box(300, 20, 20, (150, 0, shoulder_z)).val())
    shapes.append(elbow_yoke().translate((300, 0, shoulder_z)).val())
    shapes.append(forearm_link_hub().translate((300, 0, shoulder_z)).val())
    shapes.append(_box(220, 20, 20, (410, 0, shoulder_z)).val())
    shapes.append(wrist_carrier().translate((520, 0, shoulder_z)).val())
    shapes.append(gripper_palm().translate((526, 0, shoulder_z - 72)).val())
    # Servo packaging proxies: J1, mirrored J2, J3 and G1.
    shapes.append(_servo_envelope(MG996R_BODY).translate((0, 0, -34)).val())
    for y in (-43, 43):
        servo = _servo_envelope(MG996R_BODY).rotate((0, 0, 0), (1, 0, 0), 90)
        shapes.append(servo.translate((0, y, shoulder_z - 10)).val())
    servo_j3 = _servo_envelope(MG996R_BODY).rotate((0, 0, 0), (1, 0, 0), 90)
    shapes.append(servo_j3.translate((300, 43, shoulder_z - 10)).val())
    shapes.append(_servo_envelope(MG90S_BODY).translate((512, 0, shoulder_z - 90)).val())
    return cq.Workplane(obj=cq.Compound.makeCompound(shapes))


def _layout_shape(part_ids: list[str], columns: int, gap: float = 18.0) -> cq.Workplane:
    placed: list[cq.Shape] = []
    x_cursor = 0.0
    y_cursor = 0.0
    row_depth = 0.0
    for index, part_id in enumerate(part_ids):
        shape = PARTS[part_id][0]()
        bounds = shape.val().BoundingBox()
        if index and index % columns == 0:
            x_cursor = 0.0
            y_cursor += row_depth + gap
            row_depth = 0.0
        translated = shape.translate((x_cursor - bounds.xmin, y_cursor - bounds.ymin, -bounds.zmin))
        placed.append(translated.val())
        x_cursor += bounds.xlen + gap
        row_depth = max(row_depth, bounds.ylen)
    return cq.Workplane(obj=cq.Compound.makeCompound(placed))


def build() -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "fit_check_first").mkdir(parents=True, exist_ok=True)
    manifest_rows = []
    for part_id, (builder, qty, phase) in PARTS.items():
        shape = builder()
        export_shape(shape, OUT, part_id, ("step", "stl"))
        if phase == "PRINT FIRST":
            cq.exporters.export(
                shape,
                str(OUT / "fit_check_first" / f"{part_id}.stl"),
                exportType="STL",
                tolerance=0.08,
                angularTolerance=0.1,
            )
        box = shape.val().BoundingBox()
        manifest_rows.append(
            [part_id, qty, phase, round(box.xlen, 2), round(box.ylen, 2), round(box.zlen, 2), "PETG prototype", "PHYSICAL VALIDATION REQUIRED"]
        )

    with (OUT / "PRINT_MANIFEST.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(["part_id", "quantity", "phase", "x_mm", "y_mm", "z_mm", "material", "status"])
        writer.writerows(manifest_rows)

    contract = {
        "revision": "PRINTABLE-V1",
        "status": "DIGITAL PROTOTYPE / PHYSICAL VALIDATION REQUIRED",
        "servo_nominal_mm": {"MG996R": MG996R_BODY, "MG90S": MG90S_BODY},
        "clearance_mm": {"servo_body_total": BODY_CLEARANCE, "20mm_tube_socket": TUBE_SOCKET},
        "architecture": {
            "J1": "one MG996R; printed annular sliding support limits horn bending",
            "J2": "two mirrored MG996R clamped by flange bars",
            "J3": "one MG996R plus opposite M8 printed-bushing pivot",
            "G1": "one MG90S with two linked scoop fingers",
            "links": "20 x 20 x 1.5 mm aluminium tube, 300 mm and 220 mm nominal",
        },
        "first_print_gate": [
            "print FIT-001 through FIT-006 only",
            "verify servo insertion, flange capture, horn slots and tube socket",
            "measure delivered parts before changing BODY_CLEARANCE or holes",
        ],
    }
    (OUT / "PRINTABLE_V1.json").write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")

    readme = (
        "FIGBOT MG996R/MG90S PRINTABLE V1 — FIRST PRINT\n\n"
        "1. Print only the six FIT files first.\n"
        "2. Suggested start point: PETG, 0.20 mm layer, 4 walls, 35% infill.\n"
        "3. Do not scale the STL in the slicer.\n"
        "4. Check MG996R and MG90S body insertion without forcing.\n"
        "5. Check clamp bars with loose M3 hardware; do not crush the servo case.\n"
        "6. Check the supplied horn against the radial-slot coupon.\n"
        "7. Check the actual 20 mm tube in FIT-005.\n"
        "8. Record measured body, flange, horn and tube dimensions before full printing.\n\n"
        "These parts are a fit check, not a safety or strength release.\n"
    )
    (OUT / "fit_check_first" / "README.txt").write_text(readme, encoding="utf-8")

    fit_ids = [part_id for part_id, (_, _, phase) in PARTS.items() if phase == "PRINT FIRST"]
    structural_ids = [part_id for part_id, (_, _, phase) in PARTS.items() if phase != "PRINT FIRST"]
    render_preview(
        _layout_shape(fit_ids, columns=3),
        ROOT / "renders" / "FIGBOT_MG996R_FIT_CHECK_FIRST.png",
        "FIGBOT | print these fit coupons first",
        elev=34,
        azim=-55,
    )
    render_preview(
        _layout_shape(structural_ids, columns=4),
        ROOT / "renders" / "FIGBOT_MG996R_PRINTED_PARTS_LAYOUT.png",
        "FIGBOT | printable V1 structural part layout",
        elev=34,
        azim=-55,
    )

    with zipfile.ZipFile(OUT / "FIGBOT_MG996R_FIT_CHECK_FIRST.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        archive.write(OUT / "fit_check_first" / "README.txt", "README.txt")
        for part_id in fit_ids:
            archive.write(OUT / "fit_check_first" / f"{part_id}.stl", f"{part_id}.stl")
    with zipfile.ZipFile(OUT / "FIGBOT_MG996R_PRINTABLE_V1_ALL_STL.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        if (OUT / "README.md").is_file():
            archive.write(OUT / "README.md", "README.md")
        archive.write(OUT / "PRINT_MANIFEST.csv", "PRINT_MANIFEST.csv")
        archive.write(OUT / "PRINTABLE_V1.json", "PRINTABLE_V1.json")
        for part_id in PARTS:
            archive.write(OUT / f"{part_id}.stl", f"{part_id}.stl")

    assembly = assembly_shape()
    cq.exporters.export(assembly, str(ASSEMBLY_OUT), exportType="STEP")
    render_preview(assembly, RENDER_OUT, "FIGBOT | MG996R printable arm V1", elev=20, azim=-55)
    return OUT


if __name__ == "__main__":
    print(build())
