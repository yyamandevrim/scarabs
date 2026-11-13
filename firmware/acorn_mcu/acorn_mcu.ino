// ACORN station microcontroller sketch for the Arduino UNO Q (STM32U585, Zephyr core).
//
// - Reads a Joy-IT KY-026 flame sensor (analog level + digital comparator output),
//   smoothed and debounced so one noisy sample never raises a trigger.
// - Drives one status LED (on-board LED4 and/or an external RGB LED).
// - Talks to the station on the Linux side through Arduino_RouterBridge:
//     up:   Bridge.notify("acorn_reading", ...) every 500 ms and on every trigger change
//     down: Linux calls "acorn_state"(state, seq) about once per second
// - Works on its own: flame lights the LED at once without Linux, and Linux
//   silence for LINUX_TIMEOUT_MS is shown on the LED.
//
// The KY-026 is a short-range infrared flame sensor at the station itself
// (open flame within roughly a metre). It is not remote fire detection.

#include <Arduino_RouterBridge.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include "acorn_config.h"
#include "acorn_logic.h"

using namespace acorn;

#if LED_ONBOARD == 3
#define ONBOARD_R LED3_R
#define ONBOARD_G LED3_G
#define ONBOARD_B LED3_B
#elif LED_ONBOARD == 4
#define ONBOARD_R LED4_R
#define ONBOARD_G LED4_G
#define ONBOARD_B LED4_B
#endif

static Settings make_settings() {
  Settings s = default_settings();
  s.adc_max = (uint16_t)((1u << FLAME_ADC_BITS) - 1u);
  s.analog_flame_lowers_voltage = FLAME_ANALOG_LOWERS_VOLTAGE;
  s.trigger_ms = FLAME_TRIGGER_MS;
  s.release_ms = FLAME_RELEASE_MS;
  s.analog_trigger_permille = FLAME_ANALOG_TRIGGER_PERMILLE;
  s.analog_release_permille = FLAME_ANALOG_RELEASE_PERMILLE;
  s.hold_ms = FLAME_LED_HOLD_MS;
  s.linux_timeout_ms = LINUX_TIMEOUT_MS;
  return s;
}

static FlameDetector detector(make_settings());
static LedRenderer renderer;

// State shared between the I/O thread and loop(), guarded by state_lock.
struct Shared {
  uint16_t raw, smoothed, level;
  bool digital, triggered, linux_silent;
  uint8_t led;
  uint32_t trigger_changes;
};
static struct k_mutex state_lock;
static Shared shared = {0, 0, 0, false, false, true, LED_BOOT, 0};
static atomic_t linux_heard_ms = ATOMIC_INIT(0);
static atomic_t linux_ever = ATOMIC_INIT(0);
static atomic_t linux_requested = ATOMIC_INIT(LED_NORMAL);

static void write_led(Rgb c) {
#if LED_ONBOARD
  // On-board LEDs are active-low and treated as on/off.
  digitalWrite(ONBOARD_R, c.r ? LOW : HIGH);
  digitalWrite(ONBOARD_G, c.g ? LOW : HIGH);
  digitalWrite(ONBOARD_B, c.b ? LOW : HIGH);
#endif
#if LED_EXTERNAL
#if LED_COMMON_CATHODE
  analogWrite(LED_PIN_R, c.r);
  analogWrite(LED_PIN_G, c.g);
  analogWrite(LED_PIN_B, c.b);
#else
  analogWrite(LED_PIN_R, 255 - c.r);
  analogWrite(LED_PIN_G, 255 - c.g);
  analogWrite(LED_PIN_B, 255 - c.b);
#endif
#endif
}

