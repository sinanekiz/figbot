from cad.config import parameters as p
from cad.rover.geometry_checks import clearance_report


def test_rev_g_clearances_meet_packaging_minimum():
    report = clearance_report()
    assert set(report) >= {
        "dual_arm_mount_gap_mm",
        "arm_mount_to_front_wheel_sweep_mm",
        "basket_front_to_frame_mm",
        "basket_side_to_arm_mount_mm",
        "basket_to_rear_tyre_mm",
        "basket_floor_rise_mm",
        "basket_front_internal_depth_mm",
    }
    assert report["steered_tyre_to_frame_mm"] >= p.P0_STEER_CLEARANCE_MIN
    assert report["rear_tyre_to_frame_mm"] >= p.P0_STEER_CLEARANCE_MIN
    assert report["camera_mast_to_front_wheel_sweep_mm"] >= p.P0_STEER_CLEARANCE_MIN
    assert 50 < report["basket_floor_rise_mm"] < 60
    assert report["basket_front_internal_depth_mm"] > 120
