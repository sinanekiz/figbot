"""Train and export the bootstrap FIGBOT detector for Android LiteRT."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from ultralytics import YOLO


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--device", default="cpu")
    parser.add_argument(
        "--weights",
        default="yolo11n.pt",
        help="Initial checkpoint. Use the previous reviewed detector for field adaptation.",
    )
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    model = YOLO(args.weights)
    train_result = model.train(
        data=str(args.data),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        project=str(args.output),
        name="training",
        exist_ok=True,
        seed=17,
        deterministic=True,
        patience=20,
        workers=0,
        optimizer="AdamW",
        lr0=0.0005,
        lrf=0.1,
        warmup_epochs=1.0,
        degrees=12,
        translate=0.10,
        scale=0.35,
        fliplr=0.5,
        flipud=0.1,
        hsv_h=0.03,
        hsv_s=0.5,
        hsv_v=0.4,
        mosaic=0.5,
        close_mosaic=5,
    )
    best_path = Path(train_result.save_dir) / "weights" / "best.pt"
    best = YOLO(best_path)
    metrics = best.val(data=str(args.data), imgsz=args.imgsz, device=args.device, workers=0)
    export_path = Path(best.export(format="onnx", imgsz=args.imgsz, nms=False, simplify=True))
    destination = args.output / "figbot_fig_detector.onnx"
    shutil.copy2(export_path, destination)
    summary = {
        "status": "BOOTSTRAP MODEL — UNVERIFIED ON FIGBOT FIELD DATA",
        "initial_weights": str(args.weights),
        "source_weights": str(best_path),
        "export": str(destination),
        "imgsz": args.imgsz,
        "map50": float(metrics.box.map50),
        "map50_95": float(metrics.box.map),
        "precision": float(metrics.box.mp),
        "recall": float(metrics.box.mr),
    }
    (args.output / "MODEL_CARD.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
