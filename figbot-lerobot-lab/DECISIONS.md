# Kararlar — 29 Eylül 2026

1. Kullanıcının talebiyle `figbot-lerobot-lab` bağımsız klasörü açıldı. Eski projenin sanal ortamı da kullanılmadı.
2. İlk karşılaştırma resmî `lerobot/smolvla_base` ile toplama için uyarlanmış `Harrysunshine/so101-smolvla-9task` arasında yapılır. İkinci model deney adayıdır; fiziksel doğrulama iddiası yoktur.
3. LeRobot 0.6.1 ve CUDA 12.8 için PyTorch 2.10.0 kullanılır. Tüm çözülmüş paketler `uv.lock` içinde sabitlenir.
4. Tam policy ağırlıkları `strict=True` ile yüklenir. Mimari ve tokenizer yerel backbone dosyalarından oluşturulur; checkpoint tüm parametreleri sağladığı için ayrı VLM ağırlıkları indirilmez.
5. Modelin kendi ön/son işleyicileri ve normalizasyon istatistikleri birlikte kullanılır. Eksik istatistik kabul edilmez.
6. Var olan kayıtlar ve gözden geçirilmiş hedefler SHA256 doğrulamasıyla kopyalanır. Eski küçük CNN ağırlıkları bu modellerle karıştırılmaz.
7. Ham enkoder birimleri uydurma katsayılarla normalize edilmez. Eşleme doğrulanana kadar yerel eylem çıkarımı/eğitim dışa aktarımı açıklayıcı hata verir; kamera bağlantı testi ayrı yürür.
8. Eğitim dışa aktarımı 10 Hz kullanır, zaman boşluklarını ayrı bölümlere ayırır ve son toplama çevrimini doğrulamaya bırakır. Uyarlama komutu 16 hedeflik blok ve batch=1 ile başlar; başarı veya yeterli bellek garantisi değildir.
9. İnternete veri gönderimi, ücretli eğitim ve motor sürüşü bu sürümün parçası değildir.
10. Gerçek dosya incelemesinde base modelin istatistik anahtarları güncel işleyiciyle uyumsuz bulundu. İlk base çıktı metrikleri geçersiz işaretlendi. Referans smoke testi açık veri seti istatistikleriyle tekrar edilir. Görev modelinde eklem/eylem istatistikleri doğrudan doğrulanır. Kamera smoke testi bu görev modelini kullanır.

## 2026-09-29 preserve existing motor calibration
User authorized calibration and paper drop setup. Add passive measurement commands in the isolated lab. Snapshot existing motor settings and reject non-READ bus instructions, including SDK writes. Do not run upstream calibrate automatically because it rewrites homing offsets and position limits shared with the original project. Original source remains unchanged.

## 2026-09-30 code review corrections
Live image tests use the current scene task; recorded examples retain their session task.
Read encoders throughout stationary camera capture and retain bounded timing associations.
Include USB roundtrip in conservative frame age. Verify pinned model/backbone/reference hashes
before use. Reject invalid encoder intervals, discontinuities, incomplete source hashes,
and overlapping pickup cycles. Keep the joint mapping UNVERIFIED pending physical evidence.

## 2026-09-30 learn grasp; program fixed rear-crate transfer
User clarified that deployment release location stays fixed behind the arm.
Learn locating/approaching/grasping the fig. Confirm retention with a controlled
short lift before handing control to a deterministic transfer/release controller.
The fixed endpoint does not imply an identical route from every grasp pose;
plan from measured current pose, optionally through a validated common transfer pose.
Optimize travel only within physically validated collision-free motion.
The primary camera need not see the crate; its grasp workspace view must be useful.
Current live diagnostic task is grasp-only. Existing full pick/place recordings keep
their original tasks until a separate segmented dataset is reviewed and exported.
Plan: configs/task_plan.json. Transfer, grasp detection and segmented export are pending.

