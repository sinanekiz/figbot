"""Build a dry-fig-only YOLO bootstrap dataset from Mendeley Data.

The source is an image-classification dataset: every positive image contains one
centred dried fig. GrabCut generates approximate boxes. Those boxes are suitable
for a phone experiment, but they are not human-reviewed orchard annotations.
"""

from __future__ import annotations

import argparse
import json
import random
import shutil
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import cv2
import numpy as np


DATASET_ID = "yfhgn8py5f"
DATASET_VERSION = 1
FOLDERS = {
    "jumbo": "9829d4a4-a954-4b70-8495-233b7ec5bed5",
    "medium": "e0562bfa-d83a-47c1-9eae-c77221c0e53e",
    "small": "5c2d7443-56ac-4b94-aad1-79b9a2a87223",
}


def _fetch_json(url: str) -> object:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.mendeley-public-dataset.1+json",
            "User-Agent": "Mozilla/5.0 FIGBOT research dataset builder",
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def _list_source_files() -> dict[str, list[dict]]:
    result = {}
    for subtype, folder_id in FOLDERS.items():
        url = (
            f"https://data.mendeley.com/public-api/datasets/{DATASET_ID}/files"
            f"?version={DATASET_VERSION}&folder_id={folder_id}"
        )
        result[subtype] = list(_fetch_json(url))
    return result


def _download(url: str, destination: Path) -> None:
    if not destination.exists():
        request = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0 FIGBOT research dataset builder"}
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            destination.write_bytes(response.read())


def _approximate_box(image_path: Path) -> tuple[float, float, float, float]:
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Unreadable image: {image_path}")
    original_height, original_width = image.shape[:2]
    scale = min(1.0, 256.0 / max(original_height, original_width))
    if scale < 1.0:
        image = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    height, width = image.shape[:2]
    pad = max(2, int(min(height, width) * 0.04))
    mask = np.zeros((height, width), np.uint8)
    background = np.zeros((1, 65), np.float64)
    foreground = np.zeros((1, 65), np.float64)
    cv2.grabCut(
        image,
        mask,
        (pad, pad, width - 2 * pad, height - 2 * pad),
        background,
        foreground,
        3,
        cv2.GC_INIT_WITH_RECT,
    )
    binary = np.where((mask == 1) | (mask == 3), 1, 0).astype(np.uint8)
    count, _, stats, centroids = cv2.connectedComponentsWithStats(binary)
    centre_x, centre_y = width / 2, height / 2
    candidates = []
    for index in range(1, count):
        x, y, box_width, box_height, area = stats[index]
        if area < 0.01 * width * height:
            continue
        distance = (centroids[index][0] - centre_x) ** 2 + (centroids[index][1] - centre_y) ** 2
        candidates.append((distance, -area, x, y, box_width, box_height))
    if candidates:
        _, _, x, y, box_width, box_height = min(candidates)
    else:
        x, y = int(width * 0.1), int(height * 0.1)
        box_width, box_height = int(width * 0.8), int(height * 0.8)
    margin = int(max(box_width, box_height) * 0.03)
    left = max(0, x - margin)
    top = max(0, y - margin)
    right = min(width, x + box_width + margin)
    bottom = min(height, y + box_height + margin)
    area_ratio = (right - left) * (bottom - top) / (width * height)
    if area_ratio < 0.03 or area_ratio > 0.94:
        left, top, right, bottom = width * 0.1, height * 0.1, width * 0.9, height * 0.9
    return (
        (left + right) / (2 * width),
        (top + bottom) / (2 * height),
        (right - left) / width,
        (bottom - top) / height,
    )


def _add_hard_negatives(source: Path, output: Path, seed: int) -> int:
    image_root = source / "images" / "test"
    examples = [path for path in image_root.glob("*") if path.is_file()]
    random.Random(seed).shuffle(examples)
    split_at = int(len(examples) * 0.8)
    for split, items in (("train", examples[:split_at]), ("val", examples[split_at:])):
        for index, image_path in enumerate(items):
            stem = f"negative_{index:04d}_{image_path.stem}"
            shutil.copy2(image_path, output / "images" / split / f"{stem}{image_path.suffix.lower()}")
            (output / "labels" / split / f"{stem}.txt").write_text("", encoding="utf-8")
    return len(examples)


