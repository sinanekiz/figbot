# Software safety supervisor

`interlocks.py` is a testable supervisory state machine for V0 development. It
defaults to de-energized, latches E-stop/fault states and requires an explicit
reset before re-arming.

It is **not safety-rated** and must never be the sole means of stopping hazardous
motion. A physical, hardwired E-stop must remove or inhibit actuator energy via a
human-reviewed circuit independently of this process. Contactors/STO, braking,
stored energy and reset behavior are `TBD — SAFETY ENGINEERING REVIEW REQUIRED`.
The complete system is `UNVERIFIED — PHYSICAL VALIDATION REQUIRED`.

