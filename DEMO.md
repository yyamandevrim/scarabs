# ACORN — stage demo runbook

ACORN — Aerial Canopy Observation and Reporting Node. Scarabs, Junction 2026 Helsinki, Green European Renaissance challenge. This replaces the rehearsal-2 draft and its short-lived-ledger workaround.

The laptop demo uses real recorded smoke/fog footage and real on-device inference, **LoRa link (simulated transport)** over UDP, plus an explicit Wi-Fi imagery aid. No radio range, calibrated bearing, fire location, battery percentage or confirmed fire is claimed. One MicroMesh has arrived, but its physical variant/firmware and real ACORN link remain unverified; see [the hardware investigation and single-radio demo limits](station/LORA_HARDWARE.md).

| App | Purpose | Demo address |
|---|---|---|
| Station, Turkish | Full-detail ranger Wi-Fi panel: feeds, evidence, decisions | http://127.0.0.1:18091 |
| Ground, English/Turkish | Remote packet-only view; explicit Wi-Fi demo switch | http://127.0.0.1:18092 |
| Placement, English/Turkish | Simulated geometric launch-point comparison | http://127.0.0.1:18787 |

UDP is 19901 in this runbook. These ports avoid existing 8080/8787 demos. Change a port and all matching URLs/configuration together.

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

Open the three addresses above. Sign into the station panel. Ground defaults to **demo off**, English, with zero camera images/video. Leave the apps running during rehearsal; prepare a clean review list by archiving if useful, rather than resetting a budget. A smoke suspicion generally opens after a few analyses; packet delivery waits for the next legal slot, up to about 12 s without backlog. The recorded smoke loop can create another distinct suspicion about every 55 s.

For a long-range configuration use SF12 on **both** station and ground: the same 1% limit requires **241-second slots**. Ground receives the calculated contact window in every packet and shows a duty-cycle wait. Alerts have longer latency and may queue under sustained overload; no legitimate setting can carry two-second frames every ten seconds at 1%. All radio figures remain calculated/simulated.

## C. Three-minute walkthrough

| Step | Action | Explain |
|---|---|---|
| 1 | Show both station feeds and the inactive third-slot status | “Real recorded footage, not live airborne cameras; two inputs active, three mounted.” |
| 2 | Open a “Duman şüphesi” card and play its clip | “A consistent smoke suspicion saves evidence; this is not confirmed fire.” |
| 3 | Confirm or reject that specific card | “The operator annotates the suspicion.” Queue arrivals are deferred while pointer or focus is inside; the new-record notice means pending arrivals will appear after leaving the queue. Use Değiştir to correct a decision. |
| 4 | Show ground with the Wi-Fi switch **off** | “The original remote view contains only received packet data: approximate whole-degree direction, confidence, camera/source and decisions. No imagery over LoRa.” Decision updates also wait for a legal slot. |
| 5 | Expand link details | “Version-2 smoke alerts are 42 bytes, status 40, flame/decision 37. At demo SF7 airtime is about 82–87 ms, calculated. The sender obeys a 36 s rolling-hour budget and announces the expected contact window.” |
| 6 | Enable **Show Wi-Fi demo** | Point to the bounded label: “Demo only: shown over Wi-Fi, not available over LoRa.” Untick it and show imagery disappears. |
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
