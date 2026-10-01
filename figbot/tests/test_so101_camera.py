import unittest
from types import SimpleNamespace
from software.st3215_test.camera import open_camera

class Capture:
    def __init__(self,opened,frame):self.opened=opened;self.frame=frame;self.released=False
    def isOpened(self):return self.opened
    def read(self):return self.frame is not None,self.frame
    def release(self):self.released=True

class CameraTests(unittest.TestCase):
    def fake(self,captures,available=(1,2)):
        self.calls=[]
        def factory(index,backend):self.calls.append((index,backend));return captures[backend]
        return SimpleNamespace(CAP_MSMF=1,CAP_DSHOW=2,
            videoio_registry=SimpleNamespace(hasBackend=lambda b:b in available),VideoCapture=factory)
    def test_prefers_msmf_and_validates_frame(self):
        cap=Capture(True,object());cv=self.fake({1:cap})
        returned,frame,name=open_camera(1,cv=cv)
        self.assertIs(returned,cap);self.assertFalse(cap.released)
        self.assertEqual(self.calls,[(1,1)])
    def test_failed_read_released_before_fallback(self):
        first=Capture(True,None);second=Capture(True,object());cv=self.fake({1:first,2:second})
        self.assertIs(open_camera(0,cv=cv)[0],second)
        self.assertTrue(first.released)
    def test_absent_backend_skipped(self):
        cap=Capture(True,object());cv=self.fake({2:cap},(2,))
        open_camera(0,cv=cv);self.assertEqual(self.calls,[(0,2)])
    def test_all_fail_and_cancel(self):
        a=Capture(False,None);b=Capture(False,None);cv=self.fake({1:a,2:b})
        with self.assertRaisesRegex(RuntimeError,'masaüstü'):open_camera(0,cv=cv)
        self.assertTrue(a.released and b.released)
        with self.assertRaisesRegex(RuntimeError,'iptal'):open_camera(0,cancelled=lambda:True,cv=cv)

if __name__=='__main__':unittest.main()
