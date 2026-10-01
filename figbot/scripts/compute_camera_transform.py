#!/usr/bin/env python3
"""
Compute camera-to-arm-base transform from fixed mounting geometry.

Arm Base Frame (B): Origin at base motor axis projection on mount plane (O).
  +X: Forward (fig pickup direction)
  +Y: Right
  +Z: Up

Camera Frame (C): OpenCV/ Android CameraX convention.
  +X: Right (image width)
  +Y: Down (image height)
  +Z: Forward (optical axis out of lens)

Fixed mounting (user-specified):
  Camera position in B: [0, +200, +150] mm
  Camera orientation: yaw=-30°, pitch=-45°, roll=0° (looking forward-down-left)
"""

import json
import numpy as np
from pathlib import Path
from scipy.spatial.transform import Rotation as R


def rotation_matrix(yaw_deg, pitch_deg, roll_deg):
    """Z-Y-X (yaw-pitch-roll) extrinsic rotations."""
    # Note: scipy uses intrinsic rotations by default. For extrinsic Z-Y-X,
    # we can use 'zyx' with angles in reverse order or use extrinsic directly.
    # Here: yaw (Z), pitch (Y), roll (X) — all extrinsic.
    # Equivalent to intrinsic X-Y-Z with same angles.
    return R.from_euler('ZYX', [yaw_deg, pitch_deg, roll_deg], degrees=True).as_matrix()


def build_transform(tx, ty, tz, yaw_deg, pitch_deg, roll_deg):
    """4x4 homogeneous transform from Camera (C) to Base (B): X_B = T_B_C @ X_C"""
    R_B_C = rotation_matrix(yaw_deg, pitch_deg, roll_deg)
    t_B_C = np.array([tx, ty, tz], dtype=float)
    T = np.eye(4)
    T[:3, :3] = R_B_C
    T[:3, 3] = t_B_C
    return T


def transform_point(T, point_c):
    """Transform point from camera frame to base frame."""
    p = np.array([point_c[0], point_c[1], point_c[2], 1.0])
    p_b = T @ p
    return p_b[:3]


def main():
    # Mounting parameters (mm)
    tx, ty, tz = 0.0, 200.0, 150.0
    yaw, pitch, roll = -30.0, -45.0, 0.0

    T_B_C = build_transform(tx, ty, tz, yaw, pitch, roll)

    print("=== Camera -> Arm Base Transform (T_B_C) ===")
    print(f"Translation (mm): [{tx}, {ty}, {tz}]")
    print(f"Orientation (deg): yaw={yaw}, pitch={pitch}, roll={roll}")
    print("\n4x4 Matrix:")
    np.set_printoptions(precision=6, suppress=True)
    print(T_B_C)

    # Verify: Camera optical center (0,0,0) in C -> should be camera position in B
    cam_in_B = transform_point(T_B_C, [0, 0, 0])
    print(f"\nCamera origin in Base frame: {cam_in_B} mm")
    print(f"Expected: [{tx}, {ty}, {tz}]")

    # Test: Point 1m forward in camera frame (along optical axis)
    pt_forward_c = np.array([0, 0, 1000.0])
    pt_forward_b = transform_point(T_B_C, pt_forward_c)
    print(f"\nPoint 1000mm along camera +Z (forward) in Base: {pt_forward_b} mm")

    # Test: Point 1m right in camera frame (+X_cam)
    pt_right_c = np.array([1000.0, 0, 0])
    pt_right_b = transform_point(T_B_C, pt_right_c)
    print(f"Point 1000mm along camera +X (right) in Base: {pt_right_b} mm")

    # Test: Point 1m down in camera frame (+Y_cam)
    pt_down_c = np.array([0, 1000.0, 0])
    pt_down_b = transform_point(T_B_C, pt_down_c)
    print(f"Point 1000mm along camera +Y (down) in Base: {pt_down_b} mm")

    # Save to cartesian_reference.json
    ref_path = Path("GUNCEL/YAZILIM/ST3215_TEST/cartesian_reference.json")
    with open(ref_path, 'r', encoding='utf-8') as f:
        ref = json.load(f)

    ref["camera_to_base_transform"] = {
        "translation_mm": [float(tx), float(ty), float(tz)],
        "rotation_deg": {"yaw": float(yaw), "pitch": float(pitch), "roll": float(roll)},
        "matrix": T_B_C.tolist(),
        "convention": {
            "base_frame": "vendor_base_link (+X forward, +Y right, +Z up)",
            "camera_frame": "opencv (+X right, +Y down, +Z forward)",
            "transform_direction": "camera_to_base (X_base = T @ X_cam)"
        },
        "source": "computed_from_fixed_mount_geometry",
        "verified": False,
        "notes": "yaw=-30° (look left), pitch=-45° (look down). Verify with 4-point calibration."
    }

    with open(ref_path, 'w', encoding='utf-8') as f:
        json.dump(ref, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Updated {ref_path}")

    # Also create Android app calibration format (if needed)
    android_calib = {
        "schema": "figbot.camera_calib.v1",
        "camera_to_base": {
            "translation_mm": [float(tx), float(ty), float(tz)],
            "rotation_deg": {"yaw": float(yaw), "pitch": float(pitch), "roll": float(roll)},
            "matrix": T_B_C.tolist()
        },
        "base_frame": "vendor_base_link",
        "camera_frame": "android_camera_opencv",
        "mounting": {
            "position_mm": {"x": 0, "y": 200, "z": 150},
            "orientation_deg": {"yaw": -30, "pitch": -45, "roll": 0},
            "description": "Camera at arm base rear center, 20cm right, 15cm up. Looking forward-down-left."
        },
        "verified": False
    }

    android_path = Path("GUNCEL/YAZILIM/ST3215_TEST/camera_calibration_android.json")
    with open(android_path, 'w', encoding='utf-8') as f:
        json.dump(android_calib, f, indent=2, ensure_ascii=False)
    print(f"[OK] Created {android_path} for Android app")


if __name__ == "__main__":
    main()