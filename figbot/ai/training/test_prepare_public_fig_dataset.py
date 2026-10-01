from pathlib import Path

from PIL import Image

from ai.training.prepare_public_fig_dataset import _create_object_centric_crops


def test_object_centric_crop_preserves_fig_label(tmp_path: Path) -> None:
    image_root = tmp_path / "images" / "train"
    label_root = tmp_path / "labels" / "train"
    image_root.mkdir(parents=True)
    label_root.mkdir(parents=True)
    Image.new("RGB", (400, 300), (90, 120, 70)).save(image_root / "sample.jpg")
    (label_root / "sample.txt").write_text(
        "0 0.50000000 0.50000000 0.10000000 0.13333333\n", encoding="utf-8"
    )

    created = _create_object_centric_crops(tmp_path, "train", context=4.0)

    assert created == 1
    crop = Image.open(image_root / "sample_crop_000.jpg")
    assert crop.size == (160, 160)
    fields = (label_root / "sample_crop_000.txt").read_text(encoding="utf-8").split()
    assert fields[0] == "0"
    assert abs(float(fields[1]) - 0.5) < 0.01
    assert abs(float(fields[2]) - 0.5) < 0.01
    assert abs(float(fields[3]) - 0.25) < 0.01
    assert abs(float(fields[4]) - 0.25) < 0.01
