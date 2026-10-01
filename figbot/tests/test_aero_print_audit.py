import cadquery as cq
import pytest

from cad.prototype_arm.audit_aero_v2 import mesh_audit, relation


def test_relation_distinguishes_touch_from_solid_interference_and_gap():
    block = cq.Workplane("XY").box(10, 10, 10).val()
    assert relation(block, block.translate((10, 0, 0)))["classification"] == "CONTACT"
    assert relation(block, block.translate((11, 0, 0)))["gap_mm"] == pytest.approx(1)
    clash = relation(block, block.translate((9, 0, 0)))
    assert clash["classification"] == "INTERFERENCE"
    assert clash["overlap_mm3"] == pytest.approx(100)


def test_mesh_audit_rejects_wrong_scale_even_when_watertight(tmp_path):
    block = cq.Workplane("XY").box(10, 10, 10)
    path = tmp_path / "cube.stl"
    cq.exporters.export(block, str(path))
    assert mesh_audit(path, block.val())["mesh_ok"]
    enlarged = cq.Workplane("XY").box(20, 20, 20).val()
    assert not mesh_audit(path, enlarged)["mesh_ok"]


def test_mesh_audit_rejects_disconnected_print_part(tmp_path):
    block = cq.Workplane("XY").box(10, 10, 10).val()
    compound = cq.Compound.makeCompound([block, block.translate((20, 0, 0))])
    path = tmp_path / "two_solids.stl"
    cq.exporters.export(compound, str(path))
    report = mesh_audit(path, compound)
    assert report["components"] == 2
    assert not report["mesh_ok"]
