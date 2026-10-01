"""Assembly and export checks; no physical friction or strength certification."""
import json,hashlib
from pathlib import Path
from collections import Counter
import numpy as np
import trimesh
import xml.etree.ElementTree as ET
from cad.prototype_arm import build_motor_bearing_pb02 as b
from cad.prototype_arm.audit_aero_v4 import overlaps


def volume(s):return s.val().Volume()


def test_valid_parts_and_assembled_clearance():
    for fn,n in b.PARTS.values():
        s=fn();assert s.val().isValid() and len(s.solids().vals())==1
    assert overlaps(b.base_assembly())==[]
    assert overlaps(b.assembly(),between_frames_only=True)==[]


def test_side_caps_install_without_passing_through_closed_deck():
    for side in [-1,1]:
        for dx in [0,1,2,4,6,8,10,15,20,30,50,80]:
            cap=b.cap_half(side).translate((side*dx,0,0))
            for fixed in [b.fixed_race(),b.rotor(),b.base()]:
                assert volume(cap.intersect(fixed))<1e-5
        assert volume(b.cap_half(side).translate((0,0,1)).intersect(b.fixed_race()))>1
        # Clearance is deliberately larger; the roof must still capture uplift.
        assert volume(b.rotor().translate((0,0,1.2)).intersect(b.cap_half(side)))>1


def test_retainer_roof_has_print_clearance_and_remains_captive():
    rotor=b.rotor()
    roof_band=b.pb.annulus(52,53.5,65,73)
    flange=rotor.intersect(roof_band)
    for side in [-1,1]:
        cap=b.cap_half(side)
        roof=cap.intersect(roof_band)
        gap=roof.val().BoundingBox().zmin-flange.val().BoundingBox().zmax
        assert abs(gap-1.0)<1e-6
        assert roof.val().BoundingBox().zlen>=2.39
        assert volume(rotor.translate((0,0,.9)).intersect(cap))<1e-5
        assert volume(rotor.translate((0,0,1.2)).intersect(cap))>1


def test_old_star_and_rigid_caps_fit_and_key_transmits_rotation():
    horn=next(i.shape for i in b.local_items() if i.name=='J1 original horn')
    assert volume(horn.intersect(b.rotor()))<1e-5
    assert volume(horn.rotate((0,0,0),(0,0,1),3).intersect(b.rotor()))>0.1
    rigid=b.a.large.build()[1].intersect(b.a.box(33.8,60,4,(0,0,1)))
    for travel in [0,2,5,10,20,30,46]:
        for cap in b.a.large.caps_pose(rigid,travel):
            assert volume(b.a.transform(cap,b.a.YAW_HORN).intersect(b.rotor()))<1e-5


def test_motor_and_fixed_race_have_insertion_access():
    items=b.base_assembly()
    motor=next(i.shape for i in items if i.name=='J1 case')
    for dz in [0,1,5,10,20,40,65]:
        assert volume(motor.translate((0,0,dz)).intersect(b.base()))<1e-5
    installed=[i.shape for i in items if i.name.startswith('J1 ') and ('case' in i.name or 'clamp' in i.name)]+[b.base()]
    for dz in [0,1,4,10,20,40]:
        race=b.fixed_race().translate((0,0,dz))
        for fixed in installed:assert volume(race.intersect(fixed))<1e-5


def test_ball_contact_preserves_motor_height_and_rotational_clearance():
    ball=b.pb.ball().translate((45,0,b.BEARING_Z+b.BALL_CENTRE_Z))
    assert volume(ball.intersect(b.fixed_race()))<1e-5
    assert volume(ball.intersect(b.rotor()))<1e-5
    assert volume(ball.translate((0,0,-.05)).intersect(b.fixed_race()))>.01
    assert volume(ball.translate((0,0,.05)).intersect(b.rotor()))>.01
    fixed=[b.base(),b.fixed_race(),b.cap_half(1),b.cap_half(-1)]
    motor=next(i.shape for i in b.base_assembly() if i.name=='J1 case')
    fixed.append(motor)
    for theta in [-180,-90,-30,0,30,90,180]:
        rot=b.rotor().rotate((0,0,0),(0,0,1),theta)
        for f in fixed:assert volume(rot.intersect(f))<1e-5
    old=b.a.PARTS['A4-02-SHOULDER-DECK'][0]()
    region=b.a.box(200,200,40,(0,0,98.5001))
    newtop=b.rotor().intersect(region);oldtop=old.intersect(region)
    assert abs(volume(newtop)-volume(oldtop))<1e-3
    assert b.a.SHOULDER_Z==124 and b.a.UPPER==300 and b.a.FORE==220


def test_generated_exports_quantities_and_estimate():
    m=json.loads((b.OUT/'MANIFEST.json').read_text())
    assert m['source_sha256']==hashlib.sha256(Path(b.__file__).read_bytes()).hexdigest()
    counts=Counter()
    for plate in m['plates']:
        assert plate['sha256']==hashlib.sha256((b.OUT/plate['file']).read_bytes()).hexdigest()
        for n in plate['objects']:counts[n.rsplit('__',1)[0]]+=1
        assert np.all(np.array(plate['bounds_mm'])[1]<=[246,246,256])
    assert counts==Counter({n:q for n,(f,q) in b.PARTS.items()})
    for p in m['parts']:
        mesh=trimesh.load_mesh(b.OUT/'TEKIL'/(p['part']+'.stl'))
        assert mesh.is_volume and mesh.is_watertight and len(mesh.split())==1
        assert abs(mesh.bounds[0,2])<1e-4
    assert abs(m['new_print_full_solid_PLA_g_ESTIMATE']-sum(p['volume_mm3']*p['qty']*.00124 for p in m['parts']))<1e-5
    assert m['cost_TRY'] is None and not m['physical_validation'] and not m['printer_job_sent']
    urdf=b.OUT/'URDF/PB02_ARM_REVIEW.urdf'
    root=ET.parse(urdf).getroot()
    assert len(root.findall('joint'))==5
    for mesh in root.findall('.//mesh'):assert (urdf.parent/mesh.attrib['filename']).exists()


def test_offline_supports_and_current_inputs():
    audit=json.loads((b.OUT/'OFFLINE_SLICE_AUDIT.json').read_text())
    assert len(audit['results'])==5 and not audit['printer_commands_sent']
    for r in audit['results']:
        assert r['returncode']==0 and not r['warnings'] and r['support_sections']>0
        assert r['input_sha256']==hashlib.sha256((b.OUT/r['file']).read_bytes()).hexdigest()
