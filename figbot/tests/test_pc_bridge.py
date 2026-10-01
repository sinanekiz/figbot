import socket
import threading
import unittest
from unittest.mock import Mock,patch
from software.st3215_test.protocol import packet,Feedback
from software.st3215_test.pc_bridge import validate,receive_packet,serve_client,hold_on_disconnect


class PcBridgeTests(unittest.TestCase):
    def test_read_and_finite_writes(self):
        self.assertEqual(validate(packet(1,2,bytes([40,31])))[3],31)
        validate(packet(2,3,bytes([41,50])+b'\x00\x08\0\0\x48\x0d'))
        validate(packet(254,0x83,bytes([42,2,1,0,8,2,0,7])))

    def test_forbidden_packets_never_reach_bus(self):
        bad=[packet(1,3,b'\x05\x02'),packet(7,2,b'\x28\x1f'),
             packet(1,3,bytes([41,0])+b'\0\x08\0\0\0\0'),
             packet(254,0x83,bytes([42,2,1,0,8,1,0,7])),packet(254,3,b'\x28\0')]
        for frame in bad:
            with self.assertRaises(ValueError):validate(frame)
        with self.assertRaises(ValueError):validate(packet(1,2,b'\x28\x1f')[:-1]+b'\0')

    def test_fragmented_and_coalesced_frames(self):
        a,b=socket.socketpair()
        with a,b:
            first=packet(1,2,b'\x28\x1f');second=packet(2,2,b'\x28\x1f')
            a.sendall(first[:3]);a.sendall(first[3:]+second)
            self.assertEqual(receive_packet(b),first);self.assertEqual(receive_packet(b),second)

    def test_eof_is_not_empty_success(self):
        a,b=socket.socketpair();a.close()
        with b,self.assertRaises(EOFError):receive_packet(b)

    def test_partial_packet_times_out(self):
        a,b=socket.socketpair()
        with a,b:
            a.sendall(b'\xff\xff\x01')
            with self.assertRaises(TimeoutError):receive_packet(b)

    def test_enabled_joints_hold_fresh_feedback_with_readback(self):
        bus=Mock();bus.feedback_state.return_value=(Feedback(2048,0,12,30,0,False),1)
        bus.read.side_effect=lambda motor,address,length: b'\x32' if address==85 else b'\0\x08'
        self.assertIn('doğrulandı',hold_on_disconnect(bus))
        self.assertEqual(bus.goal.call_count,6)
        bus.goal.assert_any_call(1,2048,3400,50)
        bus.write.assert_not_called()

    def test_read_only_disconnect_has_no_hold_write(self):
        a,b=socket.socketpair();bus=Mock();bus.transact.return_value=b'\x09\x03'
        def run():
            try:serve_client(b,bus)
            except EOFError:pass
        with patch('software.st3215_test.pc_bridge.hold_on_disconnect') as hold:
            t=threading.Thread(target=run);t.start()
            a.sendall(packet(1,2,b'\x03\x02'))
            self.assertEqual(receive_packet(a),packet(1,0,b'\x09\x03'))
            a.close();t.join(2);b.close();self.assertFalse(t.is_alive());hold.assert_not_called()

    def test_disconnect_never_enables_disabled_motors(self):
        bus=Mock();bus.feedback_state.return_value=(Feedback(2048,0,12,30,0,False),0)
        self.assertIn('doğrulandı',hold_on_disconnect(bus));bus.goal.assert_not_called()

    def test_unknown_hold_is_reported_without_torque_cut(self):
        bus=Mock();bus.feedback_state.side_effect=IOError('USB yok')
        self.assertIn('BELİRSİZ',hold_on_disconnect(bus));bus.write.assert_not_called()

    def test_ambiguous_write_attempts_hold_without_replay(self):
        a,b=socket.socketpair();bus=Mock();bus.transact.side_effect=IOError('ACK kayıp')
        a.sendall(packet(1,3,b'\x28\x01'))
        with a,b,patch('software.st3215_test.pc_bridge.hold_on_disconnect',return_value='hold') as hold:
            with self.assertRaises(IOError):serve_client(b,bus)
            self.assertEqual(bus.transact.call_count,1);hold.assert_called_once_with(bus)
