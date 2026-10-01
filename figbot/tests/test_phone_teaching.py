import io
import unittest
from software.st3215_test.phone_teaching import camera_sample,require_passive,ReadOnlyTeachingBus
from software.st3215_test.protocol import BusError

class Response(io.BytesIO):
    headers={'X-Age-Ns':'50000000','X-Capture-Ns':'123','X-Generation':'2','X-Intrinsics':'400,400,320,240'}

class PhoneTeachingTests(unittest.TestCase):
    def test_passive_transport_rejects_goal_torque_and_broadcast_before_io(self):
        class NoIo:
            def __getattr__(self,name):raise AssertionError('Unexpected serial access '+name)
        bus=ReadOnlyTeachingBus(NoIo())
        for motor,instruction,data in [(1,3,b'\x28\x01'),(2,3,b'\x2a\x00\x04'),(254,2,b'\x38\x02')]:
            with self.assertRaises(BusError):bus.transact(motor,instruction,data)
    def test_camera_preserves_capture_identity_and_exposes_alignment_uncertainty(self):
        times=iter([10.,10.02])
        data,t=camera_sample('unused',lambda *a,**kw:Response(b'\xff\xd8rgb\xff\xd9'),lambda:next(times))
        self.assertEqual(t['phone_capture_ns'],123)
        self.assertAlmostEqual(t['estimated_capture_monotonic'],9.96)
        self.assertAlmostEqual(t['transport_uncertainty_seconds'],.01)

    def test_slow_camera_and_invalid_bytes_are_rejected(self):
        for duration,data in [(.4,b'\xff\xd8rgb\xff\xd9'),(.01,b'bad')]:
            times=iter([10.,10.+duration])
            with self.assertRaises(ValueError):camera_sample('unused',lambda *a,**kw:Response(data),lambda:next(times))

    def test_partial_or_enabled_motor_chain_rejected(self):
        row=dict(torque=0,position=1000,voltage=12,temperature=30,current_raw=0)
        rows={i:row.copy() for i in range(1,7)};require_passive(rows)
        rows[2]['torque']=1
        with self.assertRaises(BusError):require_passive(rows)
        rows.pop(2)
        with self.assertRaises(BusError):require_passive(rows)

if __name__=='__main__':unittest.main()