// Sensing and LED run in their own thread so they keep working even if
// Bridge.begin() is still waiting for the Linux router during boot.
static void io_thread(void*, void*, void*) {
  LinkWatch watch(LINUX_TIMEOUT_MS);
  bool last_triggered = false;
  uint32_t boot_started = k_uptime_get_32();
  while (true) {
    uint32_t now = k_uptime_get_32();
    uint16_t raw = (uint16_t)analogRead(FLAME_ANALOG_PIN);
    bool level = digitalRead(FLAME_DIGITAL_PIN) == HIGH;
    bool digital = FLAME_DIGITAL_ACTIVE_HIGH ? level : !level;
    detector.sample(now, raw, digital);

    if (atomic_get(&linux_ever)) {
      watch.heard((uint32_t)atomic_get(&linux_heard_ms), (uint8_t)atomic_get(&linux_requested));
    }
    bool silent = watch.silent(now);
    bool flame = detector.flame_shown(now);
    LedState led = select_led(flame, silent, watch.requested());
    Rgb colour;
    if (!flame && now - boot_started < BOOT_TEST_MS) {
      led = LED_BOOT;
      colour = boot_colour(now - boot_started);
    } else {
      colour = renderer.render(now, led);
    }
    write_led(colour);

    k_mutex_lock(&state_lock, K_FOREVER);
    shared.raw = detector.last_raw();
    shared.smoothed = detector.smoothed_raw();
    shared.level = detector.level_permille();
    shared.digital = detector.digital();
    shared.triggered = detector.triggered();
    shared.linux_silent = silent;
    shared.led = led;
    if (detector.triggered() != last_triggered) {
      last_triggered = detector.triggered();
      shared.trigger_changes++;
    }
    k_mutex_unlock(&state_lock);
    k_msleep(5);
  }
}

// Called by Linux (runs in loop() context because of provide_safe).
int acorn_state(int state, int seq) {
  (void)seq;
  atomic_set(&linux_requested, state);
  atomic_set(&linux_heard_ms, (atomic_val_t)k_uptime_get_32());
  atomic_set(&linux_ever, 1);
  return PROTOCOL_VERSION;
}

static k_thread_stack_t* io_stack;
static struct k_thread io_thread_data;

void setup() {
  analogReadResolution(FLAME_ADC_BITS);
  pinMode(FLAME_DIGITAL_PIN, INPUT);
#if LED_ONBOARD
  pinMode(ONBOARD_R, OUTPUT);
  pinMode(ONBOARD_G, OUTPUT);
  pinMode(ONBOARD_B, OUTPUT);
#endif
#if LED_EXTERNAL
  pinMode(LED_PIN_R, OUTPUT);
  pinMode(LED_PIN_G, OUTPUT);
  pinMode(LED_PIN_B, OUTPUT);
#endif
  write_led(Rgb{0, 0, 0});
  k_mutex_init(&state_lock);
  io_stack = k_thread_stack_alloc(2048, 0);
  k_tid_t tid = k_thread_create(&io_thread_data, io_stack, 2048, io_thread,
                                NULL, NULL, NULL, 7, 0, K_NO_WAIT);
  k_thread_name_set(tid, "acorn_io");

  Bridge.begin();
  Bridge.provide_safe("acorn_state", acorn_state);
}

void loop() {
  static uint32_t seq = 0;
  static uint32_t last_sent = 0;
  static uint32_t sent_changes = 0;
  uint32_t now = k_uptime_get_32();

  k_mutex_lock(&state_lock, K_FOREVER);
  Shared s = shared;
  k_mutex_unlock(&state_lock);

  if (s.trigger_changes != sent_changes || now - last_sent >= READING_INTERVAL_MS) {
    sent_changes = s.trigger_changes;
    last_sent = now;
    // Field order is the protocol (station/station/mcu_protocol.py READING_FIELDS).
    Bridge.notify("acorn_reading", PROTOCOL_VERSION, (int)++seq, (int)now,
                  (int)s.raw, (int)s.smoothed, (int)s.level, (int)FLAME_ADC_BITS,
                  s.digital, s.triggered, (int)s.led, !s.linux_silent);
  }
  delay(2);  // keep loop() short: provide_safe callbacks run between iterations
}
