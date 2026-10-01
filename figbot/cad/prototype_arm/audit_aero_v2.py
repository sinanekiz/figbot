"""Reproducible print-file and assembly audit; never a physical release test."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import cadquery as cq
import numpy as np
import trimesh

from cad.prototype_arm import build_aero_v2 as arm


def relation(a: cq.Shape, b: cq.Shape) -> dict:
    overlap = a.intersect(b).Volume()
    gap = a.distance(b)
    return {"gap_mm": round(gap, 4), "overlap_mm3": round(overlap, 4),
            "classification": "INTERFERENCE" if overlap > 0.1 else
            ("SEPARATED" if gap > 0.1 else "CONTACT")}


def mesh_audit(path: Path, shape: cq.Shape) -> dict:
    mesh = trimesh.load_mesh(path, process=True)
    box = shape.BoundingBox()
    expected = np.array([[box.xmin, box.ymin, box.zmin], [box.xmax, box.ymax, box.zmax]])
    error = float(np.max(np.abs(mesh.bounds - expected)))
    count = len(mesh.split(only_watertight=False))
    ok = bool(mesh.is_watertight and mesh.is_winding_consistent and mesh.volume > 0
              and np.isfinite(mesh.vertices).all() and count == 1 and error < 0.3)
    return {"file": path.name, "mesh_ok": ok, "watertight": bool(mesh.is_watertight),
            "winding_consistent": bool(mesh.is_winding_consistent), "components": count,
            "cad_bounds_error_mm": round(error, 5),
            "size_mm": [round(x, 3) for x in mesh.extents],
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def build_report() -> dict:
    components = {item.name: item.shape.val() for item in arm.assembly_components()}
    checks = []
    pairs = [
        ("J1_SHAFT_GAP", "J1 MG996R-shaft", "J1 yaw deck"),
        ("J1_CASE_UNMOUNTED", "J1 MG996R-case", "J1 rounded base"),
        ("LEFT_JAW_PALM", "left curved jaw", "rounded gripper palm"),
        ("RIGHT_JAW_PALM", "right curved jaw", "rounded gripper palm"),
        ("J2_HORN_HUB", "J2 horn", "upper hub"),
        ("J3_HORN_HUB", "J3 horn", "forearm hub"),
    ]
    for key, a, b in pairs:
        checks.append({"id": key, "a": a, "b": b, **relation(components[a], components[b])})
    # Inspect the specified hollow 20x20x1.5 tube, not the solid presentation box.
    # Both root sockets start at X=8 mm while the assembly tube starts at X=0.
    for key, hub, length in [("UPPER_TUBE_ROOT", arm.upper_link_hub_aero, 300),
                              ("FOREARM_TUBE_ROOT", arm.forearm_link_hub_aero, 220)]:
        tube = cq.Workplane("YZ").rect(20, 20).rect(17, 17).extrude(length).val()
        checks.append({"id": key, "a": "specified hollow tube at current origin",
                       "b": hub.__name__, **relation(tube, hub().val())})
    meshes = [mesh_audit(arm.OUT / f"{key}.stl", builder().val())
              for key, (builder, _, _) in arm.PARTS.items()]
    return {
        "date": "2026-09-05", "revision": "AERO-V2 / DEC-039",
        "status": "HOLD FULL ARM AND GRIPPER PRINT; FIT COUPONS ONLY RECOMMENDED",
        "scope": "Static component interfaces and exported mesh integrity. Not a complete self-collision, motion, strength or physical-fit test.",
        "existing_tests": "Legacy geometry tests can pass despite these assembly defects; do not interpret them as assembly readiness.",
        "mesh_count": len(meshes), "all_meshes_ok": all(m["mesh_ok"] for m in meshes),
        "meshes": meshes, "assembly_findings": checks,
        "other_open_items": [
            "J2/J3 displayed horn planes are not perpendicular to their Y-axis shafts; touching solids do not validate a spline interface.",
            "J1 has no explicit supplied-horn component or complete servo mounting stack.",
            "Gripper links in assembly are presentation bars, not instances of printed PRT-H12; full linkage closure and spacer stack remain unresolved.",
            "Tube cut lengths and end insertions must be derived from pivot-centre distances; 300/220 mm must not be issued as confirmed saw-cut lengths.",
            "Final M3/M4 lengths, opposite-side elbow support and dual-shoulder servo coupling remain undefined.",
            "Printer: user-ordered ELEGOO Centauri Carbon 2 Combo; official bed 256x256x256 mm and included nozzle 0.4 mm. Filament unknown; no machine-specific slicing/G-code validation.",
        ],
        "photo_evidence": "User has MG996R-labelled servo and supplied black horns of several forms. No scale: spline count, hole pitch, hub height and screw thread unverified. Keep nominal servo body assumption.",
    }


def main():
    report = build_report()
    target = arm.OUT / "FINAL_PRINT_AUDIT.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "meshes"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