def _add_fresh_fig_negatives(source: Path, output: Path) -> int:
    """Copy every labelled generic/fresh fig view as an explicit dry-fig negative."""
    created = 0
    for split in ("train", "val"):
        label_root = source / "labels" / split
        image_root = source / "images" / split
        for label_path in label_root.glob("*.txt"):
            if not label_path.stat().st_size:
                continue
            image_path = next(image_root.glob(f"{label_path.stem}.*"))
            stem = f"fresh_fig_negative_{created:04d}_{image_path.stem}"
            shutil.copy2(
                image_path,
                output / "images" / split / f"{stem}{image_path.suffix.lower()}",
            )
            (output / "labels" / split / f"{stem}.txt").write_text("", encoding="utf-8")
            created += 1
    return created


def build_dataset(
    fruit_dataset_root: Path,
    fresh_fig_dataset_root: Path | None,
    output: Path,
    samples_per_subtype: int = 200,
    seed: int = 29,
) -> None:
    if output.exists():
        shutil.rmtree(output)
    for split in ("train", "val"):
        (output / "images" / split).mkdir(parents=True)
        (output / "labels" / split).mkdir(parents=True)

    source_files = _list_source_files()
    jobs = []
    rng = random.Random(seed)
    for subtype, files in source_files.items():
        rng.shuffle(files)
        selected = files[:samples_per_subtype]
        split_at = int(len(selected) * 0.8)
        for index, item in enumerate(selected):
            split = "train" if index < split_at else "val"
            stem = f"dry_fig_{subtype}_{index:04d}"
            destination = output / "images" / split / f"{stem}.jpg"
            jobs.append((item["content_details"]["download_url"], destination))
    with ThreadPoolExecutor(max_workers=12) as executor:
        list(executor.map(lambda job: _download(*job), jobs))

    for split in ("train", "val"):
        for image_path in (output / "images" / split).glob("dry_fig_*.jpg"):
            centre_x, centre_y, width, height = _approximate_box(image_path)
            (output / "labels" / split / f"{image_path.stem}.txt").write_text(
                f"0 {centre_x:.8f} {centre_y:.8f} {width:.8f} {height:.8f}\n",
                encoding="utf-8",
            )

    negatives = _add_hard_negatives(fruit_dataset_root, output, seed)
    fresh_fig_negatives = (
        _add_fresh_fig_negatives(fresh_fig_dataset_root, output)
        if fresh_fig_dataset_root is not None
        else 0
    )
    (output / "data.yaml").write_text(
        f"path: {output.as_posix()}\n"
        "train: images/train\n"
        "val: images/val\n"
        "names:\n"
        "  0: dry_fig\n",
        encoding="utf-8",
    )
    metadata = {
        "status": "BOOTSTRAP DRY-FIG DATASET — APPROXIMATE BOXES — FIELD TEST REQUIRED",
        "dry_fig_images": samples_per_subtype * len(FOLDERS),
        "hard_negative_images": negatives,
        "fresh_fig_negative_images": fresh_fig_negatives,
        "box_generation": "GrabCut centre component; not human reviewed",
        "source": {
            "name": "Dry Fruit Image Dataset",
            "doi": "10.17632/yfhgn8py5f.1",
            "license": "CC BY 4.0",
            "authors": "Choudhary, Kale, Rajput, Meshram, Meshram (2023)",
        },
    }
    (output / "DATASET_METADATA.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fruit-dataset-root", type=Path, required=True)
    parser.add_argument("--fresh-fig-dataset-root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--samples-per-subtype", type=int, default=200)
    parser.add_argument("--seed", type=int, default=29)
    args = parser.parse_args()
    build_dataset(
        args.fruit_dataset_root,
        args.fresh_fig_dataset_root,
        args.output,
        args.samples_per_subtype,
        args.seed,
    )


if __name__ == "__main__":
    main()
