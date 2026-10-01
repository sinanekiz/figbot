# Camera-to-robot calibration procedure

Status: `UNVERIFIED — PHYSICAL VALIDATION REQUIRED`

Frames use SI units and right-handed axes. `camera_optical` follows the selected
camera SDK convention; `base_link` is the mechanical base datum. The stored matrix
must state direction explicitly as `T_base_camera` and map camera XYZ into base XYZ.

## Equipment

- rigidly mounted camera and final lens/focus settings;
- traceable or independently checked target dimensions;
- calibration target suitable for the selected library;
- robot-disabled pointer or surveyed fiducials in the base frame;
- data-capture record with camera serial, resolution, mount revision and software commit.

## Procedure

1. Mechanically inspect and mark both camera and base datums. Disable actuator power.
2. Lock resolution, depth mode, focus and exposure policy used by runtime.
3. Calibrate intrinsics using images spanning the image area and target orientations.
   Save raw images and reprojection residuals; do not keep only a single summary.
4. Measure target poses relative to `base_link` at multiple positions spanning the
   intended pick area and height range. Avoid nearly collinear samples.
5. Solve the rigid camera-to-base transform using a reviewed calibration library.
6. Validate on independent holdout points not used to solve the transform. Record
   signed X/Y/Z errors, Euclidean error, sample location and depth confidence.
7. Repeat after remounting, impact, focus/resolution change, or failed daily check.
8. Store the accepted matrix as JSON and run `software.vision.transforms.load_transform`.

## Acceptance

Numeric limits are `TBD` until grasp-clearance and positioning-error budgets are
allocated. Before that decision, calibration cannot pass for autonomous picking.
The reviewer must confirm coverage of the whole workspace, absence of systematic
edge/height bias, and repeatability after a power cycle. A low mean error alone is
insufficient; maximum and percentile errors must be reported.

## Daily verification

With drives disabled, observe at least three fixed check points distributed across
the workspace. Compare measured base coordinates with their recorded values. Any
movement, unexplained residual shift or invalid depth marks calibration failed and
prevents arming until recalibration. The number and threshold remain `TBD`.

