"""Offline contracts for endpoint-driven simultaneous arm trajectories."""
import copy
import hashlib
import json
import math
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from software.st3215_test.goal_route import build_goal_route
from software.st3215_test.protocol import BusError
from software.st3215_test.coordinated import validate_waypoints
from software.st3215_test.smooth_path import SmoothPath


class GoalRouteTests(unittest.TestCase):
    def setUp(self):
        # Measured poses, including small passive-roll recording noise.
        self.home = dict(zip(range(1, 7), [1971, 921, 3946, 2681, 3129, 791]))
        self.pickup = dict(zip(range(1, 7), [2308, 2871, 2337, 1864, 3127, 894]))
        self.basket = dict(zip(range(1, 7), [3363, 2177, 2602, 2593, 3125, 1153]))
        self.start = dict(self.home)

    def build(self, **kwargs):
        return build_goal_route(self.start, self.home, self.pickup, self.basket, **kwargs)

    def test_targets_repeat_then_return_home_without_changing_inputs(self):
        original = copy.deepcopy((self.start, self.home, self.pickup, self.basket))
        waypoints, metadata = self.build(cycles=2)
        self.assertTrue(metadata['goal_only'])
        self.assertEqual(metadata['speed_limit'], 1200)
        self.assertEqual(len(waypoints), 17)
        self.assertEqual((self.start, self.home, self.pickup, self.basket), original)
        for index in (1, 6, 11):
            for motor in (1, 2, 3, 4, 6):
                self.assertEqual(waypoints[index]['positions'][str(motor)], self.pickup[motor])
        for index in (4, 9, 14):
            for motor in (1, 2, 3, 4, 6):
                self.assertEqual(waypoints[index]['positions'][str(motor)], self.basket[motor])
        for motor in (1, 2, 3, 4, 6):
            self.assertEqual(waypoints[-1]['positions'][str(motor)], self.home[motor])
        self.assertTrue(all(w['positions']['5'] == self.start[5] for w in waypoints))

    def test_midpoints_are_generated_from_targets_and_clearance_only_on_transfer(self):
        waypoints, _ = self.build(cycles=1)
        legs = [(0, self.start, self.pickup, 0),
                (2, self.pickup, self.basket, 64),
                (5, self.basket, self.pickup, 64),
                (7, self.pickup, self.basket, 64),
                (10, self.basket, self.home, 0)]
        for index, start, end, clearance in legs:
            midpoint = waypoints[index]
            self.assertTrue(midpoint['goal_midpoint'])
            self.assertTrue(waypoints[index + 1]['goal_stop'])
            for motor in (1, 2, 3, 4):
                expected = round((start[motor] + end[motor]) / 2)
                if motor == 2:
                    expected -= clearance
                self.assertEqual(midpoint['positions'][str(motor)], expected)
        self.assertEqual(waypoints[0]['positions']['6'], self.basket[6])
        self.assertEqual(waypoints[5]['positions']['6'], self.basket[6])
        self.assertEqual(waypoints[2]['positions']['6'], self.pickup[6])
        self.assertEqual(waypoints[7]['positions']['6'], self.pickup[6])

    def test_release_remains_at_basket_with_approach_lead_and_measured_endpoints(self):
        waypoints, metadata = self.build(cycles=3, release_lead=.18, opening_seconds=.56)
        releases = [k for k, w in enumerate(waypoints) if w.get('release_gate')]
        self.assertEqual(len(releases), 4)
        for k in releases:
            closed, opened = waypoints[k], waypoints[k + 1]
            self.assertEqual(closed['positions']['6'], self.pickup[6])
            self.assertEqual(opened['positions']['6'], self.basket[6])
            self.assertAlmostEqual(closed['release_lead_seconds'], .18)
            self.assertAlmostEqual(opened['stream_seconds'], .38)
            for motor in (1, 2, 3, 4, 5):
                self.assertEqual(closed['positions'][str(motor)], opened['positions'][str(motor)])
        windows = metadata['harvest_windows']
        self.assertEqual(len(windows), 3)
        for window in windows:
            start, end = window['start_knot'], window['end_knot']
            self.assertLess(start, end)
            self.assertEqual(waypoints[start - 1]['positions'], waypoints[end - 1]['positions'])
            self.assertEqual(waypoints[end - 1]['positions']['6'], self.basket[6])
        self.assertTrue(all(a['end_knot'] == b['start_knot'] for a, b in zip(windows, windows[1:])))

    def test_zero_clearance_and_zero_release_lead_are_supported(self):
        waypoints, _ = self.build(clearance_counts=0, release_lead=0)
        for w in waypoints:
            if w.get('release_gate'):
                self.assertEqual(w.get('release_lead_seconds', 0), 0)
        self.assertEqual(waypoints[2]['positions']['2'], round((self.pickup[2] + self.basket[2]) / 2))

    def test_route_has_no_file_or_recorded_waypoint_dependency(self):
        with patch('builtins.open', side_effect=AssertionError('Unexpected file access')), \
                patch('pathlib.Path.read_text', side_effect=AssertionError('Unexpected text read')), \
                patch('pathlib.Path.read_bytes', side_effect=AssertionError('Unexpected bytes read')):
            waypoints, metadata = self.build()
        self.assertTrue(waypoints)
        self.assertTrue(metadata['goal_only'])
        self.assertFalse(any('sample' in w or 'gripper_sample' in w for w in waypoints))

    def test_finite_timing_grows_when_speed_or_acceleration_is_lowered(self):
        fast, _ = self.build()
        slow_speed, _ = self.build(speed_limit=800)
        slow_acceleration, _ = self.build(acceleration=10)
        duration = lambda route: sum(w['stream_seconds'] for w in route)
        self.assertGreater(duration(slow_speed), duration(fast))
        self.assertGreater(duration(slow_acceleration), duration(fast))
        for w in fast:
            self.assertTrue(math.isfinite(w['stream_seconds']))
            self.assertGreater(w['stream_seconds'], 0)
            self.assertEqual(w['seconds'], .25)
            self.assertEqual(set(w['positions']), set('123456'))
            self.assertTrue(all(type(p) is int and 0 <= p <= 4095 for p in w['positions'].values()))

    def test_invalid_motion_configuration_is_rejected(self):
        invalid = [dict(cycles=v) for v in (0, 4, True, 1.5)]
        invalid += [dict(speed_limit=v) for v in (0, 3401, float('nan'), float('inf'))]
        invalid += [dict(home_joint_speed_limit=v) for v in (0, 3401, True, 1.5, float('nan'), float('inf'))]
        invalid += [dict(acceleration=v) for v in (0, 151, True, 1.5)]
        invalid += [dict(clearance_counts=v) for v in (-1, 65, True, 1.5)]
        invalid += [dict(release_lead=v) for v in (-.01, .251, float('nan'), float('inf'))]
        invalid += [dict(opening_seconds=v) for v in (0, .18, float('nan'), float('inf'))]
        for kwargs in invalid:
            with self.subTest(kwargs=kwargs), self.assertRaises((BusError, ValueError)):
                self.build(**kwargs)

    def test_invalid_pose_shape_and_encoder_values_are_rejected(self):
        for name in ('start', 'home', 'pickup', 'basket'):
            for mutation in ('missing', 'extra', 'string_key', 'negative', 'overflow', 'float', 'bool'):
                poses = {k: dict(getattr(self, k)) for k in ('start', 'home', 'pickup', 'basket')}
                pose = poses[name]
                if mutation == 'missing':
                    del pose[6]
                elif mutation == 'extra':
                    pose[7] = 1000
                elif mutation == 'string_key':
                    pose['1'] = pose.pop(1)
                else:
                    pose[2] = {'negative': -1, 'overflow': 4096, 'float': 1000.0, 'bool': True}[mutation]
                with self.subTest(pose=name, mutation=mutation), self.assertRaises((BusError, ValueError)):
                    build_goal_route(**poses)

    def test_single_goal_motion_does_not_slow_at_generated_midpoint(self):
        waypoints, _ = self.build(clearance_counts=0)
        envelopes = {i: (0, 4095) for i in range(1, 7)}
        validated = validate_waypoints(waypoints, self.start, envelopes, 50, continuous=True)
        path = SmoothPath(self.start, validated, 50, curve_kind='quintic_c2')
        for k, waypoint in enumerate(waypoints, 1):
            if waypoint.get('goal_midpoint'):
                start_time, mid_time, end_time = path.times[k - 1:k + 2]
                duration = end_time - start_time
                delta = path.curve(end_time)[:4] - path.curve(start_time)[:4]
                np.testing.assert_allclose(path.curve(mid_time, 1)[:4], 1.875 * delta / duration, atol=1e-7)
                # One shared time law drives all four axes concurrently.
                for fraction in (.1, .3, .7, .9):
                    u = 10 * fraction ** 3 - 15 * fraction ** 4 + 6 * fraction ** 5
                    expected = path.curve(start_time)[:4] + u * delta
                    np.testing.assert_allclose(path.curve(start_time + duration * fraction)[:4], expected, atol=.51)
            if waypoint.get('goal_stop'):
                np.testing.assert_allclose(path.curve(path.times[k], 1)[:5], 0, atol=1e-7)

    def test_generated_clearance_path_preserves_c2_and_motor_limits(self):
        waypoints, metadata = self.build()
        envelopes = {i: (min(self.start[i], self.home[i], self.pickup[i], self.basket[i]),
                         max(self.start[i], self.home[i], self.pickup[i], self.basket[i]))
                     for i in range(1, 7)}
        plan = validate_waypoints(waypoints, self.start, envelopes, 50, continuous=True)
        path = SmoothPath(self.start, plan, 50, curve_kind='quintic_c2')
        self.assertEqual(len(path.release_windows), len(metadata['harvest_windows']) + 1)
        self.assertLessEqual(path.max_speed, 3400.0001)
        self.assertLessEqual(path.max_acceleration, 5000.0001)
        for k in range(1, len(path.times) - 1):
            t = path.times[k]
            np.testing.assert_allclose(path.curve(t - 1e-7, 1)[:5], path.curve(t + 1e-7, 1)[:5], atol=.01)
            np.testing.assert_allclose(path.curve(t - 1e-7, 2)[:5], path.curve(t + 1e-7, 2)[:5], atol=.1)
        values = path.curve(np.linspace(0, path.duration, 2001))
        for j, motor in enumerate(path.ids):
            self.assertGreaterEqual(values[:, j].min(), envelopes[motor][0] - 1e-6)
            self.assertLessEqual(values[:, j].max(), envelopes[motor][1] + 1e-6)
        np.testing.assert_allclose(values[:, path.ids.index(5)], self.start[5], atol=1e-6)

    def test_home_joint_cap_changes_only_initial_and_final_leg_timing(self):
        limited, metadata = self.build()
        unrestricted, _ = self.build(home_joint_speed_limit=3400)
        self.assertEqual(metadata['home_joint_speed_limit'], 1000)
        self.assertEqual(limited[2:-2], unrestricted[2:-2])
        for index in (0, 1, len(limited) - 2, len(limited) - 1):
            self.assertEqual(limited[index]['positions'], unrestricted[index]['positions'])
            self.assertGreater(limited[index]['stream_seconds'], unrestricted[index]['stream_seconds'])
        self.assertEqual([g['home_leg'] for g in metadata['generated_legs']],
                         [True, False, False, False, False, False, True])
        for cap in (800, 1000):
            waypoints, _ = self.build(home_joint_speed_limit=cap)
            plan = validate_waypoints(waypoints, self.start, {i: (0, 4095) for i in self.start}, 50, continuous=True)
            path = SmoothPath(self.start, plan, 50, curve_kind='quintic_c2')
            for first, last in ((0, 2), (len(waypoints) - 2, len(waypoints))):
                velocity = path.curve(np.linspace(path.times[first], path.times[last], 10001), 1)
                self.assertLessEqual(np.abs(velocity[:, 1:3]).max(), cap + .01)

    def test_recorded_target_adapter_passes_home_joint_cap(self):
        from software.st3215_test.arm_control import ArmControl
        from software.st3215_test.teaching import TeachingRecorder
        from software.st3215_test.taught_replay import prepare_replay
        from tests.test_arm_control import FakeBus

        with tempfile.TemporaryDirectory() as folder:
            control = ArmControl(FakeBus())
            recorder = TeachingRecorder(folder)
            recorder.start(control)
            recorder.sample(control.read_all())
            recorder.stop()
            path = Path(folder) / 'replay_plan.json'
            plan = dict(recording=recorder.path.name,
                        recording_sha256=hashlib.sha256(recorder.path.read_bytes()).hexdigest(),
                        start_sample=0, route_mode='direct_goals',
                        goal_route=dict(pickup_sample=0, basket_sample=1, home_joint_speed_limit=777))
            path.write_text(json.dumps(plan), encoding='utf-8')
            with patch('software.st3215_test.goal_route.build_goal_route', return_value=([], {})) as builder:
                prepare_replay(path, control)
                self.assertEqual(builder.call_args.kwargs['home_joint_speed_limit'], 777)
                self.assertEqual(builder.call_args.kwargs['speed_limit'], 1200)
                del plan['goal_route']['home_joint_speed_limit']
                plan['goal_route']['speed_limit'] = 1250
                path.write_text(json.dumps(plan), encoding='utf-8')
                prepare_replay(path, control)
                self.assertEqual(builder.call_args.kwargs['home_joint_speed_limit'], 1000)
                self.assertEqual(builder.call_args.kwargs['speed_limit'], 1250)


if __name__ == '__main__':
    unittest.main()
