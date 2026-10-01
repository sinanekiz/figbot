import tkinter as tk
import pytest
from software.servo_panel.pca_controller import PCAController
from software.servo_panel.pca_app import App, Worker


class Link:
    def __init__(self, **kwargs):
        self.data = b'FIGBOT_PCA9685_V5\nSTATUS5 0,0\n'
        self.written = []
    @property
    def in_waiting(self): return len(self.data)
    def read(self, n):
        data, self.data = self.data[:n], self.data[n:]
        return data
    def write(self, data): self.written.append(data)
    def close(self): pass


def controller():
    c = PCAController(factory=Link, clock=lambda: 10)
    c.connect('TEST')
    c.poll()
    return c


def test_connection_and_enable_never_emit_position():
    c = controller()
    assert c.ready and c.enabled == c.active == 0
    assert c.link.written == [b'H\n']
    c.arm(0, True)
    assert c.link.written[-1] == b'E0\n'
    with pytest.raises(RuntimeError): c.position(0, 90, 30)
    c.handle_line('STATUS5 1,0')
    c.position(0, 95, 30)
    assert c.link.written[-1] == b'P0,95,30,1000,2000\n'
    c.position(0, 180, 60, True)
    assert c.link.written[-1] == b'P0,180,60,500,2500\n'
    with pytest.raises(RuntimeError): c.position(1, 95, 30)


def test_invalid_channels_and_values_never_write():
    c = controller()
    c.handle_line('STATUS5 4095,0')
    before = list(c.link.written)
    for ch, angle, speed in ((12, 90, 30), (-1, 90, 30), (True, 90, 30), (0, 181, 30), (0, -1, 30), (0, 90, 0)):
        with pytest.raises(ValueError): c.position(ch, angle, speed)
    assert c.link.written == before
    c.position(11, 90, 30)
    assert c.link.written[-1].startswith(b'P11,')


def test_stale_link_reset_and_stop_clear_arming():
    c = controller()
    c.handle_line('STATUS5 1,1')
    c.stop()
    assert c.enabled == c.active == 0
    assert c.link.written[-1] == b'X\n'
    c.handle_line('STATUS5 1,1')
    c.handle_line('FIGBOT_PCA9685_V5')
    assert not c.ready and not c.enabled
    c.handle_line('STATUS5 1,1')
    c.clock = lambda: 12
    with pytest.raises(RuntimeError): c.poll()


def test_queue_keeps_latest_per_channel_stop_discards_all():
    w = Worker()
    w.submit('arm', (0, True))
    w.submit('position', (0, 90, 30, False))
    w.submit('position', (1, 90, 30, False))
    w.submit('position', (0, 95, 30, False))
    assert len(w.tasks) == 3
    w.submit('stop')
    w.submit('position', (0, 180, 30, False))
    w.submit('arm', (0, True))
    assert list(w.tasks) == [('stop', None)]


def test_pair_requires_both_channels_centre_and_rejects_individual_follower():
    c = controller()
    c.handle_line('STATUS5 6,0')
    before = list(c.link.written)
    with pytest.raises(ValueError): c.position(1, 100, 30)
    with pytest.raises(ValueError): c.position(2, 90, 30)
    with pytest.raises(ValueError): c.arm(8, True)
    with pytest.raises(ValueError): c.position(1, 90, 361)
    with pytest.raises(ValueError): c.position(1, 90, 30, True)
    assert c.link.written == before
    c.position(1, 90, 30)
    assert c.link.written[-1] == b'S1,90,30,1000,2000\n'
    c.handle_line('STATUS5 6,6')
    c.position(1, 100, 30)
    c.handle_line('PAIR 1,100,30,1000,2000')
    assert c.acks[1][0] == 100 and c.acks[2][0] == 80
    with pytest.raises(RuntimeError): c.handle_line('STATUS5 2,2')
    with pytest.raises(RuntimeError): c.handle_line('STATUS 0,0')


