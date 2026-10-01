"""Small, explicit training launcher for the first detection baseline."""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="Local reviewed checkpoint")
    parser.add_argument("--data", default=str(Path(__file__).with_name("dataset.yaml")))
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()
    if args.epochs < 1 or args.imgsz < 64:
        parser.error("epochs must be >=1 and imgsz must be >=64")
    if not Path(args.model).is_file():
        parser.error("--model must point to a local checkpoint; no download is automatic")
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise SystemExit("Optional dependency missing: install a reviewed ultralytics version") from exc
    model = YOLO(args.model)
    model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        device=args.device,
        project=str(Path(__file__).with_name("runs")),
        name="baseline",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

