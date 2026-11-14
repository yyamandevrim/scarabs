# ACORN — stage demo runbook

ACORN — Aerial Canopy Observation and Reporting Node. Scarabs, Junction 2026 Helsinki, Green European Renaissance challenge. This replaces the rehearsal-2 draft and its short-lived-ledger workaround.

The laptop demo uses real recorded smoke/control footage and real local inference, **LoRa link (simulated transport)** over UDP, plus an explicit Wi-Fi imagery aid. No radio range, calibrated bearing, fire location, battery percentage or confirmed fire is claimed. One MicroMesh has arrived, but its physical variant/firmware and real ACORN link remain unverified; see [the hardware investigation and single-radio demo limits](station/LORA_HARDWARE.md).

| App | Purpose | Demo address |
|---|---|---|
| Station, English | Full-detail ranger Wi-Fi panel: feeds, evidence, decisions | http://127.0.0.1:18091 |
| Ground, English by default | Remote packet-only view; explicit Wi-Fi demo switch | http://127.0.0.1:18092 |
| Placement, English by default | Simulated geometric launch-point comparison | http://127.0.0.1:18787 |

The stage commands in section B use UDP 19901 and the addresses above. The laptop-only fallback below uses separate ports because these stage ports were occupied during rehearsal. Change a port and all matching URLs/configuration together.

## Live camera screen demonstration — working recipe, 2026-11-14

**[UNO Q, measured live]** With the recipe below (screen filling the view, player controls hidden), the Center camera filming the project clip `smoke.ogv` on a full-screen laptop raised **three smoke suspicions in three clip loops** (10:00:45, 10:01:39, 10:02:36 UTC), opening confidence 0.36 / 0.44 / 0.40, peak **0.74 / 0.76 / 0.62**, **3 s** from the smoke first reaching the camera (raw 0.20) to the suspicion. The left camera on the hall stayed silent in the same window. The model detects smoke, not flames; the event is a suspicion for a person to confirm.

Settings: DEMO profile, input **192**, confidence **0.35**, **1 analysis/s/camera**, spatial **3 of 5 / IoU 0.25**, timeout 12 s, and **`detector_view = "center_crop"`** in `[station]` of the board config (commit `8a05ecd`). The crop analyses the centred 240×240 square of each 320×240 frame at full input resolution instead of letterboxing the whole frame; the outer 40-pixel strips on each side are not analysed. Without it the same screen scored about 0.00–0.05 and never fired. Threshold and alarm rule are unchanged.

1. Both USB cameras connected in their labelled ports; check `/api/status`: both connected, counters advancing, `analysis_profile.detector_view` = `center_crop`, no pipeline error. Sign in again after any restart.
2. Play the **recommended live clip**, `LOOP_01_crane_fire_22-39s_x10.mp4`: seconds 22–39 of **“Crane Fire 6-19-21”**, an ALERTCalifornia / UC San Diego tower-camera recording ([Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Crane_Fire_6-19-21.ogg), public domain `{{PD-automated}}`; credit ALERTCalifornia/UCSD; the frames carry PG&E and ALERTWildfire overlays), looped to 170 s. Make it locally from the Commons file, for example `ffmpeg -ss 22 -to 39 -i Crane_Fire_6-19-21.ogg -an -c:v libx264 -pix_fmt yuv420p crane.mp4` and loop it in the player; it is not in the repository. As a 320×240 file with the crop it scores **0.52–0.83 every second**, and it held a median of about 0.47 under a harsh *simulated* screen wash-out where `smoke.ogv` fell to 0.07. **It has not yet been filmed live by the board cameras.** The project's own clip **`station/media/smoke.ogv`**, “Wildfire Near Monserrate” (Peter Angritt / Mrtony77, CC BY-SA 4.0), remains the fallback: start it at **0:27** (0:27–0:49 scores 0.63–0.72 as a file; 0:08–0:13 is weak), keep the attribution. Play either **truly full screen**, looping.
3. **Move the mouse off the screen so the player bar and taskbar disappear.** With the control bar visible in the bottom quarter of the view, both cameras scored ≤0.08 and nothing fired.
4. Put the laptop close to **one** camera so the screen **fills its whole view**, no bezel or hall at the edges, and tilt the camera so the **tops of the plumes are inside the picture**. About 25–35 cm was used; distance was not measured. Point the other camera at the hall.
5. Start timing when the plume is in view; expect a suspicion within about 3–5 s of a strong passage and one per loop. Record time, camera (Left/Center) and confidence from the new **Smoke suspicion** card; a person then uses **Confirm suspicion** or **Reject suspicion**. The other camera must stay silent.
6. Negatives to show or rehearse: the hall, and an ordinary video (the fireplace video was used). Do not lower the threshold for any footage.

