// ACORN microcontroller logic: flame-sensor debouncing/smoothing, Linux
// heartbeat watch, LED state selection and blink patterns.
//
// Plain C++ with no Arduino or Zephyr dependency, so the exact same code is
// compiled into the sketch and into the host unit test (firmware/test).
// The station's simulated MCU (station/station/mcu_model.py) is a line-by-line
// port; both are checked against firmware/test/vectors.txt.
#pragma once
#include <stdint.h>

namespace acorn {

// Bump when the reading/state message layout changes (station checks it).
static const int PROTOCOL_VERSION = 1;

// LED states. Values travel over the bridge; keep in sync with
// station/station/mcu_protocol.py.
enum LedState : uint8_t {
  LED_BOOT = 0,           // lamp test at power-up
  LED_NORMAL = 1,         // observing normally
  LED_SMOKE_PENDING = 2,  // camera "suspected smoke" event awaits operator
  LED_DEGRADED = 3,       // an active camera lost / analysis failing
  LED_FLAME = 4,          // local flame sensor triggered
  LED_LINUX_SILENT = 5,   // no state message from Linux within timeout
};

struct Settings {
  uint16_t adc_max;                // 4095 at 12-bit resolution
  bool analog_flame_lowers_voltage;// Joy-IT: "signal is inverted"
  uint8_t ema_shift;               // smoothing factor alpha = 1 / 2^shift
  uint32_t trigger_ms;             // input must stay active this long to trigger
  uint32_t release_ms;             // input must stay inactive this long to release
  uint16_t analog_trigger_permille;// 0 = analog level never triggers (digital only)
  uint16_t analog_release_permille;// hysteresis for the analog trigger
  uint32_t hold_ms;                // LED keeps showing flame this long after release
  uint32_t linux_timeout_ms;       // silence before LED_LINUX_SILENT
};

inline Settings default_settings() {
  Settings s;
  s.adc_max = 4095;
  s.analog_flame_lowers_voltage = true;
  s.ema_shift = 3;
  s.trigger_ms = 150;
  s.release_ms = 1000;
  s.analog_trigger_permille = 0;
  s.analog_release_permille = 0;
  s.hold_ms = 3000;
  s.linux_timeout_ms = 5000;
  return s;
}

// Debounced flame trigger. Feed one sample every few milliseconds.
class FlameDetector {
 public:
  explicit FlameDetector(const Settings& s) : s_(s) {}

  void sample(uint32_t now, uint16_t raw, bool digital_active) {
    if (raw > s_.adc_max) raw = s_.adc_max;
    // Exponential moving average in 1/16 fixed point.
    int32_t x16 = (int32_t)raw * 16;
    if (!primed_) { ema16_ = x16; primed_ = true; }
    else { ema16_ += (x16 - ema16_) / (int32_t)(1 << s_.ema_shift); }
    last_raw_ = raw;
    digital_ = digital_active;

    uint16_t level = level_permille();
    if (s_.analog_trigger_permille > 0) {
      if (!analog_active_ && level >= s_.analog_trigger_permille) analog_active_ = true;
      else if (analog_active_ && level < s_.analog_release_permille) analog_active_ = false;
    }
    bool input = digital_active || analog_active_;
    if (input == triggered_) {
      changing_ = false;
    } else {
      if (!changing_) { changing_ = true; change_since_ = now; }
      uint32_t need = input ? s_.trigger_ms : s_.release_ms;
      if ((uint32_t)(now - change_since_) >= need) {
        triggered_ = input;
        changing_ = false;
        if (!triggered_) released_at_ = now;
        ever_released_ = ever_released_ || !triggered_;
      }
    }
  }

  bool triggered() const { return triggered_; }
  bool digital() const { return digital_; }
  uint16_t last_raw() const { return last_raw_; }
  uint16_t smoothed_raw() const { return (uint16_t)((ema16_ + 8) / 16); }
  // Relative infrared intensity, 0..1000. Uncalibrated: not a distance or size.
  uint16_t level_permille() const {
    uint32_t v = smoothed_raw();
    if (v > s_.adc_max) v = s_.adc_max;
    if (s_.analog_flame_lowers_voltage) v = s_.adc_max - v;
    return (uint16_t)((v * 1000u + s_.adc_max / 2) / s_.adc_max);
  }
  // True while triggered and for hold_ms after release (what the LED shows).
  bool flame_shown(uint32_t now) const {
    if (triggered_) return true;
    return ever_released_ && (uint32_t)(now - released_at_) < s_.hold_ms;
  }

