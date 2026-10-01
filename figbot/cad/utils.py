"""CAD export, preview, drawing, and metadata helpers."""

from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path
from typing import Iterable

import cadquery as cq


ROOT = Path(__file__).resolve().parents[1]


def export_shape(shape: cq.Workplane | cq.Shape, out_dir: Path, part_number: str, formats: Iterable[str]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    value = shape.val() if isinstance(shape, cq.Workplane) else shape
    for fmt in formats:
        destination = out_dir / f"{part_number}.{fmt}"
        if fmt == "step":
            cq.exporters.export(value, str(destination), exportType="STEP")
        elif fmt == "stl":
            cq.exporters.export(value, str(destination), exportType="STL", tolerance=0.08, angularTolerance=0.1)
            # STL stores disconnected triangles and some consumers do not merge
            # coincident vertices automatically. Normalize the exported mesh and
            # reject any file that still is not a closed printable volume.
            import trimesh

            mesh = trimesh.load_mesh(destination, process=True, validate=True)
            mesh.remove_unreferenced_vertices()
            mesh.merge_vertices(digits_vertex=5)
            if not mesh.is_watertight or not mesh.is_winding_consistent:
                raise ValueError(f"Non-printable STL export for {part_number}: {destination}")
            mesh.export(destination)
        elif fmt == "dxf":
            cq.exporters.export(shape.section() if isinstance(shape, cq.Workplane) else cq.Workplane(obj=value).section(), str(destination), exportType="DXF")
        else:
            raise ValueError(f"Unsupported CAD format: {fmt}")


def shape_mesh(shape: cq.Workplane | cq.Shape):
    import numpy as np

    value = shape.val() if isinstance(shape, cq.Workplane) else shape
    vertices, triangles = value.tessellate(0.35, 0.15)
    xyz = np.array([[p.x, p.y, p.z] for p in vertices], dtype=float)
    faces = np.array(triangles, dtype=int)
    return xyz, faces


def render_preview(shape: cq.Workplane | cq.Shape, path: Path, title: str, elev: float = 24, azim: float = -50) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    vertices, faces = shape_mesh(shape)
    fig = plt.figure(figsize=(7.2, 5.4), facecolor="#f4f7f4")
    ax = fig.add_subplot(111, projection="3d")
    mesh = Poly3DCollection(vertices[faces], facecolor="#d89236", edgecolor="#594527", linewidth=0.12, alpha=0.95)
    ax.add_collection3d(mesh)
    mins, maxs = vertices.min(axis=0), vertices.max(axis=0)
    centre = (mins + maxs) / 2
    radius = max(float((maxs - mins).max()) / 2, 1.0)
    ax.set_xlim(centre[0] - radius, centre[0] + radius)
    ax.set_ylim(centre[1] - radius, centre[1] + radius)
    ax.set_zlim(centre[2] - radius, centre[2] + radius)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    ax.set_title(title, fontsize=14, weight="bold", color="#243126", pad=12)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=170, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)


