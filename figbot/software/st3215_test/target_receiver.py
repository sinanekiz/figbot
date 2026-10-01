"""Local, observation-only Android bridge. No serial or motor-control imports."""
import argparse
import json
import math
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


def validate(payload):
    if not isinstance(payload, dict):
        raise ValueError('JSON object required')
    if payload.get('schema') not in ('figbot.target-observations.v2', 'figbot.target-observations.v3'):
        raise ValueError('Unsupported schema')
    if payload.get('arm_motion_authorized') is not False:
        raise ValueError('Only observations with motion disabled are accepted')
    if payload.get('coordinate_frame') != 'base_link' or payload.get('units') != 'millimetres':
        raise ValueError('Expected base_link / millimetres')
    targets = payload.get('targets')
    if not isinstance(targets, list) or len(targets) > 100:
        raise ValueError('Invalid target list')
    if payload['schema'].endswith('.v3'):
        state = payload.get('observation_status')
        if state not in ('RECENT_STATIONARY_SCENE', 'UNAVAILABLE_OR_STALE'):
            raise ValueError('Missing observation status')
        if state == 'UNAVAILABLE_OR_STALE' and targets:
            raise ValueError('Unavailable observations must clear targets')
        if state == 'RECENT_STATIONARY_SCENE':
            age = payload.get('capture_age_ms_at_send')
            if type(age) not in (int, float) or not math.isfinite(age) or not 0 <= age <= 750:
                raise ValueError('Invalid or stale capture age')
            if payload.get('camera_tracking') != 'TRACKING' or payload.get('association') != 'STATIONARY_SCENE_APPROXIMATION':
                raise ValueError('Unsupported image-depth association')
            image_time, depth_time = (payload.get(k) for k in ('image_timestamp_ns', 'depth_frame_timestamp_ns'))
            if any(type(t) is not int or t <= 0 for t in (image_time, depth_time)) or not 0 <= depth_time-image_time <= 750_000_000:
                raise ValueError('Invalid image/depth timestamps')
    for target in targets:
        if not isinstance(target, dict):
            raise ValueError('Invalid target')
        keys = ('robot_x_mm', 'robot_y_mm', 'robot_z_mm')
        values = [target[k] for k in keys if k in target]
        if len(values) not in (0, 3):
            raise ValueError('Incomplete XYZ')
        for value in values + [target.get('confidence')]:
            if type(value) not in (int, float) or not math.isfinite(value):
                raise ValueError('Finite numeric observations required')
        if not 0 <= target['confidence'] <= 1:
            raise ValueError('Invalid confidence')
    json.dumps(payload, allow_nan=False)  # Reject non-finite metadata before any store mutation.
    return payload


class ObservationStore:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.latest = None
        self.count = 0
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        self.log = self.directory / ('phone_observations_' + stamp + '.jsonl')

    def accept(self, payload):
        validate(payload)
        freshness = 'UNKNOWN_V2_HAS_NO_CAPTURE_TIMESTAMP'
        if payload['schema'].endswith('.v3'):
            freshness = ('PHONE_REPORTS_RECENT_NETWORK_DELAY_UNKNOWN'
                         if payload['observation_status'] == 'RECENT_STATIONARY_SCENE'
                         else 'UNAVAILABLE_OR_STALE')
        record = dict(received_unix=time.time(), sequence=self.count + 1,
                      motion_allowed=False, capture_freshness=freshness,
                      physical_calibration='UNVERIFIED', observation=payload)
        encoded = json.dumps(record, ensure_ascii=False, allow_nan=False)
        with self.log.open('a', encoding='utf8') as stream:
            stream.write(encoded + '\n')
        temp = self.directory / 'phone_latest.tmp'
        temp.write_text(encoded, encoding='utf8')
        temp.replace(self.directory / 'phone_latest.json')
        self.count += 1
        self.latest = record
        return record

    def status(self):
        age = None if self.latest is None else time.time()-self.latest['received_unix']
        capture_lower_bound = None
        if self.latest is not None:
            sent_age = self.latest['observation'].get('capture_age_ms_at_send')
            if type(sent_age) in (int, float):
                capture_lower_bound = sent_age + max(0, age)*1000
        return dict(received_count=self.count, motion_allowed=False,
                    receive_age_seconds=age,
                    capture_age_lower_bound_ms=capture_lower_bound,
                    stale_by_age=capture_lower_bound is not None and capture_lower_bound > 750,
                    latest=self.latest)


def handler_for(store):
    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(3)

        def reply(self, code, payload):
            data = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode('utf8')
            self.send_response(code)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path not in ('/', '/api/status'):
                return self.reply(404, {'error': 'Not found'})
            self.reply(200, store.status())

        def do_POST(self):
            if self.path != '/api/targets':
                return self.reply(404, {'error': 'Not found'})
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 65536 or self.headers.get('Transfer-Encoding'):
                    return self.reply(413, {'error': 'Expected bounded Content-Length'})
                data = self.rfile.read(length)
                if len(data) != length:
                    raise ValueError('Incomplete body')
                payload = json.loads(data.decode('utf8'))
                record = store.accept(payload)
            except (ValueError, UnicodeError, TimeoutError) as error:
                return self.reply(400, {'error': str(error)})
            self.reply(200, {'received': record['sequence'], 'motion_allowed': False})

        def log_message(self, *args):
            pass
    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8872)
    parser.add_argument('--output', type=Path, default=Path(__file__).parent / 'KAYITLAR')
    args = parser.parse_args()
    store = ObservationStore(args.output)
    server = HTTPServer(('127.0.0.1', args.port), handler_for(store))
    print(f'Observation receiver: http://127.0.0.1:{args.port}/api/status', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
