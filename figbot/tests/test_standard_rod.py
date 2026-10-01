"""DEC-085 actual output and assembly regression, not physical certification."""
import json,hashlib,zipfile
from collections import Counter
import numpy as np
import pytest
import trimesh
from scripts.project_paths import CAD,PRINTS,ROOT
from cad.prototype_arm import build_linka_v1 as a

def test_printed_sleeve_has_substantial_wall_and_unclamped_rod():
    assert (a.ROD_BUSH_OD-a.ROD_BUSH_ID)/2==pytest.approx(1.35)
    assert a.ROD_PIVOT_BORE-a.ROD_BUSH_OD==pytest.approx(.3)
    assert a.ROD_BUSH_LENGTH-a.ROD_END_THICK==pytest.approx(.4)
    assert 10-6-.5==pytest.approx(3.5)
    for pid in ['L1-15-COUPLER','L1-26-ROD-BUSH']:
        m=trimesh.load_mesh(CAD/'PRINT_STL'/f'{pid}.stl')
        assert m.is_watertight and len(m.split())==1
    audit=json.loads((CAD/'CUBUK_MAFSALI/AUDIT.json').read_text())
    assert len(audit['local_contacts'])==40
    assert max(r['collision_mm3'] for r in audit['local_contacts'])<1e-5
    assert audit['physical_approval'] is False

def test_existing_crank_and_forearm_exports_are_unchanged():
    previous=json.loads((ROOT/'reports/linka_cable_exit_audit/COMPARISON_TO_L12.json').read_text())
    for row in previous:
        if row['part'] in ['L1-10-FORE-L','L1-14-DRIVE-CRANK']:
            assert hashlib.sha256((CAD/'PRINT_STL'/f"{row['part']}.stl").read_bytes()).hexdigest().upper()==row['new_sha']

def test_only_one_rod_and_two_bushes_in_new_plate_and_full_set():
    manifest=json.loads((PRINTS/'TABLA_LISTESI.json').read_text())
    plate=next(p for p in manifest['plates'] if p['name']=='09_CUBUK_VE_BURCLAR')
    assert Counter(e['id'] for e in plate['instances'])=={'L1-15-COUPLER':1,'L1-26-ROD-BUSH':2}
    assert sum(e['id']=='L1-15-COUPLER' for p in manifest['plates'] for e in p['instances'])==1
    m=trimesh.load_mesh(PRINTS/plate['name']/(plate['name']+'.stl'))
    assert m.is_watertight and len(m.split())==3
    assert np.all(m.bounds[0,:2]>=8) and np.all(m.bounds[1,:2]<=248)
    with zipfile.ZipFile(PRINTS/plate['name']/(plate['name']+'.3mf')) as z:
        import xml.etree.ElementTree as ET
        root=ET.fromstring(z.read('3D/3dmodel.model'))
        assert len(root.find('{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}build'))==3

def test_rod_does_not_hit_adjacent_structure_along_recorded_transfer():
    from scripts.arm_engineering_review import TARGETS
    items={i.name:i for i in a.local_items()}
    moving=items['L1-15-COUPLER']
    poses=[a.ik(t) for t in TARGETS.values()]
    hits=[]
    for left,right in zip(poses,poses[1:]):
        for t in np.linspace(0,1,5):
            fs=a.frames((1-t)*np.array(left)+t*np.array(right))
            for name in ['L1-06-DECK','L1-10-FORE-L','L1-14-DRIVE-CRANK']:
                fixed=items[name]
                other=a.h.move(fixed.shape,np.linalg.inv(fs[moving.frame])@fs[fixed.frame])
                volume=moving.shape.intersect(other).val().Volume()
                if volume>1e-5:hits.append((name,float(t),volume))
    assert hits==[]
