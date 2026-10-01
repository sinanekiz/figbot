"""Delivery checks: prevent stale or mixed-revision print packages."""
import csv
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'cad/prototype_arm/aero_v3'


def test_delivery_matches_audited_source():
    digest = hashlib.sha256((ROOT/'cad/prototype_arm/build_aero_v3.py').read_bytes()).hexdigest()
    audit = json.loads((OUT/'GEOMETRY_AUDIT.json').read_text())
    assert audit['digital_geometry_ok']
    assert audit['source_sha256'] == digest == (OUT/'EXPORT_SOURCE_SHA256.txt').read_text()
    assert len(audit['motion_samples']) == 22
    assert len(audit['jaw_samples']) == 11
    assert len(audit['dual_arm_key_poses']) == 3
    for filename, count in [('MESH_AUDIT.json', 15), ('FIT_MESH_AUDIT.json', 9)]:
        rows = json.loads((OUT/filename).read_text())
        assert len(rows) == count and all(row['mesh_ok'] for row in rows)


def test_print_archives_contain_exact_current_parts():
    for kind, folder, count in [('FIT_CHECK_FIRST', 'FIT_STL', 9), ('BENCH_PRINT_STL', 'PRINT_STL', 15)]:
        with zipfile.ZipFile(OUT/f'AERO_V3_{kind}.zip') as z:
            assert z.testzip() is None
            files = [n for n in z.namelist() if n.endswith('.stl')]
            assert len(files) == count
            assert {Path(n).name for n in files} == {p.name for p in (OUT/folder).glob('*.stl')}
            for name in files:
                assert z.read(name) == (OUT/folder/Path(name).name).read_bytes()
            assert z.read('GEOMETRY_AUDIT.json') == (OUT/'GEOMETRY_AUDIT.json').read_bytes()
    with (OUT/'PRINT_ORDER.csv').open(encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    assert sum(int(r['quantity']) for r in rows) == 29
    assert all(max(float(r[k]) for k in ('x_mm','y_mm','z_mm')) <= 256 for r in rows)


def test_review_urdf_references_real_meshes_and_connected_tree():
    directory = OUT/'urdf'
    robot = ET.parse(directory/'AERO_V3_REVIEW.urdf').getroot()
    links = {l.attrib['name'] for l in robot.findall('link')}
    children = set()
    for joint in robot.findall('joint'):
        parent = joint.find('parent').attrib['link']
        child = joint.find('child').attrib['link']
        assert parent in links and child in links and child not in children
        children.add(child)
    assert links - children == {'base'} and len(children) == 5
    for mesh in robot.findall('.//mesh'):
        assert (directory/mesh.attrib['filename']).stat().st_size > 84
        assert mesh.attrib['scale'] == '0.001 0.001 0.001'
    assert robot.find("joint[@name='W1']/mimic") is None  # W1 depends on TWO angles.