## 2026-09-30 mouse-driven virtual leader

User requests a PC 3D leader using left-held joint drag and right-held vertical
gripper drag, holding position on release. Build in the isolated lab, keeping
the original project read-only. Copy current SO101 visual mesh/hierarchy with
SHA256 and Apache-2.0 provenance. Kinematic joint visualization only, not a
physics or collision simulation. No IK is implied by dragging an individual joint.

Add a separate guarded SRAM-only motor adapter; preserve passive calibration's
READ-only bus unchanged. Connect/read never enables motors. Powered control
requires a reviewed URDF-angle/encoder profile, unchanged hardware offsets,
stable current pose, bounded target streaming, release-to-measured-hold and
a browser watchdog. No inferred physical direction/zero/limits. Start disabled
until profile is complete. Simulation and real-action recordings are explicitly
different and not camera-synchronized visual training datasets.

User subsequently connected the robot. All six responded on COM5 with torque=0;
only READ commands were sent. Evidence: runs/20260930T082347_693378Z_virtual_leader_readonly.
No powered teleoperation or physical matching has been tested by this implementation.

## 2026-09-30 coordinated tip control

User clarified the final mouse layout: left drag translates the arm tip with
coordinated joints, wheel changes jaw opening, right drag rotates the view only.
Shift + left drag changes depth; Shift + wheel zooms. Retain individual sliders.
Use bounded damped numerical IK over five arm joints, preserving jaw opening
and softly preserving tool orientation. Rebase each target from the achieved tip
position; do not accumulate unreachable motion. Derive the visual tip reference
from the original fixed-finger STL, retaining exact model joint transforms.
The physical mapping gate remains in force; no powered robot motion is implied.

## 2026-09-30 supervised relative base commissioning

User explicitly authorized the assistant to move the connected arm. Add a separate
single base-motor probe from freshly measured current counts: six counts of
excursion, two counts per command, then return. It requires a recent reviewed
whole-arm camera capture, visible fixed base and clearance, hands outside the
small motion, an initially unpowered stationary arm, unchanged position-mode
hardware, fresh camera frames and bounded telemetry throughout. Only motor 1
SRAM goals and torque-on are allowed by this probe's packet guard. Other joints
remain unpowered. The base stays holding its last small target after execution
or a communication failure; no automatic torque-off or retry is issued.

This probe is motor commissioning, not a mechanical range measurement or an
absolute angle calibration. Do not create a VERIFIED profile from its results.
The full virtual leader profile gate and passive calibration READ-only guard
remain unchanged. Camera freshness does not provide collision detection.

## 2026-09-30 six motor commissioning and explicit hardware risk acceptance

User requested sequential tests of all motors and then explicitly accepted risk
of damage to the robot to accelerate progress. Add a separate batch probe with
fixed relative paths from fresh measured counts, initially 12 counts, subsequently
48 counts (~4.22 encoder degrees) per motor. Commands change by at most eight
counts, with at most sixteen counts of lead over live measured position. Returned
and peak positions allow eight counts of tracking error. These are experimental
test budgets, not inferred mechanical envelopes or calibrated model angles.

Only the selected motor receives SRAM writes; the guard rejects other motors,
broadcast, persistent settings, torque-off, repeated tests and out-of-budget
goals. Each tested motor remains holding its last target. Stable feedback and
fresh camera frames are required throughout. Unexpected other-joint motion flags
pause further commands for at most 250 ms; position/speed drift still rejects
immediately. Persistent flags abort. The first attempts aborted on an unexpected
movement flag and an endpoint error; their records are retained separately.
Hardware-damage authorization does not justify motion into nearby people.

Physical tests exposed passive joint velocity pulses when a loaded parent moved.
Prepare current-position holds on all six motors before sequential probes.
Allow resuming a recorded powered pose only when torque states match the fresh
review and existing goals are close to measured positions. No new goal is sent
while unexpected speed/movement flags persist. Loaded shoulder tracking required
a maximum thirty-two-count goal lead and sixteen-count endpoint/other-joint
tolerance; fixed forty-eight-count excursion and eight-count step budgets remain.
The observed final return errors were smaller than these acceptance budgets.

