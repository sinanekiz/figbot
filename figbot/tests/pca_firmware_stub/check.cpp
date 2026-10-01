#include <cassert>
#include "../../firmware/uno_pca9685/uno_pca9685.ino"
void send(const char* text) { Serial.input = text; loop(); }
int ticks(int c) { return Wire.regs[8+4*c] + 256*Wire.regs[9+4*c]; }
int main() {
  setup(); assert(available);
  for (int c=0;c<16;++c) assert(ticks(c)==4096);
  // Exact Android connection burst must return status without arming motion.
  Serial.output.clear();
  send("X\nH\nH\n");
  assert(Serial.output=="OFF ALL\nSTATUS5 0,0\nSTATUS5 0,0\n");
  for (int c=0;c<16;++c) assert(ticks(c)==4096);
  // A genuinely corrupt frame still fails closed; do not hide ERR FRAME.
  Serial.output.clear();
  send("garbled\n");
  assert(Serial.output=="ERR FRAME\n");
  send("H\n");
  assert(Serial.output=="ERR FRAME\nSTATUS5 0,0\n");
  send("H\nE0\n"); assert(enabled[0] && !active[0]); assert(ticks(0)==4096);
  send("P1,90,30,1000,2000\n"); assert(!active[1]);
  send("P0,90,30,1000,2000\n"); fakeTime+=20; loop();
  assert(active[0] && ticks(0)==307);
  for (int c=1;c<16;++c) assert(ticks(c)==4096);
  send("P0,180,30,1000,2000\n"); fakeTime+=20; loop();
  assert(currentUs[0]>1500 && currentUs[0]<1504); // ramp, not instant jump
  float previousUs=currentUs[0];
  send("P0,180,360,1000,2000\n"); fakeTime+=20; loop();
  assert(rates[0]==360 && fabs(currentUs[0]-previousUs-40)<.01);
  send("P0,0,361,1000,2000\n");
  assert(rates[0]==360 && targetUs[0]==2000);
  int before=targetUs[0];
  send("P0,181,30,1000,2000\nP12,90,30,1000,2000\nP0,90,0,1000,2000\nP0,90,30,0,9999\n");
  assert(targetUs[0]==before);
  send("P0,9X\n"); assert(!active[0] && !enabled[0] && ticks(0)==4096);
  send("P0,90,30,1000,2000\n"); assert(!active[0]);
  send("E0\nP0,90,30,1000,2000\n"); fakeTime+=1600; loop();
  assert(!active[0] && !enabled[0] && ticks(0)==4096);
  send("H\nP0,90,30,1000,2000\n"); assert(!active[0]); // heartbeat cannot rearm
  send("E11\nP11,180,30,500,2500\n"); fakeTime+=20; loop(); assert(ticks(11)==512);
  send("D11\n"); assert(!enabled[11] && ticks(11)==4096);
  // Both arms: shared trajectory, complementary pulses and one STOP update.
  for (int c : {1,7}) {
    std::string enable="E"+std::to_string(c)+"\n";
    send(enable.c_str());
    assert(enabled[c] && enabled[c+1] && !active[c] && !active[c+1]);
    assert(Wire.transactions.back().size()==9 && Wire.transactions.back()[0]==6+4*c);
    std::string bad="S"+std::to_string(c)+",100,30,1000,2000\n";
    send(bad.c_str()); assert(!active[c]); // first position must be centre
    std::string centre="S"+std::to_string(c)+",90,30,1000,2000\n";
    send(centre.c_str()); fakeTime+=20; loop();
    assert(active[c] && active[c+1] && ticks(c)==307 && ticks(c+1)==307);
    std::string individual="P"+std::to_string(c)+",0,30,1000,2000\nP"+std::to_string(c+1)+",180,30,1000,2000\n";
    send(individual.c_str()); assert(targetUs[c]==1500 && targetUs[c+1]==1500);
    std::string move="S"+std::to_string(c)+",180,30,1000,2000\n";
    send(move.c_str());
    for (int i=0; i<160; ++i) {
      send("H\n");
      fakeTime+=20; loop();
      assert(fabs(currentUs[c]+currentUs[c+1]-3000)<.001);
      assert(currentUs[c]>1500 && currentUs[c+1]<1500);
      assert(Wire.transactions.back().size()==9);
    }
    assert(currentUs[c]==2000 && currentUs[c+1]==1000);
    // At 180 command degrees/s, a full1000us span takes one second.
    std::string fast="S"+std::to_string(c)+",0,180,1000,2000\n";
    send(fast.c_str());
    std::string invalid="S"+std::to_string(c)+",180,361,1000,2000\n";
    send(invalid.c_str()); assert(targetUs[c]==1000 && rates[c]==180);
    for (int i=0; i<49; ++i) {
      send("H\n"); fakeTime+=20; loop();
      assert(fabs(currentUs[c]+currentUs[c+1]-3000)<.001);
    }
    assert(currentUs[c]>1000); // not an instant jump
    fakeTime+=20; loop();
    assert(currentUs[c]==1000 && currentUs[c+1]==2000);
    // At 360 command degrees/s each full span takes 500ms, in both directions.
    for (int destination : {180, 0}) {
      std::string maximum="S"+std::to_string(c)+","+std::to_string(destination)+",360,1000,2000\n";
      send(maximum.c_str());
      assert(rates[c]==360);
      int goal=destination==180?2000:1000;
      for (int i=0; i<24; ++i) {
        send("H\n"); fakeTime+=20; loop();
        assert(fabs(currentUs[c]+currentUs[c+1]-3000)<.001);
        assert(currentUs[c]!=goal);
      }
      fakeTime+=20; loop();
      assert(currentUs[c]==goal && currentUs[c+1]==3000-goal);
      assert(Wire.transactions.back().size()==9);
    }
    // Disable via follower also stops both and requires fresh centering.
    std::string disable="D"+std::to_string(c+1)+"\n";
    send(disable.c_str());
    assert(!enabled[c] && !enabled[c+1] && ticks(c)==4096 && ticks(c+1)==4096);
    send(enable.c_str()); send(centre.c_str()); fakeTime+=1600; loop();
    assert(!enabled[c] && !enabled[c+1] && ticks(c)==4096 && ticks(c+1)==4096);
  }
  // Each calibration step keeps one mirrored ramp; active ranges cannot change.
  for(int c : {1,7}) for(int lo=1000;lo>=500;lo-=100) {
    std::string prefix="S"+std::to_string(c)+",";
    std::string range=","+std::to_string(lo)+","+std::to_string(3000-lo)+"\n";
    send(("E"+std::to_string(c)+"\n").c_str());
    send((prefix+"180,360"+range).c_str());assert(!active[c]);
    send((prefix+"90,360"+range).c_str());fakeTime+=20;loop();
    assert(currentUs[c]==1500 && currentUs[c+1]==1500);
    send((prefix+"0,360"+range).c_str());
    for(int i=0;i<13;i++){send("H\n");fakeTime+=20;loop();}
    assert(currentUs[c]==lo && currentUs[c+1]==3000-lo);
    send((prefix+"180,360,750,2250\n").c_str());assert(targetUs[c]==lo);
    int alternate=lo==1000?900:1000;
    send((prefix+"180,360,"+std::to_string(alternate)+","+std::to_string(3000-alternate)+"\n").c_str());
    assert(targetUs[c]==lo); // valid but different range requires re-arm
    send((prefix+"180,360"+range).c_str());
    for(int i=0;i<24;i++){send("H\n");fakeTime+=20;loop();assert(currentUs[c]<3000-lo);}
    fakeTime+=20;loop();assert(currentUs[c]==3000-lo && currentUs[c+1]==lo);
    send("X\n");assert(!active[c] && !active[c+1]);
  }
  send("E0\nP0,90,30,1000,2000\n"); Wire.fail=true; fakeTime+=20; loop();
  assert(!available && !active[0]);
  return 0;
}
