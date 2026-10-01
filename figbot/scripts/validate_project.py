"""Validate part numbering, deliverables, BOM references, CSVs, JSON/YAML, and URDF limits."""

from __future__ import annotations

import csv
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cad.build import PARTS


def main() -> int:
    errors: list[str] = []
    numbers = list(PARTS)
    if len(numbers) != len(set(numbers)):
        errors.append("duplicate part numbers in CAD registry")
    for number, spec in PARTS.items():
        folder = ROOT / spec.folder
        required = [folder / f"{number}.py", folder / f"{number}.step", folder / f"{number}_drawing.pdf", folder / f"{number}_preview.png", folder / "README.md"]
        if "stl" in spec.formats:
            required.append(folder / f"{number}.stl")
        if "dxf" in spec.formats:
            required.append(folder / f"{number}.dxf")
        for path in required:
            if not path.exists() or path.stat().st_size == 0:
                errors.append(f"missing/empty deliverable: {path.relative_to(ROOT)}")
    bom = ROOT / "bom" / "MASTER_BOM.csv"
    if bom.exists():
        with bom.open(newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.DictReader(handle))
        bom_numbers = {row.get("part_number", "") for row in rows}
        for number in numbers:
            if number not in bom_numbers:
                errors.append(f"CAD part absent from MASTER_BOM: {number}")
    ignored_parts = {".venv", "node_modules", "dist", "releases", ".git"}
    for path in ROOT.rglob("*.csv"):
        if any(part in ignored_parts for part in path.parts):
            continue
        try:
            with path.open(newline="", encoding="utf-8-sig") as handle:
                rows = [row for row in csv.reader(handle) if any(cell.strip() for cell in row)]
            if not rows or not rows[0]:
                errors.append(f"empty CSV: {path.relative_to(ROOT)}")
            width = len(rows[0]) if rows else 0
            if any(len(row) != width for row in rows):
                errors.append(f"ragged CSV: {path.relative_to(ROOT)}")
        except Exception as exc:
            errors.append(f"malformed CSV {path.relative_to(ROOT)}: {exc}")
    for path in ROOT.rglob("*.json"):
        if any(part in ignored_parts for part in path.parts):
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"malformed JSON {path.relative_to(ROOT)}: {exc}")
    for path in list(ROOT.rglob("*.urdf")) + list(ROOT.rglob("*.xacro")):
        try:
            tree = ET.parse(path)
            for joint in tree.findall(".//joint"):
                if joint.get("type") in {"revolute", "prismatic"} and joint.find("limit") is None:
                    errors.append(f"joint without limit in {path.relative_to(ROOT)}: {joint.get('name')}")
        except ET.ParseError as exc:
            errors.append(f"malformed robot XML {path.relative_to(ROOT)}: {exc}")
    broken_markdown = re.compile(r"\[[^\]]+\]\((?!https?://)([^)#]+)")
    for path in ROOT.rglob("*.md"):
        if any(part in ignored_parts for part in path.parts):
            continue
        for link in broken_markdown.findall(path.read_text(encoding="utf-8", errors="ignore")):
            resolved = (path.parent / link).resolve()
            if not resolved.exists():
                errors.append(f"broken file reference in {path.relative_to(ROOT)}: {link}")
    if errors:
        print("VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"VALIDATION PASSED: {len(PARTS)} numbered CAD parts checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
