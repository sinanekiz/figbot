import unittest
from pathlib import Path
import numpy as np
from software.st3215_test.so101_kinematics import SO101Model, encoder_to_angles
from software.st3215_test.reference_pose import reference_angles

URDF=Path(__file__).resolve().parents[1]/'references/vendor/so101/Simulation/SO101/so101_new_calib.urdf'

class KinematicsTests(unittest.TestCase):
    def setUp(self): self.model=SO101Model(URDF)

    def test_rigid_frames_and_vendor_base_joint(self):
        frames=self.model.forward([.2,-.3,.5,-.4,.1])
        np.testing.assert_allclose(frames['shoulder_pan'][:3,3],[.0388353,-8.97657e-9,.0624])
        for t in frames.values():
            np.testing.assert_allclose(t[:3,:3].T@t[:3,:3],np.eye(3),atol=1e-12)
            self.assertAlmostEqual(np.linalg.det(t[:3,:3]),1)

    def test_reference_pose_aligns_joint_centres(self):
        frames=self.model.forward(reference_angles())
        shoulder=frames['shoulder_lift'][:3,3]; elbow=frames['elbow_flex'][:3,3]; wrist=frames['wrist_flex'][:3,3]
        np.testing.assert_allclose(shoulder[:2],elbow[:2],atol=2e-6)
        self.assertAlmostEqual(elbow[2],wrist[2],places=5)

    def test_inverse_reproduces_reachable_target_and_axis(self):
        q=np.array([.3,-.4,.7,-.6,.2]); tip=self.model.forward(q)['gripper_frame']
        result=self.model.inverse(tip[:3,3],q+.06,tip[:3,2])
        self.assertTrue(result['geometric_solution'])
        self.assertLess(result['position_error_m'],1e-6)
        self.assertFalse(result['motion_authorized'])
        self.assertFalse(result['collision_checked'])

    def test_unreachable_and_invalid_targets(self):
        self.assertFalse(self.model.inverse([3,3,3],[0]*5)['geometric_solution'])
        for target in ([1,2],[float('nan'),0,0]):
            with self.assertRaises(ValueError): self.model.inverse(target,[0]*5)
        with self.assertRaises(ValueError): self.model.inverse([.2,0,.2],[0]*5,[0,0,0])

    def test_encoder_mapping_requires_explicit_sign_and_rejects_wrap(self):
        q=encoder_to_angles([2024]*5,[1000]*5,[0]*5,[1,-1,1,-1,1])
        np.testing.assert_allclose(q,np.array([1,-1,1,-1,1])*np.pi/2)
        with self.assertRaises(ValueError): encoder_to_angles([1]*5,[4000]*5,[0]*5,[1]*5)
        with self.assertRaises(ValueError): encoder_to_angles([1000]*5,[1000]*5,[0]*5,[0]*5)