 private:
  Settings s_;
  bool primed_ = false;
  int32_t ema16_ = 0;
  uint16_t last_raw_ = 0;
  bool digital_ = false;
  bool analog_active_ = false;
  bool triggered_ = false;
  bool changing_ = false;
  uint32_t change_since_ = 0;
  bool ever_released_ = false;
  uint32_t released_at_ = 0;
};

// Tracks the last state message from Linux.
class LinkWatch {
 public:
  explicit LinkWatch(uint32_t timeout_ms) : timeout_(timeout_ms) {}
  void heard(uint32_t now, uint8_t requested) {
    last_ = now; ever_ = true; requested_ = requested;
  }
  bool silent(uint32_t now) const {
    return !ever_ || (uint32_t)(now - last_) >= timeout_;
  }
  uint8_t requested() const { return requested_; }
 private:
  uint32_t timeout_;
  uint32_t last_ = 0;
  bool ever_ = false;
  uint8_t requested_ = LED_NORMAL;
};

// One rule for every combination: local flame > Linux silent > what Linux asked.
inline LedState select_led(bool flame_shown, bool linux_silent, uint8_t requested) {
  if (flame_shown) return LED_FLAME;
  if (linux_silent) return LED_LINUX_SILENT;
  switch (requested) {
    case LED_NORMAL: return LED_NORMAL;
    case LED_SMOKE_PENDING: return LED_SMOKE_PENDING;
    case LED_DEGRADED: return LED_DEGRADED;
    case LED_FLAME: return LED_FLAME;
    default: return LED_DEGRADED;  // unknown request: do not claim "normal"
  }
}

struct Rgb { uint8_t r, g, b; };

// Each state has its own colour AND rhythm, so it is readable without colour.
struct Pattern {
  Rgb colour;
  uint16_t period_ms;  // 0 = steady on
  uint8_t pulses;      // pulses per period
  uint16_t on_ms;
  uint16_t gap_ms;     // gap between pulses within one period
};

inline Pattern pattern_for(LedState s) {
  switch (s) {
    case LED_NORMAL:        return Pattern{{0, 255, 0}, 0, 1, 0, 0};          // steady
    case LED_SMOKE_PENDING: return Pattern{{255, 80, 0}, 1200, 2, 150, 150};  // double blink
    case LED_FLAME:         return Pattern{{255, 0, 0}, 200, 1, 100, 0};      // 5 Hz
    case LED_DEGRADED:      return Pattern{{0, 0, 255}, 2000, 1, 1000, 0};    // slow 1 s on / 1 s off
    case LED_LINUX_SILENT:  return Pattern{{0, 0, 255}, 2000, 1, 100, 0};     // short flash every 2 s
    case LED_BOOT:
    default:                return Pattern{{255, 255, 255}, 0, 1, 0, 0};
  }
}

// t = milliseconds since the state was entered, so a new state starts "on".
inline bool pattern_on(const Pattern& p, uint32_t t) {
  if (p.period_ms == 0) return true;
  uint32_t phase = t % p.period_ms;
  for (uint8_t i = 0; i < p.pulses; ++i) {
    uint32_t start = (uint32_t)i * (p.on_ms + p.gap_ms);
    if (phase >= start && phase < start + p.on_ms) return true;
  }
  return false;
}

// Power-up lamp test: red, green, blue, 250 ms each, then off.
static const uint32_t BOOT_TEST_MS = 750;
inline Rgb boot_colour(uint32_t t) {
  if (t < 250) return Rgb{255, 0, 0};
  if (t < 500) return Rgb{0, 255, 0};
  if (t < BOOT_TEST_MS) return Rgb{0, 0, 255};
  return Rgb{0, 0, 0};
}

// Tracks state changes so each new state's pattern starts at its "on" phase.
class LedRenderer {
 public:
  Rgb render(uint32_t now, LedState s) {
    if (!started_ || s != state_) { state_ = s; since_ = now; started_ = true; }
    Pattern p = pattern_for(s);
    return pattern_on(p, now - since_) ? p.colour : Rgb{0, 0, 0};
  }
 private:
  bool started_ = false;
  LedState state_ = LED_BOOT;
  uint32_t since_ = 0;
};

}  // namespace acorn
