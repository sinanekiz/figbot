from __future__ import annotations

import numpy as np

from .common import JOINTS, load_json


class JointMapping:
    """Explicit piecewise calibration; no inference from demonstration min/max."""

    def __init__(self, path):
        self.document = load_json(path)
        if self.document.get("status") != "VERIFIED" or not self.document.get("evidence"):
            raise ValueError("Joint mapping is UNVERIFIED; supply calibration evidence before local inference")
        if self.document.get("joint_order") != list(JOINTS):
            raise ValueError("Joint order does not match SO-101")
        if self.document.get("state_convention") != "lerobot_range_m100_100_gripper_0_100":
            raise ValueError("Unsupported state convention; degrees and raw counts are not interchangeable")
        self.knots = []
        for name in JOINTS:
            entry = self.document["joints"][name]
            raw = np.asarray(entry["raw_counts"], dtype=float)
            normalized = np.asarray(entry["policy_values"], dtype=float)
            if raw.ndim != 1 or len(raw) < 2 or raw.shape != normalized.shape:
                raise ValueError(f"Invalid mapping knots for {name}")
            if not np.isfinite(raw).all() or not np.isfinite(normalized).all() or np.any(np.diff(raw) <= 0):
                raise ValueError(f"Unsorted/nonfinite calibration for {name}")
            if np.any((raw < 0) | (raw > 4095)):
                raise ValueError(f"Raw calibration outside single-turn encoder range for {name}")
            if not (np.all(np.diff(normalized) > 0) or np.all(np.diff(normalized) < 0)):
                raise ValueError(f"Nonmonotonic policy calibration for {name}")
            lo, hi = (0, 100) if name == "gripper" else (-100, 100)
            if normalized.min() < lo or normalized.max() > hi:
                raise ValueError(f"Out of convention calibration for {name}")
            self.knots.append((raw, normalized))

    def convert(self, raw):
        raw = np.asarray(raw, dtype=float)
        if raw.shape[-1:] != (6,) or not np.isfinite(raw).all():
            raise ValueError("Expected six finite raw motor values")
        result = np.empty_like(raw)
        for j, (x, y) in enumerate(self.knots):
            if np.any(raw[..., j] < x[0]) or np.any(raw[..., j] > x[-1]):
                raise ValueError(f"{JOINTS[j]} outside calibrated range; no clipping or extrapolation")
            result[..., j] = np.interp(raw[..., j], x, y)
        return result.astype(np.float32)


def validate_state(state):
    state = np.asarray(state, dtype=np.float32)
    if state.shape != (6,) or not np.isfinite(state).all():
        raise ValueError("State must contain six finite values in checkpoint units")
    return state
