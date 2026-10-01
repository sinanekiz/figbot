package com.figbot.scanner;

import org.json.JSONException;
import org.json.JSONObject;

/** One user-confirmed fig observation. */
public record ScanTarget(
        int trackId,
        Vec3 worldPoint,
        double cameraDistanceMetres,
        String depthSource,
        long timestampMillis) {

    public JSONObject toJson(BaseFrameCalibration calibration) throws JSONException {
        JSONObject object = new JSONObject();
        object.put("track_id", trackId);
        object.put("class", "fig_candidate");
        object.put("detection_mode", "MANUAL_TAP");
        object.put("distance_m", cameraDistanceMetres);
        object.put("depth_source", depthSource);
        object.put("timestamp_ms", timestampMillis);
        object.put("coordinate_status", "UNVERIFIED — PHYSICAL VALIDATION REQUIRED");
        if (calibration.isReady()) {
            Vec3 base = calibration.toBase(worldPoint);
            object.put("robot_x_mm", base.x() * 1000.0);
            object.put("robot_y_mm", base.y() * 1000.0);
            object.put("robot_z_mm", base.z() * 1000.0);
        } else {
            object.put("robot_xyz_mm", JSONObject.NULL);
            object.put("coordinate_status", "UNCALIBRATED");
        }
        return object;
    }
}
