# ACORN ground receiver

The original remote dashboard is **LoRa-only**. It is a separate FastAPI process on the operator laptop. Its operational state is decoded only from packet bytes received by **LoRa link (simulated transport)**. It neither reads the station database nor calls its API during normal viewing. The compass shows approximate directions from a configured heading, yaw and FOV; no fire location or distance is measured.

English is the default; the top-right button switches to Turkish and remembers that language. Fonts and every other asset are local. No model, capture worker or inference runtime is started in this process. The local `forest-station` dependency supplies the shared codec/transport modules; its Python dependencies are installed, but detection modules are not imported by the receiver.

## Run

From the repository root, after station model/recorded media preparation:

```sh
cd ground
uv sync --locked --python 3.11
uv run --offline --frozen pytest -q
# Optional: set only if using explicit Wi-Fi demo/evidence collection.
read -s 'ACORN_STATION_SECRET?Station panel secret: '; export ACORN_STATION_SECRET; echo
uv run --offline --frozen acorn-ground --port 8092 --udp-port 9901 \
  --station-url http://127.0.0.1:8091
```

The secret-entry example uses macOS zsh (for bash use `read -rs -p 'Station panel secret: ' ACORN_STATION_SECRET`). Use the same secret configured on the station; never put it in a command argument, URL or committed file. Leave it unset for a packet-only receiver. HTTP and UDP default to loopback; the ground app is a local laptop application without a remote multi-user login. Keep its HTTP server bound to loopback. For two-machine simulation, set `--udp-host` to the laptop's private LAN address and station `lora.peer_host` to that same address; UDP/9901 must be allowed on that private network. This is still simulated transport, with no radio hardware involved.

Open **http://127.0.0.1:8092**. The station serves on **8091**, never the existing 8080/8787 demo ports. Start the receiver before the station so the first packets are heard. Set `[lora] enabled = true` in an ignored station `*.local.toml`, then run the station as described in its [Communication section](../station/README.md#communication).

The radio calculator defaults to SF10, BW125000, CR1 (4/5). Match station settings with `--sf`, `--bandwidth` and `--coding-rate`. See [the complete packet specification and airtime table](../station/station/lora/PACKETS.md). `--transport serial --serial-port DEVICE` selects the serial skeleton and deliberately raises `NotImplementedError` until a modem is selected and implemented. Both adapters feed the same receiver; transport labelling follows the adapter, without dashboard changes.

## What the operator sees

With the switch off, there are **no `<img>` or `<video>` elements, frame requests, evidence media requests or automatic station HTTP calls**. The compass and alert queue contain station ID, received time, camera, approximate bearing, box dimensions, model confidence, source marker and station decision as actually carried in packets. Local flame-sensor triggers have a separate label and no fabricated camera/bearing/confidence. Camera sectors/status, uptime and pending total require a status packet; they are unknown before one arrives. Battery is not measured.

Link details expand to received packet count, provisional sequence gaps, duplicate datagrams, last packet size, calculated time-on-air and sender-calculated remaining duty budget at the latest TX. The receiver cannot know later transmissions it did not hear, so this is not live available airtime. RSSI/SNR and battery percentages are absent. Acknowledging an alert persists locally and does not contact or change the station.

`--stale-after` defaults to 660 seconds and `--lost-after` to 1200 seconds, suitable for a five-minute status period with missed packets. Stale/lost are based on **local receipt age**, independent of the station clock. They mean silence; duty refusal, radio loss or a stopped station can all cause it. Set thresholds in relation to the chosen heartbeat/repeat policy. Existing alerts remain historical evidence, not a current all-clear. A newly received packet restores the recent state.

## Explicit Wi-Fi paths

**Show Wi-Fi demo** is off at each ground process startup. Enabling it reveals a bounded amber area headed **“Demo only: shown over Wi-Fi, not available over LoRa.”** Only that area shows station camera frames and previously collected evidence. The ground backend logs into the fixed configured station origin with the supplied environment secret, keeps the station session in memory and proxies imagery over Wi-Fi; credentials never reach the ground browser. Disabling the switch removes the media elements and blocks all media-serving endpoints, including cached imagery. This switch is shared by tabs of this single local receiver process.

