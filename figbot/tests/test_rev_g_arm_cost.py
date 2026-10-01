from scripts.build_rev_g_arm_cost import build


def test_rev_g_arm_cost_extract_matches_rover_bom():
    two_arm_total, one_arm_equivalent = build()
    assert two_arm_total == 10278.86
    assert one_arm_equivalent == 5139.43
