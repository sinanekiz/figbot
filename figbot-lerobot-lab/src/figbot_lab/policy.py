from __future__ import annotations

import time

import numpy as np

from .assets import MODELS, validate_model_files, verify_asset
from .common import ROOT, load_json
from .mapping import validate_state


def normalization_stats(path):
    from safetensors.torch import load_file
    result = {}
    for config_name, registry, feature in [
        ("policy_preprocessor.json", "normalizer_processor", "observation.state"),
        ("policy_postprocessor.json", "unnormalizer_processor", "action"),
    ]:
        step = next(s for s in load_json(path / config_name)["steps"] if s["registry_name"] == registry)
        flat = load_file(path / step["state_file"])
        result[feature] = {name: flat[f"{feature}.{name}"].numpy() for name in ("mean", "std")
                           if f"{feature}.{name}" in flat}
    return validate_stats(result)


def validate_stats(stats):
    result = {}
    for feature in ("observation.state", "action"):
        result[feature] = {}
        for name in ("mean", "std"):
            value = np.asarray(stats.get(feature, {}).get(name, []), dtype=np.float32)
            if value.shape != (6,) or not np.isfinite(value).all() or (name == "std" and np.any(value <= 0)):
                raise ValueError(f"Missing/invalid normalization {feature}.{name}. This checkpoint requires explicit target-dataset statistics; reference-test supplies them for base.")
            result[feature][name] = value
    return result


class PolicyRunner:
    def __init__(self, alias="base", device="auto", stats=None, stats_source=None):
        if alias not in MODELS or device not in ('auto', 'cpu', 'cuda'):
            raise ValueError('Unknown model alias or device')
        self.path = ROOT / "models" / alias
        validate_model_files(self.path)
        self.revision = verify_asset(MODELS[alias], self.path)
        backbone_id = load_json(self.path / 'config.json')['vlm_model_name']
        verify_asset(backbone_id, ROOT / 'models/backbone')
        import torch
        from lerobot.policies.smolvla.configuration_smolvla import SmolVLAConfig
        from lerobot.policies.smolvla.modeling_smolvla import SmolVLAPolicy
        from lerobot.policies.factory import make_pre_post_processors

        torch.set_num_threads(min(8, torch.get_num_threads()))
        self.alias = alias
        self.stats = validate_stats(stats) if stats is not None else normalization_stats(self.path)
        self.stats_source = stats_source if stats is not None else "CHECKPOINT_PROCESSOR_STATISTICS"
        self.device = ("cuda" if torch.cuda.is_available() else "cpu") if device == "auto" else device
        if self.device == "cuda" and not torch.cuda.is_available():
            raise ValueError("CUDA unavailable; use --device cpu")
        self.config = SmolVLAConfig.from_pretrained(self.path)
        # Build the architecture on CPU, then strictly restore the complete policy.
        # No separate VLM weight download and no randomly initialized missing keys.
        self.config.device = "cpu"
        self.config.load_vlm_weights = False
        self.config.vlm_model_name = str(ROOT / "models" / "backbone")
        started = time.perf_counter()
        self.policy = SmolVLAPolicy.from_pretrained(self.path, config=self.config, strict=True)
        self.policy.to(self.device).eval()
        self.config.device = self.device
        pre_overrides = {
            "device_processor": {"device": self.device},
            "tokenizer_processor": {"tokenizer_name": self.config.vlm_model_name},
        }
        post_overrides = {"device_processor": {"device": "cpu"}}
        if stats is not None:
            pre_overrides["normalizer_processor"] = {"stats": self.stats}
            post_overrides["unnormalizer_processor"] = {"stats": self.stats}
        self.pre, self.post = make_pre_post_processors(
            self.config, str(self.path),
            preprocessor_overrides=pre_overrides, postprocessor_overrides=post_overrides,
        )
        self.load_seconds = time.perf_counter() - started

    def training_mean_state(self):
        return validate_state(self.stats["observation.state"]["mean"])

    def predict(self, images, state, task, seed=42):
        import torch
        state = validate_state(state)
        if not task.strip():
            raise ValueError("Task instruction is required")
        if not images or not set(images).issubset(self.config.image_features):
            raise ValueError(f"Use image keys from {list(self.config.image_features)}")
        batch = {"observation.state": torch.from_numpy(state), "task": task}
        for key, image in images.items():
            array = np.asarray(image)
            if array.ndim != 3 or array.shape[2] != 3 or array.dtype != np.uint8:
                raise ValueError("Images must be RGB uint8 HWC")
            batch[key] = torch.from_numpy(array.copy()).permute(2, 0, 1).float() / 255.0
        torch.manual_seed(seed)
        self.policy.reset()  # independent observations; no queued stale actions
        if self.device == "cuda":
            torch.cuda.reset_peak_memory_stats()
            torch.cuda.synchronize()
        started = time.perf_counter()
        with torch.inference_mode(), torch.autocast(
                device_type=self.device, dtype=torch.bfloat16, enabled=self.device == "cuda"):
            prepared = self.pre(batch)
            normalized = self.policy.predict_action_chunk(prepared)
            action = self.post(normalized)
        if self.device == "cuda":
            torch.cuda.synchronize()
        latency = time.perf_counter() - started
        output = action.detach().float().cpu().numpy()
        if output.shape != (1, self.config.chunk_size, 6) or not np.isfinite(output).all():
            raise ValueError(f"Invalid policy output: {output.shape}")
        return {"model": MODELS[self.alias], "revision": self.revision, "device": self.device,
                "task": task, "seed": seed, "state": state.tolist(),
                "camera_keys": list(images),
                "missing_cameras": sorted(set(self.config.image_features) - set(images)),
                "load_seconds": self.load_seconds, "inference_seconds": latency,
                "peak_cuda_allocated_mib": torch.cuda.max_memory_allocated() / 2**20 if self.device == "cuda" else None,
                "action_units": "CHECKPOINT_POSTPROCESSED_UNITS_NOT_RAW_MOTOR_COUNTS",
                "normalization_source": self.stats_source,
                "actions": output[0].tolist(), "motor_commands_sent": False,
                "physical_success": "UNVERIFIED"}


def error_metrics(prediction, target, state):
    pred, target, state = map(np.asarray, (prediction, target, state))
    if pred.shape != target.shape or pred.ndim != 2 or pred.shape[1] != 6 or state.shape != (6,):
        raise ValueError("Metrics require aligned [time,6] actions and [6] state")
    if not all(np.isfinite(x).all() for x in (pred, target, state)) or len(pred) == 0:
        raise ValueError("No finite comparable targets")
    mae = np.abs(pred - target).mean(0)
    baseline = np.abs(state - target).mean(0)
    return {"compared_steps": len(pred), "mae_per_joint": mae.tolist(),
            "hold_baseline_mae_per_joint": baseline.tolist(),
            "mae": float(mae.mean()), "hold_baseline_mae": float(baseline.mean()),
            "beats_hold_baseline": bool(mae.mean() < baseline.mean()),
            "interpretation": "OFFLINE_DIAGNOSTIC_NOT_CLOSED_LOOP_SUCCESS"}
