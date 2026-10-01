# FIGBOT V0 electrical package

This package defines a bench-prototype electrical baseline. It is not a production wiring design.

- Nominal actuator bus: 24 VDC (`ESTIMATE`, pending dynamometer tests).
- Logic rails: isolated/protected 5 VDC and 3.3 V logic as required by selected modules.
- Motion: J1/J3/J4 candidate closed-loop stepper kits; J2 candidate closed-loop NEMA 23 kit; G1 candidate current-reporting smart servo.
- Safety: a dual-channel emergency-stop concept that removes actuator power independently of application software.

Every numerical field is tagged in its source file as `ESTIMATE`, `CALCULATED`, or `UNVERIFIED`. Candidate products are research inputs only. Do not buy motors until the torque-speed curve has been checked at the intended bus voltage and reduction ratio.

> **HUMAN ENGINEERING REVIEW REQUIRED** before mains wiring, energization, motion testing, or physical prototype use.

