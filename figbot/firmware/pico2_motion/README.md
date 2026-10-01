# Pico 2 motion firmware — release candidate

This firmware provides four synchronized STEP/DIR axes, sequential NC-switch homing, active-low drive enable,
CRC-protected USB serial commands, driver-alarm monitoring, NC home inputs, a
300 ms host heartbeat watchdog, fault latching, and explicit arm/disarm states.

It does **not** replace the hardwired two-channel E-stop/safety relay. GPIO
inputs only monitor the safety relay auxiliary contact. Drive energy must be
removed independently of this MCU.

## Build and load

1. Install the official Raspberry Pi Pico SDK, CMake, Ninja, ARM GNU toolchain, and a native compiler for `picotool`.
2. On the prepared FIGBOT Windows workstation run `powershell -ExecutionPolicy Bypass -File scripts/build_pico2_firmware.ps1` from the repository root.
3. The controlled build uses Pico SDK 2.3.0 and emits `build-pico2-sdk230/figbot_pico2_motion.uf2` plus ELF/BIN/HEX outputs.
4. Hold BOOTSEL while connecting Pico 2 and copy
   `build-pico2-sdk230/figbot_pico2_motion.uf2` to the USB mass-storage device.

Verified build on 2026-08-20: Pico 2/RP2350 ARM-S, Pico SDK 2.3.0, ARM GNU 15.2.1;
UF2 SHA-256 `66458639DF1F5BC0FD7604F225D16FD46E649B3E661BE93F9A596CC48BCB3746`.

Before any motor is coupled to the arm, follow `docs/COMMISSIONING_V0.md`. Pin
polarity, home direction, current settings, zero offsets and the physical
E-stop response are `PHYSICAL VALIDATION REQUIRED`.