**What does not work, measured:** aerial top-down fire footage, a small player window, the Guardian Victoria/Buchan clip (peak 0.085 even as a file at 640), and this clip filmed with the player bar showing. The cameras render the screen blue and flat (blue/red ratio about 1.5–1.6 against about 1.3 in the file; the left camera's blacks are about 40 levels higher than the centre's), which costs roughly 0.4 of score compared with the file. Software colour correction was tried and **rejected**: grey-world plus levels lifted one Pyronear no-smoke photo to 0.55 and barely helped the centre camera; CLAHE lifted hall and fireplace frames past 0.35. V4L2 white balance, exposure, contrast, saturation and gamma gave at most 0.14. Details: [board record](firmware/BOARD_NOTES.md#2026-11-14-live-screen-smoke-fix--center-crop).

**Not yet confirmed live** (the board went off the network before these could be run; see [`station/BOARD_RETURN_CHECKLIST.md`](station/BOARD_RETURN_CHECKLIST.md)):

- the Crane Fire loop through a board camera;
- a second, repeated live run of the recipe after the board's restart, and the Left camera as the smoke camera (only Center fired live; Left on the same screen side by side scored at most 0.08, with the player bar visible);
- a full 3-minute hall window and 3-minute ordinary-video window on the camera facing the screen (hall views were silent for several minutes on both cameras and the fireplace video for about 3.5 minutes, but not in one dedicated run);
- the English panel on the board (the board still runs the Turkish panel strings);
- the optional `centre_zoom` view (Mac replay only).

Say to the jury: **“This camera is watching a real wildfire smoke recording on a screen, live. The station raises a smoke suspicion; a person confirms it.”** Do not call it real smoke in the hall, a confirmed fire, or flame detection. If the screen demo fails at the table, use the explicitly labelled **Recorded demo** file-source mode (`smoke.ogv` as a file opened a suspicion at video t=3 s, confidence 0.371, on the board) and say so.

## A. Prepare with reliable internet

From the repository root, after installing `uv` and Node 20+:

```sh
cd station
uv sync --locked --python 3.11
uv run python scripts/fetch_model.py
uv run python scripts/fetch_footage.py
uv run --offline --frozen pytest -q
npm ci --ignore-scripts
npm test
node --test ../ground/tests/dashboard.test.mjs
cd ../ground
uv sync --locked --python 3.11
uv run --offline --frozen pytest -q
cd ../placement
uv sync --frozen --python 3.12
uv run python scripts/prepare_data.py
uv run --offline --frozen pytest -q tests ../tools/tests
cd ..
```

The footage fetcher retries 429/503 politely: up to five attempts, 30/60/120/240 s exponential waits, longer if Retry-After requires it. Verified completed files are skipped, partial files are discarded, hashes still checked. If all retries fail, try later. Do downloads/data preparation before reaching the venue. Keep local model/media/prepared-data backups and screenshots of the successful walkthrough.

## Laptop only, no board

**Use Recorded demo for the jury if the UNO Q is not healthy.** Complete section A while online first. From the repository root, start all three offline services with:

```sh
uv run --offline --frozen --project station python station/scripts/laptop_demo.py
```

The launcher privately prompts for one panel secret and supplies it to ground too (or reuses exported `ACORN_PANEL_SECRET`). Sign into station with it. **Ctrl+C stops all three services**; a service failure also stops the others. Station is http://127.0.0.1:28091, ground http://127.0.0.1:28092, placement http://127.0.0.1:38787/map. These ports and UDP **49173** avoid the occupied stage ports found in rehearsal. If changing ports, update the launcher, station peer port and matching ground URLs/UDP binding together.

`station/demo-laptop.toml` runs two real file sources, `smoke.ogv` and `cloud.webm`, labelled **Recorded demo**. Station and ground each persist their own `data/laptop/`. Leave duty accounting intact. The Mac rehearsal opened a suspicion after **2.085 s**, score **0.354259**, and ground received it at **8.25 s** after startup with an existing ledger. These are **laptop timings, not board measurements**, and are not delivery guarantees.

**Live native Mac camera — separate form:**

```sh
uv run --offline --frozen --project station python station/scripts/laptop_demo.py --live
```

Stop the recorded run first. This selects `station/demo-mac-camera.toml`, with only **Left** active: `kind = "avfoundation"`, string `source = "0"`, requested **1280×720 / 30 capture fps**, **`center_crop`**, input **192**, **1 analysis/s**, confidence **0.35**, unchanged spatial **3 of 5 / IoU 0.25**, timeout **12 s**. The panel labels it **Live camera** and its clip **Camera recording**. Live station/ground data is in their separate `data/laptop-live/` directories; do not switch directories to bypass a duty wait.

AVFoundation is macOS-only; Linux USB persistent paths, V4L2 and YUYV negotiation are unchanged. Index 0 is normally built-in; change `source` in the live config if another camera is selected. Keep `capture_format` empty. Check the actual preview and authenticated `/api/status`: connected, counters advancing, measured dimensions/fps, `center_crop`, no pipeline error. Native launcher/capture was checked at 1280×720, about 30 fps, with advancing analyses and no pipeline error. Requested capture fps is not a measurement. If macOS requests camera access, grant it to the terminal/app running Python, restart and sign in again.

**Live smoke through the Mac camera remains unverified: nobody held the footage in front of it.** Play the local Crane loop on a phone/second screen, hide controls, fill the central square with plume and forest, and time a new suspicion; then run dedicated hall and ordinary-video controls without changing thresholds. The board recipe above supplies framing guidance, not a Mac latency promise. The earlier private Mac adapter's **180.148 s / 179-analysis** ordinary-hall control at actual **1280×720 / approximately 30 fps** had peak raw score **0.003035** and zero detections/suspicions. That is not a live smoke-positive result.

**The laptop cannot show the real flame sensor, physical LED or UNO Q board.** Both configs set MCU **off**: **Flame sensor not configured**, **Status LED: unavailable**; no trigger or LED response is silently simulated. Radio stays explicitly simulated UDP. Ground imagery needs **Show Wi-Fi demo**; its **Camera feeds · Wi-Fi** disclosure starts the separate feeds. Placement remains geometric simulation.

Section D's flame simulation commands deliberately return **409** with these hardware-off configs. Its recorded dropout commands use `stage.local.toml`; substitute `--config demo-laptop.toml` for the recorded laptop run. Live Mac's sole input is `left`, and file-dropout commands do not apply.

## B. Configure once; rehearse as long as needed

The sustainable demo uses **SF7/BW125/CR4/5 and a strict 1% duty limit**. A four-second heartbeat is a request, not an impossible transmission promise: the sender spaces transmissions into **12-second calculated slots**, with new alerts first, then decisions, due limited repeats and heartbeats. The rolling ledger and next legal slot survive restart. It does not go silent after four minutes. No “start one minute before going on” workaround or ledger-reset command is needed.

Copy the prepared config and change only the UDP destination for these ports:

```sh
# From repository root:
cp station/demo-lora.toml station/stage.local.toml
# No secret in this file. Paths remain relative to station/.
python3 - <<'PY'
from pathlib import Path
p=Path('station/stage.local.toml')
p.write_text(p.read_text().replace('peer_port = 9901','peer_port = 19901'))
PY
```

The config uses `station/data/stage/`; ground below uses its own `ground/data/stage/`. `data-*/` alternatives are also ignored by each sub-project. To clear the review list, **stop the station first**, then use `uv run --offline --frozen forest-station --config stage.local.toml archive-events` in `station/`. This archives evidence/decisions and preserves radio accounting. Do not remove or replace `lora-duty.json` to gain allowance. If upgrading a previously exhausted old ledger, wait until authenticated `/api/communication.calculated_next_tx_at`; already-used airtime cannot legally be reclaimed.

Choose the panel secret privately and share it out of band. The following commands prompt for it without placing its value in a command argument, file, screenshot or shell history. They use **macOS zsh**; for bash replace a prompt with `read -rs -p 'Station secret: ' ACORN_PANEL_SECRET; export ACORN_PANEL_SECRET; echo` (use the matching ground variable in its terminal).

**Terminal 1 — placement:**

```sh
cd placement
uv run --offline --frozen uvicorn forest_placement.api:app --host 127.0.0.1 --port 18787
```

**Terminal 2 — ground (start before station):**

```sh
cd ground
read -s 'ACORN_STATION_SECRET?Station panel secret: '; export ACORN_STATION_SECRET; echo
uv run --offline --frozen acorn-ground --port 18092 --udp-port 19901 --sf 7 \
  --data data/stage --station-url http://127.0.0.1:18091 --stale-after 10 --lost-after 20
```

**Terminal 3 — station:**

```sh
cd station
read -s 'ACORN_PANEL_SECRET?Station secret: '; export ACORN_PANEL_SECRET; echo
uv run --offline --frozen forest-station --config stage.local.toml serve --port 18091
```

Open the three addresses above. Sign into the station panel. Ground defaults to **demo off**, English, with zero camera images/video. Leave the apps running during rehearsal; prepare a clean review list by archiving if useful, rather than resetting a budget. A smoke suspicion generally opens after a few analyses; packet delivery waits for the next legal slot, up to about 12 s without backlog. Do not promise a fresh suspicion on every recorded loop: the Mac rehearsal kept one suspicion open for more than six minutes. A new event needs the unchanged tracker to expire; existing decisions can still be corrected.

For a long-range configuration use SF12 on **both** station and ground: the same 1% limit requires **241-second slots**. Ground receives the calculated contact window in every packet and shows a duty-cycle wait. Alerts have longer latency and may queue under sustained overload; no legitimate setting can carry two-second frames every ten seconds at 1%. All radio figures remain calculated/simulated.

## C. Three-minute recorded-source walkthrough

| Step | Action | Explain |
|---|---|---|
| 1 | Show both station feeds and the inactive third-slot status | “Real recorded footage, not live airborne cameras; two active inputs and a third configured inactive slot. No camera hardware is attached in the laptop fallback.” |
| 2 | Open a “Smoke suspicion” card and play its clip | “A consistent smoke suspicion saves evidence; this is not confirmed fire.” |
| 3 | Confirm or reject that specific card | “The operator annotates the suspicion.” Queue arrivals are deferred while pointer or focus is inside; the new-record notice means pending arrivals will appear after leaving the queue. Use **Change** to correct a decision. |
| 4 | Show ground with the Wi-Fi switch **off** | “The original remote view contains only received packet data: approximate whole-degree direction, confidence, camera/source and decisions. No imagery over LoRa.” Decision updates also wait for a legal slot. |
| 5 | Expand link details | “Version-2 smoke alerts are 42 bytes, status 40, flame/decision 37. At demo SF7 airtime is about 82–87 ms, calculated. The sender obeys a 36 s rolling-hour budget and announces the expected contact window.” |
| 6 | Enable **Show Wi-Fi demo** | Point to **Imagery & evidence · Wi-Fi only** and its note: “Images and clips are not carried by LoRa.” Untick it and show imagery disappears; expand **Camera feeds · Wi-Fi** only when showing the separate feeds. |
| 7 | Open placement map | “These hectare figures are simulated geometric visibility over real terrain/canopy, not optical detection range.” The simulation label sits beside the figures. |
| 8 | Change Haukilahti heading 180° → 0°, then restore | Compare the changed simulated visible forest; use Recalculate both sites if an edit is still pending. |
| 9 | Compare/select camera pairs | Explain which two of three mounted cameras to connect. Rounded-zero priority values have empty bars and no arbitrary Best badge. |

The compass demo uses configured module heading **0°**, independently of placement's candidate heading. Say so when comparing screens: placement is a launch-planning simulation, not telemetry from this particular station configuration.

## D. Optional extensions

### Local flame-sensor simulation, with working authentication

In a fourth terminal, from `station/` (macOS zsh):

```sh
ACORN_BASE_URL=http://127.0.0.1:18091
read -s 'ACORN_PANEL_SECRET?Station secret: '; export ACORN_PANEL_SECRET; echo
ACORN_COOKIE_JAR=$(mktemp); chmod 600 "$ACORN_COOKIE_JAR"
uv run --offline --frozen python -c 'import json,os; print(json.dumps({"secret":os.environ["ACORN_PANEL_SECRET"]}))' | \
  curl --fail-with-body -sS -c "$ACORN_COOKIE_JAR" -X POST "$ACORN_BASE_URL/api/auth/login" \
    -H 'Content-Type: application/json' --data-binary @-
curl --fail-with-body -sS -b "$ACORN_COOKIE_JAR" -X POST "$ACORN_BASE_URL/api/mcu/simulate" \
  -H 'Content-Type: application/json' -d '{"flame":true}'
# Wait about one second for debounce; this is a separate sensor event, not camera confirmation.
curl --fail-with-body -sS -b "$ACORN_COOKIE_JAR" "$ACORN_BASE_URL/api/events?kind=flame_sensor"
# Release; the red logical LED state holds briefly before returning to station state.
curl --fail-with-body -sS -b "$ACORN_COOKIE_JAR" -X POST "$ACORN_BASE_URL/api/mcu/simulate" \
  -H 'Content-Type: application/json' -d '{"flame":false}'
rm "$ACORN_COOKIE_JAR"
```

Expected: a separately labelled local short-range sensor trigger and simulated LED state. Ground receives it at a legal slot, not necessarily within two seconds. If 401 occurs, repeat login after a station restart; 429 means wait five minutes after failed logins; 409 means the station uses real/router or off mode and simulation is deliberately unavailable.

### Real radio (Meshtastic), only after a bench test

- The jury demo stays on the simulated LoRa transport unless the Meshtastic bench test in [station/LORA_HARDWARE.md](station/LORA_HARDWARE.md) passed that day with two radios. The Meshtastic transport is implemented and tested against a fake interface only; it has never run on hardware.
- With two radios, plug in the ground node and show the label change from "radio absent" to "radio connected", then one smoke suspicion arriving. Say that range and reliability were not measured.

### Collect full evidence when in range

On a received **smoke** alert, press **Collect evidence over Wi-Fi**. Its saved-evidence marker becomes visible on the alert, even with imagery off. **View saved evidence · Wi-Fi** selects it and enables the bounded viewing area; the evidence names its alert time and UUID. Reload restores the newest collected alert. Flame alerts have no direction/media buttons. Collection fetches only that received event UUID, checks station identity and saves locally. Stop the station: saved JPEG/WebM remain accessible with the demo view enabled, while live Wi-Fi feeds fail honestly.

### Camera-dropout demonstration on Mac

In `station/`, while using this same config:

```sh
uv run --offline --frozen forest-station --config stage.local.toml unplug centre
# Show reduced coverage; left continues. Then restore:
uv run --offline --frozen forest-station --config stage.local.toml replug centre
```

This is a recorded-file dropout simulation. It is not a verified USB unplug on the board.

### Silence, language and priority area

- Stop station. Ground first shows the advertised **calculated duty-cycle wait**; after the window +5 s it becomes stale, then lost after the configured grace. With the 12 s demo slot the advertised window is 15 s; ten seconds is only the minimum, not a reason to label legal silence as loss. A stopped station still eventually becomes lost.
- Toggle Turkish on ground/placement: approximate directions use whole degrees, confidence is `%54`, the simulated transport label is translated, and negative angles use `−`.
- Draw a priority polygon around Nuuksio. The headline and pair bars use priority forest. Haukilahti may legitimately show no visible priority forest; empty bars and no Best badge are expected. Clear the polygon afterwards.
- Three-camera reference changes both sites for comparison only; it is not an achievable three-input station mode. Restore the two-input setting afterwards.

## E. Hardware truth and fallbacks

The team has run station on a **real Arduino UNO Q using recorded clips and subsequently two live USB cameras**, with the MCU bridge, KY-026 responding and the **on-board status LED** following station state. This is separate from the laptop rehearsal. See `firmware/BOARD_NOTES.md` for dated bring-up and ongoing measurements. Board timing and resource use were measured at inputs 192, 320, 416 and 640 with two live cameras after the USB bandwidth fix. Automatic startup and orderly power-cycle recovery were verified; the later direct Wi-Fi bind was not power-cycle tested. The controlled timing curve used confidence 0.35; the exact field profile at 0.25 remains unmeasured. AP mode, the external RGB LED and any real LoRa radio remain unverified. Mac timing figures remain Mac measurements; reduced-resolution experiments do not validate detection accuracy.

For a future ranger AP demonstration, follow the explicitly unverified NetworkManager procedure in `station/README.md`; do not present AP mode as tested. No board or firmware change is required for this laptop runbook.

If a service hangs, stop and restart that terminal; decisions and accounting persist. If a port is busy, use a free port and update matching settings. If Wi-Fi evidence fails, check the fixed station URL/secret and close-range reachability, then keep showing the packet-only view. If an old exhausted ledger is waiting, show its reported legal recovery time or the prepared screenshots; never delete accounting to manufacture airtime. Under genuine high alert rates, acknowledge that a small legal link queues messages.

Stop every started server with Ctrl+C afterwards. Remove private cookie jars. Keep or archive local evidence as needed. Generated data remains in ignored per-project folders; no credentials belong in this file or the public repository.
