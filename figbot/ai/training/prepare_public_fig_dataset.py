"""Build a small, reproducible fig-only YOLO dataset from public LVIS material.

This is a bootstrap dataset for the Android field experiment, not a substitute for
FIGBOT orchard imagery. It extracts the LVIS `fig` category, downloads only the
referenced COCO images, and adds non-fig fruit/vegetable images as hard negatives.
"""

from __future__ import annotations

import argparse
import json
import random
import shutil
import urllib.request
from pathlib import Path

from PIL import Image


def _write_yolo_label(path: Path, boxes: list[list[float]], width: int, height: int) -> None:
    rows = []
    for x, y, box_width, box_height in boxes:
        rows.append(
            "0 "
            f"{(x + box_width / 2) / width:.8f} "
            f"{(y + box_height / 2) / height:.8f} "
            f"{box_width / width:.8f} "
            f"{box_height / height:.8f}"
        )
    path.write_text("\n".join(rows), encoding="utf-8")


def _download_lvis_split(lvis_root: Path, output: Path, split: str) -> int:
    payload = json.loads((lvis_root / f"lvis_v1_{split}.json").read_text(encoding="utf-8"))
    fig_category_ids = {
        item["id"]
        for item in payload["categories"]
        if item["name"] in {"fig", "fig_(fruit)", "fig_fruit"}
    }
    boxes_by_image: dict[int, list[list[float]]] = {}
    for annotation in payload["annotations"]:
        if annotation["category_id"] in fig_category_ids:
            boxes_by_image.setdefault(annotation["image_id"], []).append(annotation["bbox"])

    images = {item["id"]: item for item in payload["images"] if item["id"] in boxes_by_image}
    destination_split = "train" if split == "train" else "val"
    for image_id, image in images.items():
        stem = f"lvis_{split}_{image_id}"
        image_path = output / "images" / destination_split / f"{stem}.jpg"
        image_url = image.get("coco_url") or image.get("flickr_url")
        if not image_path.exists():
            download_url = image_url.replace(
                "http://images.cocodataset.org/",
                "https://s3.amazonaws.com/images.cocodataset.org/",
            )
            urllib.request.urlretrieve(download_url, image_path)
        _write_yolo_label(
            output / "labels" / destination_split / f"{stem}.txt",
            boxes_by_image[image_id],
            image["width"],
            image["height"],
        )
    return len(images)


def _add_fruit_dataset_examples(source: Path, output: Path, seed: int) -> tuple[int, int]:
    image_root = source / "images" / "test"
    label_root = source / "labels" / "test"
    examples: list[tuple[Path, list[str]]] = []
    for image_path in sorted(image_root.glob("*")):
        if not image_path.is_file():
            continue
        source_label = label_root / f"{image_path.stem}.txt"
        lines = source_label.read_text(encoding="utf-8").splitlines() if source_label.exists() else []
        fig_lines = ["0" + line[2:] for line in lines if line.startswith("27 ")]
        examples.append((image_path, fig_lines))

    rng = random.Random(seed)
    rng.shuffle(examples)
    positive = [item for item in examples if item[1]]
    negative = [item for item in examples if not item[1]]

    # Preserve at least one public fig image for validation; split hard negatives 80/20.
    train_examples = positive[:-1] + negative[: int(len(negative) * 0.8)]
    val_examples = positive[-1:] + negative[int(len(negative) * 0.8) :]
    for split, items in (("train", train_examples), ("val", val_examples)):
        for index, (image_path, fig_lines) in enumerate(items):
            stem = f"fv_{index:04d}_{image_path.stem}"
            shutil.copy2(image_path, output / "images" / split / f"{stem}{image_path.suffix.lower()}")
            (output / "labels" / split / f"{stem}.txt").write_text(
                "\n".join(fig_lines), encoding="utf-8"
            )
    return len(positive), len(negative)


def _read_yolo_boxes(path: Path, width: int, height: int) -> list[list[float]]:
    boxes = []
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if len(fields) != 5 or fields[0] != "0":
            continue
        centre_x, centre_y, box_width, box_height = map(float, fields[1:])
        boxes.append(
            [
                (centre_x - box_width / 2) * width,
                (centre_y - box_height / 2) * height,
                box_width * width,
                box_height * height,
            ]
        )
    return boxes


