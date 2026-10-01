"""Generate the concise illustrated V0 assembly PDF from repository artifacts."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assembly" / "ASSEMBLY_MANUAL.pdf"


def build_manual() -> Path:
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Cover", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=24, leading=28, textColor=colors.HexColor("#243126"), alignment=TA_CENTER, spaceAfter=12))
    styles.add(ParagraphStyle(name="Warning", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=10, leading=14, textColor=colors.HexColor("#A44A3F"), borderColor=colors.HexColor("#A44A3F"), borderWidth=1, borderPadding=8, spaceBefore=8, spaceAfter=12))
    styles.add(ParagraphStyle(name="Step", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=15, textColor=colors.HexColor("#243126"), spaceBefore=10, spaceAfter=6))
    doc = SimpleDocTemplate(str(OUT), pagesize=A4, rightMargin=18*mm, leftMargin=18*mm, topMargin=16*mm, bottomMargin=16*mm, title="FIGBOT V0 Assembly Manual")
    story = [Paragraph("FIGBOT V0<br/>ASSEMBLY MANUAL", styles["Cover"]), Paragraph("Rev A | 2026-08-20 | Digital prototype package", styles["BodyText"])]
    iso = ROOT / "renders" / "FIGBOT_V0_isometric.png"
    if iso.exists():
        story += [Spacer(1, 8), Image(str(iso), width=145*mm, height=145*mm*0.76)]
    story += [Paragraph("PROTOTYPE - NOT YET PRODUCTION VALIDATED. Human mechanical, electrical, and safety review is mandatory before energizing. Secure the stand, use current-limited one-axis commissioning, and verify the physical E-stop energy path.", styles["Warning"]), PageBreak()]

    exploded = ROOT / "renders" / "FIGBOT_V0_exploded.png"
    if exploded.exists():
        story += [Paragraph("Exploded reference", styles["Step"]), Image(str(exploded), width=170*mm, height=105*mm), Spacer(1, 8)]
    steps = [
        ("1. Secure the bench base", "CHA-001", "Anchor the plywood/CNC base to a stable bench. Verify flatness and exclusion zone. Fastener size and tightening torque remain TBD."),
        ("2. Install arm base", "ARM-001, ARM-002", "Attach the base plate and J1/shoulder housing. Do not use printed walls as an unreviewed primary bolt-bearing surface."),
        ("3. Assemble shoulder and upper link", "ARM-003, ARM-007", "Install the 6002 bearings, 15 mm shaft and 300 mm tube. Confirm free movement before fitting the jaw coupling."),
        ("4. Assemble elbow and forearm", "ARM-004, ARM-005, ARM-007", "Fit the 220 mm tube and elbow shaft. Check joint stops and cable clearance through the full manual range."),
        ("5. Install wrist", "ARM-006, ARM-007", "Mount J4 housing with the tool axis downward in the home pose. Verify power-loss gravity behavior before adding the gripper."),
        ("6. Install one gripper prototype", "GRP-001 plus GRP-002 or GRP-003 or GRP-004", "Use only one configured variant at a time. Cast silicone with GRP-005/006/007 tooling and follow the damage-test protocol."),
        ("7. Mount camera and funnel", "VIS-001, FUN-001, FUN-002, FUN-003", "Align the optical center and keep the funnel outside the target rectangle. Perform camera-to-base calibration after final tightening."),
        ("8. Mount electronics and wire safety chain", "ELE-001 and PUR electrical items", "Follow electrical/WIRING.md. A qualified reviewer must approve mains protection, dual-channel E-stop, contactors, EDM, grounding, and controlled restart."),
        ("9. Commission", "All V0 parts", "Run PRE_POWER_CHECKLIST.md, mechanically support gravity-loaded axes or decouple couplings for first motion, current-limit each axis, verify limits/encoders, then run the physical test plan."),
    ]
    for title, codes, body in steps:
        block = [Paragraph(title, styles["Step"]), Table([["Parts", codes], ["Instruction", body]], colWidths=[28*mm, 137*mm], style=TableStyle([
            ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#E9EFEB")), ("TEXTCOLOR", (0,0), (-1,-1), colors.HexColor("#243126")),
            ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"), ("FONTNAME", (1,0), (1,-1), "Helvetica"),
            ("FONTSIZE", (0,0), (-1,-1), 8.7), ("LEADING", (0,0), (-1,-1), 12), ("GRID", (0,0), (-1,-1), .4, colors.HexColor("#AAB7AF")),
            ("VALIGN", (0,0), (-1,-1), "TOP"), ("LEFTPADDING", (0,0), (-1,-1), 6), ("RIGHTPADDING", (0,0), (-1,-1), 6),
            ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ])), Spacer(1, 5)]
        story.append(KeepTogether(block))

    def footer(canvas, document):
        canvas.saveState(); canvas.setFont("Helvetica", 7.5); canvas.setFillColor(colors.HexColor("#586B5B"))
        canvas.drawString(18*mm, 9*mm, "FIGBOT V0 - PROTOTYPE / PHYSICAL VALIDATION REQUIRED")
        canvas.drawRightString(192*mm, 9*mm, f"Page {document.page}"); canvas.restoreState()
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return OUT


if __name__ == "__main__":
    print(build_manual())
