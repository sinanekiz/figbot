"""Regressions for measured, bounded jaw opening during basket approach.

These tests use a fake bus only. Encoder feedback deliberately differs from
the planned path in delayed-arrival cases, so a time-only release cannot pass.
"""
import unittest
from dataclasses import replace

import numpy as np

from software.st3215_test.arm_control import ArmControl
from software.st3215_test.protocol import BusError
from tests.test_smooth_path import StreamBus


class ReleaseOverlapTests(unittest.TestCase):
    def setUp(self):
        self.bus = StreamBus()
        self.now = 0.
        self.control = ArmControl(self.bus, lambda: self.now)
        self.control.arm(True)
        self.now = 1.
        self.control.poll()
        self.bus.history.clear()
        self.closed = self.control.targets[6]
        self.opened = self.closed + 259

    def points(self, lead=.18):
        return [
            {'positions': {'2': 1300}, 'stream_seconds': .5,
             'release_gate': True, 'release_lead_seconds': lead},
            {'positions': {'6': self.opened}, 'stream_seconds': .38},
            {'positions': {'2': 1064}, 'stream_seconds': .5},
        ]

    def start(self, points=None):
        self.control.play_smooth(self.points() if points is None else points,
                                 True, curve_kind='quintic_c2')
        self.path = self.control.smooth_path
        self.started = self.now
        self.window = self.path.release_windows[0]

    def tick(self, elapsed, *, shoulder=None, shoulder_speed=None,
             passive_offset=0, jaw=None):
        self.now = self.started + elapsed
        offset = self.control.active['time_offset']
        phase = max(0., elapsed - offset)
        positions = self.path.sample(phase)
        velocities = self.path.curve(min(phase, self.path.duration), 1)
        for index, i in enumerate(self.path.ids):
            position = positions[i]
            speed = int(round(velocities[index]))
            if i == 2:
                if shoulder is not None:
                    position = shoulder
                if shoulder_speed is not None:
                    speed = shoulder_speed
            if i == 5:
                position += passive_offset
            if i == 6:
                position = self.control.targets[i] if jaw is None else jaw
                speed = 0
            self.bus.f[i] = replace(self.bus.f[i], position=position,
                                    speed=speed, moving=abs(speed) > 0)
        self.control.poll()

    def advance(self, elapsed, **feedback):
        while self.now - self.started < elapsed - 1e-9:
            next_time = min(elapsed, self.now - self.started + .02)
            self.tick(next_time, **feedback)

    def test_invalid_overlap_is_rejected_before_hardware_write(self):
        for lead in (0., -.1, .251, float('nan'), float('inf'), True, '0.18'):
            with self.subTest(lead=lead):
                with self.assertRaises(BusError):
                    self.control.play_smooth(self.points(lead), True)
                self.assertEqual(self.bus.history, [])

    def test_overlap_requires_release_gate_and_previous_approach_interval(self):
        cases = []
        without_gate = self.points()
        without_gate[0].pop('release_gate')
        cases.append(without_gate)
        longer_than_approach = self.points()
        longer_than_approach[0]['stream_seconds'] = .1
        cases.append(longer_than_approach)
        for points in cases:
            with self.subTest(points=points):
                with self.assertRaises(BusError):
                    self.control.play_smooth(points, True)
                self.assertEqual(self.bus.history, [])

    def test_physical_jaw_duration_includes_overlap_and_stays_bounded(self):
        self.start()
        w = self.window
        self.assertLess(w['start'], w['arrival'])
        self.assertLess(w['arrival'], w['end'])
        self.assertAlmostEqual(w['duration'], w['end'] - w['start'])
        self.assertAlmostEqual((w['arrival'] - w['start']) / w['duration'],
                               .18 / .56)
        self.assertEqual(w['closed'], self.closed)
        self.assertEqual(w['opened'], self.opened)
        jaw = [self.path.sample(t)[6]
               for t in np.linspace(w['start'], w['end'], 501)]
        self.assertEqual(jaw[0], self.closed)
        self.assertEqual(jaw[-1], self.opened)
        self.assertTrue(all(a <= b for a, b in zip(jaw, jaw[1:])))
        self.assertLessEqual(self.path.max_speed, 3400.0001)
        self.assertLessEqual(self.path.max_acceleration, 5000.0001)
        # A legacy 0.38s jaw spline would unnecessarily scale the whole path.
        # The valid 0.56s physical stroke must instead save real program time.
        self.assertLess(self.path.duration, 1.56)

    def test_lookahead_does_not_open_before_actual_approach_window(self):
        self.start()
        self.advance(self.window['start'] - .04)
        # Feedback can already be inside the proximity envelope, but the
        # 100ms lookahead must not arm a release before its actual time window.
        self.tick(self.window['start'] - .02,
                  shoulder=1280, shoulder_speed=100)
        self.assertEqual(self.control.targets[6], self.closed)
        self.assertEqual(self.control.active['release_started'], {})

    def test_measured_lag_keeps_jaws_closed_without_freezing_approach(self):
        self.start()
        self.advance(self.window['start'] - .01)
        before = self.control.targets[2]
        self.advance(self.window['arrival'] - .01,
                     shoulder=1210, shoulder_speed=100)
        self.assertEqual(self.control.active['time_offset'], 0.)
        self.advance(self.window['arrival'] + .08,
                     shoulder=1210, shoulder_speed=100)
        self.assertEqual(self.control.targets[6], self.closed)
        self.assertEqual(self.control.active['release_started'], {})
        self.assertGreater(self.control.targets[2], before)
        self.assertEqual(self.control.targets[2], 1300)
        self.assertEqual(self.control.state, 'MOVING')

    def test_passive_axis_drift_and_motion_away_cannot_arm_release(self):
        for feedback in (
                {'shoulder': 1260, 'shoulder_speed': -150},
                {'shoulder': 1280, 'shoulder_speed': 150,
                 'passive_offset': 25}):
            with self.subTest(feedback=feedback):
                self.setUp()
                self.start()
                self.advance(self.window['start'] - .01)
                self.advance(self.window['start'] + .06, **feedback)
                self.assertEqual(self.control.targets[6], self.closed)
                self.assertEqual(self.control.active['release_started'], {})

    def test_arm_and_jaws_change_in_same_broadcast_while_approaching(self):
        self.start()
        self.advance(self.window['start'] - .01)
        self.bus.history.clear()
        self.advance(self.window['arrival'] - .02)
        self.assertGreater(self.control.targets[6], self.closed)
        self.assertTrue(any(kind == 'stream' and 2 in targets and 6 in targets
                            for kind, targets in self.bus.history))
        self.assertEqual(self.control.active['time_offset'], 0.)

    def test_late_gate_starts_jaw_ramp_without_nominal_catchup_jump(self):
        self.start()
        self.advance(self.window['start'] - .01)
        self.advance(self.window['arrival'] + .08,
                     shoulder=1210, shoulder_speed=100)
        armed_at = self.now - self.started + .02
        self.tick(armed_at, shoulder=1280, shoulder_speed=100)
        self.assertAlmostEqual(self.control.active['release_started'][0],
                               armed_at)
        # Even with the normal bounded lookahead, a newly armed stroke must
        # remain near its beginning rather than jump to the nominal 50%+ pose.
        self.assertLessEqual(self.control.targets[6] - self.closed, 30)
        self.advance(armed_at + .12)
        self.assertGreater(self.control.targets[6], self.closed)
        self.assertEqual(self.control.state, 'MOVING')

    def test_departure_waits_for_measured_jaw_open_after_overlap(self):
        self.start()
        self.advance(self.window['end'] - .1)
        # A modest real jaw lag is below the general tracking-error guard,
        # but must still prevent the arm departing with a retained object.
        self.advance(self.window['end'] + .08,
                     shoulder=1300, shoulder_speed=0,
                     jaw=self.opened - 45)
        self.assertEqual(self.control.targets[2], 1300)
        self.assertGreater(self.control.active['time_offset'], 0.)
        self.assertEqual(self.control.state, 'MOVING')
        self.tick(self.now - self.started + .02,
                  shoulder=1300, shoulder_speed=0, jaw=self.opened)
        self.advance(self.now - self.started + .08)
        self.assertLess(self.control.targets[2], 1300)

    def test_release_completion_uses_existing_arm_encoder_jitter_allowance(self):
        self.start()
        self.advance(self.window['end'] - .1)
        self.advance(self.window['end'] + .02,
                     shoulder=1321, shoulder_speed=0, jaw=self.opened)
        self.assertEqual(self.control.active['checkpoint_index'], 2)
        self.assertEqual(self.control.active['time_offset'], 0.)
        self.assertEqual(self.control.active['checkpoint_events'][-1]['phase'],
                         'release_complete')
        self.advance(self.now - self.started + .06)
        self.assertLess(self.control.targets[2], 1300)

    def test_second_cycle_requires_its_own_measured_release_start(self):
        points = self.points()
        points[2] = {'positions': {'2': 1064, '6': self.closed},
                     'stream_seconds': .7}
        points.extend(self.points())
        self.start(points)
        second = self.path.release_windows[1]
        while (self.now - self.started - self.control.active['time_offset']
               < second['start'] - .04):
            self.tick(self.now - self.started + .02)
        first_start = self.control.active['release_started'][0]
        self.assertNotIn(1, self.control.active['release_started'])
        self.assertEqual(self.control.targets[6], self.closed)
        self.advance(self.now - self.started + .10)
        self.assertIn(1, self.control.active['release_started'])
        self.assertEqual(self.control.active['release_started'][0], first_start)
        self.assertGreater(self.control.active['release_started'][1], first_start)


if __name__ == '__main__':
    unittest.main()
