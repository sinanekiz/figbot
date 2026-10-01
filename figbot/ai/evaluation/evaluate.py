"""Evaluate one-label-per-row exports and emit JSON metrics."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

CLASSES = (
    "dry_fig_collect",
    "green_fig_ignore",
    "stone_avoid",
    "leaf_ignore",
    "branch_avoid",
)
NO_OBJECT = "__none__"


def compute_metrics(rows: list[dict[str, str]]) -> dict:
    labels = (*CLASSES, NO_OBJECT)
    confusion = {truth: {pred: 0 for pred in labels} for truth in labels}
    for row in rows:
        truth, prediction = row["truth"], row["prediction"]
        if truth not in labels or prediction not in labels or (truth == prediction == NO_OBJECT):
            raise ValueError(f"unknown class in row: {row}")
        confusion[truth][prediction] += 1
    per_class = {}
    for label in CLASSES:
        tp = confusion[label][label]
        predicted = sum(confusion[truth][label] for truth in labels)
        actual = sum(confusion[label].values())
        per_class[label] = {
            "precision": tp / predicted if predicted else None,
            "recall": tp / actual if actual else None,
            "support": actual,
        }

    def dry_false_positive_rate(source: str):
        total = sum(confusion[source].values())
        return confusion[source]["dry_fig_collect"] / total if total else None

    return {
        "samples": len(rows),
        "class_counts": dict(Counter(row["truth"] for row in rows if row["truth"] != NO_OBJECT)),
        "per_class": per_class,
        "green_to_dry_false_positive_rate": dry_false_positive_rate("green_fig_ignore"),
        "stone_to_dry_false_positive_rate": dry_false_positive_rate("stone_avoid"),
        "confusion_matrix": confusion,
        "unmatched_label": NO_OBJECT,
        "status": "UNVERIFIED — PHYSICAL VALIDATION REQUIRED",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="CSV: truth,prediction[,confidence]")
    parser.add_argument("--output")
    args = parser.parse_args()
    with Path(args.input).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    result = compute_metrics(rows)
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
