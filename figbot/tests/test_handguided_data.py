import unittest
import numpy as np
from ai.training.handguided_data import corrected_targets, eligible, suspect_intervals


class HandguidedDataTests(unittest.TestCase):
    def test_opening_standardized_without_changing_raw_or_grasp_width(self):
        t=np.arange(0,10,.1);q=np.full((len(t),6),1000.);q[:,5]=1200
        q[(t>=4)&(t<7),5]=950;q[0,5]=1500;original=q.copy()
        c=dict(start=0,close_start=3,close_end=4,release_start=7,release_end=8,end=10)
        clean,group,phase=corrected_targets(t,q,[c],1500)
        np.testing.assert_array_equal(q,original)
        self.assertTrue(np.all(clean[phase=='approach',5]==1500))
        self.assertTrue(np.all(clean[phase=='carry',5]==950))
        self.assertTrue(np.all(clean[:,0]==1000))

    def test_samples_cannot_bridge_cycles_or_suspect_spans(self):
        t=np.arange(0,4,.1);g=np.where(t<2,0,1)
        ok=eligible(t,g,[[.8,1.]])
        self.assertFalse(ok[np.argmin(abs(t-1.8))])
        self.assertFalse(ok[np.argmin(abs(t-.4))])
        self.assertTrue(ok[np.argmin(abs(t-2.5))])

    def test_sudden_drop_excluded_with_padding(self):
        t=np.arange(0,2,.1);q=np.zeros((len(t),6));q[10:,1]=500
        spans=suspect_intervals(t,q)
        self.assertEqual(len(spans),1)
        self.assertLess(spans[0][0],.9);self.assertGreater(spans[0][1],1.)

    def test_impossible_open_and_overlap_rejected(self):
        t=np.arange(0,10,.1);q=np.full((len(t),6),1000.)
        c=dict(start=0,close_start=3,close_end=4,release_start=7,release_end=8,end=10)
        with self.assertRaises(ValueError):corrected_targets(t,q,[c],2000)
        with self.assertRaises(ValueError):corrected_targets(t,q,[c,c],1000)


if __name__=='__main__':unittest.main()
