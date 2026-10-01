"""Check that optional diagnostics preserve UART bytes and never block on USB."""
import shutil
import subprocess
from pathlib import Path
import pytest


def test_usb_trace_preserves_bytes_and_skips_full_debug_buffer(tmp_path):
    compiler = shutil.which('g++')
    if not compiler:
        pytest.skip('g++ required')
    (tmp_path / 'AltSoftSerial.h').write_text(r'''
#pragma once
#include <cstdint>
#include <cstddef>
#include <string>
#define F(x) x
struct DebugPort {
  int room=64, baud=0;
  std::string output;
  void begin(int b) { baud=b; }
  void println(const char* s) { output+=s; output+='\n'; }
  int availableForWrite() { return room; }
  size_t write(const uint8_t* p,size_t n) { output.append((const char*)p,n); return n; }
} Serial;
class AltSoftSerial {
 public:
  uint16_t baud=0; bool fail=false;
  std::string input,output;
  void begin(uint16_t b) { baud=b; }
  virtual int read() { if(input.empty())return -1; int c=(uint8_t)input[0];input.erase(0,1);return c; }
  virtual size_t write(uint8_t c) { if(fail)return 0;output+=(char)c;return 1; }
};
''')
    root = Path(__file__).resolve().parents[1]
    source = tmp_path / 'check.cpp'
    source.write_text(r'''
#include <cassert>
#include "trace_transport.h"
int main() {
 TracedHc05 port; port.begin(9600);
 assert(port.baud==9600 && Serial.baud==115200);
 assert(Serial.output.find("RX=D8 TX=D9")!=std::string::npos);
 Serial.output.clear(); port.input="H\n";
 assert(port.read()=='H'); assert(port.read()=='\n'); assert(port.read()==-1);
 assert(Serial.output=="R 48\nR 0A\n");
 Serial.output.clear(); assert(port.write('X')==1);
 assert(port.output=="X" && Serial.output=="T 58\n");
 Serial.output.clear(); Serial.room=0; port.input="E";
 assert(port.read()=='E');assert(port.write('\n')==1);
 assert(Serial.output.empty() && port.output=="X\n");
 Serial.room=64;port.fail=true;assert(port.write('Q')==0);
 assert(Serial.output.empty() && port.output=="X\n");
}
''')
    exe = tmp_path / 'trace_test.exe'
    subprocess.run([compiler, '-std=c++11', '-I', str(tmp_path), '-I',
                    str(root / 'firmware/uno_pca9685_hc05'), str(source), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
