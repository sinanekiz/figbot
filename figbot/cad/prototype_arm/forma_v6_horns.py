"""Original-hardware horn references and insert-fastened V6 interfaces.

No printed spline, old mounting capsule or servo-body clamp is used here.
The MG996R outline comes from InterSideraVersor, Thingiverse 4816510,
CC BY-NC-SA 4.0 (personal prototype reference; preserve attribution).
The MG90 Arm03 reference is user supplied; its source licence is UNVERIFIED.
Neither reference establishes fit of the present physical servo specimens.
"""
from functools import lru_cache
import hashlib
import math

import cadquery as cq
import trimesh
from shapely import affinity
from shapely.geometry import Polygon
from shapely.ops import unary_union

from cad.utils import ROOT

MATING_Z = 7.5
LARGE_PLATE = 1.9
MICRO_PLATE = 1.65
POCKET_CLEARANCE = .20
MICRO_MOUNT_X = 11.5  # Candidate: preserves >=1.4mm beside OD3.2 insert envelope.
COVER_THICKNESS = 2.0
AXIAL_CLEARANCE = .15  # Trial running clearance, not measured hardware fit.
SOURCES = {
    False: ROOT / 'references/servo_horn_trials/originals/USER_20260907/MG996R_Standard_Servo_Horn_6_Arm.stl',
    True: ROOT / 'references/servo_horn_trials/originals/MG90_USER_20260908/MG90_Arm03_canonical.stl',
}


def cylinder(radius, z, height, x=0., y=0.):
    return cq.Workplane('XY').center(x, y).circle(radius).extrude(height).translate((0, 0, z))


def prism(poly, z, height):
    """Only the exterior contour; explicit source holes are added separately."""
    return (cq.Workplane('XY').polyline(list(poly.exterior.coords)[:-1])
            .close().extrude(height).translate((0, 0, z)))


@lru_cache(None)
def source_mesh(micro=False):
    return trimesh.load_mesh(SOURCES[micro], process=False)


def section_loops(micro, z):
    cut = source_mesh(micro).section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if cut is None:
        raise ValueError(f'No horn section for {micro=} at {z=}')
    return [Polygon(path[:, :2]) for path in cut.discrete]


@lru_cache(None)
def profile(micro=False):
    zs = [.01, .5, 1., 1.6] if micro else [4.81, 5.5, 6.29, 6.5, 6.69]
    outside = unary_union([max(section_loops(micro, z), key=lambda p: p.area) for z in zs])
    outside = outside.simplify(.003, preserve_topology=True)
    # Proper 180deg rotation about X maps (x,y,z) to (x,-y,-z).
    # The supplied hub consequently faces the motor, not the printed output face.
    return affinity.scale(outside, xfact=1, yfact=-1, origin=(0, 0))


@lru_cache(None)
def source_holes(micro=False):
    """Peripheral hole centres and equivalent radii recovered from real sections.

    These are digital reference measurements, never physical measurements.
    Tiny MG90 holes remain approximately 1mm; M2 screws do not pass through them.
    """
    loops = section_loops(micro, 1. if micro else 5.5)
    result = []
    for p in loops:
        x, y = p.centroid.coords[0]
        if math.hypot(x, y) < 3 or p.area > 5:
            continue
        result.append((float(x), float(-y), math.sqrt(p.area / math.pi)))
    return tuple(sorted(result))


@lru_cache(None)
def points(micro=False):
    """External enclosure screws; NEVER pass through factory horn holes."""
    if micro:
        return ((-MICRO_MOUNT_X, 0.), (MICRO_MOUNT_X, 0.))
    return ((-19., 0.), (19., 0.))


def cover_top(micro=False):
    return MATING_Z - (MICRO_PLATE if micro else LARGE_PLATE) - AXIAL_CLEARANCE


def pocket_tool(micro=False):
    return prism(profile(micro).buffer(POCKET_CLEARANCE, quad_segs=8),
                 cover_top(micro)-.05, MATING_Z-cover_top(micro)+.05)


def closure_outline(micro=False):
    if not micro:
        from shapely.geometry import Point
        return Point(0, 0).buffer(22.8, quad_segs=32)
    from shapely.geometry import Point
    return unary_union([profile(True).buffer(2.8, quad_segs=8)] +
                       [Point(x,y).buffer(3.3, quad_segs=16) for x,y in points(True)])


@lru_cache(None)
def closure(micro=False):
    """Motor-facing half of the captive socket, secured from its outer face.

    Central aperture clears the original hub. The plate traps the star rim;
    no thread or extra fixing is made in the star itself.
    """
    z=cover_top(micro)-COVER_THICKNESS
    shape=prism(closure_outline(micro),z,COVER_THICKNESS)
    shape=shape.cut(cylinder(3.8 if micro else 6.3,z-.05,COVER_THICKNESS+.1))
    for x,y in points(micro):
        shape=shape.cut(cylinder(1.1,z-.05,COVER_THICKNESS+.1,x,y))
    return shape


