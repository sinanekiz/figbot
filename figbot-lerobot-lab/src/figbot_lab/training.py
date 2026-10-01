from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .common import JOINTS, ROOT, lab_output, load_json, save_json
from .mapping import JointMapping
from .records import read_episode, read_rows, recorded_task


def select_training_rows(episode, mapping):
    """Resample reviewed targets at 10 Hz; keep entire pickup cycles in one split.

    Targets are the old project's corrected future measured positions, not
    demonstrated leader commands. That limitation follows the exported dataset.
    """
    episode = Path(episode)
    data = read_episode(episode)
    if load_json(episode / "outcome.json").get("outcome") != "SUCCESSFUL_MANUAL_DEMONSTRATION":
        raise ValueError("Training export requires an explicitly successful manual demonstration")
    corrections = read_rows(episode / "corrected_training/corrected_targets.jsonl")
    review = load_json(episode / "corrected_training/data_review.json")
    annotations = load_json(episode / "training_annotations.json")
    if len(corrections) != len(data["rows"]):
        raise ValueError("Corrected targets and observations have different lengths")
    # Check provenance before trusting the old project's reviewed targets.
    from .common import sha256
    required_sources = {'episode/camera.avi', 'episode/samples.jsonl', 'timing.jsonl'}
    if not required_sources.issubset({p.replace('\\', '/') for p in review.get('source_hashes', {})}):
        raise ValueError("Corrected targets require hashes for video, samples and timing")
    for relative, digest in review["source_hashes"].items():
        candidate = (episode / relative).resolve()
        if not candidate.is_relative_to(episode.resolve()) or sha256(candidate) != digest:
            raise ValueError("Corrected target provenance mismatch")
    ct = np.asarray([r["time"] for r in corrections], dtype=float)
    targets = np.asarray([r["corrected"] for r in corrections], dtype=float)
    if targets.shape != data["raw"].shape or not np.isfinite(targets).all() or not np.isfinite(ct).all() or np.any(np.diff(ct) <= 0):
        raise ValueError("Invalid corrected targets")
    offset = float(np.median(data["encoder"] - data["elapsed"]))
    encoder_t, camera_t = data["encoder"] - offset, data["capture"] - offset
    if not np.allclose(ct, encoder_t, atol=1e-4):
        raise ValueError("Corrected target times disagree with source encoder times")
    excluded = review["excluded_suspect_intervals"]
    for interval in excluded:
        if len(interval) != 2 or not np.isfinite(interval).all() or interval[0] > interval[1]:
            raise ValueError("Invalid excluded interval in data review")
    cycles = annotations["cycles"]
    if len(cycles) < 2:
        raise ValueError("At least two whole pickup cycles are needed for a separate holdout")
    previous_end = None
    for cycle in cycles:
        start, end = cycle["start"], cycle["end"]
        if (not np.isfinite([start, end]).all() or start >= end
                or (previous_end is not None and start < previous_end)):
            raise ValueError("Pickup cycles must be ordered, finite and nonoverlapping")
        previous_end = end
    result = []
    for cycle_id, cycle in enumerate(cycles):
        segment, last_time, previous_frame = 0, None, None
        for stamp in np.arange(cycle["start"] + .2, cycle["end"] - .2, .1):
            index = int(np.argmin(abs(camera_t - stamp)))
            target_t = stamp + .1
            if (abs(camera_t[index] - stamp) > .06 or index == previous_frame
                    or abs(camera_t[index] - encoder_t[index]) > .2
                    or stamp < encoder_t[0] or target_t > encoder_t[-1]
                    or any(stamp - .2 <= b and target_t + .2 >= a for a, b in excluded)):
                continue
            bracket = np.searchsorted(encoder_t, stamp)
            bracket_end = np.searchsorted(encoder_t, target_t)
            if np.any(np.diff(encoder_t[max(0, bracket - 1):bracket_end + 1]) > .25):
                continue
            if last_time is not None and stamp - last_time > .15:
                segment += 1
            state = np.array([np.interp(stamp, encoder_t, data["raw"][:, j]) for j in range(6)])
            target = np.array([np.interp(target_t, ct, targets[:, j]) for j in range(6)])
            result.append({"cycle": cycle_id, "segment": segment,
                           "split": "validation" if cycle_id == len(cycles) - 1 else "train",
                           "source_frame": index, "source_time_s": float(stamp),
                           "state": mapping.convert(state), "action": mapping.convert(target)})
            previous_frame, last_time = index, stamp
    if not result or not all(any(r["split"] == split for r in result) for split in ("train", "validation")):
        raise ValueError("No usable train/validation data after quality filtering")
    return result


