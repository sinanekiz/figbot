# Varsayımlar ve doğrulama durumu

- Yeni çalışma alanı kullanıcının isteğiyle mevcut FIGBOT projesinin yanında oluşturuldu.
- Mevcut FIGBOT kodu, APK'sı, motor ayarları ve yayın paketleri bu çalışma tarafından değiştirilmez.
- Kaynak bilgisayar: NVIDIA RTX 3050 Ti Laptop, 4 GB VRAM. Çıkarım CUDA ile test edildi; uyarlama eğitiminin belleğe sığması ayrıca ölçülmelidir.
- PC kamerası ve sonrasında telefonun USB kamera aktarımı fiziksel olarak denendi. Kullanıcı telefon kamerasını seçti; mevcut FIGBOT v37 aktarımı kullanılıyor. Motor verisi bu bağlantıda alınmıyor.
- Mevcut kayıt: tek telefon görüntüsü, altı ham motor sayımı, ayrı kamera/enkoder zamanları. Ham sayım → hazır model eklem birimi eşlemesi UNVERIFIED.
- Eski koordinat referanslarının tamamlanmış LeRobot kalibrasyonu olduğu kabul edilmez. Bu nedenle eşleme şablonundaki sayılar boş bırakıldı.
- `camera-smoke`, eksik gerçek eklem verisi yerine modelin eğitim ortalamasını kullanır. Yalnız görüntü/model bağlantısı ve süre ölçümüdür; hareket doğruluğu veya toplama testi değildir.
- Tek kamera girişi SmolVLA kodunda çalışır; iki/üç kamerayla eğitilen modelin tek kamerada aynı başarıyı koruyacağı doğrulanmadı.
- SmolVLA base bir uyarlama başlangıcıdır. Dokuz görevli modelin yayımlayıcısı fiziksel doğrulama bulunmadığını belirtir.
- Referans örneklerin modellerin eğitiminde kullanılıp kullanılmadığı UNKNOWN. Çıkarım testleri bağımsız başarı değerlendirmesi değildir.
- Base referans denemesinde normalizasyon referans veri setinin tamamından alınır; bağımsız doğrulama olarak kullanılamaz. Görev modelinin kamera2 girdisi bilek görünümü için eğitilmişken referans veride yandan görünüm vardır; karşılaştırma bir aktarım denemesidir.
- Eski düzeltilmiş hedeflerdeki kıskaç değerleri sentetiktir; bunlar gerçek lider kol komutları değildir. Eğitim dışa aktarımı bu bilgiyi korur.
- Aynı kayıttaki son inciri ayırmak yeni sahne genellemesi kanıtı değildir. Eğitim ve doğrulama aynı sahneden farklı tam çevrimlerdir.
- Bu aşamada robot komutu, motor kalibrasyonu ve fiziksel toplama denemesi yapılmadı.

## 2026-09-29 passive calibration baseline
All six motors answered on COM5 at 1 Mbaud, torque=0, stable raw positions [1956,768,3952,2749,1255,1280]. Evidence: runs/20260929T082136_402956Z_calibration_baseline/measurement.json. Register limits all 0..4095 are not proven mechanical limits. Neutral pose, ranges, directions, software wrap handling, and paper release pose require physical review. No VERIFIED mapping or executable route has been produced.

## 2026-09-30 review validation
72 tests passed. Archived-image CUDA inference used the current paper-placement task
and checkpoint mean state, not current robot telemetry. No physical movement or new
hardware calibration was performed during this review. Initial calibration photo
measurements predate continuous encoder observation; do not treat those old files
as having the new per-image timing associations. Review: KOD_INCELEMESI_20260930.md.

## 2026-09-30 fixed release location
User states the rear crate stays at a fixed location in deployment. Treat its
position relative to the robot base as the intended fixed reference; numeric
pose, release height, reachability and transfer corridors remain UNVERIFIED.
The learned stage ends at grasp; verified retention is the handoff gate.
No grasp detector, physical short-lift routine, route planner or grasp-only
training export has been implemented by this design/configuration update.

## 2026-09-30 virtual leader

