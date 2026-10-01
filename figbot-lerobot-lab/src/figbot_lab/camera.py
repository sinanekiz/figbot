from __future__ import annotations

import time

from .common import current_scene_task, new_run, save_json


def capture(index=0, seconds=5, backend="dshow"):
    """Explicitly invoked PC-camera capture. No motor interface is imported."""
    import cv2
    if index < 0 or not 0 < seconds <= 120:
        raise ValueError("Camera index must be >=0 and duration within (0,120] seconds")
    api = {"dshow": cv2.CAP_DSHOW, "msmf": cv2.CAP_MSMF, "auto": cv2.CAP_ANY}[backend]
    cap = cv2.VideoCapture(index, api)
    writer = None
    run = new_run("camera")
    started = time.monotonic()
    frame_times = []
    try:
        if not cap.isOpened():
            raise ValueError(f"PC camera {index} could not be opened ({backend})")
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        while time.monotonic() - started < seconds:
            ok, bgr = cap.read()
            now = time.monotonic()
            if not ok:
                raise ValueError("Camera stopped returning frames")
            if writer is None:
                h, w = bgr.shape[:2]
                writer = cv2.VideoWriter(str(run / "camera.avi"), cv2.VideoWriter_fourcc(*"MJPG"), 30, (w, h))
                if not writer.isOpened():
                    raise ValueError("Cannot create camera video")
                if not cv2.imwrite(str(run / "first.jpg"), bgr):
                    raise ValueError("Cannot save camera frame")
            writer.write(bgr)
            frame_times.append(now - started)
        if not frame_times:
            raise ValueError("Camera produced no frames")
        if not cv2.imwrite(str(run / "latest.jpg"), bgr):
            raise ValueError("Cannot save final frame")
        save_json(run / "capture.json", {"camera_index": index, "backend": backend,
                  "frames": len(frame_times), "read_times_s": frame_times,
                  "video_nominal_fps": 30, "timing_source": "PC_READ_COMPLETION_NOT_SENSOR_TIMESTAMP",
                  "has_robot_state": False, "motor_commands_sent": False})
    finally:
        cap.release()
        if writer is not None:
            writer.release()
    return run


def camera_smoke(image_path, alias="pickplace", device="auto", task=None):
    """Image plumbing/latency check, with an explicitly synthetic robot state."""
    import numpy as np
    from PIL import Image
    from .policy import PolicyRunner
    task = current_scene_task() if task is None else task
    if not isinstance(task, str) or not task.strip():
        raise ValueError("Task instruction is required")
    runner = PolicyRunner(alias, device)
    image = np.asarray(Image.open(image_path).convert("RGB"))
    result = runner.predict({"observation.images.camera1": image}, runner.training_mean_state(), task)
    result.update(scope="IMAGE_PIPELINE_SMOKE_TEST_ONLY",
                  state_source="CHECKPOINT_TRAINING_MEAN_NOT_CURRENT_ROBOT",
                  source_image=str(image_path), suitable_for_robot_control=False)
    run = new_run("camera_smoke")
    save_json(run / "prediction.json", result)
    return run
