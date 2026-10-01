import pytest
from figbot_lab.virtual_server import Application
from figbot_lab.virtual_motion import MotionController
from test_five_motor_arm import FiveBus


def test_pending_id_change_cannot_enable_torque_or_start_mouse_control():
    app = Application()
    bus = FiveBus()
    app.motion = MotionController(bus, active_ids=(1, 2, 3, 4, 5))
    app.hardware = {'replacement': {'status': 'PENDING_PHYSICAL_ID_VERIFICATION'}}
    with pytest.raises(ValueError, match='ID6'):
        app.action('activate_trial', {'angles': [0] * 6})
    assert not bus.writes and set(bus.torque.values()) == {0}
