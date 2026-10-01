import csv,json,zipfile
import xml.etree.ElementTree as ET
import pytest
import trimesh
from cad.prototype_arm import build_linka_v1 as a
from scripts.validate_linka_v1 import potential

def test_potential_uses_kg_metres_and_gravity():
    assert potential([dict(frame='base',mass_g=1000,center_mm=[0,0,1000])],0,0,0,0)==pytest.approx(9.80665)

def test_bom_and_explicit_unknown_cost():
    with (a.OUT/'PRINT_BOM.csv').open() as f:rows=list(csv.DictReader(f))
    assert {r['id'] for r in rows}==set(a.PARTS)
    assert all(int(r['count'])==a.PARTS[r['id']][1] for r in rows)
    cost=json.loads((a.OUT/'COST_ESTIMATE.json').read_text())
    assert cost['printed_part_instances']==sum(int(r['count']) for r in rows)
    assert cost['total'] is None and cost['hardware_total'] is None

def test_all_exported_parts_watertight_and_3mf_present():
    for pid in a.PARTS:
        m=trimesh.load_mesh(a.OUT/'PRINT_STL'/f'{pid}.stl',process=True)
        assert m.is_watertight and m.is_winding_consistent,pid
        with zipfile.ZipFile(a.OUT/'3MF'/f'{pid}.3mf') as z:
            assert '3D/3dmodel.model' in z.namelist()
            ET.fromstring(z.read('Metadata/Slic3r_PE_model.config'))

def test_urdf_mesh_scale_and_declared_loop():
    root=ET.parse(a.OUT/'URDF/LINKA_L1_REVIEW.urdf').getroot()
    assert len(root.findall('link'))==7
    for link in root.findall('link'):
        m=trimesh.load_mesh(a.OUT/'URDF'/f"{link.attrib['name']}.stl",process=True)
        assert max(m.extents)<1
    closure=json.loads((a.OUT/'URDF/CLOSED_LOOP.json').read_text())
    assert closure['rod_tip_mm'][0]==a.ROD
