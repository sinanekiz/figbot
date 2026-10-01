# Vision coordinate pipeline

The V0 pipeline is:

`camera pixels + depth/plane estimate -> camera XYZ -> robot-base XYZ -> reach/collision checks`

`transforms.py` provides a dependency-free homogeneous transform implementation
for calibration and unit tests. It does not estimate depth or solve calibration.
For RGB-D, use deprojected camera coordinates from the reviewed camera SDK. For an
RGB-only fixed bench camera, intersect a calibrated camera ray with the measured
table plane; this is unsuitable once ground height varies.

Calibration procedure and acceptance records are in
`docs/CAMERA_ROBOT_CALIBRATION.md`. Transform accuracy and camera suitability are
`UNVERIFIED — PHYSICAL VALIDATION REQUIRED`.

