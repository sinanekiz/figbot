"""Conservative geometric collision proxies for early V0 motion screening.

These primitives do not replace CAD interference analysis or physical safety
validation. They intentionally provide a fast, deterministic first filter.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

from software.kinematics.model import ArmKinematics, JointState


Point3 = tuple[float, float, float]


@dataclass(frozen=True)
class BoxProxy:
    name: str
    minimum: Point3
    maximum: Point3


@dataclass(frozen=True)
class CylinderProxy:
    name: str
    center_xy: tuple[float, float]
    radius: float
    z_min: float
    z_max: float


@dataclass(frozen=True)
class CollisionReport:
    collision: bool
    contacts: tuple[str, ...]


def _load_default_proxies() -> tuple[tuple[BoxProxy, ...], tuple[CylinderProxy, ...]]:
    try:
        from cad.config import parameters

        camera_center = tuple(float(value) / 1000.0 for value in parameters.CAMERA_CENTER_XYZ)
        funnel_center = tuple(float(value) / 1000.0 for value in parameters.FUNNEL_CENTER_XYZ)
        funnel_radius = min(float(parameters.FUNNEL_WIDTH), float(parameters.FUNNEL_DEPTH)) / 2000.0
        funnel_height = float(parameters.FUNNEL_HEIGHT) / 1000.0
    except (ImportError, AttributeError, TypeError, ValueError):
        camera_center = (0.18, 0.0, 0.82)
        funnel_center = (-0.12, 0.25, 0.21)
        funnel_radius = 0.095
        funnel_height = 0.15
    cx, cy, cz = camera_center
    boxes = (
        # Camera dimensions are ESTIMATE / UNVERIFIED; center comes from CAD.
        BoxProxy("camera", (cx - 0.07, cy - 0.045, cz - 0.035), (cx + 0.07, cy + 0.045, cz + 0.035)),
        # Base plate proxy covers chassis contact near ground.
        BoxProxy("chassis", (-0.12, -0.11, 0.0), (0.12, 0.11, 0.012)),
    )
    fx, fy, fz = funnel_center
    cylinders = (
        # Pedestal proxy below the shoulder pivot; hub geometry remains a CAD
        # interference-review item.
        CylinderProxy("base", (0.0, 0.0), 0.060, 0.012, 0.115),
        CylinderProxy("funnel", (fx, fy), funnel_radius, fz - funnel_height / 2, fz + funnel_height / 2),
    )
    return boxes, cylinders


DEFAULT_BOXES, DEFAULT_CYLINDERS = _load_default_proxies()


def _distance(a: Point3, b: Point3) -> float:
    return sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def _point_segment_distance(point: Point3, a: Point3, b: Point3) -> float:
    ab = tuple(y - x for x, y in zip(a, b))
    ap = tuple(y - x for x, y in zip(a, point))
    denominator = sum(value * value for value in ab)
    if denominator <= 1e-15:
        return _distance(point, a)
    fraction = max(0.0, min(1.0, sum(x * y for x, y in zip(ap, ab)) / denominator))
    nearest = tuple(x + fraction * delta for x, delta in zip(a, ab))
    return _distance(point, nearest)


def _sample_segment(a: Point3, b: Point3, steps: int = 12) -> tuple[Point3, ...]:
    return tuple(tuple(x + (y - x) * index / steps for x, y in zip(a, b)) for index in range(steps + 1))


def _inside_box(point: Point3, box: BoxProxy, margin: float) -> bool:
    return all(low - margin <= value <= high + margin for value, low, high in zip(point, box.minimum, box.maximum))


def _inside_cylinder(point: Point3, cylinder: CylinderProxy, margin: float) -> bool:
    dx = point[0] - cylinder.center_xy[0]
    dy = point[1] - cylinder.center_xy[1]
    return (
        dx * dx + dy * dy <= (cylinder.radius + margin) ** 2
        and cylinder.z_min - margin <= point[2] <= cylinder.z_max + margin
    )


class CollisionChecker:
    def __init__(
        self,
        arm: ArmKinematics,
        boxes: tuple[BoxProxy, ...] = DEFAULT_BOXES,
        cylinders: tuple[CylinderProxy, ...] = DEFAULT_CYLINDERS,
        link_radius: float = 0.025,
        ground_clearance: float = 0.005,
    ) -> None:
        self.arm = arm
        self.boxes = boxes
        self.cylinders = cylinders
        self.link_radius = link_radius
        self.ground_clearance = ground_clearance

    def check(self, joints: JointState, ignore: frozenset[str] = frozenset()) -> CollisionReport:
        contacts: set[str] = set()
        if not self.arm.within_limits(joints):
            contacts.add("joint_limit")
        points = self.arm.link_points(joints)
        segments = tuple(zip(points[1:-1], points[2:]))  # shoulder->elbow->wrist->tool

        for segment_index, (start, end) in enumerate(segments):
            for sample_index, point in enumerate(_sample_segment(start, end)):
                if point[2] < self.ground_clearance:
                    contacts.add("ground")
                for box in self.boxes:
                    if box.name not in ignore and _inside_box(point, box, self.link_radius):
                        contacts.add(box.name)
                for cylinder in self.cylinders:
                    if cylinder.name in ignore:
                        continue
                    # The shoulder pivot and first centimetres are intentionally
                    # allowed inside the base's conservative hub envelope.
                    if cylinder.name == "base" and segment_index == 0 and sample_index <= 2:
                        continue
                    if _inside_cylinder(point, cylinder, self.link_radius):
                        contacts.add(cylinder.name)

        # Non-adjacent upper-arm/tool proximity is the relevant self-collision
        # mode for this serial planar chain. Adjacent joints share endpoints.
        upper_start, upper_end = segments[0]
        tool_start, tool_end = segments[2]
        proximity = min(
            _point_segment_distance(upper_start, tool_start, tool_end),
            _point_segment_distance(upper_end, tool_start, tool_end),
            _point_segment_distance(tool_start, upper_start, upper_end),
            _point_segment_distance(tool_end, upper_start, upper_end),
        )
        if proximity < 2.0 * self.link_radius:
            contacts.add("self")
        return CollisionReport(bool(contacts), tuple(sorted(contacts)))

    def collides(self, joints: JointState, ignore: frozenset[str] = frozenset()) -> bool:
        return self.check(joints, ignore=ignore).collision
