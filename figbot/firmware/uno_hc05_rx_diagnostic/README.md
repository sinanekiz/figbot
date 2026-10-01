# HC-05 receive-only diagnostic

Temporary diagnostic, not a motor controller. Keep battery and servo power off.
Uses existing HC-05 TXD to UNO D10, D11 to RXD via divider, shared ground.
Stock SoftwareSerial receives at 9600 baud but never transmits radio bytes.
USB at 115200 prints `R HH` for every received byte, reports receive overflow,
and accepts no commands. Startup attempts to set FULL_OFF on all 16 PCA9685
channels at address 0x40; an I2C acknowledgement is not a physical power check.

Android will report a response timeout by design. Connect once and wait about
10 seconds without enabling motors. This isolates receive-only behavior from
the production controller's bidirectional traffic and parser. A clean capture
would not by itself prove the complete electrical path or identify a library bug.

2026-09-10: the D10 wiring correction did not resolve the fault. The second trace,
`hc05-trace-20260910-002306.log`, contains `AC 0A` followed by ERR FRAME as well as
correct H/LF pairs. This diagnostic compiled (5340 flash bytes, 537 RAM bytes),
passed native receive-only/output-disable tests, and was uploaded to COM3 with
all 5340 flash bytes verified. See `.codex_artifacts/arduino/hc05-rx-only-upload-20260910.log`.
Physical receive-only retry is pending. Restore the regular HC-05 controller
after diagnosis and before any further motor test; do not treat this as a fix.
