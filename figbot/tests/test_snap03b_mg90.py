import numpy as np
import trimesh
from cad.prototype_arm import build_snap03b_mg90 as s
from cad.prototype_arm import build_snap03_mg90 as old

def vol(a,b):return max(0,a.intersect(b).val().Volume())

def test_new_reference_asymmetry_and_no_scale():
    m=trimesh.load_mesh(s.SOURCE)
    assert m.is_watertight
    assert np.allclose(m.extents,[16.496,33.698,3.8],atol=.01)
    assert np.allclose(s.profile().bounds,[-8.248,-15.673,8.248,18.025],atol=.01)

def test_excess_short_side_is_closed_and_long_side_extended():
    body,_=s.build();previous,_=old.build()
    short=s.box(.5,.3,1,(0,-16.5,2))
    long=s.box(.5,.15,1,(0,17.95,2))
    assert vol(body,short)>.149 and vol(previous,short)<1e-6
    assert vol(body,long)<1e-6 and vol(previous,long)>.07

def test_existing_covers_and_output_interface_unchanged():
    b,c=s.build();ob,oc=old.build()
    assert abs(c.val().Volume()-oc.val().Volume())<1e-6
    assert vol(c,oc)>c.val().Volume()-1e-6
    keep=s.box(40,23,8,(0,33.5,3))
    assert abs(vol(b,keep)-vol(ob,keep))<1e-6
    assert len(b.solids().vals())==1 and b.val().isValid()

def test_insertion_retention_and_rotation_audit():
    audit=s.audit_geometry()
    assert max(audit['checks']['closed_pair_overlaps_mm3'].values())<1e-6
    assert audit['checks']['insertion']['horn_overlap_mm3']<1e-6
    assert min(audit['checks']['torque_stop_overlap_at_rotation_mm3'].values())>1