SO101 render uses the published MuJoCo visual hierarchy and exact source meshes.
URDF/MuJoCo ranges govern visual motion only; they are not our physical motor
envelopes. Colors differ from actual prints. Servo-to-model zero/direction and
physical working ranges remain UNVERIFIED; virtual_leader.template.json is empty.
Existing pretrained policy mapping remains separate and UNVERIFIED.

Current read-only connection test: COM5, all six torque0, raw positions
[1956,768,3950,2619,1254,744], voltage12.2..12.4V, temperatures28..30C.
Later positions may change while the unpowered arm is handled. These positions
are not a zero pose or travel limits. No goal, torque or EEPROM write was issued
in this physical check. The new streaming profile45counts/s and speed/acceleration
57/1 is an initial experiment setting, not physically validated teleoperation.
Software hold/stop cannot prove an unplugged robot stopped and does not replace
a physical power stop. Simulation logs have no real images or physical success.

## 2026-09-30 tip IK control

The visual tip reference is the centroid of mesh vertices in the final 2% of
the fixed finger's local Z extent, transformed by its published visual pose.
This is a software interaction reference, not a measured physical TCP or grasp
center. Physical TCP, collision clearances and real IK tracking remain UNVERIFIED.
Five arm DOFs cannot guarantee arbitrary six-dimensional pose tracking; the
solver prioritizes position while softly retaining the starting orientation.
Per-event joint changes are bounded at 0.12 rad using published model ranges;
these are visual limits, not verified physical working ranges.

## 2026-09-30 relative base probe

Motor 1 association and encoder-positive clockwise direction were observed in
the user's manual base test: runs/20260930T102830_172846Z_virtual_leader_pan_direction.
Six raw counts are about 0.53 degrees of encoder-reported rotation. The small
relative probe does not establish absolute model zero, calibrated TCP or working
limits. Its speed/current/temperature checks are experimental software checks,
not a physically validated collision or force protection system. Powered results
must be recorded separately; preparing the probe alone is not physical validation.

Physical base probe completed after a fresh side-view review. Evidence:
`runs/20260930T162139_586762Z_base_probe_execution/probe_result.json` and
`probe_events.jsonl`, with 40 captured frames. Measured home=2103, excursion
peak=2098, final=2102 counts; final speed/current=0. Motor 1 torque remains on;
IDs 2..6 torque stays off, positions stationary within one count. Persistent
registers 0..39 compared equal before/after. The serial owner was returned to
the existing server in CONNECTED read-only state. This validates the small
relative base probe only; absolute zeros, other joint directions and working
limits remain UNVERIFIED. No VERIFIED profile was created.

Batch attempts at `runs/20260930T164356_323803Z_six_joint_probe_execution`
and `runs/20260930T164744_298707Z_six_joint_probe_execution` did not complete.
Only base goals were sent. The second stopped with base measured 2091 and goal
2087 counts, with reported speed 0 and current_raw 1. The encoder changed by
eight counts from that attempt's start; the tighter two-count endpoint criterion
failed. This is an observed tracking residual, not evidence of a mechanical stop.
LeRobot's register table identifies CW/CCW dead zones at 26/27; the preserved
baseline settings contain 1/1. Do not attribute this residual to a larger factory
dead zone without further evidence. All remaining motor tests are pending until
successful physical measurements are recorded. No angle calibration was created.

## 2026-09-30 completed six motor commissioning

Successful evidence: `runs/20260930T172625_981517Z_six_joint_probe_execution`.
All six current-position holds were verified before individual relative tests.
Measured home/peak/final-at-end-of-batch counts:
1: 2084/2038/2083; 2: 1106/1146/1105; 3: 3914/3877/3914;
4: 2680/2713/2681; 5: 1252/1297/1253; 6: 743/788/748.
All final speeds are zero and torques are one. Persistent registers 0..39 compared
equal before/after. Saved 541 camera frames and command/readback/feedback events.
The server regained exclusive serial ownership in CONNECTED telemetry-only state.
This establishes motor response and approximate return for these six small paths.
It does not establish absolute model angles, axis directions for every joint,
mechanical limits, collision clearance for other motions or learned grasp success.
The VERIFIED virtual leader profile is still absent. Current motors remain holding.

