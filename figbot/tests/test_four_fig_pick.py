import unittest,json,tempfile
from pathlib import Path
from unittest.mock import patch
from reports.four_fig_pick.run import planned,source,OPEN,FLOORS,ROUTES


class Tests(unittest.TestCase):
    def test_four_plans_preserve_jaw(self):
        pose,_=source()
        for cycle in (1,2,3,4):
            initial=pose(43);initial[6]=OPEN
            for stage in ('approach','lower','lift','turn','carry','release'):
                if stage=='lift':initial[6]=FLOORS[cycle]+4
                points,_=planned(initial,cycle,stage)
                if stage!='release':
                    self.assertTrue(all(p['positions'][6]==(OPEN if stage in ('approach','lower') else FLOORS[cycle]+4) for p in points))
                self.assertEqual(points[-1]['positions'][6],OPEN if stage in ('approach','lower','release') else FLOORS[cycle]+4)
                initial=points[-1]['positions'].copy()
            self.assertEqual(initial[1],3215)
    def test_wrong_pose_and_closed_approach_are_rejected(self):
        pose,_=source();q=pose(43);q[6]=939
        with self.assertRaisesRegex(ValueError,'Open jaw'):planned(q,1,'approach')
        q[6]=OPEN;q[1]-=100
        with self.assertRaisesRegex(ValueError,'checkpoint'):planned(q,1,'approach')
    def test_narrow_open_moves_only_jaw(self):
        pose,_=source();q=pose(43);q[6]=1556
        points,_=planned(q,1,'open')
        self.assertEqual(points[-1]['positions'][6],1283)
        self.assertTrue(all(p['positions'][i]==q[i] for p in points for i in range(1,6)))
    def test_suspect_intervals_not_dispatched_or_bridged(self):
        for phases in ROUTES.values():
            for times in phases.values():
                for lo,hi in [(61.3,62.5),(92.212,93.232)]:
                    self.assertFalse(any(lo<=t<=hi for t in times))
                    # Remote basket anchor jumps are reviewed separately; none
                    # replays suspect local carry samples on both sides.
                    self.assertFalse(any(lo-1<a<lo and hi<b<hi+1 for a,b in zip(times,times[1:])))
    def test_camera_resume_requires_unchanged_hold_and_specific_fault(self):
        pose,_=source();q=pose(52);q[2]-=33;q[4]+=38;q[6]=1280
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory);p=out/'fig2_approach_result.json'
            failed=dict(state='ABORTED',error='Kamera kesildi veya görüntü donmuş olabilir.',
                        rows={str(i):dict(position=v) for i,v in q.items()})
            p.write_text(json.dumps(failed))
            with patch('reports.four_fig_pick.run.OUT',out):
                points,_=planned(q,2,'approach_resume')
                self.assertEqual(points[0]['positions'][2],pose(52)[2])
                shifted=dict(q);shifted[1]+=13
                with self.assertRaisesRegex(ValueError,'hold changed'):planned(shifted,2,'approach_resume')
                failed['error']='Unrelated fault';p.write_text(json.dumps(failed))
                with self.assertRaisesRegex(ValueError,'reviewed camera'):planned(q,2,'approach_resume')
    def test_interrupted_lower_recreates_reviewed_remaining_segment(self):
        pose,_=source();q=pose(70.4);q[6]=1280
        points,_=planned(q,3,'lower')
        current=q.copy();current[2]+=40;current[4]-=63
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory)
            (out/'fig3_lower_result.json').write_text(json.dumps(dict(state='ABORTED',error='Kamera kesildi veya görüntü donmuş olabilir.',rows={str(i):dict(position=v) for i,v in current.items()})))
            (out/'fig3_lower_plan.json').write_text(json.dumps(dict(initial=q,points=points)))
            with patch('reports.four_fig_pick.run.OUT',out):
                resumed,_=planned(current,3,'lower_resume')
                self.assertEqual(resumed,points)
                current[1]+=20
                with self.assertRaisesRegex(ValueError,'hold changed'):planned(current,3,'lower_resume')

if __name__=='__main__':unittest.main()
