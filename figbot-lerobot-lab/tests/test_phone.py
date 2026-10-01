import io

import cv2
import numpy as np
import pytest

from figbot_lab.phone import phone_frame


class Response(io.BytesIO):
    def __init__(self, age=10_000_000, width=64, capture=1000000000):
        ok, image = cv2.imencode('.jpg', np.zeros((48, 64, 3), dtype=np.uint8))
        assert ok
        super().__init__(image.tobytes())
        self.headers = {'X-Age-Ns': str(age), 'X-Capture-Ns': str(capture), 'X-Generation': '1',
                        'X-Intrinsics': '400,400,32,24', 'X-Height': '48', 'X-Width': str(width)}


def test_fresh_phone_image():
    ticks = iter([1., 1.01])
    _, frame, meta = phone_frame('fixture', opener=lambda *a, **kw: Response(), clock=lambda: next(ticks))
    assert frame.shape == (48, 64, 3)
    assert meta['age_s'] == .01


@pytest.mark.parametrize('age,width,capture,delay', [(400000000,64,1000000000,.01),
    (-1,64,1000000000,.01),(1,60,1000000000,.01),(1,64,0,.01),(1,64,1000000000,.4),
    (250000000,64,1000000000,.1)])
def test_phone_rejects_stale_or_invalid(age, width, capture, delay):
    ticks = iter([1., 1. + delay])
    with pytest.raises(ValueError):
        phone_frame('fixture', opener=lambda *a, **kw: Response(age,width,capture), clock=lambda: next(ticks))


@pytest.mark.parametrize('failure', ['missing', 'bad_focal'])
def test_phone_metadata_errors_are_explicit(failure):
    response = Response()
    if failure == 'missing': del response.headers['X-Age-Ns']
    if failure == 'bad_focal': response.headers['X-Intrinsics'] = '-1,400,32,24'
    ticks = iter([1., 1.01])
    with pytest.raises(ValueError, match='metadata'):
        phone_frame('fixture', opener=lambda *a, **kw: response, clock=lambda: next(ticks))


@pytest.mark.parametrize('observer_failure', [False, True])
def test_phone_observer_and_cleanup_preserve_original_failure(tmp_path, monkeypatch, observer_failure):
    import figbot_lab.phone as phone
    from figbot_lab.common import load_json
    state = {'clock': 1., 'capture': 0, 'observations': 0, 'removed': 0}
    def adb(*args):
        if args == ('devices',): return 'List of devices attached\nphone\tdevice'
        if '--remove' in args:
            state['removed'] += 1
            if observer_failure: raise ValueError('cleanup error')
        if 'tcp:0' in args: return '12345'
        return ''
    def frame(url):
        state['capture'] += 1
        return b'jpeg', np.zeros((48,64,3), dtype=np.uint8), {
            'capture_ns': state['capture'], 'generation': 1,
            'pc_capture_interval': [state['clock']-.01, state['clock']]}
    def observe(meta):
        state['observations'] += 1
        if observer_failure: raise ValueError('motor fault')
    monkeypatch.setattr(phone, 'adb', adb)
    monkeypatch.setattr(phone, 'phone_frame', frame)
    monkeypatch.setattr(phone, 'new_run', lambda _: tmp_path)
    monkeypatch.setattr(phone.time, 'monotonic', lambda: state['clock'])
    monkeypatch.setattr(phone.time, 'sleep', lambda seconds: state.update(clock=state['clock']+seconds))
    if observer_failure:
        with pytest.raises(ValueError, match='motor fault'):
            phone.capture_phone(seconds=.3, on_frame=observe)
        assert load_json(tmp_path / 'capture.json')['error'] == 'motor fault'
        assert (tmp_path / 'cleanup_error.json').exists()
    else:
        assert phone.capture_phone(seconds=.3, on_frame=observe) == tmp_path
        assert state['observations'] >= 4
    assert state['removed'] == 1
