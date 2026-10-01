"""Offline checks for the bounded test harness; never opens a serial port."""
import unittest
from reports.first_taught_dry_run.run import plan
from software.st3215_test.coordinated import profiles_for


class FirstTaughtDryRunTests(unittest.TestCase):
    def test_actual_preflight_plan_keeps_gripper_open_and_speed_bounded(self):
        initial={1:2068,2:932,3:3957,4:2701,5:1212,6:1559}
        points,_=plan(initial)
        previous=initial
        for point in points:
            self.assertEqual(point['positions'][6],1559)
            _,profiles=profiles_for(previous,point['positions'],point['seconds'],1)
            self.assertTrue(all(speed<=200 for _,speed,_ in profiles.values()))
            previous=point['positions']

    def test_far_start_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'not near'):
            plan({1:1000,2:932,3:3957,4:2701,5:1212,6:1559})

    def test_empty_carry_has_no_gripper_closure(self):
        points,_=plan({1:2193,2:2858,3:2997,4:1276,5:1155,6:1559},'carry_empty')
        self.assertTrue(all(p['positions'][6]==1559 for p in points))

    def test_return_follows_recorded_path_with_open_jaw(self):
        points,_=plan({1:3214,2:1713,3:3203,4:2022,5:1151,6:1559},'return_hover')
        self.assertTrue(all(p['positions'][6]==1559 for p in points))
        self.assertLess(points[-1]['positions'][1],points[0]['positions'][1])
        self.assertEqual(points[-1]['positions'][2],2757)


if __name__=='__main__':unittest.main()