def _crop_boxes(
    boxes: list[list[float]], crop_left: int, crop_top: int, crop_size: int
) -> list[list[float]]:
    cropped = []
    crop_right = crop_left + crop_size
    crop_bottom = crop_top + crop_size
    for x, y, width, height in boxes:
        centre_x = x + width / 2
        centre_y = y + height / 2
        if not (crop_left <= centre_x <= crop_right and crop_top <= centre_y <= crop_bottom):
            continue
        clipped_left = max(x, crop_left)
        clipped_top = max(y, crop_top)
        clipped_right = min(x + width, crop_right)
        clipped_bottom = min(y + height, crop_bottom)
        clipped_width = clipped_right - clipped_left
        clipped_height = clipped_bottom - clipped_top
        if clipped_width <= 1 or clipped_height <= 1:
            continue
        cropped.append(
            [
                clipped_left - crop_left,
                clipped_top - crop_top,
                clipped_width,
                clipped_height,
            ]
        )
    return cropped


def _create_object_centric_crops(output: Path, split: str, context: float = 4.0) -> int:
    """Create one square training view around every annotated fig.

    LVIS contains many tiny figs inside wide scene images. Phone testing is much closer
    to these object-centric crops than to a full COCO frame, and exact duplicate images
    do not add the scale information that the detector needs.
    """
    image_root = output / "images" / split
    label_root = output / "labels" / split
    positive_labels = [path for path in label_root.glob("*.txt") if path.stat().st_size]
    created = 0
    for label_path in positive_labels:
        source_image_path = next(image_root.glob(f"{label_path.stem}.*"))
        with Image.open(source_image_path) as source_image:
            source_image = source_image.convert("RGB")
            image_width, image_height = source_image.size
            boxes = _read_yolo_boxes(label_path, image_width, image_height)
            for target_index, (x, y, width, height) in enumerate(boxes):
                crop_size = int(round(max(width, height) * context))
                crop_size = max(128, min(crop_size, image_width, image_height))
                centre_x = x + width / 2
                centre_y = y + height / 2
                crop_left = int(round(centre_x - crop_size / 2))
                crop_top = int(round(centre_y - crop_size / 2))
                crop_left = max(0, min(crop_left, image_width - crop_size))
                crop_top = max(0, min(crop_top, image_height - crop_size))
                crop_labels = _crop_boxes(boxes, crop_left, crop_top, crop_size)
                if not crop_labels:
                    continue
                crop = source_image.crop(
                    (crop_left, crop_top, crop_left + crop_size, crop_top + crop_size)
                )
                stem = f"{label_path.stem}_crop_{target_index:03d}"
                crop.save(image_root / f"{stem}.jpg", quality=92)
                _write_yolo_label(label_root / f"{stem}.txt", crop_labels, crop_size, crop_size)
                created += 1
    return created


def build_dataset(
    lvis_root: Path,
    fruit_dataset_root: Path,
    output: Path,
    seed: int = 17,
) -> None:
    if output.exists():
        shutil.rmtree(output)
    for split in ("train", "val"):
        (output / "images" / split).mkdir(parents=True, exist_ok=True)
        (output / "labels" / split).mkdir(parents=True, exist_ok=True)

    lvis_train = _download_lvis_split(lvis_root, output, "train")
    lvis_val = _download_lvis_split(lvis_root, output, "val")
    fv_positive, fv_negative = _add_fruit_dataset_examples(fruit_dataset_root, output, seed)
    object_crops_train = _create_object_centric_crops(output, "train")
    object_crops_val = _create_object_centric_crops(output, "val")

    (output / "data.yaml").write_text(
        f"path: {output.as_posix()}\n"
        "train: images/train\n"
        "val: images/val\n"
        "names:\n"
        "  0: fig\n",
        encoding="utf-8",
    )
    metadata = {
        "status": "BOOTSTRAP DATASET — NOT FIGBOT FIELD VALIDATION",
        "lvis_fig_train_images": lvis_train,
        "lvis_fig_val_images": lvis_val,
        "fruit_dataset_fig_images": fv_positive,
        "fruit_dataset_hard_negative_images": fv_negative,
        "object_centric_training_crops": object_crops_train,
        "object_centric_validation_crops": object_crops_val,
        "sources": [
            {
                "name": "LVIS v1",
                "url": "https://www.lvisdataset.org/",
                "note": "Annotations and image URLs; individual image licenses remain source-specific.",
            },
            {
                "name": "Fruits-And-Vegetables-Detection-Dataset",
                "url": "https://github.com/henningheyen/Fruits-And-Vegetables-Detection-Dataset",
                "license": "MIT repository; derived from LVIS and source image licenses still apply.",
            },
        ],
    }
    (output / "DATASET_METADATA.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lvis-root", type=Path, required=True)
    parser.add_argument("--fruit-dataset-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=17)
    args = parser.parse_args()
    build_dataset(
        args.lvis_root,
        args.fruit_dataset_root,
        args.output,
        args.seed,
    )


if __name__ == "__main__":
    main()
