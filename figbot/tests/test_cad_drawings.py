from __future__ import annotations

from pypdf import PdfReader

from cad.parts import BUILDERS
from cad.utils import _projected_paths, drawing_pdf


def test_hlr_projection_contains_real_bounded_geometry() -> None:
    shape = BUILDERS["ARM-001"]().val()
    paths = _projected_paths(shape, projection=(0, 0, 1), width=240, height=160)

    assert len(paths) >= 8
    assert any(not hidden for hidden, _ in paths)
    points = [point for _, path in paths for point in path]
    assert all(-0.01 <= x <= 240.01 and -0.01 <= y <= 160.01 for x, y in points)


def test_drawing_pdf_has_four_cad_views(tmp_path) -> None:
    output = tmp_path / "ARM-001_drawing.pdf"
    drawing_pdf(
        BUILDERS["ARM-001"](),
        output,
        part_number="ARM-001",
        name="V0 arm base/J1 motor plate",
        material="EN AW-6082-T6 aluminium plate",
        method="CNC mill from plate",
        critical=["12 mm plate; pilot and mounting pattern require manufacturing review."],
    )

    text = PdfReader(output).pages[0].extract_text()
    assert "FRONT VIEW (X-Z)" in text
    assert "TOP VIEW (X-Y)" in text
    assert "RIGHT VIEW (Y-Z)" in text
    assert "ISOMETRIC VIEW" in text
    assert "SIMPLIFIED FRONT PROJECTION" not in text
