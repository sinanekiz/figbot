"""Master builders for numbered FIGBOT custom parts."""

from __future__ import annotations

import math

import cadquery as cq

from cad.config import parameters as p


def _rounded_box(x: float, y: float, z: float, radius: float = 3.0) -> cq.Workplane:
    solid = cq.Workplane("XY").box(x, y, z)
    try:
        return solid.edges("|Z").fillet(radius)
    except Exception:
        return solid


def arm_001() -> cq.Workplane:
    plate = _rounded_box(p.BASE_PLATE_WIDTH, p.BASE_PLATE_DEPTH, p.BASE_PLATE_THICKNESS, 7)
    holes = [(-135, -115), (-135, 115), (135, -115), (135, 115)]
    for x, y in holes:
        plate = plate.cut(cq.Workplane("XY").center(x, y).circle(4.5).extrude(p.BASE_PLATE_THICKNESS * 2, both=True))
    # J1 NEMA23 geared-motor pilot and four-hole flange pattern.
    plate = plate.cut(cq.Workplane("XY").circle(p.NEMA23_PILOT_DIAMETER / 2 + 0.25).extrude(p.BASE_PLATE_THICKNESS * 2, both=True))
    h = p.NEMA23_MOUNT_PITCH / 2
    for x, y in ((-h, -h), (-h, h), (h, -h), (h, h)):
        plate = plate.cut(cq.Workplane("XY").center(x, y).circle(p.NEMA23_MOUNT_HOLE / 2).extrude(p.BASE_PLATE_THICKNESS * 2, both=True))
    return plate


def arm_002() -> cq.Workplane:
    # Rotating shoulder pedestal: machined/fabricated aluminium, not a printed
    # load-bearing shell. J2 axis is along Y at z=ARM_BASE_HEIGHT.
    base = _rounded_box(180, 150, 12, 6).translate((0, 0, 6))
    left = _rounded_box(96, 12, p.SHOULDER_PEDESTAL_HEIGHT, 5).translate((0, -57, p.SHOULDER_PEDESTAL_HEIGHT / 2))
    right = _rounded_box(96, 12, p.SHOULDER_PEDESTAL_HEIGHT, 5).translate((0, 57, p.SHOULDER_PEDESTAL_HEIGHT / 2))
    bridge = _rounded_box(96, 126, 12, 4).translate((0, 0, 42))
    body = base.union(left).union(right).union(bridge)
    bearing = cq.Workplane("XZ").center(0, p.SHOULDER_PEDESTAL_HEIGHT).circle(p.J1_J2_BEARING_OD / 2 + 0.02).extrude(160, both=True)
    body = body.cut(bearing)
    # J2 motor pilot and M5 clearance holes in the outer cheek.
    pilot = cq.Workplane("XZ").center(0, p.SHOULDER_PEDESTAL_HEIGHT).circle(p.NEMA23_PILOT_DIAMETER / 2 + 0.25).extrude(18).translate((0, -70, 0))
    body = body.cut(pilot)
    h = p.NEMA23_MOUNT_PITCH / 2
    for x, z in ((-h, -h), (-h, h), (h, -h), (h, h)):
        hole = cq.Workplane("XZ").center(x, p.SHOULDER_PEDESTAL_HEIGHT + z).circle(p.NEMA23_MOUNT_HOLE / 2).extrude(18).translate((0, -70, 0))
        body = body.cut(hole)
    return body


def _tube(length: float) -> cq.Workplane:
    outer = cq.Workplane("XY").box(length, p.ARM_LINK_TUBE_WIDTH, p.ARM_LINK_TUBE_HEIGHT).translate((length / 2, 0, 0))
    inner = cq.Workplane("XY").box(length + 2, p.ARM_LINK_TUBE_WIDTH - 2*p.ARM_LINK_WALL, p.ARM_LINK_TUBE_HEIGHT - 2*p.ARM_LINK_WALL).translate((length / 2, 0, 0))
    tube = outer.cut(inner)
    for x in (16, length - 16):
        tube = tube.cut(cq.Workplane("XZ").center(x, 0).circle(3.2).extrude(p.ARM_LINK_TUBE_WIDTH * 2, both=True))
    return tube


def arm_003() -> cq.Workplane:
    return _tube(p.ARM_UPPER_LENGTH)


