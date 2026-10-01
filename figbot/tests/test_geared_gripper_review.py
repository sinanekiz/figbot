"""Geometry evidence for the unselected two-jaw comparison; not physical approval."""
import json
import xml.etree.ElementTree as ET
from pathlib import Path

from cad.prototype_arm import geared_gripper as g
from scripts.export_geared_gripper_review import OUT


def test_candidate_printed_shapes_are_connected_and_valid():
    for item in g.items():
        if item.part_id:
            assert item.shape.val().isValid(), item.name
            assert len(item.shape.val().Solids()) == 1, item.name


def test_audit_covers_limits_and_service_paths():
    report = json.loads(Path('reports/geared_gripper/AUDIT.json').read_text())
    assert [p['angle'] for p in report['poses']] == [0, 6, 12, 18, g.OPEN]
    assert all(not p['hits'] for p in report['poses'])
    assert all(x['collision_mm3'] < 1e-4 for path in report['new_service'].values() for x in path)
    assert any(x['collision_mm3'] > 1 for path in report['old_straight_insertion'].values() for x in path)


def test_review_exports_and_mass_are_not_a_print_or_lightness_claim():
    for suffix in ['CLOSED', 'OPEN', 'SERVICE', 'ARM']:
        for extension in ['step', 'glb']:
            assert (OUT / f'LINKA_L1_GEARED_{suffix}.{extension}').stat().st_size > 100
        assert (OUT / f'GEARED_{suffix}.png').stat().st_size > 100
    data = json.loads((OUT / 'MASS_AND_PARTS.json').read_text())
    assert data['comparison']['new_with_same_wrist_hardware_g'] > data['comparison']['old_tool_g']
    assert all(p['status'].startswith('REVIEW ONLY') for p in data['parts'])
    root = ET.parse(OUT / 'URDF/REVIEW.urdf').getroot()
    assert root.find("joint[@name='right_jaw']/mimic").get('multiplier') == '-1'
    assert all(j.find('limit').get('effort') == '0' for j in root.findall('joint'))
    assert 'baskı sürümü değildir' in (OUT / 'OKU.md').read_text(encoding='utf-8')
