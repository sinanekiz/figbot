import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from ai.training.prepare_field_dry_fig_dataset import build_dataset


class PrepareFieldDryFigDatasetTest(unittest.TestCase):
    def test_crop_translates_boxes_and_preserves_negatives(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            Image.new("RGB", (100, 80), "white").save(root / "positive.jpg")
            Image.new("RGB", (100, 80), "gray").save(root / "negative.jpg")
            manifest = {
                "class_name": "dry_fig",
                "images": [
                    {
                        "id": "positive",
                        "source": "positive.jpg",
                        "split": "train",
                        "crop": [10, 10, 90, 70],
                        "boxes": [[30, 20, 50, 40]],
                        "repeat": 2,
                    },
                    {
                        "id": "negative",
                        "source": "negative.jpg",
                        "split": "val",
                        "boxes": [],
                    },
                ],
            }
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            summary = build_dataset(manifest_path, root / "output")

            self.assertEqual(summary["train_images"], 2)
            self.assertEqual(summary["train_boxes"], 2)
            self.assertEqual(summary["val_images"], 1)
            label = (root / "output/labels/train/positive_000.txt").read_text()
            self.assertEqual(label, "0 0.37500000 0.33333333 0.25000000 0.33333333\n")
            self.assertEqual(
                (root / "output/labels/val/negative_000.txt").read_text(), ""
            )

    def test_rejects_box_outside_crop(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            Image.new("RGB", (20, 20), "white").save(root / "source.jpg")
            manifest_path = root / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "class_name": "dry_fig",
                        "images": [
                            {
                                "id": "bad",
                                "source": "source.jpg",
                                "split": "train",
                                "crop": [5, 5, 15, 15],
                                "boxes": [[0, 0, 10, 10]],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "outside crop"):
                build_dataset(manifest_path, root / "output")


if __name__ == "__main__":
    unittest.main()