@lru_cache(None)
def horn(micro=False):
    thickness = MICRO_PLATE if micro else LARGE_PLATE
    plate_bottom = MATING_Z - thickness
    shape = prism(profile(micro), plate_bottom, thickness)
    for x, y, radius in source_holes(micro):
        # Faceted nominal2/1mm holes have smaller area-equivalent diameters.
        # Round only their analytic circular radius to0.01mm; retain source
        # values in provenance. This establishes no physical screw clearance.
        shape = shape.cut(cylinder(round(radius, 2), plate_bottom-.02, thickness+.04, x, y))
    shape = shape.cut(cylinder(1.25 if micro else 1.5, plate_bottom-.02, thickness+.04))
    hub_bottom = 3.7 if micro else 2.5
    hub_radius = 3.45 if micro else 5.91
    hub = cylinder(hub_radius, hub_bottom, plate_bottom-hub_bottom)
    # An explicit conservative spline socket envelope, not manufactured teeth.
    # Existing nominal shaft solids are D5/D6; J1 physical OD is recorded D5.7.
    socket = cylinder(2.55 if micro else 3.05, hub_bottom-.02,
                      plate_bottom-hub_bottom+.04)
    return shape.union(hub.cut(socket))


@lru_cache(None)
def receiver(micro=False):
    z=cover_top(micro)
    shape=prism(closure_outline(micro),z,13.-z).cut(pocket_tool(micro))
    for x,y in points(micro):
        shape=shape.cut(cylinder(1.45,z-.05,4.4,x,y))
    return shape.cut(cylinder(3.5,z-.05,13.1-z))


@lru_cache(None)
def fastener_heads(micro=False):
    rows = []
    for k, (x, y) in enumerate(points(micro)):
        z = cover_top(micro)-COVER_THICKNESS-2.
        height = 2.
        rows.append((f'horn mounting head{k}', cylinder(1.8, z, height, x, y)))
    rows.append(('original centre screw head', cylinder(2.0 if micro else 2.7, 7.5, 1.6)))
    return tuple(rows)


@lru_cache(None)
def hardware(micro=False):
    rows = list(fastener_heads(micro))
    for k, (x, y) in enumerate(points(micro)):
        z = cover_top(micro)-COVER_THICKNESS
        length = 6.
        rows.append((f'horn mounting shank{k}', cylinder(1., z, length, x, y)))
        iz = cover_top(micro)
        insert = cylinder(1.6, iz, 4., x, y).cut(cylinder(1., iz-.05, 4.1, x, y))
        rows.append((f'horn insert{k}', insert))
    # Original centre thread/length must be physically checked. This simplified
    # view shows its load path into the metal shaft, not a replacement screw spec.
    rows.append(('original centre screw shank', cylinder(.9 if micro else 1.15, 3.5, 4.)))
    return tuple(rows)


def provenance():
    rows = {}
    for micro, label in [(False, 'MG996R'), (True, 'MG90S')]:
        mesh = source_mesh(micro)
        rows[label] = {
            'file': str(SOURCES[micro].relative_to(ROOT)).replace('\\', '/'),
            'sha256': hashlib.sha256(SOURCES[micro].read_bytes()).hexdigest(),
            'source_bounds_mm': mesh.bounds.tolist(),
            'source': 'https://www.thingiverse.com/thing:4816510' if not micro else 'User MG90s_Arm03.stl, canonical transform X-60/-Z/Y',
            'author': 'InterSideraVersor' if not micro else 'User supplied, original author UNVERIFIED',
            'license': 'CC BY-NC-SA 4.0' if not micro else 'UNVERIFIED',
            'license_url': 'https://creativecommons.org/licenses/by-nc-sa/4.0/' if not micro else None,
            'final_transform': '(x,-y,7.5-z)' if micro else '(x,-y,12.3-z)',
            'profile_arm_count': 4 if micro else 6,
            'mounting_axes_mm': points(micro),
            'source_peripheral_holes_x_y_equiv_radius_mm': source_holes(micro),
            'analytic_peripheral_holes_x_y_radius_mm': [(x, y, round(r, 2)) for x, y, r in source_holes(micro)],
            'interface': 'shape-keyed captive socket, external printed closure + two M2x6 screws into inserts; ALL original peripheral holes undrilled and unused',
            'axial_clearance_mm': AXIAL_CLEARANCE,
            'closure_thickness_mm': COVER_THICKNESS,
            'physical_fit': 'UNVERIFIED: source geometry is not physical metrology',
            'approximations': 'Hub/spline socket/centre screw simplified; peripheral hole equivalent radii rounded to0.01mm for nominal circular geometry, not a physical clearance guarantee; screw dimensions are candidates, original centre screw must be retained',
        }
    return rows