def arm_004() -> cq.Workplane:
    # Aluminium elbow clevis. The 608 bearing bores and NEMA17 mounting face
    # are coaxial so the gearbox never carries the arm bending load alone.
    hub = cq.Workplane("XZ").circle(34).extrude(28, both=True)
    clamp = _rounded_box(82, 56, 44, 5).translate((37, 0, 0))
    body = hub.union(clamp)
    body = body.cut(cq.Workplane("XZ").circle(p.J3_J4_BEARING_OD / 2 + 0.02).extrude(80, both=True))
    body = body.cut(_rounded_box(48, p.ARM_LINK_TUBE_WIDTH + 0.6, p.ARM_LINK_TUBE_HEIGHT + 0.6, 3).translate((46, 0, 0)))
    h = p.NEMA17_MOUNT_PITCH / 2
    for x, z in ((-h, -h), (-h, h), (h, -h), (h, h)):
        body = body.cut(cq.Workplane("XZ").center(x, z).circle(p.NEMA17_MOUNT_HOLE / 2).extrude(70, both=True))
    return body


def arm_005() -> cq.Workplane:
    return _tube(p.ARM_FORE_LENGTH)


def arm_006() -> cq.Workplane:
    body = _rounded_box(82, 58, 58, 5)
    body = body.cut(_rounded_box(54, 34, 38, 5))
    body = body.cut(cq.Workplane("XZ").circle(p.J3_J4_BEARING_OD / 2 + 0.02).extrude(90, both=True))
    h = p.NEMA17_MOUNT_PITCH / 2
    for x, z in ((-h, -h), (-h, h), (h, -h), (h, h)):
        body = body.cut(cq.Workplane("XZ").center(x, z).circle(p.NEMA17_MOUNT_HOLE / 2).extrude(90, both=True))
    tool = cq.Workplane("XY").circle(18).extrude(70).translate((0, 0, -64))
    tool = tool.cut(cq.Workplane("XY").circle(8.2).extrude(90).translate((0, 0, -75)))
    return body.union(tool)


def arm_007() -> cq.Workplane:
    return cq.Workplane("XY").circle(p.J1_J2_SHAFT_DIAMETER / 2).extrude(112).edges("%Circle").chamfer(0.6)


def arm_008() -> cq.Workplane:
    return cq.Workplane("XY").circle(p.J3_J4_SHAFT_DIAMETER / 2).extrude(58).edges("%Circle").chamfer(0.5)


def grp_001() -> cq.Workplane:
    body = _rounded_box(p.GRIPPER_BODY_WIDTH, 58, 28, 4)
    mount = cq.Workplane("XY").circle(16).extrude(18).translate((0, 0, 23))
    slots = cq.Workplane("XY").center(-24, 0).rect(8, 38).extrude(40, both=True).union(
        cq.Workplane("XY").center(24, 0).rect(8, 38).extrude(40, both=True)
    )
    return body.union(mount).cut(slots)


def _finger(soft: bool = True) -> cq.Workplane:
    thick = 10 if soft else 13
    finger = cq.Workplane("XZ").moveTo(0, 0).lineTo(thick, 0).lineTo(thick + 8, -p.GRIPPER_FINGER_LENGTH).lineTo(2, -p.GRIPPER_FINGER_LENGTH + 7).close().extrude(22, both=True)
    return finger.edges().fillet(2.5 if soft else 1.5)


def grp_002() -> cq.Workplane:
    return _finger(True)


def grp_003() -> cq.Workplane:
    return _finger(False)


def grp_004() -> cq.Workplane:
    # Printable three-finger carrier only; compliant contacts are cast separately
    # from GRP-007 tooling. Each radial arm overlaps the hub, producing one solid.
    carrier = cq.Workplane("XY").circle(24).extrude(14)
    for angle in (0, 120, 240):
        arm = cq.Workplane("XY").box(44, 12, 14).translate((22, 0, 7)).rotate((0, 0, 0), (0, 0, 1), angle)
        pad = _rounded_box(18, 30, 14, 3).translate((46, 0, 7)).rotate((0, 0, 0), (0, 0, 1), angle)
        carrier = carrier.union(arm).union(pad)
        for local_y in (-8, 8):
            radians = math.radians(angle)
            x = 46 * math.cos(radians) - local_y * math.sin(radians)
            y = 46 * math.sin(radians) + local_y * math.cos(radians)
            carrier = carrier.cut(cq.Workplane("XY").center(x, y).circle(1.7).extrude(24, both=True))
    return carrier


def _mold(finger_builder) -> cq.Workplane:
    cavity = finger_builder()
    bb = cavity.val().BoundingBox()
    # The earlier cavity was fully enclosed, which produced an unusable/non-
    # watertight print export. Keep a 6 mm floor and let the cavity break through
    # the top face by 0.5 mm so the result is a real open one-piece mold.
    floor = 6.0
    block_zmin = bb.zmin - floor
    block_zmax = bb.zmax
    block_zlen = block_zmax - block_zmin
    block = cq.Workplane("XY").box(bb.xlen + 20, bb.ylen + 20, block_zlen).translate(
        ((bb.xmin + bb.xmax) / 2, (bb.ymin + bb.ymax) / 2, (block_zmin + block_zmax) / 2)
    )
    return block.cut(cavity.translate((0, 0, 2.0)))


