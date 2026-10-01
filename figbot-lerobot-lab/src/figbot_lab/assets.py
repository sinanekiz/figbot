from __future__ import annotations

from pathlib import Path
import re

from .common import ROOT, load_json, save_json, sha256

MODELS = {
    "base": "lerobot/smolvla_base",
    "pickplace": "Harrysunshine/so101-smolvla-9task",
}
DATASET = "lerobot/svla_so101_pickplace"


def download_repo(repo_id, destination, repo_type="model", patterns=None):
    from huggingface_hub import HfApi, snapshot_download

    lock_path = ROOT / "assets.lock.json"
    lock = load_json(lock_path) if lock_path.exists() else {}
    key = f"{repo_type}:{repo_id}"
    if key not in lock:
        info = HfApi().repo_info(repo_id, repo_type=repo_type)
        lock[key] = {"revision": info.sha, "url": f"https://huggingface.co/{'datasets/' if repo_type == 'dataset' else ''}{repo_id}"}
        save_json(lock_path, lock)
    revision = lock[key]["revision"]
    print(f"Downloading {repo_id} @ {revision}", flush=True)
    snapshot_download(repo_id, repo_type=repo_type, revision=revision,
                      local_dir=destination, allow_patterns=patterns, max_workers=2)
    files = {str(p.relative_to(destination)).replace('\\', '/'): sha256(p)
             for p in Path(destination).rglob('*')
             if p.is_file() and '.cache' not in p.relative_to(destination).parts}
    lock[key]["files_sha256"] = files
    save_json(lock_path, lock)
    return Path(destination)


def prepare_model(alias):
    if alias not in MODELS:
        raise ValueError(f"Unknown model: {alias}")
    destination = ROOT / "models" / alias
    download_repo(MODELS[alias], destination, patterns=["*.json", "*.safetensors", "README.md"])
    config = load_json(destination / "config.json")
    backbone_id = config["vlm_model_name"]
    # A complete policy checkpoint already includes the VLM weights. Only fetch
    # architecture/tokenizer/processor files; strict loading verifies this later.
    download_repo(backbone_id, ROOT / "models" / "backbone",
                  patterns=["*.json", "*.txt", "*.model", "*.jinja", "README.md"])
    validate_model_files(destination)
    return destination


def validate_model_files(path):
    path = Path(path).resolve()
    required = ["config.json", "model.safetensors", "policy_preprocessor.json", "policy_postprocessor.json"]
    for name in required:
        if not (path / name).is_file():
            raise ValueError(f"Missing checkpoint file: {name}; run download.")
    for name, registry in [(required[2], "normalizer_processor"), (required[3], "unnormalizer_processor")]:
        steps = load_json(path / name)["steps"]
        normalizers = [s for s in steps if s.get("registry_name") == registry]
        if len(normalizers) != 1 or not normalizers[0].get("state_file"):
            raise ValueError(f"Missing processor statistics in {name}")
        for step in steps:
            if "state_file" in step:
                state = path / step["state_file"]
                if not state.resolve().is_relative_to(path):
                    raise ValueError("Processor statistics path escapes checkpoint folder")
                if not state.is_file():
                    raise ValueError(f"Missing processor statistics: {step['state_file']}")


def verify_asset(repo_id, destination, repo_type="model"):
    """Verify local bytes against the pinned download manifest before loading."""
    entry = load_json(ROOT / "assets.lock.json").get(f"{repo_type}:{repo_id}", {})
    if not re.fullmatch(r'[0-9a-f]{40}', entry.get('revision', '')) or not entry.get('files_sha256'):
        raise ValueError(f"Missing pinned asset manifest: {repo_id}; run download")
    destination = Path(destination).resolve()
    for relative, digest in entry['files_sha256'].items():
        path = (destination / relative).resolve()
        if not path.is_relative_to(destination) or not path.is_file() or sha256(path) != digest:
            raise ValueError(f"Asset integrity mismatch: {repo_id}/{relative}")
    return entry['revision']


def prepare_reference():
    return download_repo(DATASET, ROOT / "data" / "reference", repo_type="dataset")