def test_pair_ui_single_bar_calibration_gate_and_shared_reverse(monkeypatch):
    monkeypatch.setattr(Worker, 'start', lambda _: None)
    root = tk.Tk(); root.withdraw()
    app = App(root)
    try:
        root.update()
        assert 2 not in app.rows and 8 not in app.rows
        app.apply_state(dict(ready=True, enabled=0, active=0))
        row = app.rows[1]
        for shoulder in (1, 7):
            assert tuple(map(int, app.rows[shoulder]['speed_choices'].cget('values'))) == (10, 30, 60, 90, 120, 150, 180, 240, 300, 360)
            assert app.rows[shoulder]['speed'].get() == 30
        assert row['check'].cget('state') == 'disabled'
        row['fit_check'].invoke()
        row['check'].invoke()
        assert list(app.worker.tasks) == [('arm', (1, True))]
        app.apply_state(dict(ready=True, enabled=6, active=0))
        assert row['slider'].cget('state') == 'disabled'
        row['centre'].invoke()
        assert app.worker.tasks[-1] == ('position', (1, 90, 30, False))
        app.apply_state(dict(ready=True, enabled=6, active=6))
        assert row['slider'].cget('state') == 'normal'
        row['angle'].set(100)
        row['reverse'].set(True)
        row['speed'].set(360)
        app.move(1)
        assert app.worker.tasks[-1] == ('position', (1, 80, 360, False))
        app.stop()
        assert list(app.worker.tasks) == [('stop', None)]
    finally:
        app.closed=True
        root.destroy()


def test_ui_has_two_arms_only_acknowledged_channels_can_move(monkeypatch):
    monkeypatch.setattr(Worker, 'start', lambda _: None)
    root = tk.Tk(); root.withdraw()
    app = App(root)
    try:
        root.update()
        assert len(app.rows) == 10 and len(app.notebook.tabs()) == 2
        assert not app.worker.tasks
        assert all(r['slider'].cget('state') == 'disabled' for r in app.rows.values())
        app.apply_state(dict(ready=True, enabled=0, connected=True))
        app.rows[0]['check'].invoke()
        assert list(app.worker.tasks) == [('arm', (0, True))]
        app.apply_state(dict(ready=True, enabled=1, connected=True))
        root.update()
        assert list(app.worker.tasks) == [('arm', (0, True))]
        assert app.rows[0]['slider'].cget('state') == 'normal'
        assert app.rows[1]['slider'].cget('state') == 'disabled'
        app.test()
        assert len(app.test_jobs) == 4
        app.stop()
        assert not app.test_jobs
        assert list(app.worker.tasks) == [('stop', None)]
        app.apply_state(dict(ready=False, enabled=0))
        assert all(not r['arm'].get() for r in app.rows.values())
    finally:
        app.closed = True
        app.cancel_test()
        root.destroy()


def test_both_shoulders_allow_360_and_reject_old_firmware():
    c = controller()
    c.handle_line('STATUS5 390,390')
    for ch in (1, 7):
        for speed in (90, 120, 150, 180, 240, 300, 360):
            c.position(ch, 120, speed)
            assert c.link.written[-1] == f'S{ch},120,{speed},1000,2000\n'.encode()
            c.handle_line(f'PAIR {ch},120,{speed},1000,2000')
            assert c.acks[ch+1] == [60, speed, 1000, 2000]
    for reply in ('FIGBOT_PCA9685_V2', 'STATUS2 0,0', 'FIGBOT_PCA9685_V3', 'STATUS3 0,0', 'FIGBOT_PCA9685_V4', 'STATUS4 0,0'):
        with pytest.raises(RuntimeError): c.handle_line(reply)


def test_individual_channels_accept_360_but_reject_361():
    c = controller()
    c.handle_line('STATUS5 4095,4095')
    for ch in (0, 3, 4, 5, 6, 9, 10, 11):
        c.position(ch, 120, 360)
        assert c.link.written[-1] == f'P{ch},120,360,1000,2000\n'.encode()
        with pytest.raises(ValueError): c.position(ch, 120, 361)
