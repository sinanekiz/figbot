import math
import pytest
from scripts.arm_engineering_review import torque, solve, xz_rotate, quintic_duration, TARGETS, SHOULDER, budget_rows, evaluate, gripper_transmission

def test_gripper_force_and_torque_balance():
    r=gripper_transmission(50)
    assert r['normal_each_N']*3*.4==pytest.approx(.05*9.80665*1.5)
    assert r['motor_torque_kgfcm']*.0980665*.75/.005==pytest.approx(3*r['tendon_each_N'])
    assert gripper_transmission(100)['motor_torque_kgfcm']==pytest.approx(2*r['motor_torque_kgfcm'])
    assert gripper_transmission(50,efficiency=.5)['motor_torque_kgfcm']>r['motor_torque_kgfcm']

def test_rejected_design_cannot_be_repackaged_from_old_green_tests(tmp_path,monkeypatch):
    from scripts import package_forma_v6
    (tmp_path/'RELEASE_STATUS.json').write_text('{"allow_full_arm_package":false,"decision":"DEC-076"}')
    monkeypatch.setattr(package_forma_v6.a,'OUT',tmp_path)
    with pytest.raises(RuntimeError,match='DEC-076'):
        package_forma_v6.main()

def test_point_load_units_and_downstream_membership():
    # 100g at300mm from shoulder /100mm from elbow =>3 and1 kgf.cm.
    t=torque([], [0,0,0,0], (200,100), (0,0), 100, allowance_g=0)
    assert t==pytest.approx({'shoulder':3,'elbow':1,'wrist':0})

def test_vertical_arm_has_zero_gravity_moment():
    t=torque([], [0,-90,0,0], (200,100), (0,0), 100, allowance_g=0)
    assert max(t.values())<1e-12

@pytest.mark.parametrize('target',TARGETS.values())
def test_compact_candidate_inverse_forward_roundtrip(target):
    q=solve(target,150,120,30,-45)
    x,z=xz_rotate(150,0,q[1]); fx,fz=xz_rotate(120,0,q[1]+q[2])
    x+=fx+30;z+=fz-45
    y=math.radians(q[0])
    assert (SHOULDER[0]+x*math.cos(y),SHOULDER[1]+x*math.sin(y),SHOULDER[2]+z)==pytest.approx(target,abs=1e-8)

def test_unreachable_not_silently_clipped():
    assert solve((2000,415,20),150,120,30,-45) is None

def test_profile_bounds_against_sampled_derivatives():
    for d in (1,20,90,180):
        t=quintic_duration(d)
        for i in range(1001):
            u=i/1000
            assert abs(d/t*(30*u*u-60*u**3+30*u**4))<=30+1e-8
            assert abs(d/t**2*(60*u-180*u*u+120*u**3))<=60+1e-8

def test_more_payload_increases_horizontal_moments():
    a=evaluate(budget_rows(150,120),(150,120),(30,-45),50)
    b=evaluate(budget_rows(150,120),(150,120),(30,-45),100)
    assert b['horizontal_static_kgfcm']['shoulder']-a['horizontal_static_kgfcm']['shoulder']==pytest.approx(1.5)
    assert a['all_targets_reachable'] and a['collision_checked'] is False
