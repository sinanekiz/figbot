from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np

from .common import JOINTS, ROOT, lab_output, load_json, save_json, sha256

EPISODE_FILES = ("episode/camera.avi", "episode/samples.jsonl", "episode/session.json",
                 "timing.jsonl", "status.json", "outcome.json", "training_annotations.json",
                 "corrected_training/corrected_targets.jsonl", "corrected_training/data_review.json")


def read_rows(path):
    import json
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def recorded_task(episode):
    task = load_json(Path(episode) / "episode/session.json").get("task")
    if not isinstance(task, str) or not task.strip():
        raise ValueError("Recorded session needs its original task instruction")
    return task.strip()


def snapshot_episode(source, name=None):
    source = Path(source).resolve()
    name = name or source.name
    if Path(name).name != name or name in (".", ".."):
        raise ValueError("Snapshot name must be a simple folder name")
    destination = lab_output(ROOT / "data" / "figbot" / name)
    old_manifest = None
    if destination.exists():
        old_manifest = load_json(destination / "source_manifest.json")
        if old_manifest["source"] != str(source):
            raise ValueError("Snapshot belongs to a different source")
        for relative, digest in old_manifest["files"].items():
            if sha256(source / relative) != digest or sha256(destination / relative) != digest:
                raise ValueError(f"Existing snapshot or source changed: {relative}")
    if source == destination or source.is_relative_to(destination) or destination.is_relative_to(source):
        raise ValueError("Snapshot source and destination must be independent")
    # Read and validate before any copy; active captures are never imported.
    if load_json(source / "status.json").get("state") != "STOPPED":
        raise ValueError("Only stopped recordings can be imported")
    if load_json(source / "episode/session.json").get("status") != "CLOSED":
        raise ValueError("Recording metadata is not CLOSED")
    destination.mkdir(parents=True, exist_ok=old_manifest is not None)
    manifest = {"source": str(source), "source_modified": False, "files": {}}
    for relative in EPISODE_FILES:
        src = source / relative
        if not src.exists():
            if relative in ("outcome.json", "training_annotations.json") or relative.startswith("corrected_training/"):
                continue
            raise ValueError(f"Missing required recording file: {relative}")
        before = sha256(src)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            shutil.copy2(src, target)
        if before != sha256(target) or before != sha256(src):
            raise ValueError(f"Copy verification failed: {relative}")
        manifest["files"][relative] = before
    save_json(destination / "source_manifest.json", manifest)
    audit = audit_episode(destination)
    save_json(destination / "audit.json", audit)
    return destination, audit


def read_episode(path):
    path = Path(path)
    rows = read_rows(path / "episode/samples.jsonl")
    timing = read_rows(path / "timing.jsonl")
    if not rows or len(rows) != len(timing):
        raise ValueError("Empty recording or timing/sample mismatch")
    indices, positions, elapsed, capture, encoder = [], [], [], [], []
    for row, clock in zip(rows, timing, strict=True):
        index = row["frame_index"]
        if index != clock["frame_index"] or type(index) is not int or index < 0:
            raise ValueError("Invalid camera/sample frame association")
        motors = sorted(row["motor_readings"], key=lambda m: m["id"])
        if [m["id"] for m in motors] != list(range(1, 7)) or not all(m.get("ok") for m in motors):
            raise ValueError("Six successful motor readings required")
        indices.append(index)
        positions.append([m["position"] for m in motors])
        elapsed.append(row["elapsed_seconds"])
        capture.append(clock["estimated_capture_monotonic"])
        start, end = clock["encoder_read_start"], clock["encoder_read_end"]
        if not np.isfinite([start, end]).all() or not 0 <= end - start <= .25:
            raise ValueError("Invalid encoder read interval")
        encoder.append((start + end) / 2)
    q, t, camera_t, encoder_t = map(lambda x: np.asarray(x, dtype=np.float64),
                                    (positions, elapsed, capture, encoder))
    if not all(np.isfinite(x).all() for x in (q, t, camera_t, encoder_t)):
        raise ValueError("Nonfinite recording values")
    if q.shape != (len(rows), 6) or np.any((q < 0) | (q > 4095)):
        raise ValueError("Recorded positions outside single-turn encoder range")
    if np.any(np.abs(np.diff(q, axis=0)) > 2048):
        raise ValueError("Recorded encoder wrap/discontinuity requires coordinate review")
    if indices != list(range(len(rows))):
        raise ValueError("Frame indices must be continuous from zero")
    if any(np.any(np.diff(x) <= 0) for x in (t, camera_t, encoder_t)):
        raise ValueError("Recording clocks must be strictly increasing")
    return {"rows": rows, "timing": timing, "raw": q, "elapsed": t,
            "capture": camera_t, "encoder": encoder_t, "indices": indices}


def audit_episode(path):
    import cv2
    data = read_episode(path)
    cap = cv2.VideoCapture(str(Path(path) / "episode/camera.avi"))
    if not cap.isOpened():
        raise ValueError("Recording video could not be opened")
    count = 0
    try:
        while True:
            ok, _ = cap.read()
            if not ok:
                break
            count += 1
    finally:
        cap.release()
    if count != len(data["rows"]):
        raise ValueError(f"Decoded video frames {count} != sample count {len(data['rows'])}")
    delta = np.abs(data["capture"] - data["encoder"])
    return {"frames": count, "duration_s": float(data["elapsed"][-1]),
            "camera_encoder_max_separation_s": float(delta.max()),
            "samples_over_200ms": int((delta > .2).sum()),
            "max_encoder_gap_s": float(np.diff(data["encoder"]).max()) if count > 1 else 0.0,
            "joints": list(JOINTS), "observed_raw_min": data["raw"].min(0).tolist(),
            "observed_raw_max": data["raw"].max(0).tolist(),
            "action_source": "MEASURED_POSITIONS_ONLY_NOT_COMMANDED_ACTIONS",
            "pretrained_state_mapping": "REQUIRES_EXPLICIT_CALIBRATION",
            "physical_success": "NOT_ESTABLISHED_BY_THIS_AUDIT"}


def video_frame(path, index):
    import cv2
    if index < 0:
        raise ValueError("Negative frame index")
    cap = cv2.VideoCapture(str(path))
    try:
        # Decode sequentially so codec seek rounding cannot silently offset alignment.
        for _ in range(index + 1):
            ok, frame = cap.read()
            if not ok:
                raise ValueError(f"Video has no frame {index}")
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    finally:
        cap.release()
