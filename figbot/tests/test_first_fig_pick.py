import unittest
from reports.first_fig_pick.move import held_plan


class Tests(unittest.TestCase):
    def test_lift_and_carry_preserve_measured_grip(self):
        for stage,q in [('lift',[2192,2862,2995,1271,1152,947]),
                        ('lift_high',[2192,2777,3001,1277,1152,947]),
                        ('turn',[2194,2412,3035,1445,1157,947]),
                        ('carry',[2529,1962,3036,2023,1154,947])]:
            points,_=held_plan(dict(enumerate(q,1)),stage)
            self.assertTrue(all(p['positions'][6]==947 for p in points))
            self.assertLess(points[0]['positions'][2],q[1]+10)
    def test_turn_cannot_skip_high_lift(self):
        with self.assertRaisesRegex(ValueError,'preceding verified lift'):
            held_plan(dict(enumerate([2191,2759,3003,1277,1152,947],1)),'turn')
    def test_release_requires_basket_pose(self):
        with self.assertRaisesRegex(ValueError,'Basket'):
            held_plan(dict(enumerate([2192,2862,2995,1271,1152,947],1)),'release')
        points,_=held_plan(dict(enumerate([3214,1715,3203,2022,1152,947],1)),'release')
        self.assertEqual(points[0]['positions'][6],1559)
    def test_open_jaw_cannot_be_used_as_held_grasp(self):
        with self.assertRaisesRegex(ValueError,'closed jaw'):
            held_plan(dict(enumerate([2192,2862,2995,1271,1152,1556],1)),'lift')

if __name__=='__main__':unittest.main()
