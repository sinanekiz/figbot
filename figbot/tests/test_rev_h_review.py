import math
import numpy as np
from cad.rover.build_rev_h_review import (
    BASE, BASKET_FRONT, BASKET_REAR, SLOPE, TARGETS, floor_z,
    solve_pose, pad_position, posed_arm, vehicle, review, gear, cross_arm_gap, running_gear_review,
)


def test_fixed_wrist_ik_matches_transformed_actual_pad_midpoint():
    for target in TARGETS.values():
        pose=solve_pose(target)
        assert np.allclose(pad_position(pose),target,atol=1e-6)
        pads=[c.shape.val().Center() for c in posed_arm(pose) if c.name.startswith("soft pad")]
        midpoint=np.mean([[p.x,p.y,p.z] for p in pads],axis=0)
        assert np.allclose(midpoint,target,atol=.01)


def test_basket_slopes_rearward_and_equipment_fits_below_floor():
    assert BASE[2]>254
    assert math.isclose(floor_z(BASKET_FRONT)-floor_z(BASKET_REAR),600*math.tan(math.radians(SLOPE)))
    for part in vehicle():
        if part.group=="equipment":
            b=part.shape.val().BoundingBox()
            assert floor_z(b.xmin)-b.zmax>25,part.name


def test_review_key_poses_clear_listed_obstacles_and_ground():
    for target in TARGETS.values():
        result=review(solve_pose(target))
        assert not result["obstacle_intersections_mm3"]
        assert result["lowest_arm_solid_mm"]>0


def test_fixed_wrist_connection_retained_in_all_poses():
    for target in TARGETS.values():
        items={c.name:c.shape.val() for c in posed_arm(solve_pose(target))}
        # Rigid remapping must preserve the servo-to-horn connection.
        assert items["G1 MG90S-shaft"].intersect(items["gripper servo horn"]).Volume()>1
        # 4 mm pin in 4.5 mm clearance hole: nominal radial clearance 0.25 mm.
        assert .24<items["wrist-to-palm lower pin"].distance(items["rounded gripper palm"])<.26


def test_equipment_envelopes_do_not_overlap_each_other():
    equipment=[c for c in vehicle() if c.group=="equipment"]
    for i,a in enumerate(equipment):
        for b in equipment[i+1:]:
            assert a.shape.val().intersect(b.shape.val()).Volume()<.1


def test_two_identical_arm_instances_reach_opposite_lanes():
    for target in TARGETS.values():
        pose=solve_pose(target)
        right=posed_arm(pose,-1)
        pads=[c.shape.val().Center() for c in right if c.name.startswith("soft pad")]
        midpoint=np.mean([[p.x,p.y,p.z] for p in pads],axis=0)
        assert np.allclose(midpoint,(target[0],-target[1],target[2]),atol=.01)
        assert cross_arm_gap(pose)>250


def test_running_gear_force_paths_have_no_floating_connections():
    for link in gear.connection_report():
        assert link['gap_mm']<.1,link


def test_running_gear_parts_are_valid_solids_and_wheels_touch_ground():
    for part in gear.components():
        assert part.shape.val().isValid(),part.name
        assert part.shape.val().Volume()>0,part.name
        if part.group=='wheel':
            assert abs(part.shape.val().BoundingBox().zmin)<.01


def test_lower_basket_clears_drivetrain_and_sampled_front_tire_steering():
    result=running_gear_review()
    assert not result['gear_vs_basket_equipment_camera']
    assert all(not s['intersections'] for s in result['front_tire_steering_samples'])
