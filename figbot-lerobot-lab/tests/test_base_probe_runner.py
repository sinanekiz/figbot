import io
import json
from pathlib import Path
import runpy
from types import SimpleNamespace
import pytest

from figbot_lab.common import ROOT


@pytest.fixture
def runner(monkeypatch, tmp_path):
    source = runpy.run_path(str(ROOT / 'scripts/run_base_probe.py'))
    main = source['main']
    scope = main.__globals__
    review = tmp_path / 'probe_review.json'
    review.write_text(json.dumps({'positions': {str(i): 2100 for i in range(1, 7)}}))
    calls, mode = [], {'probe_error': False, 'frame_error': False}
    monkeypatch.setattr(scope['argparse'].ArgumentParser, 'parse_args',
                        lambda self: SimpleNamespace(review=str(review)))
    scope['lab_output'] = lambda p: Path(p)
    scope['validate_review'] = lambda r, **kwargs: None
    def http(request, **kwargs):
        route = request if isinstance(request, str) else request.full_url
        route = route.rsplit('/', 1)[-1]
        calls.append(route)
        if route == 'state':
            state = {'state': 'CONNECTED', 'profile_verified': False, 'sample_age_s': 0,
                     'token': 'test-secret', 'motors': {str(i): {'position': 2100,
                       'torque': 0, 'moving': False} for i in range(1, 7)}}
        else:
            state = {'state': 'DISCONNECTED' if route == 'disconnect' else 'CONNECTED'}
        return io.BytesIO(json.dumps(state).encode())
    monkeypatch.setattr(scope['urllib'].request, 'urlopen', http)
    def adb(*args):
        calls.append(tuple(args))
        if args == ('devices',):
            return 'List of devices attached\nphone\tdevice'
        return '45678' if 'tcp:0' in args else ''
    scope['adb'] = adb
    def frame(url):
        if mode['frame_error']:
            raise ValueError('camera disconnected')
        return b'frame', None, {'generation': 1, 'capture_ns': 123}
    scope['phone_frame'] = frame
    class Connection:
        def __init__(self, *args, **kwargs):
            calls.append('serial_open')
        def close(self):
            calls.append('serial_close')
    monkeypatch.setattr(scope['serial'], 'Serial', Connection)
    scope['PanProbeBus'] = lambda connection: connection
    def probe(bus, review, fresh_frame, event):
        calls.append('probe')
        fresh_frame()
        event({'kind': 'goal_attempt', 'motor': 1, 'position': 2100})
        if mode['probe_error']:
            raise RuntimeError('lost ack')
        return {'status': 'SMALL_BASE_PROBE_MEASURED', 'physical_mapping': 'UNVERIFIED'}
    scope['run_pan_probe'] = probe
    return main, tmp_path, calls, mode


def test_serial_owner_transferred_and_restored_without_token_recording(runner):
    main, directory, calls, mode = runner
    main()
    assert calls.index('disconnect') < calls.index('serial_open') < calls.index('probe')
    assert calls.index('serial_close') < calls.index('connect')
    assert any(isinstance(c, tuple) and '--remove' in c for c in calls)
    result = (directory / 'probe_result.json').read_text()
    assert 'test-secret' not in result
    assert json.loads(result)['motor_commands_attempted'] is True


def test_fault_preserved_and_serial_restored_after_close(runner):
    main, directory, calls, mode = runner
    mode['probe_error'] = True
    main()
    result = json.loads((directory / 'probe_result.json').read_text())
    assert result['status'] == 'FAILED' and result['physical_stop_confirmed'] is False
    assert result['motor_commands_attempted'] is True
    assert calls.index('serial_close') < calls.index('connect')


def test_camera_failure_before_ownership_transfer_sends_no_commands(runner):
    main, directory, calls, mode = runner
    mode['frame_error'] = True
    main()
    result = json.loads((directory / 'probe_result.json').read_text())
    assert result['motor_commands_attempted'] is False
    assert 'disconnect' not in calls and 'serial_open' not in calls
    assert any(isinstance(c, tuple) and '--remove' in c for c in calls)


def test_duplicate_execution_rejected_before_forward_or_ownership_transfer(runner):
    main, directory, calls, mode = runner
    (directory / 'probe_events.jsonl').write_text('previous evidence')
    with pytest.raises(ValueError):
        main()
    assert calls == []
