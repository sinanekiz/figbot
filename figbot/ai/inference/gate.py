"""Conservative post-detection pick gate; not a safety-rated function."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

SUPPORTED = {
    "dry_fig_collect",
    "green_fig_ignore",
    "stone_avoid",
    "leaf_ignore",
    "branch_avoid",
}
BLOCKING = {"green_fig_ignore", "stone_avoid", "branch_avoid"}


@dataclass(frozen=True)
class Detection:
    label: str
    confidence: float
    box: tuple[float, float, float, float]

    @classmethod
    def from_dict(cls, value: dict) -> "Detection":
        label = str(value["label"])
        confidence = float(value["confidence"])
        box = tuple(float(v) for v in value["box"])
        if label not in SUPPORTED or len(box) != 4 or not 0.0 <= confidence <= 1.0:
            raise ValueError("invalid detection")
        x1, y1, x2, y2 = box
        if x2 <= x1 or y2 <= y1:
            raise ValueError("box must have positive area")
        return cls(label, confidence, box)  # type: ignore[arg-type]


def intersection_over_candidate(candidate: Detection, obstacle: Detection) -> float:
    ax1, ay1, ax2, ay2 = candidate.box
    bx1, by1, bx2, by2 = obstacle.box
    width = max(0.0, min(ax2, bx2) - max(ax1, bx1))
    height = max(0.0, min(ay2, by2) - max(ay1, by1))
    return width * height / ((ax2 - ax1) * (ay2 - ay1))


def pick_candidates(
    detections: Iterable[Detection],
    min_confidence: float,
    blocking_confidence: float,
    max_blocking_overlap: float,
) -> list[Detection]:
    """Return candidates that pass configured experimental thresholds.

    Thresholds are UNVERIFIED and must be selected on held-out data, then tested
    in the physical system. Returning a candidate is not permission to energize.
    """
    items = list(detections)
    blockers = [d for d in items if d.label in BLOCKING and d.confidence >= blocking_confidence]
    result = []
    for item in items:
        if item.label != "dry_fig_collect" or item.confidence < min_confidence:
            continue
        if any(intersection_over_candidate(item, blocker) > max_blocking_overlap for blocker in blockers):
            continue
        result.append(item)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--min-confidence", type=float, default=0.80)
    parser.add_argument("--blocking-confidence", type=float, default=0.40)
    parser.add_argument("--max-blocking-overlap", type=float, default=0.05)
    args = parser.parse_args()
    for value in (args.min_confidence, args.blocking_confidence, args.max_blocking_overlap):
        if not 0.0 <= value <= 1.0:
            parser.error("thresholds must be in [0,1]")
    raw = json.loads(Path(args.input).read_text(encoding="utf-8"))
    detections = [Detection.from_dict(item) for item in raw]
    selected = pick_candidates(
        detections, args.min_confidence, args.blocking_confidence, args.max_blocking_overlap
    )
    print(json.dumps([d.__dict__ for d in selected], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

