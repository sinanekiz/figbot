#pragma once
#include <AltSoftSerial.h>

// Optional USB observation only: USB bytes are never accepted as commands.
// Do not block the motor loop if the USB debug buffer is full.
class TracedHc05 : public AltSoftSerial {
 public:
  void begin(uint16_t baud) {
    Serial.begin(115200);
    Serial.println(F("HC05_TRACE ALT RX=D8 TX=D9 BAUD=9600"));
    AltSoftSerial::begin(baud);
  }
  int read() override {
    int value = AltSoftSerial::read();
    if (value >= 0) record('R', (uint8_t)value);
    return value;
  }
  size_t write(uint8_t value) override {
    size_t result = AltSoftSerial::write(value);
    if (result) record('T', value);
    return result;
  }
  using AltSoftSerial::write;
 private:
  void record(char direction, uint8_t value) {
    if (Serial.availableForWrite() < 5) return;
    const char digits[] = "0123456789ABCDEF";
    const uint8_t line[] = {(uint8_t)direction, ' ',
      (uint8_t)digits[value >> 4], (uint8_t)digits[value & 15], '\n'};
    Serial.write(line, sizeof(line));
  }
};
