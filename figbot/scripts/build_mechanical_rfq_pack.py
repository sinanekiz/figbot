"""Build a mechanical-only supplier RFQ package from controlled FIGBOT outputs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import shutil
import zipfile
from pathlib import Path

from pypdf import PdfWriter


ROOT = Path(__file__).resolve().parents[1]


ARM_PARTS = [f"ARM-{index:03d}" for index in range(1, 9)]
GRIPPER_PARTS = [f"GRP-{index:03d}" for index in range(1, 8)]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _copy(source: Path, destination: Path) -> Path:
    if not source.is_file() or source.stat().st_size == 0:
        raise FileNotFoundError(f"RFQ source missing or empty: {source.relative_to(ROOT)}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return destination


def _neutral_text(value: str) -> str:
    text = re.sub(r"\bfigs?\b", "handled object", value, flags=re.IGNORECASE)
    text = re.sub(r"\bfruit\b", "handled object", text, flags=re.IGNORECASE)
    text = re.sub(r"food-contact", "cleanable soft-contact", text, flags=re.IGNORECASE)
    return text


def _write_mechanical_bom(destination: Path) -> Path:
    fields = [
        "source_id",
        "subsystem",
        "description",
        "quantity",
        "make_or_buy",
        "material_or_candidate",
        "process_or_purpose",
        "release_state",
    ]
    rows: list[dict[str, str]] = []

    with (ROOT / "bom" / "MASTER_BOM.csv").open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            part_number = row["part_number"]
            if part_number not in set(ARM_PARTS + GRIPPER_PARTS) and part_number not in {
                "PUR-001", "PUR-002", "PUR-003", "PUR-011", "PUR-014"
            }:
                continue
            rows.append(
                {
                    "source_id": part_number,
                    "subsystem": row["subsystem"],
                    "description": _neutral_text(row["description"]),
                    "quantity": row["quantity"],
                    "make_or_buy": row["make_or_buy"],
                    "material_or_candidate": row["material"] or row["supplier_model"],
                    "process_or_purpose": row["manufacturing_method"],
                    "release_state": row["verification_status"],
                }
            )

    with (ROOT / "bom" / "FLAT_GROUND_ROVER_P0.csv").open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            part_id = row["part_id"]
            if part_id == "TOTAL" or not part_id.startswith(("P0-DRV", "P0-MEC", "P0-PWR", "P0-FST")):
                continue
            rows.append(
                {
                    "source_id": part_id,
                    "subsystem": row["system"],
                    "description": _neutral_text(row["part_name"]),
                    "quantity": row["quantity"],
                    "make_or_buy": "BUY_OR_SUPPLIER_MAKE",
                    "material_or_candidate": row["selected_candidate"],
                    "process_or_purpose": _neutral_text(row["purpose"]),
                    "release_state": row["release_status"],
                }
            )

    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return destination


def build_pack(revision: str) -> tuple[Path, Path]:
    pack_name = f"FIGBOT-MECHANICAL-RFQ-{revision}"
    pack_root = ROOT / "releases" / pack_name
    if pack_root.exists():
        shutil.rmtree(pack_root)
    pack_root.mkdir(parents=True)

    copied: list[tuple[Path, str, str]] = []

    def include(source_rel: str, destination_rel: str, status: str, note: str) -> None:
        destination = _copy(ROOT / source_rel, pack_root / destination_rel)
        copied.append((destination, status, note))

    include(
        "manufacturing/MECHANICAL_RFQ_BRIEF.md",
        "00_READ_ME_FIRST.md",
        "RFQ_CONTROL_DOCUMENT",
        "Defines staged design-freeze, first-article and production quotation scope.",
    )
    include(
        "manufacturing/P0_INTERFACE_FREEZE_REGISTER.csv",
        "01_REQUIREMENTS/P0_INTERFACE_FREEZE_REGISTER.csv",
        "OPEN_INTERFACE_REGISTER",
        "Every row must be closed before production release.",
    )
    include(
        "manufacturing/PRODUCTION_VALIDATION_MATRIX.csv",
        "01_REQUIREMENTS/PRODUCTION_VALIDATION_MATRIX.csv",
        "PHYSICAL_VALIDATION_PLAN",
        "Acceptance limits requiring supplier input remain design-freeze items.",
    )
    include(
        "manufacturing/SUPPLIER_QUOTE_RESPONSE_TEMPLATE.csv",
        "01_REQUIREMENTS/SUPPLIER_QUOTE_RESPONSE_TEMPLATE.csv",
        "SUPPLIER_RESPONSE_TEMPLATE",
        "Supplier may return its own format if every requested item is answered.",
    )
    include(
        "manufacturing/INTERFACE_CONTROL.csv",
        "01_REQUIREMENTS/CUSTOM_ARM_INTERFACE_CONTROL.csv",
        "ARM_INTERFACE_CONTROL",
        "Controlled arm fits; first-article inspection remains required.",
    )

    include(
        "cad/assembly/FIGBOT_CUSTOM_ARM_ASSEMBLY.step",
        "02_ASSEMBLIES/FIGBOT_CUSTOM_ARM_ASSEMBLY.step",
        "ENGINEERING_CANDIDATE",
        "Custom 605 mm arm assembly with motor/actuator envelopes; supplier DFM required.",
    )
    include(
        "cad/assembly/FIGBOT_P0_ROVER.step",
        "02_ASSEMBLIES/FIGBOT_P0_ROVER_PACKAGING_REFERENCE.step",
        "PACKAGING_REFERENCE_ONLY",
        "Do not manufacture directly; purchased-arm geometry is a space-claim reference.",
    )

    for part_number in ARM_PARTS:
        folder = f"cad/arm/{part_number}"
        include(
            f"{folder}/{part_number}.step",
            f"03_CUSTOM_PARTS/ARM/{part_number}/{part_number}.step",
            "RFQ_FIRST_ARTICLE",
            "Supplier DFM and drawing review required.",
        )
        include(
            f"{folder}/{part_number}_drawing.pdf",
            f"03_CUSTOM_PARTS/ARM/{part_number}/{part_number}_drawing.pdf",
            "RFQ_DRAWING",
            "Simplified reference drawing; supplier must complete production dimensions and tolerances.",
        )

    for part_number in GRIPPER_PARTS:
        folder = f"cad/gripper/{part_number}"
        include(
            f"{folder}/{part_number}.step",
            f"03_CUSTOM_PARTS/GRIPPER/{part_number}/{part_number}.step",
            "RFQ_PROTOTYPE_VARIANT",
            "Variant selection requires physical testing.",
        )
        include(
            f"{folder}/{part_number}_drawing.pdf",
            f"03_CUSTOM_PARTS/GRIPPER/{part_number}/{part_number}_drawing.pdf",
            "RFQ_DRAWING",
            "Simplified prototype reference drawing; production detailing and material/process review required.",
        )
        stl = ROOT / folder / f"{part_number}.stl"
        if stl.is_file():
            include(
                str(stl.relative_to(ROOT)).replace("\\", "/"),
                f"03_CUSTOM_PARTS/GRIPPER/{part_number}/{part_number}.stl",
                "RFQ_ADDITIVE_FILE",
                "Print orientation and process remain supplier-review items.",
            )

    drawing_bundle = pack_root / "MECHANICAL_DRAWINGS.pdf"
    writer = PdfWriter()
    for drawing in sorted((pack_root / "03_CUSTOM_PARTS").rglob("*_drawing.pdf")):
        writer.append(str(drawing))
    with drawing_bundle.open("wb") as handle:
        writer.write(handle)
    writer.close()
    copied.append(
        (
            drawing_bundle,
            "RFQ_DRAWING_COMPILATION",
            "15 CAD-derived reference sheets; production dimensions and tolerances remain supplier-review items.",
        )
    )

    for source_rel, destination_rel, note in (
        ("renders/FIGBOT_P0_ROVER_isometric.png", "04_REVIEW_IMAGES/ROVER_ISOMETRIC.png", "Rover packaging overview."),
        ("renders/FIGBOT_P0_ROVER_top.png", "04_REVIEW_IMAGES/ROVER_TOP.png", "Rover top packaging view."),
        ("renders/FIGBOT_P0_ROVER_front.png", "04_REVIEW_IMAGES/ROVER_FRONT.png", "Rover front packaging view."),
        ("renders/FIGBOT_P0_ROVER_side.png", "04_REVIEW_IMAGES/ROVER_SIDE.png", "Rover side packaging view."),
        ("renders/FIGBOT_P0_ROVER_layout_annotated.png", "04_REVIEW_IMAGES/ROVER_LAYOUT_ANNOTATED.png", "Calculated packaging dimensions and clearance summary."),
        ("renders/FIGBOT_arm_detail.png", "04_REVIEW_IMAGES/CUSTOM_ARM_DETAIL.png", "Custom arm mechanical detail."),
        ("renders/FIGBOT_gripper_detail.png", "04_REVIEW_IMAGES/GRIPPER_DETAIL.png", "Gripper prototype detail."),
    ):
        include(source_rel, destination_rel, "REVIEW_IMAGE", note)

    bom_path = _write_mechanical_bom(pack_root / "05_BOM/MECHANICAL_RFQ_BOM.csv")
    copied.append(
        (
            bom_path,
            "RFQ_BOM",
            "Mechanical/electromechanical quote list; exact candidates close through the interface register.",
        )
    )

    manifest_path = pack_root / "FILE_MANIFEST.csv"
    fields = ["file", "size_bytes", "sha256", "release_status", "supplier_note"]
    with manifest_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for path, status, note in sorted(copied, key=lambda item: item[0].relative_to(pack_root).as_posix()):
            writer.writerow(
                {
                    "file": path.relative_to(pack_root).as_posix(),
                    "size_bytes": path.stat().st_size,
                    "sha256": _sha256(path),
                    "release_status": status,
                    "supplier_note": note,
                }
            )

    zip_path = ROOT / "releases" / f"{pack_name}.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(pack_root.rglob("*")):
            if path.is_file():
                archive.write(path, Path(pack_name) / path.relative_to(pack_root))
    return pack_root, zip_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--revision", default="20260831-RC1")
    args = parser.parse_args()
    pack_root, zip_path = build_pack(args.revision)
    print(pack_root)
    print(zip_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
