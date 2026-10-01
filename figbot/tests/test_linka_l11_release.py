"""Release integrity: archived print jobs, replacement-only job and physical fit coupon."""
import hashlib
import json
import zipfile
from pathlib import Path
import numpy as np
import trimesh
from scripts.package_linka_plates import OUT,SOURCE,ROOT,Q
from scripts.project_paths import read_original
import xml.etree.ElementTree as ET

def test_current_part_comparison_matches_declared_revision_changes():
    rows=json.loads((OUT/'PARCA_KARSILASTIRMA.json').read_text())
    for r in rows:
        current=hashlib.sha256((SOURCE/'PRINT_STL'/(r['part']+'.stl')).read_bytes()).hexdigest().upper()
        assert current==r['new_sha256']
    assert {int(r['part'].split('-')[1]) for r in rows if not r['unchanged']}=={1,6,7,8,10,11,13,14,15,17,18,22}

def test_original_issued_zips_are_preserved():
    original=json.loads((ROOT/'reports/linka_l1r1_audit/before/PLATE_HASHES.json').read_text(encoding='utf-8-sig'))
    for r in original:
        assert hashlib.sha256(read_original(r['Path'])).hexdigest().upper()==r['Hash']

def test_replacement_only_job_cannot_duplicate_retainer_halves():
    name='02A_YALNIZ_YENI_MOTOR_TABLASI'
    with zipfile.ZipFile(OUT/name/(name+'.3mf')) as z:
        root=ET.fromstring(z.read('3D/3dmodel.model'))
    objects=root.find(Q+'resources').findall(Q+'object')
    assert len(objects)==1 and objects[0].get('name').startswith('L1-06-DECK')
    m=trimesh.load_mesh(OUT/name/(name+'.stl'))
    source=trimesh.load_mesh(SOURCE/'PRINT_STL/L1-06-DECK.stl')
    assert np.isclose(m.volume,source.volume) and len(m.faces)==len(source.faces)

def test_coupon_is_three_connected_parts_and_fits_bed():
    folder=OUT/'00_UYUM_DENEMESI'
    m=trimesh.load_mesh(folder/'00_UYUM_DENEMESI.stl')
    assert m.is_watertight and len(m.split())==3
    assert np.all(m.bounds[0,:2]>=8-1e-5) and np.all(m.bounds[1,:2]<=248)
    cap=trimesh.load_mesh(folder/'B_BEARING_CAP.stl')
    production=trimesh.load_mesh(SOURCE/'PRINT_STL/L1-22-BEARING-CAP.stl')
    assert np.isclose(cap.volume,production.volume,rtol=1e-5)
