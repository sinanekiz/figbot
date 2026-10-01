"""Reported failure regressions: assembly transforms, trapped horns and clips."""
from collections import Counter
from pathlib import Path
import json,hashlib
import numpy as np
import trimesh
from cad.prototype_arm import build_aero_v4 as a
from cad.prototype_arm.export_aero_v4 import oriented
from cad.prototype_arm.audit_aero_v4 import overlaps

def vol(x,y):return max(0,x.intersect(y).val().Volume())

def test_nested_transforms_compose_instead_of_replacing_locations():
    s=a.box(2,2,2,(10,20,30));p=a.transform(s,a.ry(90,(100,0,0))).val().Center()
    assert np.allclose([p.x,p.y,p.z],[130,20,-10])

def test_each_new_part_is_a_single_closed_printable_body_and_fits_bed():
    for pid,(fn,n) in a.PARTS.items():
        s=fn();assert s.val().isValid() and len(s.solids().vals())==1,pid
        o=oriented(pid,s).val().BoundingBox()
        assert abs(o.zmin)<1e-5 and max(o.xlen,o.ylen,o.zlen)<236,pid
        m=trimesh.load_mesh(a.OUT/'PRINT'/f'{pid}.stl')
        assert m.is_watertight and m.is_winding_consistent and len(m.split())==1,pid

def test_all_printed_fasteners_and_parts_have_matching_assembly_quantities():
    c=Counter(i.part_id for i in a.local_items() if i.part_id)
    for k,(fn,n) in a.PARTS.items():assert c[k]==n,k
    assert c['S02_01_YILDIZ_GOVDE']==4 and c['S02_02_YARIM_KAPAK']==8
    assert c['S03_01_MG90_GOVDE']==2 and c['S03_02_MG90_KAPAK']==4
    assert sum(n for fn,n in a.PARTS.values())==75
    assert len([i for i in a.local_items() if i.group=='servo'])==6

def test_existing_horn_tongues_slide_without_filing_or_reprinting():
    for micro in [False,True]:
        b=(a.small if micro else a.large).build()[0]
        for d in np.linspace(0,60,16):assert vol(b,a.receiver(micro).translate((0,float(d),0)))<1e-5
    for side in [-1,1]:
        body=a.transform(a.large.build()[0],a.horn_pose(side=side))
        assert vol(body,a.upper_carrier())<1e-5

def test_gripper_capsule_not_only_finger_clears_the_palm_through_opening():
    body=a.transform(a.small.build()[0],a.GRIP_HORN)
    for q in np.linspace(-20,0,9):
        moved=a.transform(body,a.ry(float(q),(30,0,-66)))
        assert vol(a.palm(),moved)<1e-5

def test_default_complete_assembly_has_no_solid_penetrations():
    assert overlaps(a.assembly())==[]

def test_horizontal_servo_centre_screwdriver_paths_are_accessible():
    # Centre screws inserted before passive axles; slim shaft through6.4mm bore.
    probe=a.cyl_y(2,120)
    for shape in [a.fore_carrier(),a.stator_yoke(),a.palm(),a.stator_yoke(True)]:
        assert vol(probe,shape)<1e-5
    grip_probe=a.cyl_y(2,120,(30,0,-66))
    assert vol(grip_probe,a.palm())<1e-5

def test_print_plate_counts_do_not_duplicate_already_fitted_horns():
    plates=json.loads((a.OUT/'TABLA_LISTESI.json').read_text())
    names=[x.split('__')[0] for p in plates for x in p['objects']]
    assert Counter(names)==Counter({k:n for k,(fn,n) in a.PARTS.items()})
    for p in plates:
        b=np.array(p['bounds_mm']);assert np.all(b[0]>=-1e-5) and np.all(b[1]<=[246.001,246.001,256])

def test_final_audit_matches_current_geometry_and_passes():
    p=json.loads((a.OUT/'FINAL_AUDIT.json').read_text())
    assert p['source_sha256']==hashlib.sha256(Path(a.__file__).read_bytes()).hexdigest()
    assert p['passed'] and not p['default_collisions']

def test_cost_and_material_ledger_use_exact_print_quantities_without_inventing_price():
    m=json.loads((a.OUT/'PRINT_MANIFEST.json').read_text());c=json.loads((a.OUT/'MALZEME_MALIYET_TAHMINI.json').read_text())
    assert abs(sum(p['qty']*p['solid_volume_mm3'] for p in m)*.00124-c['new_parts_full_solid_g'])<.001
    assert c['filament_price_TRY_kg'] is None and c['new_print_cost_TRY'] is None
    assert c['purchase_ledger_changed'] is False
