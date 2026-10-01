"""Build a Gmail-size supplier transmittal from the controlled mechanical RFQ."""

from __future__ import annotations

import csv
import hashlib
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_email_pack(revision: str = "20260831-RC1") -> tuple[Path, Path]:
    source = ROOT / "releases" / f"FIGBOT-MECHANICAL-RFQ-{revision}"
    if not source.is_dir():
        raise FileNotFoundError(f"Build the controlled RFQ package first: {source}")

    name = f"FIGBOT-V1-DEMO-RFQ-{revision}-EMAIL"
    staging = (ROOT / "releases" / name).resolve()
    releases = (ROOT / "releases").resolve()
    if releases not in staging.parents:
        raise ValueError(f"Unsafe email-package path: {staging}")
    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(source, staging)

    large_reference = staging / "02_ASSEMBLIES" / "FIGBOT_P0_ROVER_PACKAGING_REFERENCE.step"
    large_reference.unlink(missing_ok=True)
    v1_target = staging / "02_ASSEMBLIES" / "FIGBOT_V1_DEMO_PACKAGING_REFERENCE.step"
    shutil.copy2(ROOT / "cad" / "assembly" / "FIGBOT_V1_ASSEMBLY.step", v1_target)

    (staging / "EMAIL_PACKAGE_NOTE.txt").write_text(
        "This email-size package omits the 129 MB detailed P0 rover STEP and replaces it "
        "with the lightweight preliminary V1 demo packaging reference. The omitted model "
        "can be transferred separately if required. All files remain RFQ/DFM input only.\n",
        encoding="utf-8",
    )

    manifest = staging / "FILE_MANIFEST.csv"
    fields = ["file", "size_bytes", "sha256", "release_status", "supplier_note"]
    rows = []
    for path in sorted(staging.rglob("*")):
        if not path.is_file() or path == manifest:
            continue
        rel = path.relative_to(staging).as_posix()
        rows.append(
            {
                "file": rel,
                "size_bytes": path.stat().st_size,
                "sha256": _sha256(path),
                "release_status": "PACKAGING_REFERENCE_ONLY" if path == v1_target else "RFQ_INPUT",
                "supplier_note": "Preliminary V1 demo envelope; supplier DFM required." if path == v1_target else "See 00_READ_ME_FIRST.md.",
            }
        )
    with manifest.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    zip_path = ROOT / "releases" / f"{name}.zip"
    zip_path.unlink(missing_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(staging.rglob("*")):
            if path.is_file():
                archive.write(path, Path(name) / path.relative_to(staging))
    return staging, zip_path


if __name__ == "__main__":
    folder, archive = build_email_pack()
    print(folder)
    print(archive)
