import unittest

from software.safety.interlocks import Inputs, State, Supervisor


HEALTHY = Inputs(True, True, True, True)


class InterlockTests(unittest.TestCase):
    def test_defaults_deenergized(self):
        supervisor = Supervisor()
        self.assertEqual(supervisor.state, State.DISARMED)
        self.assertFalse(supervisor.motion_enable_request)

    def test_cannot_arm_with_missing_feedback(self):
        supervisor = Supervisor()
        self.assertFalse(supervisor.arm(Inputs(True, True, True, False)))

    def test_estop_latches_and_requires_reset_then_arm(self):
        supervisor = Supervisor()
        self.assertTrue(supervisor.arm(HEALTHY))
        supervisor.update(Inputs(False, True, True, True))
        self.assertEqual(supervisor.state, State.ESTOP_LATCHED)
        self.assertFalse(supervisor.manual_reset(Inputs(False, True, True, True)))
        self.assertTrue(supervisor.manual_reset(HEALTHY))
        self.assertEqual(supervisor.state, State.DISARMED)
        self.assertFalse(supervisor.motion_enable_request)

    def test_non_estop_fault_latches_while_armed(self):
        supervisor = Supervisor()
        supervisor.arm(HEALTHY)
        supervisor.update(Inputs(True, False, True, True))
        self.assertEqual(supervisor.state, State.FAULT_LATCHED)


if __name__ == "__main__":
    unittest.main()