def export_training(episode, mapping_path, name="figbot_figs"):
    from lerobot.datasets.lerobot_dataset import LeRobotDataset
    import cv2

    mapping = JointMapping(mapping_path)
    if not name or not all(c.isalnum() or c in "_-" for c in name):
        raise ValueError("Use a simple dataset name")
    rows = select_training_rows(episode, mapping)
    task = recorded_task(episode)
    output = lab_output(ROOT / "data/exported" / name)
    output.mkdir(parents=True, exist_ok=False)
    wanted = {r["source_frame"] for r in rows}
    images = {}
    cap = cv2.VideoCapture(str(Path(episode) / "episode/camera.avi"))
    try:
        for index in range(max(wanted) + 1):
            ok, image = cap.read()
            if not ok:
                raise ValueError("Training source video is truncated")
            if index in wanted:
                images[index] = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    finally:
        cap.release()
    shape = next(iter(images.values())).shape
    manifest = {"source": str(Path(episode).resolve()), "mapping": mapping.document,
                "action_source": "CORRECTED_FUTURE_MEASURED_POSITIONS_NOT_LEADER_COMMANDS",
                "synthetic_gripper_targets": True, "fps": 10,
                "holdout": "LAST_WHOLE_PICKUP_CYCLE_SAME_SCENE_NOT_INDEPENDENT_SCENE",
                "physical_validation": "UNVERIFIED", "task": task, "splits": {}}
    features = {
        "observation.state": {"dtype": "float32", "shape": (6,), "names": list(JOINTS)},
        "action": {"dtype": "float32", "shape": (6,), "names": list(JOINTS)},
        "observation.images.camera1": {"dtype": "image", "shape": shape, "names": ["height", "width", "channels"]},
    }
    for split in ("train", "validation"):
        selected = [r for r in rows if r["split"] == split]
        dataset = LeRobotDataset.create(f"local/{name}_{split}", fps=10, features=features,
                                        root=output / split, robot_type="so101_follower", use_videos=False,
                                        video_backend="pyav")
        previous_group = None
        try:
            for row in selected:
                group = row["cycle"], row["segment"]
                if previous_group is not None and group != previous_group:
                    dataset.save_episode()
                dataset.add_frame({"observation.state": row["state"], "action": row["action"],
                                   "observation.images.camera1": images[row["source_frame"]],
                                   "task": task})
                previous_group = group
            dataset.save_episode()
        finally:
            dataset.finalize()
        manifest["splits"][split] = {"frames": len(selected), "cycles": sorted({r["cycle"] for r in selected}),
                                      "repo_id": f"local/{name}_{split}"}
    save_json(output / "export_manifest.json", manifest)
    save_json(output / "sample_provenance.json", [{k: v for k, v in r.items() if k not in ("state", "action")} for r in rows])
    return output


def training_command(dataset, alias):
    dataset = lab_output(dataset)
    manifest = load_json(dataset / "export_manifest.json")
    if manifest["mapping"].get("status") != "VERIFIED":
        raise ValueError("Unverified dataset mapping")
    checkpoint = ROOT / "models" / alias
    config = load_json(checkpoint / "config.json")
    config.update(pretrained_path=str(checkpoint), device="cuda", push_to_hub=False,
                  vlm_model_name=str(ROOT / "models/backbone"), load_vlm_weights=False,
                  chunk_size=16, n_action_steps=16, use_amp=True)
    config["input_features"] = {k: v for k, v in config["input_features"].items()
                                if k in ("observation.state", "observation.images.camera1")}
    # Keep validation entirely outside the training loader, including stats.
    train_config = {"dataset": {"repo_id": manifest["splits"]["train"]["repo_id"],
                                 "root": str(dataset / "train"), "video_backend": "pyav"},
                    "policy": config, "batch_size": 1, "num_workers": 0, "steps": 1000,
                    "env_eval_freq": 0, "save_freq": 500, "log_freq": 25,
                    "wandb": {"enable": False}, "save_checkpoint_to_hub": False,
                    "output_dir": str(ROOT / "runs" / "finetune_first"), "job_name": "figbot_adaptation"}
    path = dataset / "train_config.json"
    save_json(path, train_config)
    return f'& "{ROOT / ".venv/Scripts/lerobot-train.exe"}" --config_path="{path}"'