def _projected_paths(
    shape: cq.Shape,
    *,
    projection: tuple[float, float, float],
    width: float,
    height: float,
) -> list[tuple[bool, list[tuple[float, float]]]]:
    """Return hidden/visible 2D HLR paths fitted to a drawing panel."""
    from cadquery.occ_impl.exporters.svg import getSVG

    svg_text = getSVG(
        shape,
        {
            "width": width,
            "height": height,
            "marginLeft": 8,
            "marginTop": 8,
            "projectionDir": projection,
            "showAxes": False,
            "showHidden": True,
            "strokeWidth": 0.7,
        },
    )
    root = ET.fromstring(svg_text)
    namespace = "{http://www.w3.org/2000/svg}"
    outer = root.find(f"{namespace}g")
    if outer is None:
        raise RuntimeError("CadQuery SVG projection contains no drawing group")
    transform = outer.attrib.get("transform", "")
    match = re.search(
        r"scale\(([-+0-9.eE]+)\s*,\s*([-+0-9.eE]+)\)\s*translate\(([-+0-9.eE]+)\s*,\s*([-+0-9.eE]+)\)",
        transform,
    )
    if not match:
        raise RuntimeError(f"Unexpected CadQuery SVG transform: {transform}")
    sx, sy, tx, ty = (float(value) for value in match.groups())
    number_pattern = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
    result: list[tuple[bool, list[tuple[float, float]]]] = []

    def visit(node: ET.Element, hidden: bool = False) -> None:
        hidden = hidden or "stroke-dasharray" in node.attrib
        if node.tag == f"{namespace}path":
            numbers = [float(item) for item in number_pattern.findall(node.attrib.get("d", ""))]
            points = []
            for index in range(0, len(numbers) - 1, 2):
                projected_x = (numbers[index] + tx) * sx
                projected_y_from_top = (numbers[index + 1] + ty) * sy
                points.append((projected_x, height - projected_y_from_top))
            if len(points) >= 2:
                result.append((hidden, points))
        for child in node:
            visit(child, hidden)

    visit(outer)
    if not result:
        raise RuntimeError("CadQuery HLR projection produced no drawable paths")
    return result


def _draw_cad_view(
    canvas,
    shape: cq.Shape,
    *,
    x: float,
    y: float,
    width: float,
    height: float,
    projection: tuple[float, float, float],
    label: str,
    overall: str,
) -> None:
    from reportlab.lib import colors

    canvas.setStrokeColor(colors.HexColor("#829086"))
    canvas.setLineWidth(0.55)
    canvas.roundRect(x, y, width, height, 5, fill=0, stroke=1)
    canvas.setFillColor(colors.HexColor("#243126"))
    canvas.setFont("Helvetica-Bold", 7.5)
    canvas.drawString(x + 7, y + height - 12, label)
    canvas.setFont("Helvetica", 6.8)
    canvas.drawRightString(x + width - 7, y + 5, overall)

    view_x = x + 6
    view_y = y + 14
    view_width = width - 12
    view_height = height - 31
    projected = _projected_paths(
        shape,
        projection=projection,
        width=view_width,
        height=view_height,
    )
    for hidden in (True, False):
        canvas.setStrokeColor(colors.HexColor("#AEB8B1") if hidden else colors.HexColor("#26362C"))
        canvas.setLineWidth(0.3 if hidden else 0.65)
        canvas.setDash(2.2, 1.8) if hidden else canvas.setDash()
        for is_hidden, points in projected:
            if is_hidden != hidden:
                continue
            path = canvas.beginPath()
            path.moveTo(view_x + points[0][0], view_y + points[0][1])
            for px, py in points[1:]:
                path.lineTo(view_x + px, view_y + py)
            canvas.drawPath(path, fill=0, stroke=1)
    canvas.setDash()


