// FIGBOT Pico 2 motion release candidate.
// Physical E-stop energy removal is hardwired; this firmware is supervisory.

#include <array>
#include <cstdint>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>

#include "hardware/watchdog.h"
#include "pico/stdlib.h"

namespace {

constexpr uint32_t kHostWatchdogMs = 300;
constexpr uint32_t kPulseWidthUs = 3;
constexpr uint32_t kMaxStepRateHz = 20000;
constexpr size_t kLineCapacity = 192;

struct AxisPins {
  uint step;
  uint direction;
  uint enable_n;
  uint home_nc;
  uint alarm_nc;
};

// A pin-map change requires matching electrical/PINOUT.csv and a bench test.
constexpr std::array<AxisPins, 4> kAxes{{
    {2, 3, 4, 10, 14},
    {5, 6, 7, 11, 15},
    {8, 9, 20, 12, 16},
    {18, 19, 21, 13, 17},
}};
constexpr uint kSafetyRelayAuxNc = 22;

enum class State { kDisarmed, kArmedIdle, kMoving, kHoming, kFaultLatched };
State state = State::kDisarmed;
std::array<int32_t, 4> position{};
std::array<int32_t, 4> target{};
std::array<uint32_t, 4> accumulator{};
std::array<uint32_t, 4> delta_abs{};
std::array<int8_t, 4> direction_sign{};
uint32_t dominant_steps = 0;
uint32_t completed_dominant_steps = 0;
uint32_t step_interval_us = 1000;
uint32_t maximum_step_rate_hz = 1000;
uint32_t acceleration_steps_s2 = 12000;
uint64_t next_step_us = 0;
uint32_t last_host_ms = 0;
uint32_t homing_remaining = 0;
uint8_t homing_axis = 0;
char line_buffer[kLineCapacity]{};
size_t line_length = 0;

uint16_t crc16_ccitt(const char* data, size_t length) {
  uint16_t crc = 0xFFFF;
  for (size_t i = 0; i < length; ++i) {
    crc ^= static_cast<uint16_t>(static_cast<uint8_t>(data[i])) << 8;
    for (int bit = 0; bit < 8; ++bit) {
      crc = (crc & 0x8000) ? static_cast<uint16_t>((crc << 1) ^ 0x1021)
                           : static_cast<uint16_t>(crc << 1);
    }
  }
  return crc;
}

const char* state_name() {
  switch (state) {
    case State::kDisarmed: return "DISARMED";
    case State::kArmedIdle: return "ARMED_IDLE";
    case State::kMoving: return "MOVING";
    case State::kHoming: return "HOMING";
    case State::kFaultLatched: return "FAULT_LATCHED";
  }
  return "UNKNOWN";
}

void send_payload(const char* payload) {
  const uint16_t crc = crc16_ccitt(payload, std::strlen(payload));
  std::printf("%s*%04X\n", payload, crc);
}

void send_reply(const char* kind, uint32_t seq, const char* detail) {
  char payload[160];
  std::snprintf(payload, sizeof(payload), "%s,%lu,%s", kind,
                static_cast<unsigned long>(seq), detail);
  send_payload(payload);
}

bool inputs_healthy() {
  if (gpio_get(kSafetyRelayAuxNc) != 0) return false;
  for (const auto& axis : kAxes) {
    if (gpio_get(axis.alarm_nc) != 0) return false;
  }
  return true;
}

void set_drives_enabled(bool enabled) {
  for (const auto& axis : kAxes) gpio_put(axis.enable_n, enabled ? 0 : 1);
}

void stop_and_latch() {
  set_drives_enabled(false);
  state = State::kFaultLatched;
  dominant_steps = 0;
}

bool parse_u32(const char* token, uint32_t* value) {
  if (!token || !*token) return false;
  char* end = nullptr;
  const unsigned long parsed = std::strtoul(token, &end, 10);
  if (*end != '\0') return false;
  *value = static_cast<uint32_t>(parsed);
  return true;
}

bool parse_i32(const char* token, int32_t* value) {
  if (!token || !*token) return false;
  char* end = nullptr;
  const long parsed = std::strtol(token, &end, 10);
  if (*end != '\0') return false;
  *value = static_cast<int32_t>(parsed);
  return true;
}

void start_move(const std::array<int32_t, 4>& requested, uint32_t rate_hz, uint32_t accel) {
  dominant_steps = 0;
  completed_dominant_steps = 0;
  accumulator.fill(0);
  target = requested;
  for (size_t i = 0; i < kAxes.size(); ++i) {
    const int64_t delta = static_cast<int64_t>(target[i]) - position[i];
    direction_sign[i] = delta >= 0 ? 1 : -1;
    delta_abs[i] = static_cast<uint32_t>(delta >= 0 ? delta : -delta);
    if (delta_abs[i] > dominant_steps) dominant_steps = delta_abs[i];
    gpio_put(kAxes[i].direction, direction_sign[i] > 0 ? 1 : 0);
  }
  maximum_step_rate_hz = rate_hz;
  acceleration_steps_s2 = accel;
  step_interval_us = 1000000u / 100u;
  next_step_us = time_us_64() + step_interval_us;
  state = dominant_steps == 0 ? State::kArmedIdle : State::kMoving;
}

void motion_tick() {
  if (state == State::kHoming) {
    if (gpio_get(kAxes[homing_axis].home_nc) != 0) {
      position[homing_axis] = 0;
      state = State::kArmedIdle;
      return;
    }
    if (homing_remaining == 0) {
      stop_and_latch();
      return;
    }
    if (time_us_64() < next_step_us) return;
    next_step_us += 1000;  // 1000 steps/s conservative homing speed.
    gpio_put(kAxes[homing_axis].step, 1);
    busy_wait_us_32(kPulseWidthUs);
    gpio_put(kAxes[homing_axis].step, 0);
    --position[homing_axis];
    --homing_remaining;
    return;
  }
  if (state != State::kMoving || time_us_64() < next_step_us) return;
  for (size_t i = 0; i < kAxes.size(); ++i) {
    if (direction_sign[i] < 0 && gpio_get(kAxes[i].home_nc) != 0) {
      stop_and_latch();
      return;
    }
  }
  next_step_us += step_interval_us;
  std::array<bool, 4> pulse{};
  for (size_t i = 0; i < kAxes.size(); ++i) {
    accumulator[i] += delta_abs[i];
    if (accumulator[i] >= dominant_steps) {
      accumulator[i] -= dominant_steps;
      gpio_put(kAxes[i].step, 1);
      pulse[i] = true;
      position[i] += direction_sign[i];
    }
  }
  busy_wait_us_32(kPulseWidthUs);
  for (size_t i = 0; i < kAxes.size(); ++i) if (pulse[i]) gpio_put(kAxes[i].step, 0);
  if (++completed_dominant_steps >= dominant_steps) {
    position = target;
    state = State::kArmedIdle;
  } else {
    const uint32_t remaining = dominant_steps - completed_dominant_steps;
    const uint32_t ramp_progress = completed_dominant_steps < remaining ? completed_dominant_steps : remaining;
    uint32_t rate = static_cast<uint32_t>(std::sqrt(2.0f * acceleration_steps_s2 * (ramp_progress + 1u)));
    if (rate < 100u) rate = 100u;
    if (rate > maximum_step_rate_hz) rate = maximum_step_rate_hz;
    step_interval_us = 1000000u / rate;
  }
}

void handle_line(char* line) {
  char* star = std::strrchr(line, '*');
  if (!star || std::strlen(star + 1) != 4) return;
  const uint16_t received = static_cast<uint16_t>(std::strtoul(star + 1, nullptr, 16));
  *star = '\0';
  if (crc16_ccitt(line, std::strlen(line)) != received) return;

  char* save = nullptr;
  const char* command = strtok_r(line, ",", &save);
  const char* sequence_text = strtok_r(nullptr, ",", &save);
  uint32_t seq = 0;
  if (!command || !parse_u32(sequence_text, &seq)) return;
  last_host_ms = to_ms_since_boot(get_absolute_time());

  if (std::strcmp(command, "HEARTBEAT") == 0) {
    send_reply("OK", seq, state_name());
  } else if (std::strcmp(command, "STATUS") == 0) {
    char detail[128];
    std::snprintf(detail, sizeof(detail), "%s,%ld,%ld,%ld,%ld", state_name(),
                  static_cast<long>(position[0]), static_cast<long>(position[1]),
                  static_cast<long>(position[2]), static_cast<long>(position[3]));
    send_reply("OK", seq, detail);
  } else if (std::strcmp(command, "ARM") == 0) {
    if (state == State::kDisarmed && inputs_healthy()) {
      set_drives_enabled(true);
      state = State::kArmedIdle;
      send_reply("OK", seq, state_name());
    } else {
      send_reply("ERR", seq, "ARM_CONDITIONS_NOT_MET");
    }
  } else if (std::strcmp(command, "DISARM") == 0) {
    set_drives_enabled(false);
    state = State::kDisarmed;
    dominant_steps = 0;
    send_reply("OK", seq, state_name());
  } else if (std::strcmp(command, "RESET") == 0) {
    if (state == State::kFaultLatched && inputs_healthy()) {
      state = State::kDisarmed;
      send_reply("OK", seq, state_name());
    } else {
      send_reply("ERR", seq, "RESET_CONDITIONS_NOT_MET");
    }
  } else if (std::strcmp(command, "MOVE") == 0) {
    std::array<int32_t, 4> requested{};
    bool valid = state == State::kArmedIdle && inputs_healthy();
    for (auto& value : requested) valid &= parse_i32(strtok_r(nullptr, ",", &save), &value);
    uint32_t rate = 0;
    uint32_t accel = 0;
    valid &= parse_u32(strtok_r(nullptr, ",", &save), &rate);
    valid &= parse_u32(strtok_r(nullptr, ",", &save), &accel);
    valid &= rate >= 100 && rate <= kMaxStepRateHz;
    valid &= accel >= 1000 && accel <= 200000;
    if (valid) {
      start_move(requested, rate, accel);
      send_reply("OK", seq, state_name());
    } else {
      send_reply("ERR", seq, "MOVE_REJECTED");
    }
  } else if (std::strcmp(command, "HOME") == 0) {
    uint32_t axis = 0;
    const bool valid = state == State::kArmedIdle && inputs_healthy() &&
                       parse_u32(strtok_r(nullptr, ",", &save), &axis) && axis < kAxes.size();
    if (valid) {
      homing_axis = static_cast<uint8_t>(axis);
      homing_remaining = 40000;
      gpio_put(kAxes[axis].direction, 0);
      next_step_us = time_us_64() + 1000;
      state = State::kHoming;
      send_reply("OK", seq, state_name());
    } else {
      send_reply("ERR", seq, "HOME_REJECTED");
    }
  } else {
    send_reply("ERR", seq, "UNKNOWN_COMMAND");
  }
}

void poll_serial() {
  int ch;
  while ((ch = getchar_timeout_us(0)) != PICO_ERROR_TIMEOUT) {
    if (ch == '\n' || ch == '\r') {
      if (line_length) {
        line_buffer[line_length] = '\0';
        handle_line(line_buffer);
        line_length = 0;
      }
    } else if (line_length + 1 < kLineCapacity) {
      line_buffer[line_length++] = static_cast<char>(ch);
    } else {
      line_length = 0;
      stop_and_latch();
    }
  }
}

}  // namespace

int main() {
  stdio_init_all();
  for (const auto& axis : kAxes) {
    for (uint pin : {axis.step, axis.direction, axis.enable_n}) {
      gpio_init(pin); gpio_set_dir(pin, GPIO_OUT); gpio_put(pin, 0);
    }
    gpio_put(axis.enable_n, 1);
    for (uint pin : {axis.home_nc, axis.alarm_nc}) {
      gpio_init(pin); gpio_set_dir(pin, GPIO_IN); gpio_pull_up(pin);
    }
  }
  gpio_init(kSafetyRelayAuxNc);
  gpio_set_dir(kSafetyRelayAuxNc, GPIO_IN);
  gpio_pull_up(kSafetyRelayAuxNc);
  watchdog_enable(1000, true);
  last_host_ms = to_ms_since_boot(get_absolute_time());

  while (true) {
    watchdog_update();
    poll_serial();
    motion_tick();
    const uint32_t now = to_ms_since_boot(get_absolute_time());
    if ((state == State::kArmedIdle || state == State::kMoving || state == State::kHoming) &&
        (now - last_host_ms > kHostWatchdogMs || !inputs_healthy())) {
      stop_and_latch();
    }
    tight_loop_contents();
  }
}
