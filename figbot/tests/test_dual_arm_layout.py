from simulation.evaluate_dual_arm_layout import evaluate


def test_rev_g_front_basket_side_arms_reduce_planar_transfer_and_yaw():
    rows, summary = evaluate(100)
    assert len(rows) == 100
    assert {row["assigned_arm"] for row in rows} == {"left", "right"}
    assert summary["new_mean_distance"] < summary["old_mean_distance"]
    assert summary["new_mean_yaw"] < summary["old_mean_yaw"]
