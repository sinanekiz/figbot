"""Conservative clearance checks for P0 Rev-G packaging."""

from __future__ import annotations

import math

from cad.config import parameters as p


def steering_swept_inboard_clearance_mm() -> float:
    """Clearance from a fully steered front tyre rectangle to the frame side.

    The tyre is conservatively represented by half its diameter along the rolling
    direction and half its width along the axle direction, rotated to the maximum
    steering angle about its centre.
    """
    angle = math.radians(p.P0_STEER_LIMIT_DEG)
    inboard_reach = (p.P0_WHEEL_DIAMETER / 2) * math.sin(angle) + (p.P0_WHEEL_WIDTH / 2) * math.cos(angle)
    wheel_center_y = p.P0_TRACK / 2
    frame_outer_y = p.P0_CHASSIS_WIDTH / 2
    return wheel_center_y - inboard_reach - frame_outer_y


def rear_tyre_to_frame_clearance_mm() -> float:
    return p.P0_TRACK / 2 - p.P0_WHEEL_WIDTH / 2 - p.P0_CHASSIS_WIDTH / 2


def camera_mast_to_front_wheel_swept_clearance_mm() -> float:
    wheel_center = (p.P0_FRONT_AXLE_X, p.P0_TRACK / 2)
    mast_center = (p.P0_CAMERA_MAST_X, p.P0_CAMERA_MAST_Y)
    center_distance = math.hypot(wheel_center[0] - mast_center[0], wheel_center[1] - mast_center[1])
    wheel_plan_radius = math.hypot(p.P0_WHEEL_DIAMETER / 2, p.P0_WHEEL_WIDTH / 2)
    mast_plan_radius = math.hypot(p.P0_CAMERA_MAST_SIZE / 2, p.P0_CAMERA_MAST_SIZE / 2)
    return center_distance - wheel_plan_radius - mast_plan_radius


def dual_arm_mount_gap_mm() -> float:
    """Plan-view edge gap between the two removable arm adapter plates."""

    return 2 * p.P0_ARM_BASE_Y_OFFSET - p.P0_ARM_MOUNT_SIZE


def arm_mount_to_front_wheel_sweep_mm() -> float:
    """Closest left/right arm-plate corner to its front tyre swept circle."""

    plate_front_x = p.P0_ARM_BASE_X + p.P0_ARM_MOUNT_SIZE / 2
    plate_outer_y = p.P0_ARM_BASE_Y_OFFSET + p.P0_ARM_MOUNT_SIZE / 2
    wheel_center_x = p.P0_FRONT_AXLE_X
    wheel_center_y = p.P0_TRACK / 2
    wheel_plan_radius = math.hypot(p.P0_WHEEL_DIAMETER / 2, p.P0_WHEEL_WIDTH / 2)
    return math.hypot(wheel_center_x - plate_front_x, wheel_center_y - plate_outer_y) - wheel_plan_radius


def basket_front_to_frame_mm() -> float:
    frame_front = p.P0_CHASSIS_LENGTH / 2
    basket_front = p.P0_BASKET_CENTER_X + p.P0_BASKET_LENGTH / 2
    return frame_front - basket_front


def basket_side_to_arm_mount_mm() -> float:
    arm_plate_inner = p.P0_ARM_BASE_Y_OFFSET - p.P0_ARM_MOUNT_SIZE / 2
    basket_side = abs(p.P0_BASKET_CENTER_Y) + p.P0_BASKET_WIDTH / 2
    return arm_plate_inner - basket_side


def basket_to_rear_tyre_mm() -> float:
    """Lateral gap from the widened basket wall to the rear tyre inner face."""

    tyre_inner_y = p.P0_TRACK / 2 - p.P0_WHEEL_WIDTH / 2
    basket_outer_y = abs(p.P0_BASKET_CENTER_Y) + p.P0_BASKET_WIDTH / 2
    return tyre_inner_y - basket_outer_y


def basket_floor_rise_mm() -> float:
    return p.P0_BASKET_FRONT_FLOOR_Z - p.P0_BASKET_BOTTOM_Z


def basket_front_internal_depth_mm() -> float:
    return p.P0_BASKET_BOTTOM_Z + p.P0_BASKET_HEIGHT - p.P0_BASKET_FRONT_FLOOR_Z


def clearance_report() -> dict[str, float]:
    return {
        "steered_tyre_to_frame_mm": steering_swept_inboard_clearance_mm(),
        "rear_tyre_to_frame_mm": rear_tyre_to_frame_clearance_mm(),
        "camera_mast_to_front_wheel_sweep_mm": camera_mast_to_front_wheel_swept_clearance_mm(),
        "dual_arm_mount_gap_mm": dual_arm_mount_gap_mm(),
        "arm_mount_to_front_wheel_sweep_mm": arm_mount_to_front_wheel_sweep_mm(),
        "basket_front_to_frame_mm": basket_front_to_frame_mm(),
        "basket_side_to_arm_mount_mm": basket_side_to_arm_mount_mm(),
        "basket_to_rear_tyre_mm": basket_to_rear_tyre_mm(),
        "basket_floor_rise_mm": basket_floor_rise_mm(),
        "basket_front_internal_depth_mm": basket_front_internal_depth_mm(),
    }
