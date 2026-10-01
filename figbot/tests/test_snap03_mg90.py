"""Regression for source conversion, keyed retention and insertable covers."""
import numpy as np
import trimesh
from cad.prototype_arm import build_snap03_mg90 as s
from cad.prototype_arm import extract_mg90_reference as extractor

def vol(a,b): return max(0,a.intersect(b).val().Volume())

def test_reference_is_closed_and_not_scaled_or_substituted():
    m=trimesh.load_mesh(s.SOURCE)
    assert m.is_watertight and m.is_winding_consistent and len(m.split())==1
    assert np.allclose(m.extents,[16.3,35,4.85],atol=.001)
    assert 466<m.volume<469
    assert s.profile().area/s.profile().convex_hull.area<.85

def test_native_recovery_reproduces_reference(tmp_path,monkeypatch):
    import shutil,hashlib
    for name in ['MG90servo_gear.SLDPRT','decode.json']:
        shutil.copyfile(extractor.REF/name,tmp_path/name)
    monkeypatch.setattr(extractor,'REF',tmp_path)
    extractor.extract()
    assert hashlib.sha256((tmp_path/'MG90_canonical.stl').read_bytes()).digest()==hashlib.sha256(s.SOURCE.read_bytes()).digest()

def test_both_rotation_directions_are_keyed():
    body,_=s.build();h=s.horn_envelope()
    assert vol(body,h)<1e-6
    for a in [-3,3]:assert vol(body,h.rotate((0,0,0),(0,0,1),a))>1

def test_cover_and_horn_installation_paths():
    b,c=s.build();h=s.horn_envelope()
    for z in np.linspace(0,15,16):assert vol(b,h.translate((0,0,float(z))))<1e-6
    for d in np.linspace(0,46,47):
        cs=s.caps_pose(c,float(d))
        for x in cs:assert vol(x,h)<1e-6
        assert vol(*cs)<1e-6

def test_retention_and_integral_output():
    b,c=s.build();h=s.horn_envelope();cs=s.caps_pose(c)
    assert sum(vol(h.translate((0,0,.5)),x) for x in cs)>1
    for x in cs:
        assert vol(b,x)<1e-6
        assert vol(b,x.translate((0,0,.5)))>1
    for x in s.caps_pose(c,1):assert vol(b,x)>0
    for x in [b,c]:assert x.val().isValid() and len(x.solids().vals())==1
    probe=s.box(8,3,1,(0,22,1))
    assert abs(vol(b,probe)-24)<1e-5

def test_complete_audit():
    a=s.audit_geometry()
    assert a['checks']['insertion']['rigid_plate_overlap_mm3']<1e-6
    assert a['checks']['motor_keepout']['printed_top_to_plane_gap_mm']==.25
