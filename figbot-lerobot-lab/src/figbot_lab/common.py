from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JOINTS = ("shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper")


def configure_environment():
    # Confine downloads and telemetry settings to this process and this lab.
    os.environ["HF_HOME"] = str(ROOT / ".cache" / "huggingface")
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
    os.environ["WANDB_MODE"] = "offline"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def current_scene_task():
    task = load_json(ROOT / "configs/current_scene.json").get("task")
    if not isinstance(task, str) or not task.strip():
        raise ValueError("Current scene needs a nonempty task instruction")
    return task.strip()


def save_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    temporary.replace(path)


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def new_run(kind):
    path = ROOT / "runs" / f"{datetime.now(timezone.utc):%Y%m%dT%H%M%S_%fZ}_{kind}"
    path.mkdir(parents=True, exist_ok=False)
    return path


def lab_output(path):
    path = Path(path).resolve()
    if not path.is_relative_to(ROOT.resolve()):
        raise ValueError("Outputs must stay inside figbot-lerobot-lab; source FIGBOT is read-only.")
    return path
