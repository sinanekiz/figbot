import unittest

from ai.inference.gate import Detection, pick_candidates


class GateTests(unittest.TestCase):
    def test_accepts_isolated_dry_candidate(self):
        dry = Detection("dry_fig_collect", 0.9, (0, 0, 10, 10))
        self.assertEqual(pick_candidates([dry], 0.8, 0.4, 0.05), [dry])

    def test_rejects_candidate_overlapping_green_fig(self):
        dry = Detection("dry_fig_collect", 0.9, (0, 0, 10, 10))
        green = Detection("green_fig_ignore", 0.5, (2, 2, 8, 8))
        self.assertEqual(pick_candidates([dry, green], 0.8, 0.4, 0.05), [])

    def test_rejects_low_confidence_dry_candidate(self):
        dry = Detection("dry_fig_collect", 0.79, (0, 0, 10, 10))
        self.assertEqual(pick_candidates([dry], 0.8, 0.4, 0.05), [])


if __name__ == "__main__":
    unittest.main()

