"""Acceptance checks on delivered CAD, slice metadata and independent URDF FK."""
import hashlib,json,math,zipfile
import xml.etree.ElementTree as ET
import numpy as np
import pytest,trimesh
from cad.prototype_arm import build_aero_v5 as a

MANIFEST=json.loads((a.OUT/'PRINT_MANIFEST.json').read_text())


@pytest.mark.parametrize('row',MANIFEST,ids=lambda r:r['part'])
def test_released_print_mesh(row):
    f=a.OUT/'PRINT_STL'/(row['part']+'.stl');m=trimesh.load_mesh(f)
    assert hashlib.sha256(f.read_bytes()).hexdigest()==row['sha256']
    assert m.is_watertight and m.is_winding_consistent and m.volume>0
    assert len(m.split())==1
    assert max(m.extents[:2])<=236 and m.extents[2]<=246
    assert m.bounds[0].min()>=-1e-5
    step=a.OUT/'PART_STEP'/(row['part']+'.step')
    assert step.stat().st_size>1000 and b'ISO-10303-21' in step.read_bytes()[:100]
    checked=json.loads((a.OUT/'STEP_ROUNDTRIP.json').read_text())
    entry=next(r for r in checked['parts'] if r['file']==f"PART_STEP/{row['part']}.step")
    assert checked['passed'] and entry['positive_valid'] and entry['solids']==1 and entry['relative_volume_error']<1e-4


def test_local_modifiers_survive_real_slicer():
    report=json.loads((a.OUT/'OFFLINE_SLICE_AUDIT.json').read_text())
    assert not report['printer_commands_sent']
    assert len(report['results'])==20
    for row in report['results']:
        f=a.OUT/'SLICER_3MF'/(row['part']+'.3mf')
        assert hashlib.sha256(f.read_bytes()).hexdigest()==row['input_sha256']
        assert row['returncode']==row['roundtrip_returncode']==0
        assert row['modifiers_preserved'] and not row['warnings']
        assert all(all(int(v)==0 for v in m.values()) for m in row['mesh_repairs'])


def test_quantity_and_material_separation():
    assert len(MANIFEST)==20 and sum(r['qty_per_arm'] for r in MANIFEST)==45
    assert [r['qty_per_arm'] for r in MANIFEST if r['material']=='TPU_OR_CUT_SILICONE']==[3]
    assert not any('LOCKING-PIN' in r['part'] for r in MANIFEST)


def test_final_discrete_collision_audit():
    from cad.prototype_arm.validate_aero_v5 import source_hashes
    report=json.loads((a.OUT/'GEOMETRY_AUDIT.json').read_text())
    assert report['passed']
    for f,h in report['sources'].items():
        if f not in ['cad/prototype_arm/export_aero_v5.py','scripts/build_aero_v5_hardware.py']:
            assert source_hashes()[f]==h
    assert len(report['path'])==20 and len(report['gripper'])==11 and len(report['steering'])==13
    assert max(report['target_errors_mm'].values())<1e-6


def test_urdf_forward_kinematics_matches_cad():
    root=ET.parse(a.OUT/'URDF/AERO_V5_REVIEW.urdf').getroot()
    qs=[(0,-35,75,-40,0),(-90,-70,85,-15,-25),(0,-24,130,-106,25)]
    for q in qs:
        vals={n:math.radians(v) for n,v in zip(['J1','J2','J3','W1','G1'],q)}
        fs={'base':np.eye(4)}
        for j in root.findall('joint'):
            parent=j.find('parent').get('link');child=j.find('child').get('link')
            o=j.find('origin');xyz=np.fromstring(o.get('xyz'),sep=' ')*1000
            rpy=np.fromstring(o.get('rpy'),sep=' ');t=np.eye(4)
            t[:3,:3]=trimesh.transformations.euler_matrix(*rpy)[:3,:3];t[:3,3]=xyz
            axis=np.fromstring(j.find('axis').get('xyz'),sep=' ')
            if j.get('type')=='prismatic':
                m=j.find('mimic');val=vals[m.get('joint')]*float(m.get('multiplier'))+float(m.get('offset'))
                move=np.eye(4);move[:3,3]=axis*val*1000
            else:move=trimesh.transformations.rotation_matrix(vals[j.get('name')],axis)
            fs[child]=fs[parent]@t@move
        for frame,t in a.frames(q).items():assert np.allclose(t,fs[frame],atol=1e-8),frame
    mount=ET.parse(a.OUT/'URDF/ROVER_MOUNT_REVIEW.urdf').getroot().find("joint[@name='mount']/origin")
    assert np.allclose(np.fromstring(mount.get('xyz'),sep=' ')*1000,a.ROVER_BASE)


def test_unknown_cost_is_not_zero_and_no_new_motor_purchase():
    from scripts.build_aero_v5_hardware import main
    cost=main()
    assert cost['historical_existing_motor_allocation_TRY']=='1135.49'
    assert cost['total_build_cost_TRY'] is None and cost['unpriced_lines']>0
    assert not cost['new_motor_purchase_required'] and not cost['purchase_ledger_changed']
