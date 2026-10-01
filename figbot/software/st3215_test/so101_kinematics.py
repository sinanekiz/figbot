"""SO-101 geometry calculations only. No serial, torque, or movement functions.

URDF joint limits describe the model, not collision-free hardware travel.
All positions are metres and all joint angles radians.
"""
from pathlib import Path
import hashlib
import xml.etree.ElementTree as ET
import numpy as np
from scipy.optimize import least_squares

JOINT_NAMES = ('shoulder_pan', 'shoulder_lift', 'elbow_flex', 'wrist_flex', 'wrist_roll')


def rotation(axis, angle):
    axis = np.asarray(axis, dtype=float)
    axis = axis / np.linalg.norm(axis)
    x, y, z = axis
    k = np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]])
    return np.eye(3) + np.sin(angle)*k + (1-np.cos(angle))*(k@k)


def origin_transform(element):
    t = np.eye(4)
    if element is None:
        return t
    t[:3, 3] = [float(x) for x in element.get('xyz', '0 0 0').split()]
    r, p, y = [float(x) for x in element.get('rpy', '0 0 0').split()]
    t[:3, :3] = rotation([0,0,1],y)@rotation([0,1,0],p)@rotation([1,0,0],r)
    return t


class SO101Model:
    def __init__(self, urdf):
        self.path = Path(urdf)
        self.sha256 = hashlib.sha256(self.path.read_bytes()).hexdigest()
        root = ET.parse(self.path).getroot()
        joints = {j.get('name'): j for j in root.findall('joint')}
        self.steps = []
        self.limits = []
        parent = 'base_link'
        for name in JOINT_NAMES:
            j = joints[name]
            if j.find('parent').get('link') != parent:
                raise ValueError('Unexpected SO101 chain')
            parent = j.find('child').get('link')
            axis = np.array([float(x) for x in j.find('axis').get('xyz').split()])
            self.steps.append((origin_transform(j.find('origin')), axis))
            limit = j.find('limit')
            self.limits.append([float(limit.get('lower')), float(limit.get('upper'))])
        tip = joints['gripper_frame_joint']
        if tip.get('type') != 'fixed' or tip.find('parent').get('link') != parent:
            raise ValueError('Unexpected gripper frame')
        self.tip = origin_transform(tip.find('origin'))
        self.limits = np.array(self.limits)

    def forward(self, angles):
        q = np.asarray(angles, dtype=float)
        if q.shape != (5,) or not np.isfinite(q).all():
            raise ValueError('Five finite joint angles required')
        t = np.eye(4)
        frames = {}
        for name, (base, axis), angle in zip(JOINT_NAMES, self.steps, q):
            t = t@base
            turn = np.eye(4); turn[:3,:3] = rotation(axis, angle)
            t = t@turn
            frames[name] = t.copy()
        frames['gripper_frame'] = t@self.tip
        return frames

    def inverse(self, target_m, seed, approach_axis=None, tolerance_m=0.002):
        target = np.asarray(target_m, dtype=float)
        q0 = np.asarray(seed, dtype=float)
        if target.shape != (3,) or not np.isfinite(target).all() or q0.shape != (5,) or not np.isfinite(q0).all():
            raise ValueError('Finite target and seed required')
        if not 0 < tolerance_m <= 0.01:
            raise ValueError('Invalid tolerance')
        direction = None
        if approach_axis is not None:
            direction = np.asarray(approach_axis,dtype=float)
            if direction.shape != (3,) or not np.isfinite(direction).all() or np.linalg.norm(direction)<1e-9:
                raise ValueError('Invalid approach axis')
            direction = direction/np.linalg.norm(direction)
        def residual(q):
            t = self.forward(q)['gripper_frame']
            parts = [t[:3,3]-target]
            if direction is not None:
                parts.append(0.1*(t[:3,2]-direction))
            return np.concatenate(parts)
        result = least_squares(residual, np.clip(q0,self.limits[:,0],self.limits[:,1]),
                               bounds=(self.limits[:,0],self.limits[:,1]), max_nfev=300,
                               ftol=1e-10, xtol=1e-10, gtol=1e-10)
        tip = self.forward(result.x)['gripper_frame']
        error = float(np.linalg.norm(tip[:3,3]-target))
        axis_error = None if direction is None else float(np.arccos(np.clip(tip[:3,2]@direction,-1,1)))
        return dict(joint_radians=result.x.tolist(), position_error_m=error,
                    approach_error_radians=axis_error,
                    geometric_solution=bool(result.success and error<=tolerance_m and (axis_error is None or axis_error<0.035)),
                    collision_checked=False, hardware_calibrated=False, motion_authorized=False)


def encoder_to_angles(raw, reference_raw, reference_angles, signs):
    """Explicit local branch only; no implicit wrap or assumed motor mounting direction."""
    arrays = [np.asarray(v, dtype=float) for v in (raw, reference_raw, reference_angles, signs)]
    if any(a.shape != (5,) or not np.isfinite(a).all() for a in arrays):
        raise ValueError('Five measured entries required for each calibration field')
    current, ref, qref, direction = arrays
    if not np.isin(direction,[-1,1]).all():
        raise ValueError('Motor directions must be established')
    if ((current<0)|(current>4095)|(ref<0)|(ref>4095)).any():
        raise ValueError('Encoder out of range')
    delta = current-ref
    if (np.abs(delta)>=2048).any():
        raise ValueError('Encoder branch is ambiguous; no automatic wrap')
    return qref+direction*delta*(2*np.pi/4096)
