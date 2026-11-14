# ACORN on Arduino UNO Q

**Aerial Canopy Observation and Reporting Node · Junction 2026**  
Portable forest smoke observation: camera events are **smoke suspicions for human review**, never confirmed fire.

**What runs where.** UNO Q Linux captures two USB cameras, runs the Pyronear YOLO11s ONNX smoke model on CPU, serves the local authenticated web panel, and stores event records/decisions in SQLite plus JPEG and video evidence. The STM32 microcontroller reads the Joy-IT KY-026 and drives on-board RGB LED4. Arduino RouterBridge joins them: Linux uses MessagePack-RPC through the router's Unix socket; `acorn_reading` carries sensor/LED telemetry up and `acorn_state` carries station state/heartbeats down. Sensing and LED control have their own MCU thread, including while the bridge waits for Linux.

**Measured on this UNO Q.** Board notes record two simultaneous live 320×240 YUYV cameras, requested capture 30 fps, UVC quirk 128, CPUExecutionProvider, two ORT threads and confidence 0.35. Pairs below are left/centre. Analysis means include preprocessing and inference, exclude capture/decode; intervals are requested per camera, rates are measured. Input 192: 30-second warm-up + 180.7-second window; other sizes: 30-second warm-up + about 300 seconds each. These are speed tests, not accuracy tests.

| Model input | Mean analysis (ms) | Interval / measured Hz | Mean station RAM (MiB) | CPU whole board / process | CPU temperature range |
|---|---:|---|---:|---|---|
| 192 | 282.21 / 282.55 | 1 s / 0.990, 0.990 | 179.8 | 42.42% / 156.5% | 41.7–47.0°C |
| 320 | 706.44 / 701.84 | 2 s / 0.500, 0.497 | 203.8 | 49.2% / 178.3% | 47.6–50.7°C |
| 416 | 1186.25 / 1172.10 | 3 s / 0.333, 0.333 | 227.5 | 50.8% / 187.1% | 45.1–51.7°C |
| 640 | 2740.66 / 2763.43 | 6 s / 0.167, 0.167 | 306.3 | 57.6% / 209.9% | 46.4–52.9°C |

RAM is process RSS; process CPU counts one full core as 100%, whole-board CPU covers all cores. Six seconds held at 640; 5.5 seconds failed. The board was restored to input 192 demo mode. The repository's exact field profile (640, confidence 0.25, final camera settings) remains unmeasured; the table uses 0.35.

**Live on-device AI update, 2026-11-14.** `detector_view = "center_crop"` analyses the centred 240×240 square of each 320×240 frame at input 192; the outer 40-pixel side strips are not analysed. Full-frame letterboxing lost screen-smoke scale. At confidence 0.35 and unchanged spatial 3-of-5 voting, a full-screen project smoke clip raised three centre-camera suspicions (peaks 0.743 / 0.759 / 0.621), about 3 s from first raw 0.20 response to suspicion; the hall camera stayed silent. Across 513 analyses per camera, mean inference was 276 ms, total analysis 281 / 282 ms, start intervals 1.012 / 1.011 s, RSS 180 MiB, with score logging active. These are measured board screen-test results, not field detection accuracy. Colour correction was rejected after Mac replay lifted negative examples.

**Local sensing and physical response.** No Modulino sensor is used at present. The KY-026 connects to header pins: 3.3 V, ground, AO to A0 and DO to D2. It is a short-range local infrared sensor, not remote fire detection. The owner observed a trigger; its IR source and distance are undocumented. Sensor events stay separate from camera suspicions.

LED4's programmed states: red/green/blue startup test; steady green = observing; yellow double blink = smoke suspicion awaiting review; slow blue = camera/analysis fault; fast red = local sensor trigger. After the programmed five-second heartbeat timeout, a short blue flash means Linux is silent. Local sensing continues and its red indication takes priority; fresh heartbeats restore station control. Green does not establish that the surroundings are safe.

**Board-specific fixes and recovery.** Two cameras through the kit hub initially failed USB bandwidth admission. Persistent `uvcvideo quirks=128` enabled simultaneous YUYV capture; physical-path device names avoid colliding camera serials. Higher-resolution trials produced corrupt frames or unsatisfactory detection and were rolled back. Aligning the board's Arduino core with the uploaded sketch let the vendor MCU-loader initializer complete. A user cron boot launcher with an exclusive lock starts station automatically. An owner-performed orderly power-off/reconnect recovered both cameras and fresh sensor telemetry without reflashing or manual launch. The later direct Wi-Fi panel bind has not been power-cycle tested.

**Not done.** The board later restarted unexpectedly and became unreachable; recovery and its cause remain unverified. The English repository panel is not yet deployed on the board. The arrived MicroMesh has not been identified or used for ACORN; transport remains simulated. External RGB LED, real LoRa radio and Wi-Fi access-point mode remain unverified. Board detection-quality comparisons across input sizes, field sensitivity/false-alarm rates, calibrated sensor range, long-duration hot-operation/supply headroom and unexpected-power-loss recovery remain unestablished. Limited standalone smoke-clip counts exist at 640/320; the broader quality study and synthetic distant-smoke proxy ran on a Mac. Smaller input speed does not establish equal sensitivity. Board evidence-encoding performance remains unmeasured.

**See it yourself — five pointers**

1. [Board record](../firmware/BOARD_NOTES.md): live-camera timings, wiring observations and recovery evidence.
2. [MCU sketch](../firmware/acorn_mcu/acorn_mcu.ino) and [LED/sensor logic](../firmware/acorn_mcu/acorn_logic.h): independent physical response.
3. [Linux bridge](../station/station/mcu_link.py) and [event/state handling](../station/station/mcu_bridge.py): real router exchange.
4. [Station operation](../station/README.md#analysis-profiles) and [quality limits](../station/DETECTION_VS_INPUT_SIZE.md): profiles and measurement conditions.
5. [DEMO.md, section C, steps 1–3](../DEMO.md#c-three-minute-walkthrough): feeds, suspicion evidence, human decision. That runbook uses recorded laptop footage; the table here uses live board cameras.