def drawing_pdf(shape: cq.Workplane | cq.Shape, path: Path, *, part_number: str, name: str, material: str, method: str, critical: list[str]) -> None:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.pdfgen.canvas import Canvas

    value = shape.val() if isinstance(shape, cq.Workplane) else shape
    bounds = value.BoundingBox()
    path.parent.mkdir(parents=True, exist_ok=True)
    page = landscape(A4)
    canvas = Canvas(str(path), pagesize=page)
    width, height = page
    canvas.setFillColor(colors.HexColor("#F4F7F4"))
    canvas.rect(0, 0, width, height, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#243126"))
    canvas.setFont("Helvetica-Bold", 18)
    canvas.drawString(34, height - 38, f"{part_number} - {name}")
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(width - 34, height - 35, "FIGBOT V0 DIGITAL PROTOTYPE")

    x0, y0 = 34, 105
    view_area_w, view_area_h = width * 0.65, height - 165
    gap = 10
    panel_w = (view_area_w - gap) / 2
    panel_h = (view_area_h - gap) / 2
    _draw_cad_view(
        canvas,
        value,
        x=x0,
        y=y0 + panel_h + gap,
        width=panel_w,
        height=panel_h,
        projection=(0, -1, 0),
        label="FRONT VIEW (X-Z)",
        overall=f"OVERALL X x Z: {bounds.xlen:.2f} x {bounds.zlen:.2f} mm",
    )
    _draw_cad_view(
        canvas,
        value,
        x=x0 + panel_w + gap,
        y=y0 + panel_h + gap,
        width=panel_w,
        height=panel_h,
        projection=(0, 0, 1),
        label="TOP VIEW (X-Y)",
        overall=f"OVERALL X x Y: {bounds.xlen:.2f} x {bounds.ylen:.2f} mm",
    )
    _draw_cad_view(
        canvas,
        value,
        x=x0,
        y=y0,
        width=panel_w,
        height=panel_h,
        projection=(1, 0, 0),
        label="RIGHT VIEW (Y-Z)",
        overall=f"OVERALL Y x Z: {bounds.ylen:.2f} x {bounds.zlen:.2f} mm",
    )
    _draw_cad_view(
        canvas,
        value,
        x=x0 + panel_w + gap,
        y=y0,
        width=panel_w,
        height=panel_h,
        projection=(-1.75, 1.1, 5),
        label="ISOMETRIC VIEW",
        overall="REFERENCE - SEE STEP FOR 3D GEOMETRY",
    )

    tx = x0 + view_area_w + 20
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawString(tx, height - 92, "MANUFACTURING DATA")
    canvas.setFont("Helvetica", 9)
    lines: list[str] = []
    for raw_line in (
        f"Material: {material}",
        f"Method: {method}",
        f"Envelope X: {bounds.xlen:.2f} mm",
        f"Envelope Y: {bounds.ylen:.2f} mm",
        f"Envelope Z: {bounds.zlen:.2f} mm",
        "Units: mm",
        "General tolerance:",
        "TBD - MANUFACTURING REVIEW REQUIRED",
        "Physical status: UNVERIFIED",
    ):
        lines.extend(_wrap(raw_line, 34))
    y = height - 112
    for line in lines:
        canvas.drawString(tx, y, line)
        y -= 15
    y -= 6
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawString(tx, y, "CRITICAL NOTES")
    y -= 17
    canvas.setFont("Helvetica", 8.5)
    for note in critical:
        for chunk in _wrap(note, 40):
            canvas.drawString(tx, y, chunk)
            y -= 12
    canvas.setFillColor(colors.HexColor("#A44A3F"))
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(34, 60, "NOT FOR PRODUCTION. FITS, STRENGTH, FOOD CONTACT, AND TOLERANCES REQUIRE HUMAN REVIEW.")
    canvas.setFillColor(colors.HexColor("#243126"))
    canvas.setFont("Helvetica", 8)
    spec_text = (ROOT / "MASTER_SPEC.md").read_text(encoding="utf-8")
    version_match = re.search(r"^Version:\s*([^\s|]+)", spec_text, flags=re.MULTILINE)
    spec_version = version_match.group(1) if version_match else "TBD"
    canvas.drawRightString(
        width - 34,
        35,
        f"Generated {date.today().isoformat()} | RFQ reference | MASTER_SPEC {spec_version}",
    )
    canvas.save()


def write_metadata(path: Path, *, part_number: str, name: str, purpose: str, material: str, method: str, qty: int, related: str, critical: str, orientation: str) -> None:
    path.write_text(
        f"# {part_number} - {name}\n\n"
        f"- Purpose: {purpose}\n- Material: {material}\n- Manufacturing method: {method}\n- Quantity: {qty}\n"
        f"- Related parts: {related}\n- Fasteners/bearings: see BOM; selection UNVERIFIED\n"
        f"- Critical dimensions: {critical}\n- Tolerances: TBD - MANUFACTURING REVIEW REQUIRED\n"
        f"- Assembly orientation: {orientation}\n- Calculation status: DIGITAL CAD ONLY\n"
        f"- Physical verification: FALSE - PHYSICAL VALIDATION REQUIRED\n",
        encoding="utf-8",
    )


def _wrap(text: str, length: int) -> list[str]:
    words, lines, current = text.split(), [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) > length and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines
