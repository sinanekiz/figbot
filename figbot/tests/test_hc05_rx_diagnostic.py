"""Receive-only diagnostic cannot reply to radio or execute motor commands."""
import shutil
import subprocess
from pathlib import Path
import pytest


def test_receive_only_forwards_bytes_and_only_disables_pwm(tmp_path):
    compiler = shutil.which('g++')
    if not compiler:
        pytest.skip('g++ required')
    (tmp_path / 'SoftwareSerial.h').write_text(r'''
#pragma once
#include <cstdint>
#include <cstddef>
#include <string>
#define F(x) x
struct Usb {
 int baud=0; std::string output;
 void begin(int b){baud=b;}
 void println(const char* s){output+=s;output+='\n';}
 void write(const uint8_t* p,size_t n){output.append((const char*)p,n);}
} Serial;
// Deliberately no transmit method: a radio write would fail compilation.
struct SoftwareSerial {
 int rx,tx,baud=0; bool overflowed=false; std::string input;
 SoftwareSerial(int r,int t):rx(r),tx(t){}
 void begin(int b){baud=b;}
 int available(){return input.size();}
 int read(){if(input.empty())return -1;int c=(uint8_t)input[0];input.erase(0,1);return c;}
 bool overflow(){bool r=overflowed;overflowed=false;return r;}
};
''')
    (tmp_path / 'Wire.h').write_text(r'''
#pragma once
#include <vector>
#include <cassert>
struct Bus {
 std::vector<std::vector<int>> writes; int error=0;
 void begin(){}
 void setWireTimeout(int t,bool r){assert(t==25000 && r);}
 void beginTransmission(int a){assert(a==0x40);writes.push_back({});}
 void write(uint8_t v){writes.back().push_back(v);}
 int endTransmission(){return error;}
} Wire;
''')
    root = Path(__file__).resolve().parents[1]
    (tmp_path / 'check.cpp').write_text(r'''
#include <cassert>
#include "uno_hc05_rx_diagnostic.ino"
int main(){
 setup();
 assert(Serial.baud==115200 && hc05.baud==9600 && hc05.rx==10 && hc05.tx==11);
 assert(Wire.writes.size()==16);
 for(int c=0;c<16;c++)assert(Wire.writes[c]==std::vector<int>({9+4*c,16}));
 assert(Serial.output.find("PCA_OFF_ACK")!=std::string::npos);
 Serial.output.clear();hc05.input="X\nH\nE0\nP0,90,30,1000,2000\n";
 hc05.input+=(char)0xAC;hc05.input+=(char)0xFF;
 loop();assert(hc05.input.empty() && Wire.writes.size()==16);
 assert(Serial.output.find("R 58\nR 0A\nR 48\nR 0A\n")==0);
 assert(Serial.output.find("R AC\nR FF\n")!=std::string::npos);
 Serial.output.clear();hc05.overflowed=true;loop();
 assert(Serial.output=="RX_OVERFLOW; CAPTURE INCOMPLETE\n");
 Serial.output.clear();Wire.error=4;setup();
 assert(Serial.output.find("PCA_OFF_UNCONFIRMED")!=std::string::npos);
}
''')
    exe = tmp_path / 'rx_diagnostic_test.exe'
    subprocess.run([compiler, '-std=c++11', '-I', str(tmp_path), '-I',
                    str(root / 'firmware/uno_hc05_rx_diagnostic'),
                    str(tmp_path / 'check.cpp'), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