**Collect evidence over Wi-Fi** is a separate, explicit action on an alert already received over LoRa. Walk into station Wi-Fi range and join its AP (see station docs), then press it. The receiver checks the Wi-Fi station's ID, fetches `/api/events/FULL_UUID`, requires the returned UUID to match exactly, and saves only that event's snapshot and clip. It never downloads the station's event list or turns Wi-Fi events into LoRa alerts. Repeat if a clip is still encoding or temporarily unavailable. A missing/expired event returns an error rather than a substitute image.

Files and a manifest stay under `data/evidence/STATION_ID/EVENT_UUID/`, independent of station retention and restart. The packet journal and local acknowledgements stay in `data/ground.sqlite3`. Enable the demo area to view saved evidence offline; file copies can also be opened directly from the local data directory. JPEG and WebM display inline; legacy AVI is download-only. Media filenames are checked against the exact UUID and expected extension. The station URL is a startup setting, not a browser-supplied proxy URL. Storage is event-based, with no automatic ground retention yet; manage the local data directory after archiving evidence.

## Side-by-side demo sequence on Mac

1. Prepare all dependencies, real recorded smoke/fog clips and ONNX model in advance. Use an ignored station config with a fresh disposable `data_dir`, two active cameras, `lora.enabled = true`, `heartbeat_seconds = 4`, `repeat_seconds = 5`, matching UDP/9901 and default SF10/1% budget. This compressed heartbeat is for a short demo only, not sustained field operation.
2. In terminal A start ground with `--port 8092 --stale-after 10 --lost-after 20`. In terminal B export `ACORN_PANEL_SECRET` and start `forest-station --config communication.local.toml serve --port 8091`. Use separate data directories from other running demos.
3. Put the ground page and authenticated station ranger panel side by side. Show the suspected-smoke alert arriving over UDP: the ground compass has a bearing and confidence, with **no imagery**. The station panel has both full recorded feeds, snapshot/clip and decisions. The recorded-source marker on the LoRa alert is explicit.
4. Turn **Show Wi-Fi demo** on. Show the labelled, bounded Wi-Fi feeds. Click **Collect evidence over Wi-Fi** on the received alert and show its snapshot and WebM clip. This imagery uses HTTP on 8091 through the ground proxy, not UDP. Toggle off and verify every image/video disappears. The locally saved files remain.
5. Stop only the station with Ctrl+C. After 10 s ground says stale; after 20 s it says link lost. Enable the demo area again: live frames fail honestly, while collected evidence remains available locally. Stop ground with Ctrl+C.
6. Repeat with a **fresh disposable data directory** and `loss = 0.35`, `seed = 1`, `duty_fraction = 0.001` (a stricter-than-required test limit on the default 1% band), `heartbeat_seconds = 2`, `repeat_seconds = 3`. Leave airtime delay enabled. The rolling allowance is now 3.6 s/hour. A seeded initial packet can be lost, an alert/repeat can still arrive, queued alerts take priority and heartbeats stop when reserve headroom is insufficient. Inspect authenticated `/api/communication` for sent/refused/queued counters and ground's sequence gaps. Exhaustion delays messages; it cannot guarantee delivery through arbitrary loss. Do not erase a real station's duty ledger to repeat this experiment.
7. Stop both processes. All demonstrations above use actual recorded footage/inference on the Mac, **not a live airborne camera, real radio or UNO Q hardware**.

## Verification

```sh
uv run --offline --frozen pytest -q
cd ../station
uv run --offline --frozen pytest -q
node --test tests/panel.test.mjs
```

Tests cover the binary boundary, CRC rejection, bearing projection, airtime vectors, rolling accounting, sender priority/repeats, UDP byte identity, de-duplication/gap repair, receipt-age states, auth sessions/lockout/fail-closed setup, off-by-default demo API gating and exact-ID offline evidence collection. Serial radio, physical AP operation and UNO Q execution remain unverified. Screenshots and the separate-process run observations are recorded in `VERIFICATION.md` after the local run.