Diagnostic evidence `runs/20260930T170951_180978Z_feedback_gate_diagnostic`
recorded shoulder temperature 68C; its preserved register-13 limit is 70C.
This triggered the earlier 55C software gate. Commissioning uses that unchanged
hardware limit; full verified teleoperation retains the lower prototype threshold.

## 2026-09-30: Active relative mouse trial

Current-position holding activation physically measured, all six torques=1,
speeds=0. Trial origin [2082,1103,3914,2681,1252,747]; final snapshot jaw748.
Absolute zeros, all model-axis signs and mechanical working limits UNVERIFIED.
Trial reference angles copied from current Chrome sliders, not metrology.
+/-256 counts (22.5deg), 90 counts/s and lead32 are software trial choices;
combined motions across that bank require physical validation. Recorded earlier
small probes do not validate the larger combined bank or collision clearance.
Phone USB camera unavailable at this activation (adb devices empty); only
current-position hold was sent, no new movement demo. End-to-end mouse-induced
physical movement has not been observed in this turn. UI command path and
release/watchdog behavior verified with fake bus tests. VERIFIED profile remains
absent. Training exports must not treat this relative state as calibrated state.

## 2026-09-30: Full-speed relative settings

Previous 22.5-degree, rate90/lead32 assumptions superseded for relative mode.
Hardware speed3400 and acceleration50 read back from all six motors; firmware
clipped requested150 to50. Current-position activation successful at3400/50.
Actual achieved velocity under load UNVERIFIED. Electronic min/max0/4095
is not evidence of mechanical clearance. Absolute zeros/all axis directions
remain UNVERIFIED; training_ready remains false. No automatic physical sweep.

## 2026-09-30: Continuity fault and home

Observed5.8V sample is not proof of benign measurement error or normal power.
Transient supply sag vs erroneous telemetry UNVERIFIED. Manual mode uses existing
register4..14V limits; nominal supply suitability not certified. Prototype150
current threshold removed only for user-authorized manual mode, hardware current
protection left unchanged. Prior snapshot stale418s after fault; fresh actual
activation origin now[1951,825,3911,2763,1152,937]. Home means these session-start
counts, not pretrained/model zero. Clicking home at this already-reached start
physically verified complete; return from other poses PHYSICAL VALIDATION REQUIRED.
Full-speed operation, all directions and collision clearance remain UNVERIFIED.

## 2026-09-30: Overheating and revised closed home

Session-start home is superseded by provisional saved folded counts and
independent virtual closed angles. Returning from an arbitrary physical pose
and absolute direction mapping remain PHYSICAL VALIDATION REQUIRED. Relative
rebase repairs software origins, not full motor or TCP calibration.

Old manual70C threshold/holding stop policy is superseded by55C torque release,
<=45C fresh activation and no automatic restart. Motor supply was removed by
the user after repeated overheating. Latest READ attempts got no responses
from all6motors; no new physical temperature/torque or damage diagnosis exists.
Motor4 overheating/stall/drive damage vs supply fault remains UNVERIFIED.
Actual case voltage variant and PSU nameplate remain UNKNOWN; model777 alone
does not distinguish published STS3215 7.4V versus12V variants. Earlier working
motion does not prove present motor health. Keep physical supply off until
the reported repeated heating is resolved; no autonomous motion after report.

## 2026-10-01: Replacement motor and missing gripper

Motor4 failure and installation of former motor6 at wrist are user reports.
Actual new wrist ID/encoder zero/direction remains UNVERIFIED until READs work.
ID6→4 write has not occurred: latest direct one-motor/two-cable tests yielded
no valid reply. Adapter/data path/USB/supply fault vs motor health remains
UNKNOWN. LEDs are not communication proof; no board failure is certified.
Old motor4 raw closed-home target must not be reused on the replacement.
The gripper is explicitly absent and must never be synthesized as live motor
telemetry. Grasp will require physical motor hardware again; user expectation
of largely standard grasp is not a verified success rate. Current goal is
approach-only, without grasp execution or training-ready success labels.
