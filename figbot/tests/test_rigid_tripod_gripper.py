"""DEC-084: topology, linkage closure, evidence and stock constraints."""
import json,math
import numpy as np
import pytest
import trimesh
from cad.prototype_arm import rigid_tripod_gripper as g
from scripts.export_rigid_tripod import PARTS,procurement
# Historical CAD regression reads the SHA-verified archive; current outputs are DEC-086.
from scripts.project_paths import ARCHIVE
import tempfile,zipfile,hashlib
from pathlib import Path
_archive_tmp=tempfile.TemporaryDirectory(prefix='figbot_dec084_')
OUT=Path(_archive_tmp.name)
with zipfile.ZipFile(ARCHIVE) as z:
    candidates=[n for n in z.namelist() if n.endswith('/CAD/TUTUCU/LINKA_L1_TRIPOD_OPEN.glb')]
    prefix=candidates[-1].rsplit('LINKA_L1_TRIPOD_OPEN.glb',1)[0]
    root_prefix=prefix.split('CAD/TUTUCU/')[0]
    verified=json.loads(z.read(root_prefix+'SNAPSHOT_SHA256.json'))
    for n in z.namelist():
        if n.startswith(prefix) and not n.endswith('/'):
            data=z.read(n)
            assert hashlib.sha256(data).hexdigest()==verified[n[len(root_prefix):]]
            dest=OUT/n[len(prefix):];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)



def test_linkage_closes_without_a_toggle_and_has_monotonic_stroke():
    states=[g.state(v) for v in np.linspace(0,g.OPEN,101)]
    for s in states:assert np.linalg.norm(s['crank']-s['slider'])==pytest.approx(g.LINK,abs=1e-9)
    z=np.array([s['slider'][2] for s in states])
    assert np.all(np.diff(z)>.03)
    assert (z[-1]-z[0])==pytest.approx(7.77171582,abs=1e-6)
    assert abs(states[-1]['gear_deg'])<30


def test_built_parts_are_single_connected_manifold_solids():
    for pid in PARTS:
        m=trimesh.load_mesh(OUT/'PROTOTIP_STL'/f'{pid}.stl',process=True)
        assert m.is_watertight and m.is_winding_consistent,pid
        assert len(m.split())==1,pid
    assert len(g.frame().val().Solids())==1


def test_final_audit_samples_all_parts_through_stroke():
    data=json.loads((OUT/'AUDIT.json').read_text())
    assert len(data['poses'])==11
    assert data['poses'][0]['angle']==0 and data['poses'][-1]['angle']==g.OPEN
    assert all(not p['hits'] for p in data['poses'])
    assert all(v['valid'] and v['count']==1 for v in data['solids'].values())


def test_a_defined_open_pose_assembly_sequence_has_clear_sampled_paths():
    data=json.loads((OUT/'SERVICE.json').read_text())
    for path in ['motor_axial_before_gears','rack_side_entry_before_gear','gear_side_entry_with_rack','guide_-1','guide_1']:
        assert all(step['collision_mm3']<1e-4 for step in data[path]),path


def test_new_usage_fits_previous_list_but_inventory_is_not_claimed():
    p=procurement()
    assert len(p['rows'])==4
    assert p['additional_buy_cost_if_list_was_bought_try']==0
    assert p['actual_buy_cost_try'] is None
    assert all(r['new_required']<=r['previous_buy_quantity'] and r['actual_owned']=='UNVERIFIED' for r in p['rows'])


def test_exported_motion_tree_has_explicit_loop_and_is_not_a_print_release():
    status=json.loads((OUT/'STATUS.json').read_text())
    assert status['print_release'] is False
    loop=json.loads((OUT/'URDF/CLOSED_LOOP.json').read_text())
    assert len(loop['states'])==101
    assert max(s['closure_error_mm'] for s in loop['states'])<1e-8
    for key in ['TRIPOD_ARM','TRIPOD_OPEN','TRIPOD_CLOSED','TRIPOD_SERVICE']:
        assert (OUT/f'LINKA_L1_{key}.glb').stat().st_size>1000
        assert (OUT/f'{key}.png').stat().st_size>1000


def test_nominal_arm_interface_has_no_reported_interference():
    report=json.loads((OUT/'ARM_INTERFACE.json').read_text())
    assert report['pose']==[0,-60,95,-35]
    assert report['hits']==[]
    assert (OUT/'ARM_REVIEW/URDF/LINKA_L1_REVIEW.urdf').exists()


def test_publisher_distinguishes_existing_prints_from_new_review():
    from scripts.project_paths import CURRENT
    status=json.loads((CURRENT/'SURUM.json').read_text())
    assert status['revision']=='DEC-086'
    assert status['design_review']['print_release'] is False
    for filename in ['BASLA_BURADAN.md','BASKI/ONCE_BUNU_OKU.md']:
        assert '07,08 ve10' in (CURRENT/filename).read_text(encoding='utf-8')
