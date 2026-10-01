"""Reproducible analytic reach check for the Rev-G per-arm command lanes."""

from __future__ import annotations

import csv
import json
from dataclasses import replace
from math import pi

from cad.config import parameters as p
from cad.utils import ROOT
from software.kinematics import ArmKinematics, load_arm_geometry


CSV_PATH = ROOT / "simulation" / "results" / "rev_g_arm_lane_reachability.csv"
SUMMARY_PATH = ROOT / "simulation" / "results" / "rev_g_arm_lane_summary.json"


def _values(start: int, stop: int, step: int) -> list[int]:
    return list(range(start, stop + 1, step))


def evaluate() -> tuple[list[dict[str, int | str]], dict[str, object]]:
    geometry = replace(load_arm_geometry(), base_height=p.TEST_ARM_SHOULDER_HEIGHT / 1000.0)
    arm = ArmKinematics(geometry)
    rows: list[dict[str, int | str]] = []
    summaries: dict[str, object] = {}

    for side, (base_x, base_y), y_range, drop in (
        ("left", p.P0_ARM_BASES[0], p.P0_LEFT_ARM_PICK_Y_RANGE, p.P0_BASKET_DROP_POINTS[0]),
        ("right", p.P0_ARM_BASES[1], p.P0_RIGHT_ARM_PICK_Y_RANGE, p.P0_BASKET_DROP_POINTS[1]),
    ):
        success = 0
        total = 0
        for x in _values(int(p.P0_ARM_PICK_X_RANGE[0]), int(p.P0_ARM_PICK_X_RANGE[1]), 10):
            for y in _values(int(y_range[0]), int(y_range[1]), 10):
                for z in _values(int(p.P0_GROUND_PICK_Z_RANGE[0]), int(p.P0_GROUND_PICK_Z_RANGE[1]), 20):
                    result = arm.inverse(
                        (x - base_x) / 1000.0,
                        (y - base_y) / 1000.0,
                        (z - p.P0_ARM_BASE_Z) / 1000.0,
                        tool_pitch=-pi / 2,
                    )
                    total += 1
                    success += int(result.success)
                    rows.append({"side": side, "x_mm": x, "y_mm": y, "z_mm": z, "status": "REACHABLE" if result.success else result.reason})
        drop_result = arm.inverse(
            (drop[0] - base_x) / 1000.0,
            (drop[1] - base_y) / 1000.0,
            (drop[2] - p.P0_ARM_BASE_Z) / 1000.0,
            tool_pitch=-pi / 2,
        )
        summaries[side] = {
            "lane_success": success,
            "lane_total": total,
            "lane_fraction": success / total,
            "drop_reachable": drop_result.success,
        }

    summary: dict[str, object] = {
        "revision": "G",
        "status": "ANALYTIC / PHYSICAL VALIDATION REQUIRED",
        "grid_step_mm": {"xy": 10, "z": 20},
        "results": summaries,
    }
    return rows, summary


def main() -> None:
    rows, summary = evaluate()
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("side", "x_mm", "y_mm", "z_mm", "status"))
        writer.writeheader()
        writer.writerows(rows)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {CSV_PATH.relative_to(ROOT)} and {SUMMARY_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
