import unittest

from ai.evaluation.evaluate import compute_metrics


class EvaluationTests(unittest.TestCase):
    def test_critical_false_positive_rate(self):
        rows = [
            {"truth": "green_fig_ignore", "prediction": "dry_fig_collect"},
            {"truth": "green_fig_ignore", "prediction": "green_fig_ignore"},
            {"truth": "stone_avoid", "prediction": "stone_avoid"},
        ]
        metrics = compute_metrics(rows)
        self.assertEqual(metrics["green_to_dry_false_positive_rate"], 0.5)
        self.assertEqual(metrics["stone_to_dry_false_positive_rate"], 0.0)

    def test_missing_class_has_null_precision_and_recall(self):
        metrics = compute_metrics([])
        self.assertIsNone(metrics["per_class"]["dry_fig_collect"]["precision"])
        self.assertIsNone(metrics["per_class"]["dry_fig_collect"]["recall"])

    def test_unmatched_rows_affect_detection_precision_and_recall(self):
        rows = [
            {"truth": "dry_fig_collect", "prediction": "dry_fig_collect"},
            {"truth": "dry_fig_collect", "prediction": "__none__"},
            {"truth": "__none__", "prediction": "dry_fig_collect"},
        ]
        metrics = compute_metrics(rows)
        self.assertEqual(metrics["per_class"]["dry_fig_collect"]["precision"], 0.5)
        self.assertEqual(metrics["per_class"]["dry_fig_collect"]["recall"], 0.5)



if __name__ == "__main__":
    unittest.main()
