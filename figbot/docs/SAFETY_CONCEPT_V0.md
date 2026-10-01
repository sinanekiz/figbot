# V0 safety concept and review boundary

Status: `CONCEPT ONLY — UNVERIFIED — PHYSICAL VALIDATION REQUIRED`

The bench arm can create pinch, impact, entanglement, electrical and unexpected-
motion hazards even with a light payload. V0 testing therefore requires a defined
restricted envelope, stable anchored stand, guarded pinch points where practicable,
cable restraint, supervised operation and a physical E-stop accessible without
entering the envelope.

The emergency-stop path must act on actuator energy independently of the AI computer,
ROS process and `software/safety` supervisor. Required stop category, contactor or
STO architecture, redundancy, diagnostic coverage, braking behavior, gravity drop,
restart interlock and component ratings are `TBD — SAFETY ENGINEERING REVIEW REQUIRED`.
Do not infer compliance with a standard from this document.

Minimum commissioning gates:

1. Human engineer reviews mechanics, electrical schematics, protective bonding,
   fusing, stored energy and the actual drive disable behavior.
2. The restricted envelope and maximum possible swept volume are physically marked.
3. E-stop is tested first with drives disabled, then at reduced energy using a safe
   fixture; measured stop time/distance and residual motion are recorded.
4. Loss of camera, communications, encoder feedback and limit signal is injected.
5. Reset never restarts motion; a separate deliberate arm/start action is required.
6. Power-cycle, brownout and software crash tests end de-energized or in the reviewed
   physical safe state.

Any failed gate blocks powered automatic cycling. Test personnel, risk assessment,
PPE, lockout and local regulatory requirements must be set by the responsible human
organization before physical work.

