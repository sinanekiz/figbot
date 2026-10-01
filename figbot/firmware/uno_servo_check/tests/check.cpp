#include <cassert>
#include <limits>
#include "../uno_servo_check.ino"
void send(char c) { Serial.input.push(c); loop(); }
void frame(const char* text) { while (*text) Serial.input.push(*text++); loop(); }
int main() {
  setup();
  assert(!motor.attached());
  send('l'); assert(motor.attached() && motor.pulse == 1600);
  send('x'); assert(!motor.attached());
  send('r'); assert(motor.attached() && motor.pulse == 1400);
  send('c'); assert(motor.attached() && motor.pulse == 1500);
  send('l'); assert(motor.pulse == 1600);
  send('r'); assert(motor.pulse == 1400);
  send('0'); assert(motor.pulse == 1400);
  nowMs = 9999; loop(); assert(motor.attached());
  nowMs = 10000; loop(); assert(!motor.attached());
  send('c'); send('x'); assert(!motor.attached());
  send('r'); assert(motor.attached());
  nowMs = std::numeric_limits<unsigned long>::max() - 4999;
  send('c'); nowMs = 5000; loop(); assert(!motor.attached());
  send('t'); assert(motor.attached() && fastRunning);
  send('x'); assert(!motor.attached());
  nowMs = 20000; send('c'); send('t');
  assert(fastRunning && motor.pulse == 1000);
  send('r'); send('l'); send('c'); send('t');
  assert(fastRunning && motor.pulse == 1000 && fastIndex == 0);
  for (int step = 1; step < 8; ++step) {
    nowMs += 700; loop();
    assert(motor.attached() && motor.pulse == FAST_TARGETS[step]);
  }
  nowMs += 700; loop(); assert(!motor.attached() && !fastRunning);
  send('c'); send('t'); nowMs += 200; send('x');
  assert(!motor.attached() && !fastRunning);
  nowMs += 1000; loop(); assert(!motor.attached());
  send('c'); send('t'); send('r'); assert(fastRunning && motor.pulse == 1000);
  send('t'); nowMs += 10000; loop(); assert(!motor.attached());
  nowMs = std::numeric_limits<unsigned long>::max() - 350;
  send('c'); send('t'); nowMs = 349; loop(); assert(fastIndex == 1 && motor.pulse == 2000);
  send('x');
  nowMs = 50000;
  frame("P0,0\n"); assert(motor.pulse == 500 && motor.attached());
  frame("P180,0\n"); assert(motor.pulse == 2500 && !rampRunning);
  frame("P90,0\n"); assert(motor.pulse == 1500);
  assert(motor.minimum == 500 && motor.maximum == 2500);
  frame("P45,0\n"); assert(motor.pulse == 1000);
  frame("P135,0\n"); assert(motor.pulse == 2000);
  frame("P90,0\n");
  for (const char* invalid : {"P181,0\n", "P90,29\n", "P90,361\n", "P,0\n", "P90,\n", "P-1,90\n", "P999999999999999999999999999999,0\n"}) {
    frame(invalid); assert(motor.pulse == 1500 && !rampRunning);
  }
  frame("P0,0\n"); frame("P180,30\n");
  assert(rampRunning && motor.pulse == 500);
  for (int i=0; i<50; ++i) { nowMs += 20; loop(); }
  assert(motor.pulse >= 832 && motor.pulse <= 834);
  for (int i=0; i<252; ++i) { nowMs += 20; loop(); }
  assert(motor.pulse == 2500 && !rampRunning);
  frame("P0,180\n"); nowMs += 20; loop(); assert(motor.pulse == 2460);
  send('x'); int stopped = motor.pulse;
  nowMs += 200; loop(); assert(!motor.attached() && motor.pulse == stopped && !rampRunning);
  frame("P90,"); nowMs += 501; loop(); frame("0\n"); assert(!motor.attached());
  frame("P180,0\n"); assert(motor.pulse == 2500);
  nowMs += TIMEOUT_MS; loop(); assert(!motor.attached());
}
