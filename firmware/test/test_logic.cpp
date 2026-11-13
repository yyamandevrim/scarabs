// Host unit test for the firmware logic (no board needed):
//   c++ -std=c++17 -Wall -Wextra -I../acorn_mcu test_logic.cpp -o test_logic && ./test_logic vectors.txt
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <sstream>
#include <string>
#include "acorn_logic.h"

using namespace acorn;

static int failures = 0;
static int checks = 0;

#define CHECK(cond, ...)                         \
  do {                                           \
    ++checks;                                    \
    if (!(cond)) {                               \
      ++failures;                                \
      std::printf("FAIL %s:%d: ", __FILE__, __LINE__); \
      std::printf(__VA_ARGS__);                  \
      std::printf("\n");                         \
    }                                            \
  } while (0)

static void run_vectors(const char* path) {
  std::ifstream in(path);
  if (!in) { std::printf("cannot open %s\n", path); std::exit(2); }
  Settings s = default_settings();
  FlameDetector* det = nullptr;
  LinkWatch* watch = nullptr;
  std::string line, scenario;
  int scenarios = 0;
  while (std::getline(in, line)) {
    if (line.empty() || line[0] == '#') continue;
    std::istringstream ls(line);
    if (line.rfind("scenario ", 0) == 0) {
      ls >> scenario >> scenario;
      delete det; delete watch;
      det = new FlameDetector(s);
      watch = new LinkWatch(s.linux_timeout_ms);
      ++scenarios;
      continue;
    }
    unsigned t, raw; int dig; std::string state, arrow, level; int trig, led;
    ls >> t >> raw >> dig >> state >> arrow >> trig >> led >> level;
    det->sample(t, (uint16_t)raw, dig != 0);
    if (state != "-") watch->heard(t, (uint8_t)std::atoi(state.c_str()));
    LedState got = select_led(det->flame_shown(t), watch->silent(t), watch->requested());
    CHECK((int)det->triggered() == trig, "%s t=%u triggered=%d want %d", scenario.c_str(), t, det->triggered(), trig);
    CHECK((int)got == led, "%s t=%u led=%d want %d", scenario.c_str(), t, (int)got, led);
    if (level != "-") {
      CHECK(det->level_permille() == std::atoi(level.c_str()), "%s t=%u level=%u want %s",
            scenario.c_str(), t, det->level_permille(), level.c_str());
    }
  }
  delete det; delete watch;
  CHECK(scenarios >= 10, "expected the shared scenarios, found %d", scenarios);
}

static void test_patterns() {
  // Each state has a distinct rhythm (count "on" ms over 2.4 s and number of rising edges).
  const LedState states[] = {LED_NORMAL, LED_SMOKE_PENDING, LED_FLAME, LED_DEGRADED, LED_LINUX_SILENT};
  int on_ms[5], edges[5];
  for (int i = 0; i < 5; ++i) {
    Pattern p = pattern_for(states[i]);
    on_ms[i] = 0; edges[i] = 0;
    bool prev = false;
    for (uint32_t t = 0; t < 2400; ++t) {
      bool on = pattern_on(p, t);
      on_ms[i] += on;
      if (on && !prev) ++edges[i];
      prev = on;
    }
    CHECK(pattern_on(p, 0), "state %d must start lit so changes show at once", (int)states[i]);
  }
  for (int a = 0; a < 5; ++a)
    for (int b = a + 1; b < 5; ++b)
      CHECK(on_ms[a] != on_ms[b] || edges[a] != edges[b], "states %d and %d share a rhythm", (int)states[a], (int)states[b]);
  CHECK(edges[2] == 12, "flame is a 5 Hz blink, got %d edges", edges[2]);
  CHECK(on_ms[0] == 2400, "normal is steady");
  CHECK(edges[1] == 4, "smoke pending is a double blink, got %d", edges[1]);

  LedRenderer r;
  Rgb c = r.render(1000, LED_FLAME);
  CHECK(c.r == 255 && c.g == 0, "flame renders red immediately");
  c = r.render(1150, LED_FLAME);
  CHECK(c.r == 0, "flame off phase");
  c = r.render(1160, LED_NORMAL);
  CHECK(c.g == 255, "state change restarts the pattern");
  CHECK(boot_colour(0).r == 255 && boot_colour(300).g == 255 && boot_colour(600).b == 255, "boot lamp test");
  CHECK(boot_colour(BOOT_TEST_MS).r == 0 && boot_colour(BOOT_TEST_MS).b == 0, "boot test ends dark");
}

static void test_wraparound_and_analog_trigger() {
  Settings s = default_settings();
  FlameDetector d(s);
  uint32_t t0 = 0xFFFFFFFFu - 50;  // millisecond counter wraps after ~49.7 days
  d.sample(t0, 4095, true);
  d.sample(t0 + 200, 4095, true);  // wraps past zero
  CHECK(d.triggered(), "trigger timing survives counter wraparound");
  LinkWatch w(5000);
  w.heard(t0, LED_NORMAL);
  CHECK(!w.silent(t0 + 4000), "heartbeat timing survives wraparound");
  CHECK(w.silent(t0 + 5000), "timeout after wraparound");

  s.analog_trigger_permille = 600;
  s.analog_release_permille = 400;
  FlameDetector a(s);
  uint32_t t = 0;
  for (; t < 2000; t += 10) a.sample(t, 4095, false);  // dark
  CHECK(!a.triggered(), "dark analog does not trigger");
  for (; t < 4000; t += 10) a.sample(t, 300, false);  // strong IR, digital silent
  CHECK(a.triggered(), "analog threshold triggers when enabled");
  for (; t < 4500; t += 10) a.sample(t, 1800, false);  // ~56%: inside hysteresis band
  CHECK(a.triggered(), "hysteresis keeps trigger between release and trigger levels");
  for (; t < 8000; t += 10) a.sample(t, 4095, false);
  CHECK(!a.triggered(), "analog trigger releases");
}

int main(int argc, char** argv) {
  run_vectors(argc > 1 ? argv[1] : "vectors.txt");
  test_patterns();
  test_wraparound_and_analog_trigger();
  std::printf("%d checks, %d failures\n", checks, failures);
  return failures ? 1 : 0;
}
