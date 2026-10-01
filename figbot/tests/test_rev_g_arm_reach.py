from simulation.evaluate_rev_g_arm import evaluate


def test_both_rev_g_pick_lanes_and_adjacent_drop_points_are_analytically_reachable():
    rows, summary = evaluate()
    assert len(rows) == 2850
    for side in ("left", "right"):
        result = summary["results"][side]
        assert result["lane_success"] == result["lane_total"]
        assert result["drop_reachable"] is True
