#include <AltSoftSerial.h>
#include <Wire.h>
// HC-05 data-mode UART: nominal9600baud, actual module must be checked.
// Fixed UNO pins: D8 RX <- module TX; D9 TX -> LEVEL DIVIDER -> module RX.
// USB Serial is deliberately not a second motor-control owner in this build.
// Timer1 belongs to AltSoftSerial. PCA9685 PWM is external over I2C;
// do not add Servo/TimerOne or analogWrite on D9/D10 to this build.
#ifdef FIGBOT_HC05_USB_TRACE
#include "trace_transport.h"
TracedHc05 hc05;
#else
AltSoftSerial hc05;
#endif
#define Serial hc05
#define FIGBOT_SERIAL_BAUD 9600
// Reuse the exact paired-shoulder state machine / watchdog / validation.
#include "pca_core.h"
