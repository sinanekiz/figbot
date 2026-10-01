from __future__ import annotations

import csv
import zipfile
from pathlib import Path

from pypdf import PdfReader

from scripts.build_email_rfq_pack import build_email_pack
from scripts.build_mechanical_rfq_pack import build_pack


def test_mechanical_rfq_pack_is_staged_and_application_neutral() -> None:
    pack_root, zip_path = build_pack("TEST-RC")
    try:
        readme = (pack_root / "00_READ_ME_FIRST.md").read_text(encoding="utf-8").lower()
        assert "not a production release" in readme
        assert "design freeze" in readme
        assert "first article" in readme
        assert "incir" not in readme
        assert " fig " not in f" {readme} "

        with (pack_root / "FILE_MANIFEST.csv").open(newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.DictReader(handle))
        assert rows
        assert all(len(row["sha256"]) == 64 for row in rows)
        status_by_file = {row["file"]: row["release_status"] for row in rows}
        assert status_by_file["02_ASSEMBLIES/FIGBOT_P0_ROVER_PACKAGING_REFERENCE.step"] == "PACKAGING_REFERENCE_ONLY"
        assert status_by_file["02_ASSEMBLIES/FIGBOT_CUSTOM_ARM_ASSEMBLY.step"] == "ENGINEERING_CANDIDATE"
        drawing_pages = PdfReader(pack_root / "MECHANICAL_DRAWINGS.pdf").pages
        assert len(drawing_pages) == 15
        assert all("ISOMETRIC VIEW" in page.extract_text() for page in drawing_pages)

        with (pack_root / "05_BOM/MECHANICAL_RFQ_BOM.csv").open(newline="", encoding="utf-8-sig") as handle:
            bom_text = handle.read().lower()
        assert "incir" not in bom_text
        assert "fig damage" not in bom_text

        with zipfile.ZipFile(zip_path) as archive:
            names = archive.namelist()
        assert any(name.endswith("FIGBOT_CUSTOM_ARM_ASSEMBLY.step") for name in names)
        assert not any("/ai/" in name or "/software/" in name for name in names)

        email_root, email_zip = build_email_pack("TEST-RC")
        try:
            assert email_zip.stat().st_size < 25 * 1024 * 1024
            with zipfile.ZipFile(email_zip) as email_archive:
                email_names = email_archive.namelist()
            assert any(name.endswith("FIGBOT_V1_DEMO_PACKAGING_REFERENCE.step") for name in email_names)
            assert not any(name.endswith("FIGBOT_P0_ROVER_PACKAGING_REFERENCE.step") for name in email_names)
        finally:
            if email_root.exists():
                import shutil

                shutil.rmtree(email_root)
            if email_zip.exists():
                email_zip.unlink()
    finally:
        if pack_root.exists():
            import shutil

            shutil.rmtree(pack_root)
        if zip_path.exists():
            zip_path.unlink()
