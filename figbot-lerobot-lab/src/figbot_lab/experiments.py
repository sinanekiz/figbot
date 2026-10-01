from __future__ import annotations

from pathlib import Path

import numpy as np

from .assets import DATASET, verify_asset
from .common import ROOT, load_json, new_run, save_json
from .mapping import JointMapping
from .policy import PolicyRunner, error_metrics
from .records import read_episode, recorded_task, video_frame


def reference_test(alias="base", device="auto", frames=(0, 120, 240)):
    from lerobot.datasets.lerobot_dataset import LeRobotDataset
    from PIL import Image

    root = ROOT / "data/reference"
    verify_asset(DATASET, root, repo_type='dataset')
    info = load_json(root / "meta/info.json")
    revision = load_json(ROOT / "assets.lock.json")[f"dataset:{DATASET}"]["revision"]
    dataset = LeRobotDataset(DATASET, root=root, revision=revision, video_backend="pyav",
                             delta_timestamps={"action": [i / info["fps"] for i in range(50)]})
    runner = PolicyRunner(alias, device,
                          stats=load_json(root / "meta/stats.json") if alias == "base" else None,
                          stats_source=f"REFERENCE_DATASET:{DATASET}@{revision}")
    run = new_run(f"reference_{alias}")
    results = []
    for index in frames:
        if index < 0 or index >= len(dataset):
            raise ValueError(f"Reference frame out of range: {index}")
        sample = dataset[index]
        # Mapping is explicitly recorded; this is an installation/transfer diagnostic.
        images = {}
        source_mapping = {"observation.images.up": "observation.images.camera1",
                          "observation.images.side": "observation.images.camera2"}
        for source, target in source_mapping.items():
            if source in sample:
                image = (sample[source].permute(1, 2, 0).numpy() * 255).round().clip(0, 255).astype(np.uint8)
                images[target] = image
                Image.fromarray(image).save(run / f"frame_{index}_{target.rsplit('.', 1)[-1]}.jpg")
        task = "Pick up a cube and place in the bin" if alias == "pickplace" else sample["task"]
        result = runner.predict(images, sample["observation.state"].numpy(), task)
        valid = ~sample["action_is_pad"].numpy().astype(bool)
        result["metrics"] = error_metrics(np.asarray(result["actions"])[valid], sample["action"].numpy()[valid],
                                           sample["observation.state"].numpy())
        result.update(frame_index=index, dataset=DATASET, dataset_revision=revision,
                      camera_mapping=source_mapping, dataset_fps=info["fps"], source_task=sample["task"],
                      held_out_from_pretraining="UNKNOWN", scope="PUBLIC_REFERENCE_SMOKE_TEST")
        save_json(run / f"frame_{index}.json", result)
        results.append(result)
        print(f"frame={index} inference={result['inference_seconds']:.3f}s MAE={result['metrics']['mae']:.3f}", flush=True)
    save_json(run / "summary.json", {"model": alias, "frames": len(results), "results": results,
                                     "physical_test": False, "training_performed": False})
    return run


def local_test(episode, mapping_path, frame, alias="pickplace", device="auto"):
    # Validate calibration BEFORE loading weights, so unverified units fail promptly.
    mapping = JointMapping(mapping_path)
    data = read_episode(episode)
    if frame < 0 or frame >= len(data["rows"]):
        raise ValueError("Local frame out of range")
    t = data["capture"][frame]
    if not data["encoder"][0] <= t <= data["encoder"][-1]:
        raise ValueError("Camera time outside recorded encoder interval")
    if abs(t - data["encoder"][frame]) > .2:
        raise ValueError("Camera and encoder alignment exceeds 200ms")
    bracket = np.searchsorted(data["encoder"], t)
    if 0 < bracket < len(data["encoder"]) and data["encoder"][bracket] - data["encoder"][bracket - 1] > .25:
        raise ValueError("Encoder interpolation crosses a recording gap")
    raw = np.array([np.interp(t, data["encoder"], data["raw"][:, j]) for j in range(6)])
    state = mapping.convert(raw)
    image = video_frame(Path(episode) / "episode/camera.avi", data["indices"][frame])
    runner = PolicyRunner(alias, device)
    result = runner.predict({"observation.images.camera1": image}, state, recorded_task(episode))
    result.update(scope="LOCAL_SINGLE_CAMERA_TRANSFER_PROBE", episode=str(episode), frame_index=frame,
                  mapping=mapping.document, raw_counts=raw.tolist(),
                  note="Single camera differs from published multi-camera tasks. No grasp score is inferred.")
    run = new_run(f"local_{alias}")
    from PIL import Image
    Image.fromarray(image).save(run / "input.jpg")
    save_json(run / "prediction.json", result)
    return run
