# V0 operating concept

Status: `PROTOTYPE — UNVERIFIED — PHYSICAL VALIDATION REQUIRED`

V0 is a supervised bench experiment. A fixed camera observes the target area, the
perception process proposes a `dry_fig_collect` target, coordinate conversion maps
it into `base_link`, and motion software checks reach and collision before sending
a trajectory. The gripper closes under a configurable experimental limit, lifts
the item, moves to the nearby funnel and releases it.

The operator remains outside the safeguarded motion envelope, monitors every run,
and can operate a physical hardwired E-stop. Initial commissioning must use no
fruit, reduced torque/current where supported, reduced speed, one axis at a time,
then inert surrogate objects. Autonomous repeated picking is not authorized until
the physical test-plan prerequisites are signed off.

The perception decision gate, collision model, torque estimates and software
interlocks are engineering aids, not safety functions. Soft fruit rejection,
damage performance, positioning accuracy, cycle time and emergency stopping
behavior all remain unverified.

## Control flow

1. Power-on keeps actuator enable de-energized.
2. Operator inspects mechanics, guards, wiring, target zone and funnel.
3. Calibration verification is run with actuators disabled.
4. Hardwired stop chain and software fault reporting are tested separately.
5. Operator resets faults, explicitly arms, and initiates one supervised cycle.
6. Any stale camera/control data, limit violation, drive fault or stop input causes
   a motion-disable request; physical stop behavior depends on the reviewed circuit.
7. After release, the system disarms or requests the next target only in the
   explicitly selected test mode.

## Prohibited assumptions

- A high detector confidence does not prove an object is safe to collect.
- A successful simulation does not prove collision clearance or structural safety.
- Software stop latency does not establish emergency-stop performance.
- Example thresholds and transforms are not commissioning values.

