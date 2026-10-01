import copy
import http.client
import json
import tempfile
import threading
import unittest
from unittest.mock import patch
from http.server import HTTPServer
from pathlib import Path
from software.st3215_test.target_receiver import ObservationStore, handler_for, validate


def sample():
    return dict(schema='figbot.target-observations.v2', arm_motion_authorized=False,
                coordinate_frame='base_link', units='millimetres',
                targets=[dict(confidence=.89, robot_x_mm=267.5, robot_y_mm=-2.9,
                              robot_z_mm=-69, depth_source='ARCORE_DEPTH_HIT')])


def sample_v3():
    return dict(sample(), schema='figbot.target-observations.v3',
                observation_status='RECENT_STATIONARY_SCENE',
                camera_tracking='TRACKING', association='STATIONARY_SCENE_APPROXIMATION',
                capture_age_ms_at_send=300, image_timestamp_ns=1000000000,
                depth_frame_timestamp_ns=1300000000)


class ReceiverTests(unittest.TestCase):
    def test_stream_staleness_and_unavailable_clears_target(self):
        with tempfile.TemporaryDirectory() as directory:
            store=ObservationStore(directory)
            with patch('software.st3215_test.target_receiver.time.time', return_value=100):
                record=store.accept(sample_v3())
                self.assertIn('NETWORK_DELAY_UNKNOWN', record['capture_freshness'])
                self.assertFalse(store.status()['stale_by_age'])
            with patch('software.st3215_test.target_receiver.time.time', return_value=101):
                self.assertTrue(store.status()['stale_by_age'])
                self.assertEqual(store.status()['capture_age_lower_bound_ms'], 1300)
            store.accept(dict(sample_v3(), observation_status='UNAVAILABLE_OR_STALE', targets=[]))
            self.assertEqual(store.latest['observation']['targets'], [])
            for changes in [dict(capture_age_ms_at_send=751), dict(capture_age_ms_at_send=True),
                            dict(camera_tracking='PAUSED'), dict(image_timestamp_ns=1400000000),
                            dict(observation_status='UNAVAILABLE_OR_STALE'), dict(extra=float('nan'))]:
                with self.subTest(changes=changes), self.assertRaises(ValueError):
                    store.accept(dict(sample_v3(), **changes))
            self.assertEqual(store.count, 2)
    def test_invalid_data_never_records(self):
        with tempfile.TemporaryDirectory() as directory:
            store = ObservationStore(directory)
            cases = [None, [], {}, dict(sample(), arm_motion_authorized=True),
                     dict(sample(), units='metres'), dict(sample(), targets=[None])]
            for field, value in [('robot_x_mm', float('nan')), ('confidence', True), ('confidence', 2)]:
                item = sample(); item['targets'][0][field] = value; cases.append(item)
            item = sample(); del item['targets'][0]['robot_z_mm']; cases.append(item)
            for payload in cases:
                with self.subTest(payload=payload), self.assertRaises(ValueError):
                    store.accept(payload)
            self.assertEqual(store.count, 0)
            self.assertIsNone(store.latest)

    def test_observation_not_motion_or_fresh_capture(self):
        with tempfile.TemporaryDirectory() as directory:
            store = ObservationStore(directory)
            record = store.accept(sample())
            self.assertFalse(record['motion_allowed'])
            self.assertIn('UNKNOWN', record['capture_freshness'])
            self.assertEqual(json.loads((Path(directory)/'phone_latest.json').read_text()), record)
            self.assertEqual(len(store.log.read_text().splitlines()), 1)
            self.assertGreaterEqual(store.status()['receive_age_seconds'], 0)

    def test_empty_or_no_xyz_is_still_an_observation(self):
        for targets in ([], [dict(confidence=.5)]):
            validate(dict(sample(), targets=targets))

    def test_http_post_status_and_rejections(self):
        with tempfile.TemporaryDirectory() as directory:
            store = ObservationStore(directory)
            server = HTTPServer(('127.0.0.1', 0), handler_for(store))
            thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
            try:
                conn = http.client.HTTPConnection(*server.server_address, timeout=3)
                conn.request('POST', '/api/targets', json.dumps(sample()))
                response = conn.getresponse(); body = json.loads(response.read())
                self.assertEqual(response.status, 200); self.assertFalse(body['motion_allowed'])
                conn.request('GET', '/api/status')
                response = conn.getresponse(); self.assertEqual(json.loads(response.read())['received_count'], 1)
                conn.request('POST', '/api/targets', json.dumps(dict(sample(), arm_motion_authorized=True)))
                response = conn.getresponse(); response.read(); self.assertEqual(response.status, 400)
                conn.request('POST', '/api/targets', '', headers={'Content-Length':'65537'})
                response = conn.getresponse(); response.read(); self.assertEqual(response.status, 413)
                self.assertEqual(store.count, 1)
                conn.close()
            finally:
                server.shutdown(); server.server_close(); thread.join()
