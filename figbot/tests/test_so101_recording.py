import json
import tempfile
import unittest
from pathlib import Path
import cv2
import numpy as np
from software.st3215_test.recording import SessionRecorder, validate_observation


def rows():
    return [dict(id=i,ok=True,torque=0,position=2000+i) for i in range(1,7)]


class Writer:
    def __init__(self,*args):self.frames=[];self.closed=False
    def isOpened(self):return True
    def write(self,frame):self.frames.append(frame.copy())
    def release(self):self.closed=True


class RecordingTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'session'
        self.frame=np.zeros((48,64,3),dtype=np.uint8)

    def make(self,**kwargs):
        rec=SessionRecorder(self.path,self.frame,100,rows(),100,now=100,
                            writer_factory=Writer,**kwargs)
        self.addCleanup(rec.close)
        return rec

    def test_stale_missing_and_enabled_motor_rejected(self):
        bad=rows();bad[2]['torque']=1
        for frame,ft,rs,rt in [(None,100,rows(),100),(self.frame,97,rows(),100),
                                (self.frame,100,rows(),97),(self.frame,100,rows()[:5],100),
                                (self.frame,100,bad,100)]:
            with self.assertRaises(ValueError):validate_observation(frame,ft,rs,rt,100)

    def test_frame_indices_timestamps_and_possible_freeze(self):
        rec=self.make()
        rec.add(self.frame,100,rows(),100,now=100)
        rec.add(self.frame,100,rows(),100,now=100.1)
        self.assertEqual(rec.index,1)
        note=rec.add(self.frame,106,rows(),105.9,now=106)
        self.assertIn('donma',note)
        self.frame[0,0,0]=1
        rec.add(self.frame,107,rows(),107,now=107)
        rec.close()
        data=[json.loads(s) for s in (self.path/'samples.jsonl').read_text().splitlines()]
        self.assertEqual([r['frame_index'] for r in data],[0,1,2])
        self.assertEqual([r['possible_frozen_image'] for r in data],[False,True,False])
        self.assertAlmostEqual(data[1]['telemetry_age_seconds'],.1)
        self.assertTrue(rec.writer.closed)

    def test_missing_motor_stops_recording_and_releases_writer(self):
        rec=self.make()
        with self.assertRaises(ValueError):rec.add(self.frame,101,rows()[:5],101,now=101)
        self.assertTrue(rec.closed);self.assertTrue(rec.writer.closed)
        self.assertEqual(json.loads((self.path/'session.json').read_text())['status'],'CLOSED')

    def test_time_limit_closes_without_new_frame(self):
        rec=self.make(max_seconds=1)
        rec.add(self.frame,101,rows(),101,now=101)
        self.assertTrue(rec.closed)
        self.assertEqual(rec.index,0)

    def test_actual_video_can_be_reopened(self):
        rec=SessionRecorder(self.path,self.frame,100,rows(),100,now=100)
        self.addCleanup(rec.close)
        for n in range(3):rec.add(self.frame,100+n*.1,rows(),100+n*.1,now=100+n*.1)
        rec.close()
        cap=cv2.VideoCapture(str(self.path/'camera.avi'))
        try:
            ok,frame=cap.read()
            self.assertTrue(ok);self.assertEqual(frame.shape,self.frame.shape)
            self.assertEqual(int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),3)
        finally:cap.release()


if __name__=='__main__':unittest.main()
