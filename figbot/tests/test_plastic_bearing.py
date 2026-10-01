"""PB01 digital fit checks; these do not establish physical strength/friction."""
from collections import Counter
from pathlib import Path
import hashlib
import json
import math
import xml.etree.ElementTree as ET
import numpy as np
import pytest
import trimesh
from cad.prototype_arm import build_plastic_bearing as b
from cad.prototype_arm.audit_aero_v4 import overlaps


@pytest.mark.parametrize('spec',[b.SMALL,b.LARGE])
def test_solids_exports_and_plate_manifest(spec):
    report=json.loads((b.OUT/spec.name/'MANIFEST.json').read_text())
    assert report['source_sha256']==hashlib.sha256(Path(b.__file__).read_bytes()).hexdigest()
    counts=Counter()
    for p in report['plates']:
        limits=np.array(p['bounds_mm'])
        assert np.all(limits[0]>=-1e-4) and np.all(limits[1]<=[246,246,256])
        for n in p['objects']:
            name='BILYE_8MM' if n.startswith('BILYE_') else n.rsplit('_',1)[0]
            counts[name]+=1
    assert counts==Counter({p['part']:p['qty'] for p in report['parts']})
    for part in report['parts']:
        m=trimesh.load_mesh(b.OUT/spec.name/'TEKIL'/(part['part']+'.stl'))
        assert m.is_watertight and m.is_volume and len(m.split())==1
        assert abs(m.bounds[0,2])<1e-4
    full_volume=sum(p['qty']*p['solid_volume_mm3'] for p in report['parts'])
    assert report['full_solid_PLA_g_ESTIMATE']==pytest.approx(full_volume*.00124)
    assert report['cost_TRY'] is None and report['load_capacity_N'] is None
    assert not report['arm_adapter_complete'] and not report['printer_job_sent']
    ur=b.OUT/spec.name/'URDF/PB01_REVIEW.urdf'
    root=ET.parse(ur).getroot()
    for m in root.findall('.//mesh'):assert (ur.parent/m.attrib['filename']).exists()
    assert len(root.findall('joint'))==len(b.items(spec))


@pytest.mark.parametrize('spec',[b.SMALL,b.LARGE])
def test_complete_assembly_no_solid_penetration(spec):
    assert overlaps(b.items(spec))==[]


@pytest.mark.parametrize('spec',[b.SMALL,b.LARGE])
def test_cap_can_be_lowered_and_twist_locked_without_clips(spec):
    lower=b.lower(spec);rotor=b.rotor(spec)
    for dz in [25,15,8,4,2,0]:
        cap=b.cap(spec).rotate((0,0,0),(0,0,1),-30).translate((0,0,dz))
        for fixed in [lower,rotor]:assert cap.intersect(fixed).val().Volume()<1e-5
    for theta in np.linspace(-30,0,13):
        cap=b.cap(spec).rotate((0,0,0),(0,0,1),float(theta))
        for fixed in [lower,rotor]:assert cap.intersect(fixed).val().Volume()<1e-5
    # The locked cap has positive geometric uplift capture, not just friction.
    assert b.cap(spec).translate((0,0,1)).intersect(lower).val().Volume()>1
    assert b.rotor(spec).translate((0,0,1)).intersect(b.cap(spec)).val().Volume()>1


@pytest.mark.parametrize('spec',[b.SMALL,b.LARGE])
def test_rotor_cage_and_balls_have_assembly_access_and_clear_sweep(spec):
    lower=b.lower(spec);cap=b.cap(spec);cage=b.cage(spec)
    for theta in np.linspace(0,360,13):
        rot=b.rotor(spec).rotate((0,0,0),(0,0,1),float(theta))
        for fixed in [lower,cap,cage]:assert rot.intersect(fixed).val().Volume()<1e-5
    for dz in [0,1,3,6,15]:
        rot=b.rotor(spec).translate((0,0,dz))
        for fixed in [lower,cage]:assert rot.intersect(fixed).val().Volume()<1e-5
    # Ball fit has nominal radial margin, not press-fit zero clearance.
    assert b.GROOVE_R>b.BALL_D/2
    assert 2*spec.pitch_r*math.sin(math.pi/spec.balls)>b.BALL_D+.5


def test_balls_are_spheres_not_split_clips_or_flat_spotted_substitutes():
    assert b.ball().val().Volume()==pytest.approx(4/3*math.pi*4**3,rel=1e-6)
    m=b.mesh(b.ball())
    assert m.volume==pytest.approx(4/3*math.pi*4**3,rel=.002)


def test_printed_lock_pins_have_heads_on_bed_to_avoid_branch_support_collision():
    s=b.print_pose('KILIT_PIMI',b.pin()).val()
    assert s.isInside(b.cq.Vector(5.5,3,.5))


@pytest.mark.parametrize('spec,filename',[(b.SMALL,'OFFLINE_SLICE_AUDIT.json'),(b.LARGE,'LARGE_OFFLINE_SLICE_AUDIT.json')])
def test_offline_plate_slicing_really_generated_ball_supports(spec,filename):
    report=json.loads((b.OUT/filename).read_text())
    assert report['printer_commands_sent'] is False
    assert report['physical_print_validated'] is False
    for row in report['results']:
        assert row['returncode']==0
        assert row['input_sha256']==hashlib.sha256((b.OUT/spec.name/row['file']).read_bytes()).hexdigest()
        assert row['warnings']==[]
        if row['file'].startswith('BILYELER'):assert row['support_sections']>0
