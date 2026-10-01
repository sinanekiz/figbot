"""Nominal checks on shipped STEP parts; NOT a physical print-fit certificate."""
from pathlib import Path
import cadquery as cq

from scripts.project_paths import CAD
PARTS = CAD / 'PART_STEP'


def test_rejected_motor_ear_screw_and_shorter_candidate():
    base = cq.importers.importStep(str(PARTS / 'L1-01-BASE.step')).val()
    volumes = {}
    for length in (8, 6):
        shaft = cq.Solid.makeCylinder(1.5, length, cq.Vector(14.95, 5, 40.2 - length))
        volumes[length] = base.intersect(shaft).Volume()
    assert volumes[8] > 5.6  # Known issue: procurement must not recommend it.
    assert volumes[6] < 1e-6  # Candidate only: actual servo ear thickness unknown.


def test_standard_625_nominal_body_fits_both_exported_pockets():
    for name, start in [('L1-07-UPPER-L', -19), ('L1-08-UPPER-R', 14)]:
        part = cq.importers.importStep(str(PARTS / (name + '.step'))).val()
        bearing = cq.Solid.makeCylinder(8, 5, cq.Vector(150, start, 0), cq.Vector(0, 1, 0))
        assert part.intersect(bearing).Volume() < 1e-6
