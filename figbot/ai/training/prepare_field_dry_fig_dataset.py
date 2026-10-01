"""Build a reviewed YOLO dataset from FIGBOT field-image annotations.

The manifest uses pixel-space boxes so annotations can be inspected without
depending on a labelling application's private format.  A source image may be
cropped before export; boxes are always expressed in the original source image.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from PIL import Image


VALID_SPLITS = {"train", "val", "test"}


def _validated_crop(image: Image.Image, crop: list[int] | None) -> tuple[int, int, int, int]:
    result = tuple(crop or [0, 0, image.width, image.height])
    if len(result) != 4:
        raise ValueError("crop must contain left, top, right, bottom")
    left, top, right, bottom = result
    if left < 0 or top < 0 or right > image.width or bottom > image.height:
        raise ValueError(f"crop {result} is outside {image.width}x{image.height}")
    if right <= left or bottom <= top:
        raise ValueError(f"crop has no area: {result}")
    return result


def _normalise_box(
    box: list[float], crop: tuple[int, int, int, int]
) -> tuple[float, float, float, float]:
    if len(box) != 4:
        raise ValueError("box must contain left, top, right, bottom")
    box_left, box_top, box_right, box_bottom = box
    crop_left, crop_top, crop_right, crop_bottom = crop
    if (
        box_left < crop_left
        or box_top < crop_top
        or box_right > crop_right
        or box_bottom > crop_bottom
        or box_right <= box_left
        or box_bottom <= box_top
    ):
        raise ValueError(f"box {box} is outside crop {crop}")
    width = crop_right - crop_left
    height = crop_bottom - crop_top
    relative_left = box_left - crop_left
    relative_top = box_top - crop_top
    return (
        (relative_left + (box_right - box_left) / 2) / width,
        (relative_top + (box_bottom - box_top) / 2) / height,
        (box_right - box_left) / width,
        (box_bottom - box_top) / height,
    )


def build_dataset(manifest_path: Path, output: Path) -> dict[str, int]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("class_name") != "dry_fig":
        raise ValueError("field manifest must define the single class dry_fig")

    if output.exists():
        shutil.rmtree(output)
    counts = {split: 0 for split in VALID_SPLITS}
    box_counts = {split: 0 for split in VALID_SPLITS}
    source_root = manifest_path.parent

    for item in manifest.get("images", []):
        split = item["split"]
        if split not in VALID_SPLITS:
            raise ValueError(f"unsupported split: {split}")
        source = source_root / item["source"]
        repeat = int(item.get("repeat", 1))
        if repeat < 1:
            raise ValueError("repeat must be at least one")
        with Image.open(source) as loaded:
            image = loaded.convert("RGB")
            crop = _validated_crop(image, item.get("crop"))
            cropped = image.crop(crop)
        labels = [_normalise_box(box, crop) for box in item.get("boxes", [])]

        image_root = output / "images" / split
        label_root = output / "labels" / split
        image_root.mkdir(parents=True, exist_ok=True)
        label_root.mkdir(parents=True, exist_ok=True)
        for copy_index in range(repeat):
            stem = f"{item['id']}_{copy_index:03d}"
            cropped.save(image_root / f"{stem}.jpg", quality=95)
            text = "".join(
                f"0 {cx:.8f} {cy:.8f} {width:.8f} {height:.8f}\n"
                for cx, cy, width, height in labels
            )
            (label_root / f"{stem}.txt").write_text(text, encoding="utf-8")
            counts[split] += 1
            box_counts[split] += len(labels)

    (output / "data.yaml").write_text(
        f"path: {output.as_posix()}\n"
        "train: images/train\n"
        "val: images/val\n"
        "names:\n"
        "  0: dry_fig\n",
        encoding="utf-8",
    )
    summary = {
        **{f"{split}_images": counts[split] for split in sorted(VALID_SPLITS)},
        **{f"{split}_boxes": box_counts[split] for split in sorted(VALID_SPLITS)},
    }
    (output / "DATASET_METADATA.json").write_text(
        json.dumps(
            {
                "status": "REVIEWED PHONE FIELD EXAMPLES — FIGBOT CAMERA UNVERIFIED",
                "manifest": str(manifest_path),
                **summary,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build_dataset(args.manifest, args.output), indent=2))


if __name__ == "__main__":
    main()
