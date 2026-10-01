import tkinter as tk

from software.servo_panel.app import App, Worker, angle_from_point


def test_stop_discards_queued_motion():
    worker = Worker()
    worker.submit("command", "r")
    worker.submit("command", "x")
    assert list(worker.tasks) == [("command", "x")]
    worker.submit("command", "l")
    assert list(worker.tasks) == [("command", "x")]
    worker.submit("close")
    assert list(worker.tasks) == [("close", None)]


def test_buttons_follow_connection_and_acknowledged_state(monkeypatch):
    # Native UI test; serial worker is never started and cannot access hardware.
    monkeypatch.setattr(Worker, "start", lambda self: None)
    root = tk.Tk()
    root.withdraw()
    app = App(root, "COM_TEST")
    try:
        assert app.centre.cget("state") == "disabled"
        app.apply_state({"ready": True, "active": False})
        assert app.centre.cget("state") == "normal"
        assert app.left.cget("state") == "normal"
        assert app.fast.cget("state") == "normal"
        app.centre.invoke()
        app.cancel_pending(); app.flush_position()
        assert list(app.worker.tasks) == [("position", (90, 60))]
        app.worker.tasks.clear()
        app.apply_state({"ready": True, "active": True, "remaining": 9})
        assert app.left.cget("state") == "normal"
        assert app.fast.cget("state") == "normal"
        app.fast.invoke()
        assert list(app.worker.tasks) == [("command", "t")]
        app.worker.tasks.clear()
        app.left.invoke()
        app.cancel_pending(); app.flush_position()
        assert list(app.worker.tasks) == [("position", (99, 60))]
        app.stop.invoke()
        assert list(app.worker.tasks) == [("command", "x")]
        app.apply_state({"ready": True, "active": True, "fast_running": True})
        assert app.fast.cget("state") == "disabled"
        assert app.stop.cget("state") == "normal"
        assert app.left.cget("state") == app.right.cget("state") == app.centre.cget("state") == "disabled"
        app.apply_state({"ready": True, "active": False})
        assert app.left.cget("state") == app.right.cget("state") == "normal"
    finally:
        app.closed = True
        app.cancel_pending()
        root.destroy()


def test_dial_geometry_and_latest_target_queue():
    assert angle_from_point(200, 100, 100, 100) == 0
    assert angle_from_point(100, 0, 100, 100) == 90
    assert angle_from_point(0, 100, 100, 100) == 180
    assert angle_from_point(0, 150, 100, 100) == 180
    worker = Worker()
    for angle in range(181):
        worker.submit("position", (angle, 90))
    assert list(worker.tasks) == [("position", (180, 90))]
    worker.submit("command", "x")
    worker.submit("position", (90, 90))
    assert list(worker.tasks) == [("command", "x")]


def test_speed_setting_and_stop_cancel_pending_drag(monkeypatch):
    monkeypatch.setattr(Worker, "start", lambda self: None)
    root = tk.Tk(); root.withdraw()
    app = App(root, "COM_TEST")
    try:
        app.apply_state({"ready": True, "active": False})
        app.maximum.set(False); app.speed_value.set(60)
        app.speed_changed()
        app.go(135)
        app.cancel_pending(); app.flush_position()
        assert list(app.worker.tasks) == [("position", (135, 60))]
        app.go(10)
        assert app.pending_position is not None
        app.stop.invoke()
        assert app.pending_position is None
        assert list(app.worker.tasks) == [("command", "x")]
    finally:
        app.closed = True; app.cancel_pending(); root.destroy()
