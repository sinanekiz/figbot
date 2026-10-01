# V0 wiring diagram and field rules

## Functional diagram

```text
FACILITY 230 VAC
  -> Q0 lockable disconnect
  -> F0 branch protection
  -> PS1 24 VDC enclosed PSU
       -> SR1 safety relay supply
       -> E-STOP CH-A / CH-B -> SR1
       -> SR1 safe outputs -> K1 + K2 coils with EDM feedback
       -> K1/K2 switched 24 V ACTUATOR BUS
            -> F1 -> J1 driver -> J1 motor + encoder
            -> F2 -> J2 driver -> J2 motor + encoder
            -> F3 -> J3 driver -> J3 motor + encoder
            -> F4 -> J4 driver -> J4 motor + encoder
            -> F5 -> DC/DC 5 V gripper -> G1
       -> F6 -> DC/DC 5 V logic -> AI computer + camera + MCU

AI computer <Ethernet/USB> MCU
MCU -> isolated STEP/DIR/ENABLE -> J1..J4 drivers
drivers -> isolated ALARM -> MCU
MCU <- limit/home switches and gripper telemetry
SR1 auxiliary status -> MCU digital input (monitoring only)
```

## Wiring rules

- Use ferrules on fine-stranded conductors in screw terminals where allowed by the device manufacturer.
- Keep mains inside a finger-safe enclosure with strain relief, PE bonding, barriers, and labels.
- Use one fuse per driver branch; never rely on software current limits as branch protection.
- Controlled prototype gauges, lengths, flex classes and termination families are listed in `CABLE_LIST.csv` and `CONNECTOR_LIST.csv`. Delivered cable pinouts, thermal derating, mains insulation/coordination and final routing remain `HUMAN ENGINEERING REVIEW REQUIRED`.
- Encoder/motor pin colors in vendor cables must be verified against the exact delivered kit; color is not a universal pinout.
- Use normally closed home/limit loops where feasible so a broken wire becomes detectable; software must treat an open circuit as a fault until homing logic is validated.
- Limit switches are operational controls, not the emergency-stop safety function.

## Bring-up sequence

1. Complete insulation, PE-continuity, polarity, and short-circuit checks with power disconnected.
2. Energize logic only; verify E-stop status and all inputs.
3. Energize one driver branch at current-limited settings with mechanics restrained and workspace excluded.
4. Verify direction, home input, encoder feedback, driver alarm, and power-loss behavior.
5. Repeat per axis, then validate the complete emergency-stop chain and measured stop time.

> **HUMAN ENGINEERING REVIEW REQUIRED** before energization.
