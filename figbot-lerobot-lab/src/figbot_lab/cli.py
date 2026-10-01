from __future__ import annotations

import argparse
import json
import sys

from .common import ROOT, configure_environment, new_run, save_json


def main():
    configure_environment()
    parser = argparse.ArgumentParser(description="FIGBOT hazır model deneme alanı — çıktılar dosyaya yazılır.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="Python, CUDA ve model durumunu göster")
    p = sub.add_parser("calibration-capture", help="Motorları hareket ettirmeden kalibrasyon ölçümü al")
    p.add_argument("--kind", choices=["baseline", "neutral", "range", "drop"], default="baseline")
    p.add_argument("--seconds", type=float, default=2)
    p.add_argument("--port", default="COM5")
    p.add_argument("--camera", action="store_true")
    p = sub.add_parser("download", help="Sabitlenmiş model ve örnek verileri indir")
    p.add_argument("--model", choices=["base", "pickplace", "all"], default="all")
    p.add_argument("--reference", action="store_true")
    p = sub.add_parser("import-recording", help="Mevcut kapalı kaydı hash doğrulamasıyla kopyala")
    p.add_argument("--source", required=True)
    p = sub.add_parser("audit", help="Video/enkoder eşleşmesini denetle")
    p.add_argument("--episode", required=True)
    p = sub.add_parser("reference-test", help="Yayımlanmış veride gerçek model çıkarımı")
    p.add_argument("--frames", type=int, nargs="+", default=[0, 120, 240])
    p.add_argument("--model", choices=["base", "pickplace"], default="base")
    p.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    p = sub.add_parser("local-test", help="Kalibrasyon eşlemesiyle yerel kayıt çıkarımı")
    p.add_argument("--episode", required=True)
    p.add_argument("--mapping", required=True)
    p.add_argument("--frame", type=int, default=100)
    p.add_argument("--model", choices=["pickplace"], default="pickplace")
    p.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    p = sub.add_parser("camera", help="PC kamerasından kısa kayıt ve fotoğraf al")
    p.add_argument("--index", type=int, default=0)
    p.add_argument("--seconds", type=float, default=5)
    p.add_argument("--backend", choices=["dshow", "msmf", "auto"], default="dshow")
    p.add_argument("--infer", action="store_true", help="Son fotoğrafta örnek eklem durumuyla model bağlantısını da dene")
    p.add_argument("--task", help="Model denemesi komutu; varsayılan mevcut sahneden alınır")
    p = sub.add_parser("phone-camera", help="FIGBOT telefon kamerasını USB üzerinden al")
    p.add_argument("--serial")
    p.add_argument("--seconds", type=float, default=5)
    p.add_argument("--infer", action="store_true")
    p.add_argument("--task", help="Model denemesi komutu; varsayılan mevcut sahneden alınır")
    p = sub.add_parser("camera-smoke", help="Bir görüntü ile model bağlantısı ve gecikme testi")
    p.add_argument("--image", required=True)
    p.add_argument("--model", choices=["pickplace"], default="pickplace")
    p.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    p.add_argument("--task", help="Varsayılan mevcut sahneden alınır")
    p = sub.add_parser("export-training", help="Doğrulanmış eşlemeyle kayıtları LeRobot eğitim formatına aktar")
    p.add_argument("--episode", required=True)
    p.add_argument("--mapping", required=True)
    p.add_argument("--name", default="figbot_figs")
    p = sub.add_parser("training-command", help="Dışa aktarılmış veri için hazır modelden uyarlama komutu")
    p.add_argument("--dataset", required=True)
    p.add_argument("--model", choices=["base", "pickplace"], default="base")
    args = parser.parse_args()
    try:
        if args.command == "doctor":
            import platform
            import torch
            from importlib.metadata import version
            report = {"root": str(ROOT), "python": platform.python_version(),
                      "lerobot": version("lerobot"), "torch": torch.__version__,
                      "cuda_available": torch.cuda.is_available(),
                      "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
                      "models": {name: (ROOT / "models" / name / "model.safetensors").is_file()
                                 for name in ("base", "pickplace")}, "motor_interface": "READ_ONLY_CALIBRATION"}
            save_json(new_run("doctor") / "doctor.json", report)
            print(json.dumps(report, indent=2))
        elif args.command == "calibration-capture":
            from .calibration import capture
            print(capture(args.kind, args.seconds, args.port, args.camera))
        elif args.command == "download":
            from .assets import prepare_model, prepare_reference
            for alias in (["base", "pickplace"] if args.model == "all" else [args.model]):
                prepare_model(alias)
            if args.reference:
                prepare_reference()
        elif args.command == "import-recording":
            from .records import snapshot_episode
            path, audit = snapshot_episode(args.source)
            print(path)
            print(json.dumps(audit, indent=2))
        elif args.command == "audit":
            from .records import audit_episode
            print(json.dumps(audit_episode(args.episode), indent=2))
        elif args.command == "reference-test":
            from .experiments import reference_test
            print(reference_test(args.model, args.device, args.frames))
        elif args.command == "local-test":
            from .experiments import local_test
            print(local_test(args.episode, args.mapping, args.frame, args.model, args.device))
        elif args.command in ("camera", "phone-camera"):
            if args.command == "phone-camera":
                from .phone import capture_phone
                run = capture_phone(args.serial, args.seconds)
            else:
                from .camera import capture
                run = capture(args.index, args.seconds, args.backend)
            print(run)
            if args.infer:
                from .camera import camera_smoke
                print("Camera/model plumbing test uses the training mean state, NOT current robot encoders.")
                print(camera_smoke(run / "latest.jpg", task=args.task))
        elif args.command == "camera-smoke":
            from .camera import camera_smoke
            print(camera_smoke(args.image, args.model, args.device, args.task))
        elif args.command == "export-training":
            from .training import export_training
            print(export_training(args.episode, args.mapping, args.name))
        elif args.command == "training-command":
            from .training import training_command
            print(training_command(args.dataset, args.model))
        return 0
    except (ValueError, FileNotFoundError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
