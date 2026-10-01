# V5 source — 2026-09-10

Current source uses V5/STATUS5 with five-field S/PAIR messages (leader, angle, speed, min, max). Symmetric min500..1000 in100us increments, max3000-min; range cannot change while active. Explicit re-arm/first centre,360speed ceiling, shared complementary ramp and shutdown/watchdog retained. Androidv0.9 required; see releases/HC05-v0.9-KURULUM.md. HC-05 build9874bytes/634RAM, USB alternative9360bytes/615RAM. V5 hardware installation pending; no live motor command issued during this implementation.

# V4 speed update — historical verified installation

Installation: normal V4 release successfully uploaded on COM4 with motor power disconnected. All 9680 application bytes passed paced per-page/full readback and separate avrdude 8 verification. USB trace is disabled in this build. Reconnection/STATUS4 from Android and actual motor operation remain pending. Bulk-write attempts failed with single-byte corruption; `tools/uno_paced_upload.py` and its tests provide a verified paced transfer path, not a diagnosis of board/driver failure. See ASM-V4-FLASH-VERIFIED.

Current source uses V4/STATUS4 and accepts 10..360 command deg/s for P and paired S commands. Pair geometry, narrow pulse span, centre-first activation, shutdown/watchdog and D8/D9 AltSoftSerial transport remain unchanged. Android v0.8 and the updated desktop client require V4; update client and controller together. Build artifacts and installation sequence are in `releases/HC05-v0.8-360-KURULUM.md`. No physical speed/torque validation follows from this setting. HC-05 build: 9680 bytes flash, 634 bytes RAM; USB alternative: 9166 bytes flash, 615 bytes RAM. Current V4 hardware installation remains pending.

The following V3 logs describe earlier hardware experiments, not the current V4 source or an installation confirmation.

# UNO HC-05 transport

**Current physical limitation (2026-09-10):** Idle readiness passed, but user-confirmed motor movement is followed by communication failure. The 00:41:52 log contains malformed input (including 0x02), then ERR FRAME and OFF ALL, with no additional startup header. Exact source remains unverified. Motor powering/ground routing must be identified and the same controller tested with servo power removed. Do not treat the AltSoftSerial change as a complete fix or this setup as validated for powered motion. No further reset/upload while the user may be exercising the arm.

Power-isolation update at 00:55:06: user reports the connection stays up after removing the Samsung 10000 mAh powerbank motor supply, and the trace contains further motion commands/status replies without a later captured ERR. The same firmware remains installed. This supports investigating motor supply/cabling/ground/interference; it does not prove that the powerbank itself is faulty. Output rating and wiring photos are pending. Stop/disarm before restoring motor power: active command state may exist while motors are unpowered.

Current build: Arduino Uno (ATmega328P), HC-05 data UART at 9600 baud, **UNO RX D8 and TX D9** through the existing 1k / 2k divider. Install **AltSoftSerial 1.4.0** with Arduino Library Manager or `arduino-cli lib install AltSoftSerial@1.4.0`. Pins are fixed by Timer1 hardware: HC-05 TXD goes directly to D8; move the existing D11-to-A18 divider input lead to D9. Retain HC-05 RXD at A14 and the divider/ground wiring. Disconnect USB and keep motor power off when moving leads.

AltSoftSerial uses Timer1; do not combine this build with Servo/TimerOne or D9/D10 analogWrite. The PCA9685 shared core generates PWM externally via I2C and does not consume Timer1. Reference: https://www.pjrc.com/teensy/td_libs_AltSoftSerial.html .

The shared PCA9685 V3 core retains frame validation, paired shoulders, disabled startup and the 1500 ms watchdog. `sync_core.py` refreshes the byte-identical generated copy after intentional core edits. No second USB command owner exists.

History: on 2026-09-09 the user reported `ERR FRAME` after pairing and uploading the SoftwareSerial build. Android sends `X\nH\n` and may send another heartbeat on its first polling tick. Stock AVR SoftwareSerial disables receive interrupts while transmitting replies. A NeoSWSerial 3.0.5 trial on D10/D11 did not resolve the fault. Those old pin assignments are superseded by D8/D9. Actual causation remains UNVERIFIED; this transport replacement is not a confirmed physical fix.

Validation: actual Uno compile, shared-core native tests including the exact Android startup burst and malformed-frame rejection. These tests do not simulate electrical UART timing. Upload results are recorded under `.codex_artifacts/arduino/`.

Source: https://github.com/SlashDevin/NeoSWSerial (simultaneous RX/TX and ATmega328P support).

## USB observation build

Compile with `compiler.cpp.extra_flags=-DFIGBOT_HC05_USB_TRACE` to log each Bluetooth byte as `R HH` (received) or `T HH` (transmitted), with hexadecimal HH, over USB at 115200 baud. `trace_transport.h` does not accept USB commands and skips trace records when the USB buffer lacks space. The control protocol and watchdog remain unchanged. Firmware tests cover unchanged byte forwarding and the full-debug-buffer case; they do not validate electrical signal levels.

The user reported continued ERR FRAME / UNO response timeout after the NeoSWSerial upload. Therefore that library change was not a confirmed resolution. The first observation upload had a flash verification mismatch; a complete retry subsequently verified all 11358 bytes. Its startup USB trace reported outgoing `FIGBOT_PCA9685_V3` and `STATUS3 0,0`, showing PCA initialization success and disabled channels at that moment. See historical `hc05-trace-upload-01a085f5.log` and timestamped `hc05-trace-*.log` under `.codex_artifacts/arduino/`.

The 2026-09-10 00:09:44 observation captured RX hex `52 E1 48 0A 48 0A 56 21 29 E1 48 0A FF`, two status replies and then `ERR FRAME`, with channels disabled. Correcting the D10 jumper did not resolve malformed input (00:23:06 log). A receive-only SoftwareSerial diagnostic then captured only valid X/LF and H/LF packets, with no overflow report (00:26:21 log). This points toward the bidirectional transport path but does not isolate software timing from electrical interaction, since both library and transmit behavior changed. It does not verify loaded operation.

Current installed firmware: AltSoftSerial observation build, compiled 10902 flash bytes / 843 RAM bytes, four relevant native tests passed, COM3 upload verified all 10902 bytes (`hc05-alt-upload-20260910.log`). Core byte equivalence, stop/watchdog and malformed-frame rejection remain intact. Normal build also compiles (9676 flash / 634 RAM). The logger runs for 900 seconds; loss of USB requires restarting it. No motor movement was commanded.

Idle physical result, 2026-09-10 00:36:52: user reports Android ready after D8/D9 rewiring. Snapshot of `hc05-trace-20260910-003215.log` captured 181 H/LF heartbeats, 180 complete `STATUS3 0,0` replies, zero captured ERR replies and zero unexpected RX bytes. Trace output can skip records when the USB buffer is full; it is not a lossless UART analyzer. This is a successful idle roundtrip with all channels disabled, not proof of the earlier root cause or loaded/long-duration operation. Keep the verified pin mapping; battery/servo powering and motion remain pending physical checks.