Read-only server telemetry now stays fresh above prototype motion thresholds;
it does not enable movement. Full virtual leader activation retains its original
55C gate. User-authorized commissioning reads and respects the unchanged hardware
thermal limit at register 13 (70C on all six motors), retaining current/voltage
checks. No thermal, gain, offset or limit register was changed.

## 2026-09-30: Relative mouse trial integration

Added RELATIVE_TRIAL separately from VERIFIED calibration. Capture current UI
angles and measured raw counts at activation; directions remain provisional +1.
Clamp targets to a fixed software bank of +/-256 counts and encoder 0..4095.
This is an experiment budget, not inferred mechanical limits. Release never
rebases this bank. Trial speed budget 90 counts/s and maximum lead 32 counts;
SRAM profile 57/1, watchdog and measured-position holds retained. Trial checks
use the unchanged register-13 hardware thermal limits through commissioning;
verified control retains 55C. Full activation rejects unverified trial profiles.
Frontend button now sends angles to activate_trial and existing target/hold path.
Trial recordings remain unverified and not training-ready. Original figbot
checkout, passive calibration guard and EEPROM settings stay unchanged.
55 affected Python tests, 9 frontend tests and Vite build passed.
Actual Chrome activation succeeded with current-position holds on all six motors.
Evidence: runs/20260930T184817_741961Z_relative_trial_activation/state.json.
Phone absent from ADB devices; no new automatic movement sweep was performed.

## 2026-09-30: User-requested full-speed relative control

Removed +/-256-count origin bank and software rate/goal-lead smoothing from
relative control only. Targets are direct; measured register9..12 bounds used
(0..4095 on all six), encoder wrap forbidden. These are electronic bounds,
not verified physical stops. Model joint ranges retained. User requested full
speed after reporting functioning movement. Dedicated RelativeMotionBus uses
speed3400/accel50, while passive/commissioning/verified profiles are unchanged.
Initial acceleration150 was physically clipped to50 and readback verification
halted activation. All six readbacks showed speed3400, acceleration50. Corrected
profile activated in current-position holds. No EEPROM/gain/limit writes.
Release, watchdog, voltage/current/hardware thermal checks remain.
57 affected Python tests and 9 frontend tests pass; build passes. Follow-up
metadata test passes. Evidence directory:
runs/20260930T185837_800785Z_relative_full_speed_activation.
Actual full-speed movement under load has not been benchmarked by agent.

## 2026-09-30: Mouse continuity and return-to-start

Captured real prior fault: ID1 voltage sample5.8V rejected by prototype10V
minimum; state FAULT_UNCONFIRMED then stale-command error hid root cause on UI.
Evidence runs/20260930T192155_181483Z_mouse_continuity_home/prior_state.json.
Relative manual mode now uses preserved voltage protection registers15/14
(4/14V measured), removes prototype current150 cutoff, retains firmware error
bits and stored thermal limits. Commissioning and verified mode unchanged.
Relative stream timeout1s holds measured pose without latching FAULT; old epochs
ignored without motion. Transient GET polling failure no longer latches UI off.
Hold verification permits0.6s settling in relative mode, without rewriting goals.
Faults always record recent feedback/commands; UI gives actual controller fault
priority over a subsequent stale-command message. Diagnostic IO failure does
not kill controller worker.
Added home API and Baslangica don UI button. Immutable current-session activation
counts and UI angles define start. Full-speed direct return polls measured
progress, mouse controls blocked until complete, stop/hold cancel. Home independent
of mouse heartbeat; timeout15s holds position without session lock. No autonomous
retry or rebase. Keyboard/pointer release invalidates pending epochs.
62 affected Python tests and9 frontend tests pass, build passes. Actual Chrome
home button tested while already at measured start: completion ACTIVE, no fault.
Away-from-start return tested with fake motor bus; physical route not swept by
agent. Calibration/profile_verified/training_ready remain unverified/false.

