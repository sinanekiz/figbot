#include <SoftwareSerial.h>
#include <Wire.h>

// Temporary receive-only isolation test. NO motor command parser, NO HC-05
// replies. Android will time out by design. Keep battery/servo supply OFF.
SoftwareSerial hc05(10, 11);

void setup() {
  Serial.begin(115200);
  Wire.begin();
  Wire.setWireTimeout(25000, true);
  bool off = true;
  for (uint8_t channel = 0; channel < 16; ++channel) {
    Wire.beginTransmission(0x40);
    Wire.write((uint8_t)(0x09 + 4 * channel)); // LEDn_OFF_H
    Wire.write((uint8_t)0x10); // FULL_OFF, no dependence on auto-increment
    if (Wire.endTransmission() != 0) off = false;
  }
  Serial.println(F("HC05_RX_ONLY D10 RX D11 IDLE BAUD=9600; NO MOTOR CONTROL"));
  Serial.println(off ? F("PCA_OFF_ACK") : F("PCA_OFF_UNCONFIRMED; KEEP SERVO POWER OFF"));
  hc05.begin(9600);
}

void loop() {
  while (hc05.available()) {
    int value = hc05.read();
    if (value < 0) break;
    const char digits[] = "0123456789ABCDEF";
    const uint8_t line[] = {'R', ' ', (uint8_t)digits[value >> 4],
      (uint8_t)digits[value & 15], '\n'};
    Serial.write(line, sizeof(line));
  }
  if (hc05.overflow()) Serial.println(F("RX_OVERFLOW; CAPTURE INCOMPLETE"));
}
