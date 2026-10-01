"""Run a local Ultralytics checkpoint and export gate-compatible detections."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ai.inference.gate import SUPPORTED


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="Local reviewed checkpoint")
    parser.add_argument("--source", required=True, help="Local image/video path")
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()
    if not Path(args.model).is_file() or not Path(args.source).exists():
        parser.error("--model and --source must exist locally; no downloads are automatic")
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise SystemExit("Optional dependency missing: install a reviewed ultralytics version") from exc

    model = YOLO(args.model)
    exported: list[dict] = []
    for frame_index, result in enumerate(model.predict(source=args.source, device=args.device, stream=True)):
        names = result.names
        for box in result.boxes:
            label = str(names[int(box.cls.item())])
            if label not in SUPPORTED:
                raise ValueError(f"checkpoint emitted unsupported class: {label}")
            exported.append({
                "frame_index": frame_index,
                "label": label,
                "confidence": float(box.conf.item()),
                "box": [float(value) for value in box.xyxy[0].tolist()],
            })
    Path(args.output).write_text(json.dumps(exported, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
