# FIGBOT V0 assembly manual

Release state: `DRAFT — UNVERIFIED — PHYSICAL VALIDATION REQUIRED`

This manual covers the bench V0 assembly, not the master CAD assembly. Use only with
the current BOM, drawings, wiring documents and inspection records. Stop on any part
code/revision mismatch. All tightening torques are `TBD – FASTENER/JOINT ENGINEERING
REVIEW REQUIRED`; do not substitute generic torque values for printed or thin-wall
joints.

## Part map

```text
CHA-001 test-stand base
├─ ARM-001 base plate
│  └─ ARM-002 J1 housing + ARM-007 shaft
│     └─ ARM-003 upper-arm tube
│        └─ ARM-004 elbow housing + ARM-007 shaft
│           └─ ARM-005 forearm tube
│              └─ ARM-006 wrist housing + ARM-007 shaft
│                 └─ GRP-001 body + one of GRP-002 / GRP-003 / GRP-004
├─ VIS-001 camera pole/bracket
├─ FUN-001 funnel + FUN-002 liner + FUN-003 channel
└─ ELE-001 electronics tray
```

GRP-005/006/007 are molds/tooling and are not installed on the robot.

## Hardware allocation (controlled V0 baseline)

| Interface | Standard/purchased reference | Fastener/washer/retainer | Torque/status |
|---|---|---|---|
| CHA-001 to bench | M10 anchors selected for the actual bench construction | washer/anchor stack requires site review | anchoring proof test required |
| ARM-001 to CHA-001 | ISO 4762 M8 class 10.9 + ISO 7089 + prevailing nuts | FASTENERS.csv | torque verified on first assembly |
| J1/J2 shaft stacks | 6002-2RS + ARM-007 15 mm | collars/retainers per signed shaft drawing | drawing signoff + fit check |
| J3/J4 shaft stacks | 608-2RS + ARM-008 8 mm | collars/retainers per signed shaft drawing | drawing signoff + fit check |
| Joint drives | PUR-001 J2; PUR-002 J1/J3/J4 geared motors | Ruland 14-to-15 and 8-to-8 jaw couplings; FASTENERS.csv | torque-speed/counterbalance tests required |
| GRP-001 actuator | ROBOTIS XL330-M288-T | M2/M2.5 schedule per FASTENERS.csv | force/current PHYSICAL VALIDATION REQUIRED |
| VIS-001, FUN-001, ELE-001 | FASTENERS.csv and STANDARD_PARTS.csv | interface-specific washers/locking hardware | first-article review |

`FASTENERS.csv`, `STANDARD_PARTS.csv` and `INTERFACE_CONTROL.csv` are the controlled
schedules. Do not substitute bearing fits, couplings, motor variants or fastener
grades without revising the affected drawing/BOM and repeating the review.

## Tools and preparation

- drawing-specified hex keys/spanners, calibrated torque tool once values are released;
- bearing/shaft installation tools that apply load to the correct race;
- square, level and measuring tools appropriate to released drawings;
- cable labels, approved ties/clamps and clean gloves for product-contact parts;
- lockout device and verified absence-of-energy method.

Inspect every part and record its revision. Keep actuator power disconnected through
mechanical assembly and continuity checks. Do not work below an unsupported arm.

## 1 — Stand and base

1. Place CHA-001 on the defined rigid bench and install its drawing-specified anchors.
2. Verify stability/level and mark the full predicted swept envelope.
3. Fit ARM-001 using BOM-listed fasteners, washers and retention method. Tighten in a
   cross pattern only to a released joint torque.
4. Confirm ARM-001 datum orientation and no rocking/gap. Record check.

Hold point A: responsible engineer approves stand anchoring and restricted envelope.

## 2 — J1

1. Inspect ARM-002 bearing seats and the correct ARM-007 shaft configuration.
2. Install bearings/shaft by the drawing method; never transmit installation force
   through rolling elements.
3. Mount ARM-002 to ARM-001 in the orientation shown by the assembly CAD.
4. Install the signed retainers and controlled coupling from the BOM. Rotate by hand through the limited
   commissioning range; verify smooth motion and axial retention.

## 3 — Shoulder and upper arm

1. Install ARM-003 with its datum/label facing the drawing-specified direction.
2. Fit the shoulder ARM-007 shaft, bearings, spacers and retainers in BOM order.
3. Fit the coaxial jaw coupling without forcing either shaft or preloading the bearings.
4. Support the arm and check that cables cannot be trapped throughout manual motion.

Install the controlled J1/J2 geared motors only after incoming shaft, pilot and hole
measurements pass. Confirm coupling gap, clamp engagement, shaft retention and the
guarded gravity-drop zone before power.

## 4 — Elbow and forearm

1. Attach ARM-004 to ARM-003; verify housing orientation and joint-axis alignment.
2. Install ARM-008 and the drawing-specified 608-2RS bearing/retainer stack.
3. Attach ARM-005, preserving tube orientation and fastener engagement.
4. Manually articulate while supported. Stop for binding, rubbing, cracking or play.

Install the controlled J3 PUR-002 geared motor and 8-to-8 jaw coupling. Verify
coupling gap, free rotation and driver/encoder cable clearance.

## 5 — Wrist

1. Attach ARM-006 to ARM-005 with the released interface hardware.
2. Install the wrist ARM-008 shaft/configuration, 608-2RS bearings and retainers.
3. Verify J4 hand motion and mechanical limits against CAD before any motor power.

Install the released J4 motor/transmission only after calculation and fit review.

## 6 — Gripper

1. Install GRP-001 with the keyed orientation toward the work surface.
2. Select exactly one trial variant: GRP-002 (A), GRP-003 (B) or GRP-004 (C).
3. Inspect silicone lot, tears, tackiness, contamination and retention features.
4. Fit fingers without preloading beyond the drawing intent. Check low-force manual
   opening/closing and clearance. Force/current limits remain `UNVERIFIED`.
5. Install the released gripper actuator (PUR-003 is only a candidate), with the
   drawing-specified fastener/washer stack and strain-relieved cable.

## 7 — Camera, funnel and electronics mounts

1. Attach VIS-001 to CHA-001; torque only after camera field-of-view setup is checked.
2. Assemble FUN-002 into FUN-001, ensuring no sharp seam or trapped contamination;
   connect FUN-003 without a step that can impact fruit.
3. Mount funnel outside modeled arm clearance and camera field obstruction zones.
4. Attach ELE-001. Maintain separation, ventilation and cable-edge protection from
   the reviewed electrical layout.

## 8 — Cabling

Follow the released wiring/pinout documents. Label both ends. Provide strain relief
before connectors, keep cables away from joints/couplings/sharp edges, preserve required
bend radii and leave only controlled service loops. Protective earth, shielding,
fusing and E-stop wiring require electrical review and continuity/insulation tests.

## 9 — Mechanical acceptance before energization

- all installed part numbers/revisions and fastener presence recorded;
- joints manually move without collision/binding in the restricted check range;
- shafts/bearings/couplings retained and aligned; no tools/loose parts remain;
- base anchored, swept envelope marked, gripper/funnel product path clean;
- camera mount rigid and calibration check points visible;
- cable strain relief and pinch clearance inspected;
- hardwired E-stop and drive-energy isolation reviewed but not yet assumed functional.

Sign the `PRE_POWER_CHECKLIST.md`. First power is performed under the physical test
plan at reduced energy/speed with one axis enabled at a time. Assembly completion is
not evidence of structural, functional or safety validation.
