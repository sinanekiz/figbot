#pragma once
#include <vector>
#include <string>
#include <sstream>
#include <cstdint>
#define F(x) x
static unsigned long fakeTime = 100;
inline unsigned long millis() { return fakeTime; }
inline void delay(int n) { fakeTime += n; }
struct FakeSerial {
  std::string input, output;
  void begin(int) {}
  int available() { return input.size(); }
  char read() { char c = input[0]; input.erase(0,1); return c; }
  template<class T> void print(T v) { std::ostringstream s; s << v; output += s.str(); }
  template<class T> void println(T v) { print(v); output += "\n"; }
} Serial;
struct FakeWire {
  std::vector<unsigned char> bytes;
  std::vector<std::vector<unsigned char>> transactions;
  unsigned char regs[256] = {};
  bool fail = false;
  void begin() {}
  void setWireTimeout(long, bool) {}
  void beginTransmission(int) { bytes.clear(); }
  void write(unsigned char v) { bytes.push_back(v); }
  int endTransmission() {
    if (fail) return 4;
    transactions.push_back(bytes);
    for (unsigned int i=1; i<bytes.size(); ++i) regs[bytes[0]+i-1] = bytes[i];
    return 0;
  }
} Wire;
