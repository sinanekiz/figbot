# V0 motor sizing basis

## Status and scope

The values in `MOTOR_REQUIREMENTS.csv` are requirements, not motor selections. They use estimated masses because final CAD mass properties and measured friction do not yet exist. Therefore the output is **CALCULATED_FROM_ESTIMATE_INPUTS**, not physically verified.

## Input set

| Input | Value | Status |
|---|---:|---|
| Upper-arm length | 0.300 m | ESTIMATE; synchronized with `cad/config/parameters.py` |
| Forearm length | 0.220 m | ESTIMATE; synchronized with `cad/config/parameters.py` |
| Upper-arm distributed mass | 0.350 kg | ESTIMATE |
| Forearm distributed mass | 0.250 kg | ESTIMATE |
| Wrist + gripper mass at tip | 0.300 kg | ESTIMATE; includes 0.220 kg gripper target plus 0.080 kg wrist allowance |
| Maximum picked product | 0.100 kg | ESTIMATE; synchronized with `cad/config/parameters.py` |
| Gravity | 9.80665 m/s² | DEFINED_CONSTANT |
| Driveline loss allowance | 10% of gravity torque | ESTIMATE |
| Sizing multiplier | 1.5 | ESTIMATE; covers input/model uncertainty only, not a certified safety factor |

The 80 g payload is deliberately above a single fig's expected mass, but has not been confirmed from the intended product population.

## Equations and results

For J2 in the fully extended horizontal pose:

`Tg = m_upper*g*(L_upper/2) + m_fore*g*(L_upper+L_fore/2) + (m_tool+m_payload)*g*(L_upper+L_fore)`

This produces about 3.56 N·m gravity torque. A lumped inertia estimate of 0.158 kg·m² at 5.236 rad/s² adds about 0.83 N·m. Adding a 10% loss allowance and applying the 1.5 uncertainty multiplier produces a peak output requirement of about 7.11 N·m. Continuous output torque is provisionally 4.00 N·m. Both require final CAD and thermal validation.

For J3:

`Tg = m_fore*g*(L_fore/2) + (m_tool+m_payload)*g*L_fore`

This produces about 1.13 N·m gravity torque. Estimated acceleration at 6.283 rad/s² and loss allowances followed by the same multiplier produce about 2.08 N·m peak output requirement.

J1 excludes gravity because its nominal axis is vertical. Its 1.64 N·m peak is based on the same 0.158 kg·m² extended-arm inertia, 6.283 rad/s² acceleration, 0.10 N·m friction, and the same multiplier. J4 and G1 remain `ESTIMATE`/`UNVERIFIED` until tool CAD and fig compression tests exist.

## Candidate screening gates

Before choosing a motor:

1. Export actual moving-body masses and centers of mass from CAD.
2. Recalculate worst-pose gravity, inertia, gearbox efficiency/backlash, bearing friction, coupling effects, and cable drag.
3. Read the manufacturer's torque-speed curve at the intended supply voltage and calculated motor rpm; holding torque is not running torque.
4. Bench-test one axis with the controlled 10:1 gearbox, coupling and controller current limit.
5. Confirm encoder fault handling, homing behavior, thermal rise, and gravity-drop behavior on loss of power.
6. Add a counterbalance or brake for J2 if a safe power-loss state cannot be demonstrated.

The controlled part numbers are documented in `purchasing/CONTROLLED_COMPONENTS.csv`, but they remain physically unverified selections. Published holding, permissible and momentary torque values must not be substituted for measured continuous torque at speed.