def grp_005() -> cq.Workplane:
    return _mold(grp_002)


def grp_006() -> cq.Workplane:
    return _mold(grp_003)


def grp_007() -> cq.Workplane:
    # One segment mold for the GRP-C three-finger arrangement.
    return cq.Workplane(obj=_mold(grp_002).val().scale(0.85))


def fun_001() -> cq.Workplane:
    top = cq.Workplane("XY").rect(p.FUNNEL_WIDTH, p.FUNNEL_DEPTH).workplane(offset=-p.FUNNEL_HEIGHT).rect(p.FUNNEL_THROAT_WIDTH, p.FUNNEL_THROAT_WIDTH * 0.75).loft(combine=True)
    inner = cq.Workplane("XY").workplane(offset=-3).rect(p.FUNNEL_WIDTH-8, p.FUNNEL_DEPTH-8).workplane(offset=-(p.FUNNEL_HEIGHT-6)).rect(p.FUNNEL_THROAT_WIDTH-8, p.FUNNEL_THROAT_WIDTH*0.75-8).loft(combine=True)
    return top.cut(inner)


def fun_002() -> cq.Workplane:
    return cq.Workplane("XY").rect(p.FUNNEL_WIDTH-12, p.FUNNEL_DEPTH-12).workplane(offset=-(p.FUNNEL_HEIGHT-10)).rect(p.FUNNEL_THROAT_WIDTH-12, p.FUNNEL_THROAT_WIDTH*0.75-12).loft(combine=True).shell(-p.FUNNEL_LINER_THICKNESS)


def fun_003() -> cq.Workplane:
    outer = cq.Workplane("XY").rect(p.FUNNEL_THROAT_WIDTH + 18, 84).extrude(210)
    inner = cq.Workplane("XY").rect(p.FUNNEL_THROAT_WIDTH, 66).extrude(214).translate((0, 0, -2))
    return outer.cut(inner).rotate((0,0,0),(1,0,0),72)


def cha_001() -> cq.Workplane:
    plate = _rounded_box(p.TEST_STAND_WIDTH, p.TEST_STAND_DEPTH, 18, 12)
    for x in (-400, 400):
        for y in (-300, 300):
            plate = plate.cut(cq.Workplane("XY").center(x,y).circle(5.5).extrude(30, both=True))
    # J1 geared motor passes through the fixture; the fixture must be mounted
    # on four legs with at least 145 mm clear height.
    return plate.cut(cq.Workplane("XY").rect(72, 72).extrude(30, both=True))


def vis_001() -> cq.Workplane:
    # 30-series extrusion proxy plus a real Camera Module 3 hole pattern.
    mast = cq.Workplane("XY").rect(30, 30).rect(24, 24).extrude(760)
    boom = cq.Workplane("XY").box(360, 30, 30).translate((165, 0, 745))
    bracket = _rounded_box(70, 58, 4, 3).translate((330, 0, 716))
    camera_holes = []
    for x in (-p.CAMERA_MOUNT_PITCH_X / 2, p.CAMERA_MOUNT_PITCH_X / 2):
        for y in (-p.CAMERA_MOUNT_PITCH_Y / 2, p.CAMERA_MOUNT_PITCH_Y / 2):
            camera_holes.append(cq.Workplane("XY").center(330 + x, y).circle(p.CAMERA_MOUNT_HOLE_DIAMETER / 2).extrude(12).translate((0, 0, 710)))
    result = mast.union(boom).union(bracket)
    for hole in camera_holes:
        result = result.cut(hole)
    return result


def ele_001() -> cq.Workplane:
    tray = _rounded_box(520, 360, 3, 6)
    for x in (-240, 240):
        for y in (-160, 160):
            tray = tray.cut(cq.Workplane("XY").center(x,y).circle(2.7).extrude(10, both=True))
    return tray


BUILDERS = {
    "ARM-001": arm_001, "ARM-002": arm_002, "ARM-003": arm_003, "ARM-004": arm_004,
    "ARM-005": arm_005, "ARM-006": arm_006, "ARM-007": arm_007, "ARM-008": arm_008,
    "GRP-001": grp_001, "GRP-002": grp_002, "GRP-003": grp_003, "GRP-004": grp_004,
    "GRP-005": grp_005, "GRP-006": grp_006, "GRP-007": grp_007,
    "FUN-001": fun_001, "FUN-002": fun_002, "FUN-003": fun_003,
    "CHA-001": cha_001, "VIS-001": vis_001, "ELE-001": ele_001,
}
