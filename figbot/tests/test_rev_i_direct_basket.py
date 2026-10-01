"""Geometry-study gates; do not certify an actuator or printed assembly."""
import math
import xml.etree.ElementTree as ET

import numpy as np
import pytest
import trimesh

from cad.rover import build_rev_i_direct_basket as arm


def test_ik_reaches_fruit_targets_and_mirrors_two_lanes():
    for target in arm.TARGETS.values():
        q=arm.solve(target)
        assert np.allclose(arm.joints(q)[-1],target,atol=1e-7)
        assert np.allclose(arm.joints(q,-1)[-1],np.array(target)*[1,-1,1],atol=1e-7)
        assert q[1]+q[2]+q[3]==pytest.approx(0)
    with pytest.raises(ValueError):arm.solve((2000,415,20))


def test_joint_excursions_fit_an_180_degree_interval_without_claiming_registration():
    sampled=np.array([q for _,_,q in arm.sampled_path()])
    assert np.all(np.ptp(sampled,axis=0)<180)
    assert np.ptp(sampled[:,0])>90  # Side transfer actually needs base yaw.


def test_motor_inventory_and_closed_hollow_links():
    items=arm.local_arm()
    assert sum(p.group=='servo' and 'MG996R' in p.name for p in items)==4
    assert sum(p.group=='servo' and 'MG90S' in p.name for p in items)==2
    for p in items:
        assert p.shape.val().isValid(),p.name
        assert p.shape.val().Volume()>0,p.name
    tube=arm.ellipse_tube(100)
    solid_volume=math.pi*12*15*100
    assert 0<tube.val().Volume()<solid_volume*.35


def test_wheel_side_entry_floor_is_above_tire_and_slopes_toward_rear():
    assert arm.floor_z(290)-5>254
    assert arm.wing_z(510)>arm.wing_z(320)
    assert arm.wing_z(320)==arm.floor_z(320)
    target=arm.TARGETS['release']
    assert target[2]-arm.FRUIT_RADIUS-arm.wing_z(target[0])>0


@pytest.fixture(scope='module')
def path_review():return arm.audit_path(steps=10)


def test_sampled_route_clears_vehicle_and_flat_ground(path_review):
    assert len(path_review)==44
    assert all(not p['collisions_mm3'] for p in path_review)
    assert min(p['min_moving_z_mm'] for p in path_review)>0
    assert min(p['fruit_bottom_z_mm'] for p in path_review)>=-1e-7


def test_front_tire_steering_samples_clear_new_stationary_geometry():
    samples=arm.steering_audit()
    assert all(not p['collisions_mm3'] for p in samples)
    assert min(p['min_new_geometry_gap_mm'] for p in samples)>0


def test_payload_static_moment_matches_horizontal_lever():
    q=arm.solve(arm.TARGETS['pickup'])
    zero=arm.gravity(q,0);loaded=arm.gravity(q,100)
    sh,_,_,fruit=arm.joints(q)
    expected=np.linalg.norm((fruit-sh)[:2])/10*.1
    assert loaded['shoulder']-zero['shoulder']==pytest.approx(expected,abs=1e-4)


def test_review_exports_and_urdf_are_present_with_correct_units():
    for pose in ('pickup','release'):
        assert (arm.OUT/f'{pose}.step').stat().st_size>1000
        scene=trimesh.load(arm.OUT/f'{pose}.glb',force='scene')
        assert len(scene.geometry)>10
    folder=arm.OUT/'urdf'
    robot=ET.parse(folder/'REV_I_INSPECTION.urdf').getroot()
    assert all(j.attrib['type']=='fixed' for j in robot.findall('joint'))
    for mesh in robot.findall('.//mesh'):
        assert mesh.attrib['scale']=='0.001 0.001 0.001'
        assert (folder/mesh.attrib['filename']).stat().st_size>1000
