#include <Servo.h>
#include <stdlib.h>

// Single unloaded servo, D9. UI 0..180 maps to provisional 500..2500 us; physical endpoints UNVERIFIED.
// Actual shaft angle/speed are NOT measured; all positions are output commands.
Servo motor;
const int PULSE_MIN = 500, PULSE_MAX = 2500;
const unsigned long TIMEOUT_MS = 10000, FAST_HOLD_MS = 700;
const int FAST_TARGETS[] = {1000, 2000, 1000, 2000, 1000, 2000, 1000, 1500};
unsigned long lastCommand = 0, fastChanged = 0, rampChanged = 0, frameStarted = 0;
unsigned int fastIndex = 0, positionUsed = 0;
bool fastRunning = false, rampRunning = false, receivingPosition = false, frameBad = false;
float currentPulse = 1500;
int targetPulse = 1500, rampSpeed = 0;
char positionFrame[20];

void disableMotor() {
  fastRunning = rampRunning = receivingPosition = false;
  positionUsed = 0;
  motor.detach();
  pinMode(9, OUTPUT);
  digitalWrite(9, LOW);
}
void writePulse(int pulse) {
  motor.writeMicroseconds(pulse);
  if (!motor.attached()) motor.attach(9, PULSE_MIN, PULSE_MAX);
  motor.writeMicroseconds(pulse);
}
void commandPosition(int pulse) {
  rampRunning = false;
  currentPulse = targetPulse = pulse;
  writePulse(pulse);
  lastCommand = millis();
}
void handlePositionFrame() {
  positionFrame[positionUsed] = '\0';
  char *end;
  long angle = strtol(positionFrame, &end, 10);
  if (frameBad || end == positionFrame || *end != ',') {
    Serial.println(F("Invalid position frame")); return;
  }
  char *speedStart = end + 1;
  long speed = strtol(speedStart, &end, 10);
  if (end == speedStart || *end != '\0' || angle < 0 || angle > 180 ||
      !(speed == 0 || (speed >= 30 && speed <= 360))) {
    Serial.println(F("Invalid position frame")); return;
  }
  targetPulse = PULSE_MIN + (angle * (PULSE_MAX - PULSE_MIN) + 90) / 180;
  rampSpeed = speed;
  if (speed == 0) {
    commandPosition(targetPulse);
  } else {
    // Initial/resumed position is the last commanded pulse, not shaft feedback.
    writePulse((int)(currentPulse + 0.5f));
    rampRunning = true;
    rampChanged = lastCommand = millis();
  }
  Serial.print(F("Position: ")); Serial.print(angle);
  Serial.print(','); Serial.println(speed);
}
void setup() {
  disableMotor();
  Serial.begin(115200);
  Serial.println(F("FIGBOT_SERVO_CHECK_V5 Pangle,speed c l r t x"));
  Serial.println(F("Provisional 0-180 maps to 500-2500us; physical limits unverified. Speed 0=unramped, 30-360=command deg/s."));
}
void loop() {
  if (receivingPosition && (unsigned long)(millis() - frameStarted) > 500) {
    receivingPosition = false; positionUsed = 0;
  }
  while (Serial.available()) {
    const char command = Serial.read();
    if (command == 'x') {
      disableMotor(); Serial.println(F("Signal disabled")); continue;
    }
    if (fastRunning) continue;
    if (receivingPosition) {
      if (command == '\n') {
        receivingPosition = false;
        handlePositionFrame(); positionUsed = 0;
      } else if (command != '\r') {
        if (!((command >= '0' && command <= '9') || command == ',')) frameBad = true;
        if (positionUsed < sizeof(positionFrame) - 1) positionFrame[positionUsed++] = command;
        else frameBad = true;
      }
      continue;
    }
    if (command == 'P') {
      receivingPosition = true; frameBad = false; positionUsed = 0; frameStarted = millis();
    } else if (command == 'c') {
      commandPosition(1500); Serial.println(F("Centre: 1500us (actual angle unverified)"));
    } else if (command == 'l' || command == 'r') {
      commandPosition(command == 'l' ? 1600 : 1400);
      Serial.println(F("Small movement requested"));
    } else if (command == 't') {
      fastRunning = true; fastIndex = 0; fastChanged = millis();
      commandPosition(FAST_TARGETS[0]);
      Serial.println(F("Fast test started: 3 cycles, 1000-2000us, angle unverified"));
    }
  }
  // Nonblocking: x interrupts either a sweep or a speed-limited move.
  if (fastRunning && (unsigned long)(millis() - fastChanged) >= FAST_HOLD_MS) {
    ++fastIndex;
    if (fastIndex >= sizeof(FAST_TARGETS) / sizeof(FAST_TARGETS[0])) {
      disableMotor(); Serial.println(F("Fast test finished: signal disabled"));
    } else {
      currentPulse = targetPulse = FAST_TARGETS[fastIndex];
      motor.writeMicroseconds(targetPulse); fastChanged = millis();
      Serial.println(targetPulse == 1000 ? F("Fast target: 1000us") :
                     targetPulse == 2000 ? F("Fast target: 2000us") : F("Fast target: centre 1500us"));
    }
  }
  if (rampRunning && (unsigned long)(millis() - rampChanged) >= 20) {
    unsigned long elapsed = millis() - rampChanged;
    if (elapsed > 50) elapsed = 50; // Avoid a large catch-up jump.
    float step = rampSpeed * (float)elapsed * (PULSE_MAX - PULSE_MIN) / 180000.0f;
    rampChanged = millis();
    if (currentPulse < targetPulse) {
      currentPulse += step;
      if (currentPulse >= targetPulse) { currentPulse = targetPulse; rampRunning = false; }
    } else {
      currentPulse -= step;
      if (currentPulse <= targetPulse) { currentPulse = targetPulse; rampRunning = false; }
    }
    motor.writeMicroseconds((int)(currentPulse + 0.5f));
  }
  if (motor.attached() && (unsigned long)(millis() - lastCommand) >= TIMEOUT_MS) {
    disableMotor(); Serial.println(F("Timeout: signal disabled"));
  }
}
