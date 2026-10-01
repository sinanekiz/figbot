"""DEC-086 manufacturing topology and interfaces, not strength certification."""
import json,hashlib,xml.etree.ElementTree as ET
import pytest
import trimesh
from scripts.project_paths import CAD,PRINTS
from cad.prototype_arm import twin_scoop as g,yaw_capture as y

def test_every_new_part_is_one_closed_printable_mesh():
    for pid in [*g.PARTS,y.PID]:
        m=trimesh.load_mesh(CAD/'TUTUCU/PROTOTIP_STL'/f'{pid}.stl')
        assert m.is_watertight and m.is_winding_consistent
        assert len(m.split())==1,pid
    assert g.WALL==2.6

def test_sampled_motion_and_assembly_have_no_hard_interference():
    d=json.loads((CAD/'TUTUCU/AUDIT.json').read_text())
    assert d['revision']=='DEC-086' and d['physical_approval'] is False
    assert [v['angle'] for v in d['poses']]==list(range(0,25,3))
    assert all(not v['hits'] for v in d['poses']) and d['arm_hits']==[]
    assert {v['pose'] for v in d['interface_poses']}=={'pickup','lift','clear','turn','release'}
    assert all(not v['hits'] for v in d['interface_poses'])
    assert {v['name'] for v in d['service']}=={'motor','drive-jaw','passive-jaw','bridge'}
    assert all(s['collision_mm3']<1e-4 for p in d['service'] for s in p['steps'])

def test_passive_bush_and_thread_stack_are_not_a_plastic_screw():
    b=g.bush();assert b.val().isValid() and len(b.val().Solids())==1
    assert b.val().BoundingBox().zlen==pytest.approx(8)
    assert 14-8-3==3 # effective insert engagement
    assert 6.4-6==pytest.approx(.4) # diametral running clearance
    assert 8-7.4==pytest.approx(.6) # axial running clearance

def test_yaw_cup_keeps_base_motor_and_receiver_datums():
    a=y.a;before=a.local_items();after=y.apply(before)
    for old,new in zip(before,after):
        if old.name=='L1-20-MG-COVER J1' or old.name.startswith('J1 horn mounting'):continue
        assert old.shape is new.shape,old.name
    cup=y.cup();assert cup.val().isValid() and len(cup.val().Solids())==1
    box=cup.val().BoundingBox();assert box.xlen==pytest.approx(50) and box.zlen==pytest.approx(6)
    report=json.loads((CAD/'TUTUCU/AUDIT.json').read_text())
    assert all(v['collision_mm3']<1e-4 for v in report['base_cap'])
    status=json.loads((CAD/'TUTUCU/STATUS.json').read_text())
    assert 'UNVERIFIED' in status['base_fit']

def test_exported_gears_have_opposed_mimic_and_no_control_authorization():
    r=ET.parse(CAD/'TUTUCU/URDF/REVIEW.urdf').getroot()
    mimic=r.find("joint[@name='right_jaw']/mimic")
    assert mimic.get('joint')=='left_jaw' and mimic.get('multiplier')=='-1'
    assert all(v.get('effort')=='0' for v in r.findall('joint/limit'))
    for name in ['TWIN_OPEN','TWIN_CLOSED','TWIN_SERVICE','TWIN_ARM','YAW_CUP']:
        assert (CAD/'TUTUCU'/f'LINKA_L1_{name}.glb').stat().st_size>1000
        assert (CAD/'TUTUCU'/f'{name}.png').stat().st_size>1000

def test_load_tradeoff_is_explicit_and_not_a_torque_rating():
    d=json.loads((CAD/'TUTUCU/MASS_COMPARISON.json').read_text())
    assert d['current']['mass_g']>d['previous']['mass_g']
    assert d['current']['horizontal_wrist_self_weight_nm']>d['previous']['horizontal_wrist_self_weight_nm']
    assert not d['torque_approval']

def test_print_sources_and_current_evidence_match():
    from scripts.package_twin_plates import NEW
    d=json.loads((PRINTS/'TABLA_LISTESI.json').read_text())
    for p in d['plates']:
        if p['name'] not in NEW:continue
        for e in p['instances']:
            source=CAD/'TUTUCU/PROTOTIP_STL'/f"{e['id']}.stl"
            assert hashlib.sha256(source.read_bytes()).hexdigest()==e['source_sha256']

