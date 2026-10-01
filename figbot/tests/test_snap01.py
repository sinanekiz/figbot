"""Digital checks for isolated clip coupon; never physical strength approval."""
import json
import xml.etree.ElementTree as ET
import numpy as np
from cad.prototype_arm.build_snap01 import build,profile,box,LID_Z,OUT

def test_fit_profile_preserves_source_but_is_not_star():
    points,original,simplified=profile()
    assert original.hausdorff_distance(simplified)<.002
    assert np.allclose(np.ptp(points,axis=0),[20.8,20.8],atol=.003)
    # Source circle is a 72-segment STL polygon; section vertices may lie on chords.
    assert np.allclose(np.linalg.norm(points,axis=1),10.4,atol=.011)

def test_closed_parts_valid_and_do_not_intersect():
    body,lid=build()
    for part in [body,lid]:
        assert part.val().isValid()
        assert len(part.solids().vals())==1
    assert body.intersect(lid.translate((0,0,LID_Z))).val().Volume()<1e-6

def test_insertion_rigid_shoulders_clear_and_only_hooks_require_flex():
    body,lid=build()
    rigid=lid.intersect(box(32,100,20,(0,0,0)))
    for y in np.linspace(-38,0,20):
        assert body.intersect(rigid.translate((0,float(y),LID_Z))).val().Volume()<1e-6
    # Deliberate interference of the undeflected latch, not a rigid free slider.
    assert body.intersect(lid.translate((0,-5,LID_Z))).val().Volume()>1

def test_rails_retain_axially_and_hooks_block_withdrawal():
    body,lid=build()
    assert body.intersect(lid.translate((0,0,LID_Z+.6))).val().Volume()>1
    assert body.intersect(lid.translate((0,-1,LID_Z))).val().Volume()>1

def test_exports_mm_print_plane_and_fixed_urdf():
    audit=json.loads((OUT/'AUDIT.json').read_text())
    assert 'NOT PROVIDED' in audit['torque_transfer']
    for part in audit['parts'].values():
        assert part['watertight'] and part['bodies']==1
        assert abs(part['minimum_z_mm'])<1e-5
        assert max(part['size_mm'])<41
    root=ET.parse(OUT/'SNAP01_FIXED_REVIEW.urdf').getroot()
    assert all(j.attrib['type']=='fixed' for j in root.findall('joint'))
    assert len(root.findall('link'))==2