## 2026-09-30: Closed home, wrist key and overheating correction

Home now means the recorded folded arm, independent of a session origin.
Saved counts [1966,859,3952,2745,1253,743] and offsets [4080,2861,85,85,85,85]
come from runs/20260930T102331_149186Z_virtual_leader_camera_alignment/reference.json.
Source SHA256 5b5f1c714332ae08873c72542764038801ad3bac3dd24a4660c2cda86b52954d.
The model resets independently; measured physical completion rebases relative
coordinates. Saved counts remain provisional; absolute calibration is absent.
Z+left vertical drag changes only wrist_flex; all other targets are unchanged.

Manual READ timeouts retain the serial handle, cancel old movement, and back off
before fresh all-six telemetry and measured hold. Uncertain goal WRITE is not
replayed. These retries cannot fix an inadequate or damaged power supply.

User reported wrist too hot to touch and repeated heating after repowering.
Prior motor4 readings61..66C and torque1 establish excessive heat and active
holding; prior supply sag4.4..5.7V/current373 are recorded, not a diagnosis.
Manual stop/disconnect now release torque instead of maintaining a holding load.
Software temperature cutoff55C releases all motors; every explicit activation
requires fresh temperatures<=45C. Firmware protection flags are typed errors
and cut torque without sending position commands that may clear protection.
Passive calibration guard and persistent motor settings are unchanged.
Observed telemetry-only manual connections also monitor temperature.

Old served asset index-C9SFzb9s.js SHA256
7913469bb2682a26306330cda45a5d546940715391e1c3f69814567346cd1cc4
contained no KeyZ/wristMode/Z hint when user reported heating. New Z source
had not been deployed. Diagnosis attempts found USB COM5 but no motor replies;
torque-off acknowledgment was absent, so no physical release was claimed.
Evidence: runs/20260930T201533_750688Z_post_overheat_diagnostics and
runs/20260930T201648_339171Z_post_overheat_power_wait. User removed motor supply.

## 2026-10-01: User-authorized wrist replacement and approach-only mode

User reports motor4 failed and moved motor6 into the wrist position. Desired
identity6→4, active motors1..5, absent gripper6. Added explicit hardware config
and five-motor read/activation/target/hold/recovery/thermal/release support.
Six-motor default and verified/probe behavior remain covered by regression
tests; an old verified6-motor profile is rejected in5-motor mode. The frontend
disables gripper slider/wheel while keeping coordinated tip and Z-wrist controls.
Approach-only recordings declare active IDs and no gripper. No grasp success
or reusable standard grasp was physically established.

ID replacement is explicitly user-authorized EEPROM ID5 only, with separate
single-write guard, volatile lock55/torque40 operations, destination collision
preflight, source model/mode/temperature checks, ROM comparison and relock.
Normal/passive bus guards are unchanged. Existing closed-home is invalidated
because physical wrist encoder alignment changed. ID6→4 must be verified
before real trial activation; configuration currently says PENDING.

Physical READ-only scans got no valid replies1..6 on COM5. User confirmed
supply and B jumper, isolated motor1 directly, then used another servo cable;
neither direct test restored a reply. Three baud rates and all DTR/RTS pairs
also failed to decode a valid response. Some raw malformed bytes were received;
this does not establish the adapter is permanently damaged. WCH-signed driver
2.1.2025.7 is installed. No EEPROM/torque/motion command was sent this turn.
Evidence: runs/20260930T224729_541827Z_direct_motor_1_diagnostic and
runs/20260930T225059_111944Z_single_motor_new_cable. Actual ID change blocked
on physical motor communication. No new arbitrary motor movement was attempted.
