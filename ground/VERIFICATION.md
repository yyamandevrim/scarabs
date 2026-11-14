# Local communication verification — 14 November 2026

Performed on this Mac using the real downloaded ONNX smoke model and the existing recorded `smoke.ogv` + `fog.webm` inputs. All radio communication was **LoRa link (simulated transport)**. The station and ground receiver ran as separate processes on TCP 8091/8092, joined for operational data only by raw UDP packets on 9901. Ground used its own data directory. Credentials were transient environment values and are not recorded here.

## Automated checks

- Station: `uv run --offline --frozen pytest -q` — **153 passed**, including the existing real-video integration tests; no skips. The final full run took 37.06 seconds on this Mac.
- Ground: `uv run --offline --frozen pytest -q` — **11 passed**.
- Existing station frontend guards: `node --test tests/panel.test.mjs` — **25 passed**, including never replacing/restarting a watched clip during polling.
- `node --check ground/ground/static/app.js` and `git diff --check` passed.
- Both Python suites emit the existing upstream Starlette/httpx deprecation warning. It is not suppressed.

## Separate-process observations

1. **LoRa-only:** the remote alert contained the real event UUID, left slot, recorded-source marker, approximate bearing around 293°, confidence and event time. Browser inspection found **zero image/video elements**, `demo.hidden = true`, and no frame/evidence requests. The resource audit showed local CSS/JS/fonts and ground `/api/state`/`api/demo` only; no station-origin request or external asset.
2. **Wi-Fi demo:** the explicit switch exposed the bounded “Demo only: shown over Wi-Fi, not available over LoRa” area. Both camera JPEGs decoded at 960 px wide. Wi-Fi source captions identified the station, camera and recorded footage.
3. **UUID collection:** a received alert's original UUID was used to collect its exact station event, JPEG and WebM. The saved JPEG decoded at 1280 px and WebM at 640 px, `readyState = 4`. The normal station view remained separately authenticated. Demo-off media routes returned 403 in tests; turning the viewing switch off removed the media area/elements after the toggle request completed.
4. **Stopped station:** in a fresh disposable simulation, the station was interrupted while the receiver continued. The UI reached the configured **10-second stale** and **20-second lost** states. After station shutdown the live feeds disappeared with a Wi-Fi-unavailable message, while the collected JPEG still decoded at 1280 px and the locally saved clip reached `readyState = 4`. This also worked after restarting ground, with demo off initially.
5. **Loss/budget:** a separate fresh simulation used SF10/BW125/CR4/5, 35% seeded loss (`seed = 1`), a stricter **0.1% = 3.6 s/hour** budget on the default 1% sub-band, two repeats three seconds apart and a two-second heartbeat. The station reported **5 transmission attempts**, **61 duty/headroom refusals**, **0 queue drops**, **0 queued items** at inspection. Ground received **3 valid packets**, one smoke event and **1 detected internal sequence gap**. Initial sequence loss is deliberately not counted. The sender's last received calculated budget was **1.00 s**, illustrating heartbeat headroom refusal before total exhaustion. The smoke alert arrived and its repeats were bounded while heartbeats yielded. No delivery-through-arbitrary-loss guarantee is made.
6. **Sustained fast heartbeat:** the earlier compressed four-second-heartbeat run reached 71 attempts and about 0.30 s remaining, after which the sender refused transmission. This was expected budget enforcement, not radio failure. Such a heartbeat is unsuitable as a sustained field setting; the documented default is five minutes.
7. **Responsive/offline:** 1440 and 390 CSS-pixel layouts were inspected, including Turkish. No horizontal overflow was found. Normal-run browser console had no application errors. Explicit station-stop checks produced the expected connection-refused/502 diagnostics; a favicon request can return 404. The snapshot tool scales some raster output, so viewport width is recorded separately from PNG pixel dimensions.

All started station/ground processes were stopped, their preview tabs closed, and TCP 8091/8092 listeners and UDP 9901 checked clear. Nothing on 8080/8787 was started or stopped.

## Screenshots

Saved to the task-requested scratchpad `lora/` directory (outside the repository):

1. `01-ground-alert-1440.png` — remote dashboard with a received smoke alert, demo off.
2. `02-ground-alert-390.png` — remote phone layout, demo off.
3. `03-ground-demo-wifi-1440.png` — bounded Wi-Fi demo with feeds and collected evidence.
4. `04-ground-stale-1440.png` — last-received alert and link-loss state after station stop (captured after the stale interval had advanced to lost).
5. `05-ranger-panel-1440.png` — authenticated full-detail station panel.
6. `06-ground-turkish-390.png` — Turkish mobile layout in lost-link state.
7. `07-ground-loss-budget-1440.png` — constrained/lossy simulation with link details expanded.

## Unverified

- Any real LoRa radio/modem, serial command/framing integration, PHY airtime measured on hardware, output power/antenna gain, RSSI/SNR, range and radio security. The serial adapter raises `NotImplementedError` deliberately.
- Subsequent board status: the station ran on a real UNO Q with recorded clips, MCU bridge, responding KY-026 and on-board status LED. Validated board inference speed for the demo, USB cameras, AP mode, external RGB LED, airborne installation and real LoRa remain unverified; see ../firmware/BOARD_NOTES.md for ongoing work.
- Every UNO Q access-point command, AP capability/driver, shared DHCP, WPA interoperability, ranger phone/laptop association and network recovery procedure. Vendor/NetworkManager documentation was checked; the board procedure was not run.
- Final national radio implementation/conformity, deployed heading/FOV calibration, power-loss reliability of unsent work, and physical internet-disconnect testing. Prototype limitations are stated in the packet specification and station README.

Rehearsal 2 update: the fast-heartbeat exhaustion described above is a historical reproduction of the pre-pacing sender. The sender now spaces legal transmissions throughout the hour and announces a bounded next-contact window; use ../DEMO.md and traffic-verification.json for current behaviour. Historical test counts above describe that dated run, not a claim about the current suite size.

The completed rehearsal-2 fix record and final suite counts are in [REHEARSAL2.md](REHEARSAL2.md); calculated three-hour results are in [traffic-verification.json](traffic-verification.json).
