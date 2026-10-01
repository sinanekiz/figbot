import math
import numpy as np
import pytest
from simulation import aero_v3_feasibility as f


def test_ballistic_range_and_height():
    # Independently known equal-height 45-degree solution R = v^2 / g.
    v=f.launch_speed(.5,0,45)
    assert v*v/f.G==pytest.approx(.5)
    assert f.ballistic_z(.5,v,45,.3)==pytest.approx(.3)
    v=f.launch_speed(.3,.1,35)
    assert f.ballistic_z(.3,v,35,.2)==pytest.approx(.3)
    with pytest.raises(ValueError):f.launch_speed(.3,.2,20)


def test_ik_reconstructs_wrist_in_si_units():
    for r,z in ((.22,.102),(.4,.102),(.22,.446)):
        q=f.ik(r,z);o,R=f.transforms(q)['tool']
        assert np.allclose(o+[0,0,.280],[r,0,z])
        assert np.allclose(R,np.eye(3))


def test_optical_axis_pitch_and_near_ground_blind_spot():
    p=f.CAM+np.array([math.cos(math.radians(35)),0,-math.sin(math.radians(35))])
    assert np.allclose(f.camera_angles(p,35),[0,0])
    h,v=f.camera_angles((.650,.415,0),0)
    assert h>51 and v>33.5
    h,v=f.camera_angles((.650,.415,0),35)
    assert abs(h)<51 and abs(v)<33.5


def test_rigid_body_gravity_and_inertia():
    bodies=f.load_bodies();q=f.ik(.27,.102);loaded=f.with_fruit(bodies,.1)
    M,t=f.mass_matrix(q,loaded)
    assert np.allclose(M,M.T,atol=1e-10)
    assert np.linalg.eigvalsh(M).min()>0
    # Independent prior CAD centre-of-mass sum from the print release.
    assert abs(t[1]/f.K)==pytest.approx(13.347,abs=.005)
    tau,gravity,_=f.torques(q,np.zeros(4),np.zeros(4),loaded)
    assert np.allclose(tau,gravity)
    assert abs(t[3]/f.K)<.03  # balanced statically, not a dynamic load guarantee
