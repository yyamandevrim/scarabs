// Wiring and behaviour choices. Edit here, then re-flash. See ../README.md.
// Each value can also be overridden with a compiler flag (-DNAME=value).
#pragma once

// ---- Flame sensor (Joy-IT KY-026), powered from the 3.3 V header pin ----
#ifndef FLAME_ANALOG_PIN
#define FLAME_ANALOG_PIN A0   // module "A0" output -> UNO Q A0 (JANALOG, 0..3.3 V only)
#endif
#ifndef FLAME_DIGITAL_PIN
#define FLAME_DIGITAL_PIN D2  // module "D0" output -> UNO Q D2
#endif
// Joy-IT documents the digital output going HIGH when the potentiometer
// threshold is exceeded. Some KY-026 clones are active-LOW: if the module's
// own "flame" LED and the reported `digital` disagree, set this to 0.
#ifndef FLAME_DIGITAL_ACTIVE_HIGH
#define FLAME_DIGITAL_ACTIVE_HIGH 1
#endif
// Joy-IT: "the signal is inverted" - more infrared gives a LOWER analog voltage.
#ifndef FLAME_ANALOG_LOWERS_VOLTAGE
#define FLAME_ANALOG_LOWERS_VOLTAGE 1
#endif
#ifndef FLAME_ADC_BITS
#define FLAME_ADC_BITS 12               // UNO Q ADC supports 8/10/12/14 bits
#endif
#ifndef FLAME_TRIGGER_MS
#define FLAME_TRIGGER_MS 150            // digital output must stay active this long
#endif
#ifndef FLAME_RELEASE_MS
#define FLAME_RELEASE_MS 1000           // ...and inactive this long to clear
#endif
#ifndef FLAME_ANALOG_TRIGGER_PERMILLE
#define FLAME_ANALOG_TRIGGER_PERMILLE 0 // 0 = trigger from the digital output only
#endif
#ifndef FLAME_ANALOG_RELEASE_PERMILLE
#define FLAME_ANALOG_RELEASE_PERMILLE 0
#endif
#ifndef FLAME_LED_HOLD_MS
#define FLAME_LED_HOLD_MS 3000          // LED keeps showing flame after it clears
#endif

// ---- Status LED ----
// On-board RGB LED driven by the MCU (LED3 or LED4; active-low, no wiring).
// 0 disables it. LED3 red is also LED_BUILTIN, so LED4 is the default.
#ifndef LED_ONBOARD
#define LED_ONBOARD 4
#endif
// External RGB LED on PWM pins (UNO Q PWM pins: D3 D5 D6 D9 D10 D11).
// Set LED_EXTERNAL 0 if nothing is wired to these pins.
#ifndef LED_EXTERNAL
#define LED_EXTERNAL 1
#endif
#ifndef LED_PIN_R
#define LED_PIN_R D9
#endif
#ifndef LED_PIN_G
#define LED_PIN_G D10
#endif
#ifndef LED_PIN_B
#define LED_PIN_B D11
#endif
// 1 = common cathode (common leg to GND, pin HIGH lights). 0 = common anode
// (common leg to 3.3 V, pin LOW lights).
#ifndef LED_COMMON_CATHODE
#define LED_COMMON_CATHODE 1
#endif

// ---- Bridge ----
#ifndef LINUX_TIMEOUT_MS
#define LINUX_TIMEOUT_MS 5000   // station sends its state every second
#endif
#ifndef READING_INTERVAL_MS
#define READING_INTERVAL_MS 500 // readings are also sent at once on trigger change
#endif
