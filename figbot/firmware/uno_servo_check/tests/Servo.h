#pragma once
#include <string>
#include <queue>
#define F(value) value
constexpr int OUTPUT = 1;
constexpr int LOW = 0;
inline unsigned long nowMs = 0;
inline unsigned long millis() { return nowMs; }
inline void pinMode(int, int) {}
inline void digitalWrite(int, int) {}
struct SerialMock {
  std::queue<char> input;
  void begin(int) {}
  void println(const char*) {}
  void print(const char*) {}
  void print(char) {}
  void print(long) {}
  void println(long) {}
  bool available() { return !input.empty(); }
  char read() { char c = input.front(); input.pop(); return c; }
} inline Serial;
class Servo {
 public:
  bool active = false;
  int pulse = 1500, minimum = 544, maximum = 2400;
  void detach() { active = false; }
  bool attached() { return active; }
  void attach(int, int low, int high) { active = true; minimum = low; maximum = high; }
  void writeMicroseconds(int value) { pulse = value < minimum ? minimum : (value > maximum ? maximum : value); }
};
