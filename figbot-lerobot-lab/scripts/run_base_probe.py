"""Run only an already reviewed base probe; no automatic visual clearance."""
import argparse
import json
from pathlib import Path
import traceback
import urllib.request
from datetime import datetime, timezone

import serial
from figbot_lab.phone import adb, phone_frame
from figbot_lab.common import ROOT, save_json, lab_output
from figbot_lab.commission_pan import PanProbeBus, run_pan_probe, validate_review
from figbot_lab.commission_batch import BatchProbeBus, run_batch_probe


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--review', required=True)
    parser.add_argument('--batch', action='store_true')
    args = parser.parse_args()
    review_path = lab_output(args.review)
    root = review_path.parent
    review = json.loads(review_path.read_text(encoding='utf-8'))
    batch = getattr(args, 'batch', False)
    validate_review(review, expected_status=('CLEARED_FOR_SIX_JOINT_PROBE' if batch
                                            else 'CLEARED_FOR_SINGLE_BASE_PROBE'))
    if (root / 'probe_events.jsonl').exists() or (root / 'probe_result.json').exists():
        raise ValueError('A physical probe run cannot be repeated or overwritten.')
    base = 'http://127.0.0.1:8890'
    state = json.load(urllib.request.urlopen(base + '/api/state', timeout=3))
    connected = state['state'] == 'CONNECTED'
    if (state['state'] not in (('CONNECTED', 'FAULT') if batch else ('CONNECTED',)) or
            state['profile_verified'] or connected and (state['sample_age_s'] > .25 or
            any(m['torque'] != (review.get('torques', {}).get(k, state['motors']['1']['torque'] if k == '1' else 0)
                               if batch else 0) or m['moving'] or
                abs(m['position'] - review['positions'][k]) > 2 for k, m in state['motors'].items()))):
        raise ValueError('The existing serial owner must have the reviewed passive pose.')

    def action(route, value):
        request = urllib.request.Request(base + '/api/' + route, data=json.dumps(value).encode(),
                  headers={'Content-Type': 'application/json', 'Origin': base,
                           'X-Figbot-Token': state['token']})
        return json.load(urllib.request.urlopen(request, timeout=5))

    devices = [line.split()[0] for line in adb('devices').splitlines()[1:]
               if len(line.split()) >= 2 and line.split()[1] == 'device']
    if len(devices) != 1:
        raise ValueError('Exactly one connected camera phone is required.')
    phone = devices[0]
    port, connection, released, frames = None, None, False, 0
    generation, previous_capture = None, None
    result = {'status': 'NOT_STARTED', 'motor_commands_attempted': False}
    # Never overwrite an earlier physical execution's evidence.
    with (root / 'probe_events.jsonl').open('x', encoding='utf-8') as log:
        def event(value):
            if value['kind'].endswith('_attempt'):
                result['motor_commands_attempted'] = True
            log.write(json.dumps({'utc': datetime.now(timezone.utc).isoformat(), **value}) + '\n')
            log.flush()
            if value['kind'] in ('joint_completed', 'current_pose_hold_completed'):
                print(json.dumps({'progress': value['kind'], 'motor': value['motor']}), flush=True)

        def fresh_frame():
            nonlocal frames, generation, previous_capture
            data, _, meta = phone_frame('http://127.0.0.1:' + port + '/frame')
            if generation is not None and meta['generation'] != generation:
                raise ValueError('Camera session changed during the probe.')
            if previous_capture is not None and meta['capture_ns'] < previous_capture:
                raise ValueError('Camera capture clock moved backwards.')
            generation, previous_capture = meta['generation'], meta['capture_ns']
            (root / f'probe_frame_{frames:04d}.jpg').write_bytes(data)
            frames += 1
            return meta

        try:
            port = adb('-s', phone, 'forward', 'tcp:0', 'tcp:8874')
            if not port.isdigit():
                raise ValueError('Invalid temporary camera port.')
            fresh_frame()
            # The server is disconnected only after verifying its passive state.
            disconnected = action('disconnect', {})
            released = True
            if disconnected['state'] != 'DISCONNECTED':
                raise ValueError('Could not transfer exclusive serial ownership.')
            connection = serial.Serial('COM5', 1000000, timeout=.02, write_timeout=.2)
            if batch:
                result.update(run_batch_probe(BatchProbeBus(connection), review, fresh_frame, event=event))
            else:
                result.update(run_pan_probe(PanProbeBus(connection), review, fresh_frame, event=event))
        except Exception as exc:
            result.update(status='FAILED', error=str(exc), traceback=traceback.format_exc(),
                          physical_stop_confirmed=False)
        finally:
            if connection:
                connection.close()
            try:
                if port and port.isdigit():
                    adb('-s', phone, 'forward', '--remove', 'tcp:' + port)
            except Exception as exc:
                result['forward_cleanup_error'] = str(exc)
            if released:
                try:
                    restored = action('connect', {'port': 'COM5'})
                    result['restored_readonly_state'] = {k: v for k, v in restored.items() if k != 'token'}
                except Exception as exc:
                    result['reconnect_error'] = str(exc)
            result['frames'] = frames
            save_json(root / 'probe_result.json', result)
    print(json.dumps({k: v for k, v in result.items() if k != 'traceback'}))


if __name__ == '__main__':
    main()
