// Uno Rev3 / ATmega328P. READ only; no torque, goal, ID or EEPROM writes.
// Requires the two-gate 74HC125 circuit in README.md. USB MUST be unplugged
// during the test because Uno pins 0/1 are shared with its USB UART bridge.
const byte TX_OE = 2, RX_OE = 3;
byte foundId = 0;
bool faultReply = false;

bool readIdentity(byte id) {
  while (Serial.available()) Serial.read();
  byte request[8] = {255, 255, id, 4, 2, 3, 3, 0};
  byte sum = 0;
  for (byte i = 2; i < 7; ++i) sum += request[i];
  request[7] = ~sum;
  digitalWrite(RX_OE, HIGH);
  digitalWrite(TX_OE, LOW);
  Serial.write(request, sizeof(request));
  Serial.flush(); // Wait for the last transmitted stop bit.
  digitalWrite(TX_OE, HIGH);
  digitalWrite(RX_OE, LOW);
  byte reply[9], used = 0;
  unsigned long start = millis();
  while (millis() - start < 30) {
    if (!Serial.available()) continue;
    byte value = Serial.read();
    if (used < 2 && value != 255) { used = 0; continue; }
    reply[used++] = value;
    if (used != sizeof(reply)) continue;
    sum = 0;
    for (byte i = 2; i < sizeof(reply); ++i) sum += reply[i];
    // STS3215 model 777, address 3 low byte / 4 high byte / 5 ID.
    if (reply[2] == id && reply[3] == 5 && sum == 255 &&
        reply[5] == 9 && reply[6] == 3 && reply[7] == id) {
      faultReply = reply[4] != 0;
      return true;
    }
    used = 0;
  }
  return false;
}

void flash(byte count, unsigned int onMs, unsigned int offMs) {
  for (byte i = 0; i < count; ++i) {
    digitalWrite(LED_BUILTIN, HIGH); delay(onMs);
    digitalWrite(LED_BUILTIN, LOW); delay(offMs);
  }
}

void setup() {
  digitalWrite(TX_OE, HIGH); pinMode(TX_OE, OUTPUT);
  digitalWrite(RX_OE, HIGH); pinMode(RX_OE, OUTPUT);
  pinMode(LED_BUILTIN, OUTPUT);
  delay(3000); // Give motor power time to stabilize; one scan per reset.
  const unsigned long rates[] = {1000000UL, 500000UL, 115200UL};
  for (byte rate = 0; rate < 3 && !foundId; ++rate) {
    Serial.begin(rates[rate]);
    digitalWrite(RX_OE, LOW);
    for (byte id = 1; id <= 6 && !foundId; ++id) {
      for (byte attempt = 0; attempt < 2; ++attempt) {
        if (readIdentity(id)) { foundId = id; break; }
        delay(5);
      }
    }
    digitalWrite(RX_OE, HIGH);
    Serial.end();
  }
}

void loop() {
  if (!foundId) {
    flash(10, 50, 50); // No verified reply; NOT proof of a dead motor.
  } else {
    if (faultReply) { flash(1, 1500, 500); }
    flash(foundId, 200, 300); // Number of short flashes = responding motor ID.
  }
  delay(3000);
}
