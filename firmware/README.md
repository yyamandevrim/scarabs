# ACORN microcontroller: KY-026 and status LED

**No board was available during implementation. The sketch compiles; it has never been flashed or tested on a UNO Q. Follow the measurement gates below before connecting signal wires.** Camera events remain **suspected smoke / “Duman şüphesi”**. The local sensor reports **“Alev sensörü tetiklendi”**. Neither proves a forest fire, and the sensor never confirms a camera event.

## Install on the Arduino UNO Q — first-time checklist

1. Set up the board and its Linux account using the [Arduino user manual](https://docs.arduino.cc/tutorials/uno-q/user-manual/). Copy this repository onto the board. Follow [station: Cold start on UNO Q Linux](../station/README.md#cold-start-on-uno-q-linux) for Linux packages, Python, model and footage. Stop the station after checking it starts. Keep the downloaded assets for offline use.
2. **Benchmark on the board before the demo**, from `station/`, with the server stopped:
   ```sh
   uv run --offline --frozen forest-station --config config.toml benchmark media/smoke.ogv --frames 60 --stride 25
   ```
   Save the JSON and the machine/board identification. This measures one detector on a file, not simultaneous USB capture or thermals. Existing published numbers are **Apple M5 Mac only**. Adjust `analysis_hz` after checking sustained two-camera operation; 1 Hz per camera is a target, not a board measurement.
3. Choose the LED type and pins below. For the simplest first bring-up use on-board LED4: set `LED_EXTERNAL` to `0` in [acorn_config.h](acorn_mcu/acorn_config.h), leaving `LED_ONBOARD` at `4`.
4. With external parts disconnected, [build and upload the sketch](#build-and-upload). Record success/failure; compilation alone does not prove it runs.
5. Shut Linux down normally, remove all board power, then [wire and measure](#wiring-and-voltage-rules). Reconnect power only at the stated checks.
6. [Select real bridge mode](#switch-the-station-to-the-real-bridge) in a local station config. Map the two USB cameras using the station guide. Do not copy the demo's `simulated` setting onto the hardware unnoticed.
7. Run the [bring-up procedure](#bring-up-and-fault-finding), including polarity calibration, station loss/recovery and the two camera checks. Record the still-unverified results. Use the [flame-free demonstration](#what-this-sensor-can-and-cannot-show) if flames are forbidden.

## What runs where

Linux runs camera inference, the operator panel and SQLite. The STM32 MCU runs [acorn_mcu.ino](acorn_mcu/acorn_mcu.ino): it samples the KY-026, smooths analog readings, debounces the digital comparator and drives status LEDs. MCU logic and LED sensing run in a separate Zephyr thread, started before `Bridge.begin()`. Actual thread/ADC behaviour and vendor loader startup timing need a board check.

Defaults in [acorn_config.h](acorn_mcu/acorn_config.h): 12-bit ADC (`0..4095`), sample loop about 5 ms, exponential smoothing α=1/8, digital trigger after 150 ms continuously active, release after 1 s continuously inactive, then 3 s of red LED hold. Analog triggering is disabled; analog intensity is displayed only. The scaled level is approximately `1000 × (4095 − smoothed_raw) / 4095`, rounded, **not confidence, distance or flame size**.

The sketch sends `acorn_reading` notifications every 500 ms and on trigger changes. Linux requests `acorn_state(state, seq)` every second; the MCU returns protocol version `1`. After 5 s without a state message the MCU shows `linux_silent`. Before the first message it is silent immediately after the lamp test. It continues local sensing while Linux is absent, once the sketch is running.

The bridge uses Arduino's [Router RPC](https://github.com/arduino/docs-content/blob/main/content/hardware/uno/boards/uno-q/tutorials/linux/routerbridge-multilanguage/content.md) Unix socket `/var/run/arduino-router.sock`. **Never open `/dev/ttyHS1` yourself**; the router owns it. This standalone station does not use App Lab's Python `Bridge` API. The sketch uses `Bridge.notify` and `Bridge.provide_safe`; it avoids blocking MCU-to-Linux `Bridge.call().result()` ([library source, v0.4.4](https://github.com/arduino-libraries/Arduino_RouterBridge/blob/0.4.4/src/bridge.h)).

## Parts and choices

- Arduino UNO Q, its suitable power supply and data-capable USB-C cable; USB camera/hub setup from the station guide.
- Joy-IT KY-026 module with labeled `+`, `G`/`GND`, `A0`/`AO`, `D0`/`DO` pins. Inspect your module: clone order and polarity can differ.
- Breadboard, insulated jumper wires, a small potentiometer screwdriver, and a multimeter for voltage/continuity checks.
- Optional **ordinary four-lead RGB LED**, or documented resistor-equipped RGB module compatible with 3.3 V GPIO. For a bare LED, three separate **1 kΩ resistors**, one per colour, are a conservative starting choice. Do not substitute an addressable RGB LED (WS2812/NeoPixel); this sketch cannot drive it.
- Optional TV remote for an experimental infrared response check, with venue permission; its ability to trigger this module is unverified. Simulation needs no extra parts.

On-board LED4 needs no wires or external resistors. `LED_ONBOARD = 3` selects LED3; `0` disables on-board mirroring. Arduino documents LED3/LED4 as MCU-controlled and active-low; LED1/LED2 belong to Linux. Core [pin definitions](https://github.com/arduino/ArduinoCore-zephyr/blob/1.1.0/variants/arduino_uno_q_stm32u585xx/variant.h) and [overlay](https://github.com/arduino/ArduinoCore-zephyr/blob/1.1.0/variants/arduino_uno_q_stm32u585xx/arduino_uno_q_stm32u585xx.overlay) identify LED3 red as the error LED, hence our LED4 default. The sketch treats on-board colours as on/off, so red+green appears yellow rather than PWM amber. Verify the physical LED label and visibility on the board.

## Wiring and voltage rules

**Use the labeled top UNO headers, not the small underside MPU connectors. Power off for wiring changes.** In the official [UNO Q datasheet, JDIGITAL/JANALOG pin maps](https://github.com/arduino/docs-content/blob/main/content/hardware/uno/boards/uno-q/datasheet/en-datasheet.md): MCU logic is **3.3 V**; MPU GPIO is **1.8 V**. A0 accepts **0..VREF+ (about 3.3 V)**. Its **VDD+0.3 V (about 3.6 V) absolute maximum is a damage limit, not a usable input range**. A0 is not 5 V tolerant. D3 is not 5 V tolerant either; do not infer voltage safety from another UNO model.

**Power the KY-026 only from UNO Q `3.3V`, never `5V` or `VIN`.** Joy-IT's [KY-026 documentation](https://sensorkit.joy-it.net/en/sensors/ky-026) includes a 3.3 V supply example, although it does not specify a complete operating range. Our single-supply design keeps its outputs within the ADC rail; verify your actual module with a meter before connecting A0/D2. If it cannot work at 3.3 V, stop and identify the module; do not “fix” it by applying 5 V to the sensor with outputs still attached. Do not power it externally or while the board is off.

### Default connection table

Connector pin numbers below are **datasheet header positions**, not MCU package pins or a left-to-right drawing. Match the board silkscreen and official pinout; never count from an assumed orientation. **Module D0 goes to board D2, not board D0.**

| Part connection | UNO Q silkscreen | Official header position / MCU | Purpose |
|---|---|---|---|
| KY-026 `+` / `VCC` | `3.3V` | JANALOG pin 4, +3V3 OUT | Sensor power |
| KY-026 `G` / `GND` | `GND` | JANALOG pin 6 or 7 | Shared ground |
| KY-026 `A0` / `AO` | `A0` | JANALOG pin 9 / PA4 | Analog input, 0..3.3 V |
| KY-026 `D0` / `DO` | `D2` | JDIGITAL pin 3 / PB3 | Comparator input |
| RGB red lead, through its resistor | `D9` | JDIGITAL pin 10 / PB8 | PWM red |
| RGB green lead, through its resistor | `D10` | JDIGITAL pin 11 / PB9 | PWM green |
| RGB blue lead, through its resistor | `D11` | JDIGITAL pin 12 / PB15 | PWM blue |
| RGB common, **common cathode** | `GND` | Same shared ground | Default: `LED_COMMON_CATHODE 1` |
| RGB common, **common anode instead** | `3.3V` | Same 3.3 V rail | Set `LED_COMMON_CATHODE 0`, rebuild/upload |

```text
UNO Q (top headers)                         KY-026 (read its labels)
3.3V -------------------------------------- + / VCC
GND  -------------------------------------- G / GND
A0   <------------------------------------- A0 / AO
D2   <------------------------------------- D0 / DO

OPTIONAL BARE RGB — COMMON CATHODE (default)
D9  ----[1 kΩ]---- R anode ---|>|---+
D10 ----[1 kΩ]---- G anode ---|>|---+---- common cathode ---- GND
D11 ----[1 kΩ]---- B anode ---|>|---+

COMMON ANODE alternative (change firmware setting first):
3.3V ---- common anode ----+---|>|--- R cathode ----[1 kΩ]---- D9
                          +---|>|--- G cathode ----[1 kΩ]---- D10
                          +---|>|--- B cathode ----[1 kΩ]---- D11

On-board LED4: no jumper wires; leave the external branch out if disabled.
These are connection diagrams, not physical leg order or board orientation.
```

### RGB resistor and polarity check

A bare RGB LED needs **one current-limiting resistor in each R/G/B branch**, not one shared resistor on its common leg. Identify its common and colour leads from the exact part datasheet or a meter's diode test; leg length alone is insufficient. Adafruit's [RGB LED lesson](https://learn.adafruit.com/adafruit-arduino-lesson-3-rgb-leds/arduino-sketch) explains common-cathode/anode inversion; its [parts list](https://learn.adafruit.com/adafruit-arduino-lesson-3-rgb-leds/parts) includes three resistors. Our 1 kΩ starting choice bounds each branch below `3.3 V / 1000 Ω = 3.3 mA`, even ignoring LED forward voltage. Blue/green may be dim at 3.3 V; check the actual part's specifications before changing resistor values. Do not connect a high-power LED directly to GPIO.

For a module, use its schematic to confirm a resistor **in every colour branch**, its polarity, current and 3.3 V compatibility before omitting external resistors. A PCB or a “5 V RGB” label alone does not establish this. Unknown module? Leave it disconnected, set `LED_EXTERNAL 0` and use LED4. Never connect the common anode to 5 V. D10/D11 also serve SPI; select different supported PWM pins in the config if another attachment uses them. The documented PWM set is D3/D5/D6/D9/D10/D11; default PWM is 8-bit ([user manual](https://docs.arduino.cc/tutorials/uno-q/user-manual/#pwm-pins)).

### Measure before attaching signal wires

1. With all power removed, connect sensor power/ground and any verified LED wiring; **leave sensor AO/DO disconnected from the board inputs**. Check no short between 3.3V and GND. Check breadboard rail splits and labels.
2. Power the board. Measure VCC-to-GND at the sensor: about 3.3 V. Measure AO-to-GND and DO-to-GND with the potentiometer at several settings and during the permitted IR check. Both must stay between GND and the 3.3 V rail. Stop for any overvoltage, unexpected heat or ambiguous pin identity. Do not attach signals until resolved.
3. Shut down, remove power, attach AO→A0 and DO→D2, then restart. No voltage divider is needed for this verified 3.3 V-only wiring. The ADC readings before attaching AO are meaningless.

## Build and upload

### Arduino IDE: preferred first upload

These steps follow the [official UNO Q user manual's Arduino IDE section](https://docs.arduino.cc/tutorials/uno-q/user-manual/#arduino-ide-beta). **Uploading replaces the borrowed board's MCU sketch**; agree with its owner which application to restore later. It does not install the station's Linux Python dependencies.

1. Connect the UNO Q directly to the development computer using a data-capable USB-C cable and complete Arduino's initial board setup. Stop other apps that might upload sketches; do not leave an App Lab app set to overwrite this sketch at startup.
2. In IDE Boards Manager, search `UNO Q` and install **Arduino Zephyr Boards / Arduino UNO Q Zephyr Core**. If absent, add `https://downloads.arduino.cc/packages/package_zephyr_index.json` under Preferences → Additional Boards Manager URLs. Our tested core is **1.1.0**.
3. In Library Manager install **Arduino_RouterBridge**, including all dependencies. Our tested version is **0.4.4**; it is a separate library, not bundled with the core. See Arduino's [library/core compatibility guidance](https://support.arduino.cc/hc/en-us/articles/27251870677916-Migrating-to-Zephyr-core-0-55-0-on-UNO-Q) if the installed board image reports a mismatch. Follow the vendor's version-specific recovery instructions rather than burning a bootloader speculatively.
4. Open `firmware/acorn_mcu/acorn_mcu.ino`. Keep `acorn_logic.h` and `acorn_config.h` alongside it. Set LED/polarity/pins in the config before upload.
5. Select **Arduino UNO Q** under the installed Zephyr board package, and its detected USB port under Tools → Port. Select **Verify**, then **Upload**. Wait for success, retaining the log. Port discovery and upload have **not** been tested here. Do not select a classic AVR UNO or invent `/dev/ttyACM0` as a substitute.
6. If discovery fails, check cable, completed Linux boot and board selection. For a Linux development computer, follow the user manual's **Linux users: USB permissions required** section, then reconnect. If upload reports firmware/loader incompatibility, use the linked Arduino guidance for that installed version; this guide does not prove loader compatibility on the borrowed board.

### Arduino CLI alternative

Install [Arduino CLI](https://docs.arduino.cc/arduino-cli/installation/) on the development computer. From the repository root, download the core/libraries while online, then compile:

```sh
arduino-cli version
arduino-cli core update-index --additional-urls https://downloads.arduino.cc/packages/package_zephyr_index.json
arduino-cli core install arduino:zephyr@1.1.0 --additional-urls https://downloads.arduino.cc/packages/package_zephyr_index.json
arduino-cli lib install 'Arduino_RouterBridge@0.4.4'
arduino-cli compile --fqbn arduino:zephyr:unoq --build-path /tmp/acorn-unoq-build firmware/acorn_mcu
arduino-cli board list
```

Copy the actual UNO Q address from `board list` into the quoted placeholder below. This example is for a **USB-connected board on the development computer**, not an assumed serial device or a command proven locally on the UNO Q Linux side:

```sh
arduino-cli upload --fqbn arduino:zephyr:unoq --port 'ADDRESS_FROM_BOARD_LIST' --build-path /tmp/acorn-unoq-build firmware/acorn_mcu
```

The [core board definition](https://github.com/arduino/ArduinoCore-zephyr/blob/1.1.0/boards.txt) selects UNO Q's vendor `remoteocd` uploader; the [upload recipe](https://github.com/arduino/ArduinoCore-zephyr/blob/1.1.0/platform.txt) uses ADB for USB. Do not manually flash a binary at an address or open the router's serial port. If discovery only offers a network endpoint, prefer IDE/App Lab's credential handling; do not paste passwords into the repo or this command. Command syntax: [core install](https://docs.arduino.cc/arduino-cli/commands-reference/arduino-cli_core_install/), [compile](https://docs.arduino.cc/arduino-cli/commands-reference/arduino-cli_compile/), [board list](https://docs.arduino.cc/arduino-cli/commands-reference/arduino-cli_board_list/), [upload](https://docs.arduino.cc/arduino-cli/commands-reference/arduino-cli_upload/).

Compile reverified on a Mac with CLI **1.6.0**, core **1.1.0**, RouterBridge **0.4.4**: **94,492 bytes flash, 38,924 bytes RAM**, default settings. This does not validate upload, dynamic-loader symbols, runtime memory use or hardware timing. After any config change, compile and upload again. App Lab can also host a sketch as documented by Arduino, but our standalone Linux service and this multi-file sketch installation have not been rehearsed through that UI; use the IDE/CLI procedure above for this project.

## Switch the station to the real bridge

On the board's Linux side, in `station/`, copy `config.toml` to `usb.local.toml` if you have not already made a camera config. **Edit its existing `[mcu]` section**, do not add a duplicate:

```toml
[mcu]
mode = "router"
socket = "/var/run/arduino-router.sock"
state_interval = 1.0
reading_timeout = 3.0
request_timeout = 2.0
reconnect_seconds = 2.0
```

`off` disables the bridge; `simulated` is the hardware-free demo; `router` requires the real sketch and daemon. First inspect the service/socket with commands from the [Arduino Router guide](https://github.com/arduino/docs-content/blob/main/content/hardware/uno/boards/uno-q/tutorials/linux/routerbridge-multilanguage/content.md):

```sh
systemctl status arduino-router
ls -l /var/run/arduino-router.sock
uv run --offline --frozen forest-station --config usb.local.toml serve --port 8080
```

In another terminal:

```sh
curl -s http://127.0.0.1:8080/api/mcu
curl -s http://127.0.0.1:8080/api/status
curl -s 'http://127.0.0.1:8080/api/events?kind=flame_sensor'
```

Require `mode: "router"`, `simulated: false`, `link.router_connected: true`, `link.registered: true`, `link.mcu_protocol: 1`, and `flame_sensor.connected: true`. Socket connectivity alone does not prove MCU readings. `connected` means **recent telemetry**, not electrical detection of a plugged-in KY-026: a disconnected sensor can float and still report data. Inspect wiring and signal response separately. The [panel API contract](../station/README.md#microcontroller-and-local-flame-sensor-api-for-the-panel-designer) explains requested versus reported LED state and event separation.

If the socket is missing or denied, inspect daemon status/logs and socket permissions under the board account. Do not make it world-writable or run the whole panel as root to hide a permissions error. `journalctl -u arduino-router -f` shows logs; after checking no other application needs it, `sudo systemctl restart arduino-router` is the vendor's recovery command. A “route already exists” error usually means a second client has registered `acorn_reading`: stop that duplicate. An `acorn_state` timeout with a working socket suggests missing/wrong sketch, blocked startup or a protocol mismatch.

## KY-026 potentiometer and polarity

Joy-IT documents **digital HIGH on threshold crossing**, and **lower analog voltage with more IR**; these are the defaults `FLAME_DIGITAL_ACTIVE_HIGH 1` and `FLAME_ANALOG_LOWERS_VOLTAGE 1`. Its indicator descriptions identify power and comparator LEDs, but one paragraph names the comparator LED differently. Use the actual module's labels/voltage change rather than trusting an LED number. Clone polarity is a bring-up measurement, not an assumption.

1. In the intended indoor lighting, remove IR test sources. Check module power indication and the meter checks above. Read `raw`, `smoothed_raw`, `digital_active` and `triggered` from `/api/mcu`.
2. Turn the potentiometer slowly in small steps, without forcing its end stops. Find the point where the comparator indicator/DO changes. Adjust away from that boundary until ambient light is stable and `digital_active: false`, then `triggered: false`. There is no documented universal clockwise direction or valid fixed ADC baseline.
3. If permitted, try the IR test described below; adjust so it switches reproducibly and clears when removed, while normal room lighting does not trigger. Do not tune at the edge where it chatters. Pulses shorter than 150 ms may never trigger.
4. Measure DO relative to GND with and without the stimulus. If this module activates LOW, set `FLAME_DIGITAL_ACTIVE_HIGH 0`, rebuild and upload. `digital_active` is already polarity-normalized; it is not the raw electrical HIGH/LOW. If AO rises rather than falls under repeatable IR exposure, identify the module and only then change `FLAME_ANALOG_LOWERS_VOLTAGE`.
5. Repeat in final venue lighting. The potentiometer sets **the digital comparator threshold**, not a calibrated distance, analog scaling or smoke threshold. Leave analog-trigger settings at zero for initial testing.

## LED state table

| Code / name | External RGB | Rhythm / meaning |
|---|---|---|
| 0 `boot` | red → green → blue | Once, 250 ms each (0.75 s total), unless local trigger takes priority |
| 1 `normal` | green | Steady; no pending smoke and active camera pipelines healthy |
| 2 `smoke_pending` | amber | Two 150 ms flashes separated by 150 ms, every 1.2 s; operator review pending |
| 3 `degraded` | blue | 1 s on / 1 s off; active camera disconnected or pipeline error |
| 4 `flame_sensor` | red | 100 ms on / 100 ms off (5 Hz); local sensor trigger, plus 3 s hold after release |
| 5 `linux_silent` | blue | 100 ms flash every 2 s; no station heartbeat |

On-board LED4 mirrors these rhythms; its pending-smoke colour is **yellow (red+green fully on)**. Actual hue/brightness depends on the external part. Priority: **MCU local trigger/hold > Linux silent > station request**. Station requests prioritize **fresh flame trigger > pending smoke > degraded camera > normal**. Therefore a pending smoke record can mask the blue camera-loss pattern; check `/api/status` for camera health. A closed smoke record still awaiting a decision remains pending. Green is an operational state, not a guarantee that the surroundings are fire-free.

## Bring-up and fault finding

These are **expected software behaviours to check on the board**, not completed hardware tests. Keep a log of time, MCU API output, meter readings and observed LED. Never rewire a powered board.

For an uncontaminated LED test, make `bringup.local.toml` from your board config in `station/`: use `data_dir = "data/bringup"`, `[mcu] mode = "router"`, and temporarily set the two active cameras to `kind = "file"`, **left** with `source = "media/fog.webm"`, **centre** with `source = "media/cloud.webm"`. Use different files so `unplug centre` does not also remove left's source. Keep the third inactive. Stop the normal server first. This provides camera-health inputs without the repeating smoke clip immediately masking every state. No model is guaranteed negative; decide any unexpected smoke records before checking `normal` or `degraded`.

| Step | Action | Expected readings / LED | If it fails |
|---|---|---|---|
| 1 — power | Power the measured, wired board with station stopped; watch after sketch starts | RGB lamp test, then short blue flash / 2 s if sensor inactive. No API yet | Check the specific LED4, upload log, power and vendor loader startup. Fast red suggests active/floating comparator; calibrate it. No board boot-time promise is made. |
| 2 — link | Start the station using the command below; query `/api/mcu` | Router/protocol checks above; raw and smoothed values `0..4095`, level `0..1000`, `adc_bits: 12`; updates roughly twice/s | Inspect daemon, socket, last_error, installed library and correct sketch. Constant 0/4095: meter AO, common GND, correct A0; saturation is not a measured flame size. |
| 3 — quiet | Calibrate ambient threshold; both active file pipelines healthy; no pending smoke | `digital_active: false`, `triggered: false`, `led.shown.name: "normal"`, steady green | Check comparator polarity, pending smoke list, camera `pipeline_error`; a stored unreviewed smoke event keeps amber/yellow. |
| 4 — IR response | Apply a permitted repeatable IR stimulus, or sweep pot across its ambient boundary for a comparator-only test | More IR should lower raw, then smoothed raw; scaled level rises. Stable active ≥150 ms gives `triggered: true`, own flame event, fast red | A remote may be unsuitable or pulsed too briefly. Check raw AO/DO and polarity. Pot-only test proves comparator/bridge, not optical flame detection. Do not use flame to resolve a venue restriction. |
| 5 — clear | Remove stimulus / restore calibrated pot setting | Digital inactive immediately; trigger clears after about 1 s; event closes; red holds a further 3 s, then next-priority state | Wait for both debounce and hold. Check ambient IR and threshold if it stays active; do not mistake the held red state for a still-open event. |
| 6 — heartbeat | Stop the station with Ctrl+C while sensor inactive | After 5 s without state messages, short blue flashes; local IR/comparator trigger should still override with red | Distinguish short blue from 1 s blue. Check another station client is not still sending state. No API is available while server is stopped. |
| 7 — recovery | Restart the same station command | Fresh telemetry, acknowledged protocol 1; quiet state recovers automatically | Check router logs/reconnect errors. A green LED alone does not prove sensor wiring. |
| 8 — smoke | Stop; change left file to `media/smoke.ogv`; restart | After the camera voting rule, a separate `kind: "smoke"` record titled “Duman şüphesi”; amber/yellow double blink. Flame reading stays independent | Check model/media, analysis counters and pending records. Review smoke via Doğrula/Reddet; no flame event should be fabricated. |
| 9 — camera loss | Return left to fog (keep centre on its separate cloud file), restart, clear pending smoke. In a second terminal run `unplug centre`, then `replug centre`, both with the same config | Centre disconnects, other feed continues; slow blue while no higher-priority state; recovery after retry | Use CLI commands below. If amber persists, inspect pending smoke. Commands accept active file sources only. |
| 10 — actual USB | Stop; return to `usb.local.toml`, with the intended two real USB paths. Repeat physical unplug/replug of the same port | One camera drops/retries; other continues. Check real fps, inference, evidence encoding and heat under sustained load | Board/hub/driver bandwidth, permissions and thermals are unverified. Use persistent device paths and inspect actual negotiated formats per station guide. |

From `station/`, the step 2/7 start command is:

```sh
uv run --offline --frozen forest-station --config bringup.local.toml serve --port 8080
```

For step 9, keep it running and use another terminal in `station/`:

```sh
uv run --offline --frozen forest-station --config bringup.local.toml unplug centre
uv run --offline --frozen forest-station --config bringup.local.toml replug centre
```

File disappearance is checked every 0.5 s; allow the panel poll and retry time (default 2 s). Always replug before fetching footage. Keep test events visibly separate by their data directory and config; the panel designer's flame widget may not yet be present, so use `/api/mcu` and the flame-event endpoint as the bring-up reference.

## What this sensor can and cannot show

The KY-026 responds to infrared at the **module's location**. Treat it as short-range, on the order of a metre or less, **not a documented/validated guaranteed range**. Joy-IT's page provides neither a distance rating nor a wavelength/angle specification. Sunlight and other IR sources can trigger it, while shielding, direction, lighting and threshold affect response. It is not a smoke, heat or gas sensor, not remote wildfire detection, and not confirmation of a camera's suspected smoke event. A TV remote test demonstrates an IR response, not detection of a real fire. Do not claim a calibrated detection range from it.

**No-flame indoor demonstration:** first use the station's explicitly labeled simulation, which is repeatable and does not exercise hardware. With a `simulated` local config, start the station and run:

```sh
curl -s -X POST http://127.0.0.1:8080/api/mcu/simulate -H 'Content-Type: application/json' -d '{"flame":true}'
# Wait at least one second and inspect /api/mcu and /api/events?kind=flame_sensor.
curl -s -X POST http://127.0.0.1:8080/api/mcu/simulate -H 'Content-Type: application/json' -d '{"flame":false}'
```

Say **“simulated sensor input”**. This does not drive the real MCU LED. For an optional physical check, with venue permission and real `router` mode, point a normal TV remote's IR emitter at the module from very close range and hold a button; response is **unverified** and modulation may be rejected by the debounce. Do not use lasers, burning material, smoke or open flame as a fallback. A potentiometer sweep can safely exercise the comparator in ambient light without claiming an optical test. Switch the config back to `router`, restart and verify `simulated: false` before any hardware claim. The simulate endpoint returns 409 outside simulated mode.

## Verification and remaining hardware checks

Reproduced locally on the Apple M5 Mac: **104 pytest cases (101 unit/API + 3 real-video integration), 21 panel JS tests, 150 C++ host checks**; the C++ vectors also check the Python simulation port. Commands:

```sh
cd station
uv run --offline --frozen pytest -q
npm test
cd ../firmware/test
c++ -std=c++17 -Wall -Wextra -I../acorn_mcu test_logic.cpp -o /tmp/acorn-test-logic
/tmp/acorn-test-logic vectors.txt
```

**Unverified on real hardware:** upload and vendor loader/core/image compatibility; reboot persistence/startup delay; `Bridge.begin()` when router is absent; real router registration, notification payload and `provide_safe(int,int)` round trips; ADC from the separate Zephyr thread; actual 3.3 V KY-026 polarity/levels/threshold stability and IR response; external PWM and on-board LED4 colours/brightness; heartbeat timing/recovery; real UNO Q device-tree model identification; Linux ARM64 installation, USB mapping/dropout/bandwidth, VP8 encoding, sustained inference, memory/thermals/power and any field performance. API “sensor connected” cannot detect sensor-wire removal.

**Team must choose and record before wiring:** on-board-only versus exact external RGB part; common cathode/anode and resistor provision/current; keep A0/D2 and D9/D10/D11 or change matching config pins; ambient comparator threshold/polarity; permitted indoor demonstration. Default pins are a proposed allocation, not confirmation that another team's shield leaves them free.
