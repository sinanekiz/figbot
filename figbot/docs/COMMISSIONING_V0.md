# FIGBOT V0 physical commissioning gate

Status: **software/mechanical release candidate — physical validation required**.
No step below may be skipped. The arm is commissioned one uncoupled axis at a
time before any link or gripper is installed.

## 1. Incoming inspection

1. Record manufacturer, part number, revision/label and serial/lot for every
   motor, driver, gearbox, camera, bearing, coupling, PSU and safety component.
2. Measure the controlled dimensions in `manufacturing/INTERFACE_CONTROL.csv`.
3. Overlay vendor STEP against the matching mount. Stop if pilot, shaft, hole
   pitch, connector or cable exit differs.
4. Rotate each gearbox by hand. Reject damage, roughness, abnormal backlash or
   shipping contamination.

## 2. Electrical inspection — power isolated

1. A qualified reviewer checks PE bonding, mains clearances, branch conductor
   sizes, fuse ratings, ferrules, glands, terminal torque and segregation.
2. Verify both E-stop channels, G9SE reset/EDM circuit and the two final
   switching devices against `electrical/E_STOP_ARCHITECTURE.md`.
3. Confirm no MCU or software output can energize the actuator bus when the
   safety relay is open.
4. Continuity-test every motor and encoder cable end-to-end; verify there is no
   phase-to-encoder or phase-to-shield short.

## 3. Firmware and uncoupled motor test

1. Build/load `firmware/pico2_motion`; leave all couplings disconnected.
2. Set each driver to 16 microsteps and the lowest current that turns the
   uncoupled motor reliably. Record switch settings and driver firmware.
3. Confirm STEP, DIR, ENA and ALM polarity. Update only
   `software/control/hardware_config.json`; do not compensate by swapping
   undocumented wires.
4. Break each NC home and alarm loop. The state must latch fault and disable all
   drive-enable requests. Remove the host USB; watchdog trip must occur within
   300 ms plus measured output delay.

## 4. Hardwired E-stop test

1. Use a current-limited supply and one drive first. Press E-stop during idle
   and low-speed motion. Measure actuator-bus voltage decay and stopping time.
2. Open each E-stop channel independently; cross-short detection and EDM reset
   behavior require human safety review.
3. Restore E-stop. Drives must remain de-energized until a deliberate reset and
   separate arm command. Software reset alone must not restore actuator energy.

## 5. Mechanical staged assembly

1. Install bearings with controlled tools; never press through rolling elements.
2. Align motor/shaft couplings within the selected coupling limits. Torque clamp
   screws with a calibrated tool and witness-mark them.
3. Assemble J1 only, then J2 with the upper arm removed, then J3/J4. At each
   stage move at <=5 deg/s and <=10% current limit while checking collision,
   cable bend radius, heat, noise and lost motion.
4. Install and tune the J2 counterbalance before the forearm/gripper payload.
   With power removed the arm must not free-fall uncontrolled.

## 6. Calibration and release tests

1. Determine home approach direction, repeatability and `zero_offset_deg` for
   every axis from at least 30 home cycles.
2. Run no-load, 25%, 50%, 75% and 100% proposed payload tests while logging
   driver alarms, motor/gearbox temperatures, following error and current.
3. Calibrate Camera Module 3 after the mast is torqued; run the reprojection and
   robot-base transform tests in `docs/CAMERA_ROBOT_CALIBRATION.md`.
4. Determine XL330 current limit and compliant finger geometry only from
   `reports/GRIPPER_DAMAGE_TEST_PLAN.md`.
5. Sign the physical test records. Until all gates pass, the machine remains a
   prototype and must not be operated unattended.
