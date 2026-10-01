from dataclasses import replace

import pytest

from figbot_lab.virtual_motion import MotionController
from figbot_lab.virtual_server import Application
from test_relative_motion import fixture, closed_reference


def app_fixture(monkeypatch, tmp_path):
    bus, clock, settings, angles = fixture()
    released = []
    def disable(motor, *, authority):
        released.append(motor)
        bus.torque[motor] = 0
    bus.disable_torque = disable
    app = Application()
    app.hardware = {}  # explicit historical six-motor fixture, independent of deployed hardware
    app.active_ids = tuple(range(1, 7))
    app.motion = MotionController(bus, clock=clock)
    app.closed_home = closed_reference(bus, settings, angles)
    monkeypatch.setattr('figbot_lab.calibration.read_settings', lambda _: settings)
    monkeypatch.setattr('figbot_lab.virtual_server.new_run', lambda _: tmp_path)
    return app, bus, clock, settings, angles, released


def test_manual_stop_releases_torque_without_a_new_holding_goal(monkeypatch, tmp_path):
    app, bus, clock, _, angles, released = app_fixture(monkeypatch, tmp_path)
    app.action('activate_trial', {'angles': angles})
    count = len(bus.writes)
    result = app.action('stop', {})
    assert result['emergency_latched'] and result['torque_release_confirmed']
    assert released == list(range(1, 7)) and len(bus.writes) == count
    with pytest.raises(ValueError):
        app.action('target', {'angles': angles, 'epoch': result['epoch'], 'sequence': 1, 'gesture': True})
    clock.advance(1); app.motion.tick()
    assert len(bus.writes) == count and set(bus.torque.values()) == {0}


def test_thermal_rearm_requires_fresh_cool_reading_and_explicit_activation(monkeypatch, tmp_path):
    app, bus, clock, _, angles, released = app_fixture(monkeypatch, tmp_path)
    app.action('activate_trial', {'angles': angles})
    original = bus.feedback
    bus.feedback = lambda i: replace(original(i), temperature=55 if i == 4 else 30)
    clock.advance(.1); app.motion.tick()
    count = len(bus.writes)
    assert app.state()['thermal_latched'] and released == list(range(1, 7))
    bus.feedback = lambda i: replace(original(i), temperature=46 if i == 4 else 30)
    with pytest.raises(ValueError, match='45'):
        app.action('activate_trial', {'angles': angles})
    assert len(bus.writes) == count and set(bus.torque.values()) == {0}
    bus.feedback = lambda i: replace(original(i), temperature=45 if i == 4 else 30)
    clock.advance(1); app.motion.tick()
    assert len(bus.writes) == count and app.state()['thermal_latched']
    result = app.action('activate_trial', {'angles': angles})
    assert result['state'] == 'ACTIVE' and not result['thermal_latched']
    assert len(bus.writes) == count + 6


def test_home_rejects_changed_offsets_before_server_sends_any_goal(monkeypatch, tmp_path):
    app, bus, _, settings, angles, _ = app_fixture(monkeypatch, tmp_path)
    app.action('activate_trial', {'angles': angles})
    settings['wrist_flex']['homing_offset_encoded'] += 1
    count = len(bus.writes)
    with pytest.raises(ValueError, match='ofseti'):
        app.action('home', {})
    assert len(bus.writes) == count and not app.motion.homing


def test_home_can_activate_from_connected_and_uses_fixed_reference(monkeypatch, tmp_path):
    app, bus, clock, _, angles, _ = app_fixture(monkeypatch, tmp_path)
    saved = dict(bus.positions)
    bus.positions[1] += 100
    result = app.action('home', {'angles': [a + .2 for a in angles]})
    assert result['homing'] and result['home_raw'] == saved
    clock.advance(.1); app.motion.tick()
    assert bus.goals == saved


def test_state_revisions_order_snapshots_and_new_server_has_own_session():
    app = Application()
    earlier, later = app.state(), app.state()
    assert later['state_revision'] > earlier['state_revision']
    assert later['server_session'] == earlier['server_session']
    assert Application().state()['server_session'] != later['server_session']
