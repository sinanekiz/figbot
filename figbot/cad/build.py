"""Build numbered FIGBOT parts from the master builder table."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from cad.parts import BUILDERS
from cad.utils import ROOT, drawing_pdf, export_shape, render_preview, write_metadata


@dataclass(frozen=True)
class PartSpec:
    folder: str
    name: str
    purpose: str
    material: str
    method: str
    quantity: int
    formats: tuple[str, ...]
    related: str
    critical: str
    orientation: str


PARTS: dict[str, PartSpec] = {
    "ARM-001": PartSpec("cad/arm/ARM-001", "V0 arm base/J1 motor plate", "Anchors J1 and locates the NEMA23 gearbox", "EN AW-6082-T6 aluminium plate", "CNC mill from plate", 1, ("step",), "ARM-002, CHA-001, J1 motor", "12 mm plate; 38.1 mm pilot; 47.14 mm NEMA23 pitch", "flat on CHA-001"),
    "ARM-002": PartSpec("cad/arm/ARM-002", "Rotating shoulder pedestal", "Carries the J2 shaft on two bearings and locates the J2 gearbox", "EN AW-6082-T6 aluminium", "CNC machined/fabricated; supplier DFM required", 1, ("step",), "ARM-001, ARM-003, ARM-007, J2 motor", "J2 coaxial bearing seats and NEMA23 flange", "J1 axis vertical; J2 axis horizontal"),
    "ARM-003": PartSpec("cad/arm/ARM-003", "Upper link tube", "Primary shoulder-to-elbow beam", "EN AW-6060-T66 or 6082-T6 rectangular tube", "saw cut + jig drill", 1, ("step",), "ARM-002, ARM-004", "40 x 30 x 2 x 300 mm nominal; end holes jig-drilled", "long axis from shoulder to elbow"),
    "ARM-004": PartSpec("cad/arm/ARM-004", "J3 elbow clevis", "Carries J3 shaft on two 608 bearings and locates NEMA17 gearbox", "EN AW-6082-T6 aluminium", "CNC mill", 1, ("step",), "ARM-003, ARM-005, ARM-008, J3 motor", "22 mm bearing seats and 31 mm NEMA17 pitch", "shaft horizontal"),
    "ARM-005": PartSpec("cad/arm/ARM-005", "Forearm link tube", "Primary elbow-to-wrist beam", "EN AW-6060-T66 or 6082-T6 rectangular tube", "saw cut + jig drill", 1, ("step",), "ARM-004, ARM-006", "40 x 30 x 2 x 220 mm nominal; end holes jig-drilled", "long axis from elbow to wrist"),
    "ARM-006": PartSpec("cad/arm/ARM-006", "J4 wrist clevis", "Carries J4 shaft and gripper interface", "EN AW-6082-T6 aluminium", "CNC mill", 1, ("step",), "ARM-005, GRP-001, ARM-008, J4 motor", "22 mm bearing seats; 31 mm NEMA17 pitch; tool bore", "tool axis downward in home pose"),
    "ARM-007": PartSpec("cad/arm/ARM-007", "Proximal joint shaft", "J1/J2 serviceable metal shaft", "42CrMo4+QT or C45 steel after machinist review", "turning + key/retention features", 2, ("step",), "ARM-001, ARM-002, 6002 bearings", "15 mm x 112 mm envelope; g6 bearing journals proposed", "chamfered end outward"),
    "ARM-008": PartSpec("cad/arm/ARM-008", "Distal joint shaft", "J3/J4 serviceable metal shaft", "42CrMo4+QT or C45 steel after machinist review", "turning + retention flats", 2, ("step",), "ARM-004, ARM-006, 608 bearings", "8 mm x 58 mm envelope; g6 bearing journals proposed", "chamfered end outward"),
    "GRP-001": PartSpec("cad/gripper/GRP-001", "Gripper body", "Carries compliant finger mechanisms", "PETG, prototype", "FDM + inserts", 1, ("step", "stl"), "ARM-006, GRP-002/003/004", "90 mm maximum nominal opening", "mount face upward"),
    "GRP-002": PartSpec("cad/gripper/GRP-002", "GRP-A very-soft finger", "Low-pressure two-finger contact pad", "Food-contact silicone candidate, nominal Shore 10A", "cast in GRP-005 mold", 2, ("step", "stl"), "GRP-001, GRP-005", "hardness and force UNVERIFIED", "concave side toward fruit"),
    "GRP-003": PartSpec("cad/gripper/GRP-003", "GRP-B medium finger", "More stable two-finger contact pad", "Food-contact silicone candidate, nominal Shore 20A", "cast in GRP-006 mold", 2, ("step", "stl"), "GRP-001, GRP-006", "hardness and force UNVERIFIED", "concave side toward fruit"),
    "GRP-004": PartSpec("cad/gripper/GRP-004", "GRP-C three-finger carrier", "Alternative centering geometry", "PETG carrier + cast silicone contacts", "FDM and casting", 1, ("step", "stl"), "GRP-001, GRP-007", "clearance and contact force UNVERIFIED", "three fingers equally spaced"),
    "GRP-005": PartSpec("cad/gripper/GRP-005", "GRP-A silicone mold", "Casts replaceable GRP-A finger", "PETG or rigid resin tooling", "FDM/resin print", 1, ("step", "stl"), "GRP-002", "allowance TBD after silicone datasheet", "cavity upward"),
    "GRP-006": PartSpec("cad/gripper/GRP-006", "GRP-B silicone mold", "Casts replaceable GRP-B finger", "PETG or rigid resin tooling", "FDM/resin print", 1, ("step", "stl"), "GRP-003", "allowance TBD after silicone datasheet", "cavity upward"),
    "GRP-007": PartSpec("cad/gripper/GRP-007", "GRP-C silicone mold", "Casts replaceable GRP-C finger segment", "PETG or rigid resin tooling", "FDM/resin print", 1, ("step", "stl"), "GRP-004", "allowance TBD after silicone datasheet", "cavity upward"),
    "FUN-001": PartSpec("cad/funnel/FUN-001", "Short wide funnel shell", "Receives released figs near the arm", "PETG prototype or thin formed polymer", "FDM prototype", 1, ("step", "stl"), "FUN-002, FUN-003, CHA-001", "230 mm entry, 92 mm throat nominal", "wide opening upward"),
    "FUN-002": PartSpec("cad/funnel/FUN-002", "Soft funnel liner", "Reduces impact and abrasion", "Food-contact silicone/foam candidate", "cast/cut and bond", 1, ("step", "stl"), "FUN-001", "4 mm nominal; food-contact review", "continuous inner surface"),
    "FUN-003": PartSpec("cad/funnel/FUN-003", "Short soft channel", "Transfers figs toward crate", "Flexible food-contact polymer candidate", "FDM pattern / formed liner", 1, ("step", "stl"), "FUN-001, crate", "slope/drop PHYSICAL VALIDATION REQUIRED", "slope downward to crate"),
    "CHA-001": PartSpec("cad/test_stand/CHA-001", "V0 test stand base", "Rigid bench target and mounting surface", "18 mm birch plywood prototype", "CNC router", 1, ("step", "dxf"), "ARM-001, VIS-001, FUN-001, ELE-001", "900 x 700 envelope; anchor pattern TBD", "flat and anchored to bench"),
    "VIS-001": PartSpec("cad/test_stand/VIS-001", "Camera mast and Camera Module 3 bracket", "Locates the downward RGB camera above the controlled plane", "30 mm T-slot aluminium extrusion + EN AW-5754 plate", "standard extrusion cut + CNC/laser bracket", 1, ("step",), "CHA-001, PUR camera", "25 x 24 mm camera board envelope; 21 x 12.5 mm hole pitch", "mast vertical; camera optical axis downward"),
    "ELE-001": PartSpec("cad/test_stand/ELE-001", "Electronics enclosure backplate", "Mounts PSU, four drivers, safety relay, distribution and compute", "3 mm EN AW-5754 aluminium sheet", "laser/waterjet + drill/tap after component layout", 1, ("step", "dxf"), "CHA-001, electrical modules", "520 x 360 mm; module holes controlled by ELECTRONICS_LAYOUT.csv", "inside earthed enclosure away from debris"),
}


def build_part(part_number: str) -> Path:
    if part_number not in PARTS:
        raise KeyError(f"Unknown part {part_number}")
    spec = PARTS[part_number]
    out_dir = ROOT / spec.folder
    shape = BUILDERS[part_number]()
    export_shape(shape, out_dir, part_number, spec.formats)
    render_preview(shape, out_dir / f"{part_number}_preview.png", f"{part_number} | {spec.name}")
    drawing_pdf(
        shape, out_dir / f"{part_number}_drawing.pdf", part_number=part_number, name=spec.name,
        material=spec.material, method=spec.method,
        critical=[spec.critical, "All dimensions and mating fits require manufacturing review."],
    )
    write_metadata(
        out_dir / "README.md", part_number=part_number, name=spec.name, purpose=spec.purpose,
        material=spec.material, method=spec.method, qty=spec.quantity, related=spec.related,
        critical=spec.critical, orientation=spec.orientation,
    )
    return out_dir


def build_all_parts() -> list[Path]:
    return [build_part(part_number) for part_number in PARTS]
