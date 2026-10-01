import unittest
from software.st3215_test.observe import ReadOnlyBus, read_sample
from software.st3215_test.protocol import Feedback

class NeverWriteSerial:
    def write(self,data):raise AssertionError('Forbidden command reached serial port')

class ReadFake:
    def feedback(self,i):
        if i==2:raise TimeoutError('No reply')
        return Feedback(2048,0,12.1,30,0,False)
    def read(self,i,a,n):
        assert (a,n)==(40,1)
        return b'\x00'

class ObserveTests(unittest.TestCase):
    def test_mutating_commands_blocked_before_serial_io(self):
        bus=ReadOnlyBus(NeverWriteSerial())
        for op in [3,4,5,6,0x83]:
            with self.assertRaises(ValueError):bus.transact(1,op)
        with self.assertRaises(ValueError):bus.write(1,40,[1])
        with self.assertRaises(ValueError):bus.goal(1,2048,0,0)
        with self.assertRaises(ValueError):bus.ping(254)

    def test_partial_failure_preserves_per_motor_status(self):
        rows=read_sample(ReadFake(),[1,2,3])
        self.assertEqual([r['ok'] for r in rows],[True,False,True])
        self.assertEqual(rows[0]['degrees'],180)
        self.assertEqual(rows[0]['torque'],0)
        self.assertIn('captured_utc',rows[0])
        self.assertNotIn('position',rows[1])

if __name__=='__main__':unittest.main()
