# FIGBOT Android v0.14 — optional PC bridge

Current release: GUNCEL/YAZILIM/FIGBOT_MOTOR_KONTROL.apk (same package as FIGBOT_INCIR_TARAYICI.apk). Options 01 direct Android USB SO101 and 02 legacy UNO/HC05 remain; option 03 uses the same Android camera/planner/controller through a loopback ST3215 socket bridge to the PC's serial adapter. See GUNCEL/YAZILIM/ST3215_TEST/PC_ILE_TOPLAMA.md for setup. The PC launcher creates adb reverse tcp:8873, owns one serial port, rejects EEPROM writes, and attempts measured hold on an altered session's disconnect. Physical calibration gates remain mandatory. Device installation and real PC motion/timing validation are pending for v0.14.

## Historical notes

# FIGBOT Android control and field scanner v0.9

Current update: `releases/FIGBOT-Kontrol-HC05-v0.9-debug.apk`, UNO V5/STATUS5. See `releases/HC05-v0.9-KURULUM.md`. Android defaults every joint to360 command deg/s, prepares all logical joints once per new validated connection without commanding positions, and hides settings behind per-joint buttons. Slider release/numeric Go sends a target; paired first-centre remains explicit. Stepped symmetric shoulder range calibration is available with active-range-change rejection and re-centering. Builds and30software tests pass; hardware installation and rendered-device validation are pending.

The following v0.8 description is historical; v0.9 requires V5 and defaults speed to360.

Two workflows: **camera collection observations** and **HC-05 manual motor tests**. Read `HC05_KULLANIM.md` before connecting. The motor screen commands the V4 controller with selectable 10..360 command deg/s, including both paired shoulders. Default remains 30. Old V3 controllers are rejected, so update APK and firmware together. Physical 360 deg/s speed is unverified. Camera-to-pick execution remains blocked on measured servo/robot calibration and path checks. Current artifact: `releases/FIGBOT-Kontrol-HC05-v0.8-debug.apk` at repository root. Builds and software tests pass; hardware installation is a separate step with motor supply disconnected and mechanism supported.

Status: **V0 PROTOTYPE — UNVERIFIED / PHYSICAL VALIDATION REQUIRED**

Bundled model: **collectable ground fig**. The positive class includes normal
dry figs and bruised, purple, dark, split, low-grade `hurda incir`. Field-fit
audit and dataset limitations are recorded in `MODEL_CARD.md`.

This Android APK tests whether an ARCore-capable phone or tablet can produce useful
fig target observations. The camera workflow does not authorize or command robot
motion; the separate manual motor screen requires explicit per-joint enablement.

## Implemented

- ARCore rear-camera preview and motion tracking.
- Automatic Depth API enablement on supported devices.
- Offline automatic dry-fig-candidate detection with green bounding boxes.
- Two-point `base_link` registration: J1 origin, then a point along robot +X.
- Base-frame XYZ text on each detected fig box when ARCore finds a usable depth,
  plane, or feature-point hit at its centre.
- JSON export and explicit HTTP POST to a configurable FIGBOT endpoint.
- Every coordinate is labelled `UNVERIFIED — PHYSICAL VALIDATION REQUIRED`.

The HTTP payload includes `arm_motion_authorized: false`. A receiving controller
must treat it as target observations only and must perform reach, collision,
uncertainty, and close-range confirmation checks before any motion.

## Limits / blocked

- The bundled detector is a 640 x 640 field-adapted experiment. It was adapted
  to 18 supplied phone scenes, including soil/concrete orchard views, grass/leaf
  failure examples, and purple/dark/split hurda figs, plus synthetic small-object compositions.
  It is not independently validated on new phone video or the fixed FIGBOT camera.
- A green box means `dry_fig_candidate`, not a field-validated collectible fig.
- Purple, dark, bruised, and split ground figs are positives. The one-class model
  does not grade sale quality; collection suitability remains field-unverified.
- Duplicate suppression around a full tree is not yet implemented.
- AprilTag/ArUco base registration is not yet implemented; V0 uses two manual taps.
- Coordinate accuracy, AR drift, sunlight performance, and branch occlusion are
  unverified. Branch picking remains outside the active FIGBOT mechanical baseline.

## Build

Requirements: JDK 17, Android SDK 36, Android Build Tools 35+, Gradle 8.13, and an
internet connection for the first dependency resolution.

```powershell
cd software/android/figbot-scanner
.\gradlew.bat testDebugUnitTest assembleDebug
```

Debug APK:

`app/build/outputs/apk/debug/app-debug.apk`

Install to a USB-debugging-enabled device:

```powershell
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

For the camera screen, the physical device must be ARCore-compatible. Manual
Bluetooth motor control does not require ARCore. Depth is preferred but
optional; without it the app reports plane/feature-point hits and their distance
must not be treated as arm-ready.

## Field procedure

1. Move the device slowly until AR tracking stabilizes.
2. Tap `1 · Orijin`, then touch the physical J1/base origin.
3. Tap a measured point along robot +X after selecting `2 · +X`.
4. Point the camera at the figs and hold it nearly still. Detection is automatic;
   do not tap a fig. Green boxes show detected candidates.
   For the intended test, keep the camera about 60 cm above the ground and tilted
   down so each fig remains at least roughly 25 pixels across in the preview.
5. A box shows `XYZ yok` until both base points and a usable AR depth/plane hit exist.
6. Compare reported XYZ against at least three independently measured control
   points before using the data outside this experiment.
7. Save JSON or explicitly send target observations to the configured endpoint.

Do not convert camera observations directly into actuator commands without measured calibration and reach/collision checks. Manual motor commands are available only in the separate motor screen.
