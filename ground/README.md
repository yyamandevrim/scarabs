# ACORN ground receiver

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="../assets/brand/acorn-wordmark-white.svg">
    <img src="../assets/brand/acorn-wordmark-black.svg" width="400" alt="ACORN">
  </picture>
  <br>
  Aerial Canopy Observation and Reporting Node
</p>

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

`--stale-after` defaults to 660 seconds and `--lost-after` to 1200 seconds, suitable for a five-minute status period with missed packets. Stale/lost are based on **local receipt age**, independent of the station clock. Version-2 packets announce a calculated next-contact window. Ground labels silence inside that window as a calculated duty-cycle wait and raises its effective stale threshold to at least window +5 s; lost follows after the configured grace. A ten-second minimum cannot override the legal SF12 interval. Unannounced version-1 packets use only the configured thresholds; remaining budget alone cannot prove the current cause of silence. Existing alerts remain historical evidence, not a current all-clear. A newly received packet restores the recent state.

## Explicit Wi-Fi paths

**Show Wi-Fi demo** is off at each ground process startup. Enabling it reveals a bounded amber area headed **“Demo only: shown over Wi-Fi, not available over LoRa.”** Only that area shows station camera frames and previously collected evidence. The ground backend logs into the fixed configured station origin with the supplied environment secret, keeps the station session in memory and proxies imagery over Wi-Fi; credentials never reach the ground browser. Disabling the switch removes the media elements and blocks all media-serving endpoints, including cached imagery. This switch is shared by tabs of this single local receiver process.

**Collect evidence over Wi-Fi** is a separate, explicit action on an alert already received over LoRa. Walk into station Wi-Fi range and join its AP (see station docs), then press it. The receiver checks the Wi-Fi station's ID, fetches `/api/events/FULL_UUID`, requires the returned UUID to match exactly, and saves only that event's snapshot and clip. It never downloads the station's event list or turns Wi-Fi events into LoRa alerts. Repeat if a clip is still encoding or temporarily unavailable. A missing/expired event returns an error rather than a substitute image.

Each received smoke alert shows its saved-evidence availability even with demo off. Reload selects the most recent collected alert; “View saved evidence · Wi-Fi” opens it in the labelled demo area with its event time and UUID. Flame alerts offer neither direction nor media collection. Files and a manifest stay under `data/evidence/STATION_ID/EVENT_UUID/`, independent of station retention and restart. The packet journal and local acknowledgements stay in `data/ground.sqlite3`. Enable the demo area to view saved evidence offline; file copies can also be opened directly from the local data directory. JPEG and WebM display inline; legacy AVI is download-only. Media filenames are checked against the exact UUID and expected extension. The station URL is a startup setting, not a browser-supplied proxy URL. Storage is event-based, with no automatic ground retention yet; manage the local data directory after archiving evidence.

## Sustainable demo on Mac

Use the root [DEMO.md](../DEMO.md) as the single step-by-step runbook. `station/demo-lora.toml` is ready to copy: real recorded smoke/fog clips, simulated transport, SF7/BW125/CR4/5, strict 1% duty, requested four-second heartbeat. Transmissions are legally paced into 12-second slots throughout the hour; alerts beat heartbeats. Start and rehearse at any time: a fresh ledger or “one minute before going on” workaround is not needed.

Match ground with `--sf 7`. SF10 uses 61-second slots and SF12 241-second slots at the same duty limit; these also sustain contact, with longer alert latency/backlogs. Every packet carries the calculated next-contact window. Ground displays a bounded scheduled wait, then stale/lost if the station misses that deadline. Stop the station and wait for the effective deadline shown by its latest packet; a fixed ten-second failure assertion would contradict a legal long-range schedule.

`archive-events` clears/archives the review list while preserving the ledger. An already-exhausted **old** burst ledger must wait for its airtime to expire; authenticated station `/api/communication` exposes the calculated earliest legal TX. Clearing it would be a regulatory bypass, so no reset-ledger shortcut is provided. New pacing persists across restarts.

The regression simulation runs three hours each at SF7, SF10 and SF12 with a new recorded suspicion every 55 s and four-second heartbeat requests, checking every rolling hour and maximum silence. See [traffic-verification.json](traffic-verification.json) for calculated figures, not measured RF results. Loss remains configurable and cannot be promised away.

## Verification

```sh
uv run --offline --frozen pytest -q
cd ../station
uv run --offline --frozen pytest -q
npm ci --ignore-scripts
node --test tests/panel.test.mjs
node --test ../ground/tests/dashboard.test.mjs
```

Tests cover the binary boundary, CRC rejection, bearing projection, airtime vectors, rolling accounting, sender priority/repeats, UDP byte identity, de-duplication/gap repair, receipt-age states, auth sessions/lockout/fail-closed setup, off-by-default demo API gating and exact-ID offline evidence collection. The station has run on a real UNO Q with recorded clips and subsequently two live USB cameras, the MCU bridge, responding KY-026 and on-board status LED. Demo-profile inference speed was measured; AP mode, external RGB LED and real LoRa radio remain unverified; see [BOARD_NOTES.md](../firmware/BOARD_NOTES.md) for bring-up measurements and validation limits. Screenshots and the separate-process run observations are recorded in `VERIFICATION.md` after the local run.

Version 2 frames are 37–42 bytes; old version-1 journals remain readable. Bearings display whole approximate degrees, Turkish uses %54 and translated transport/status/controls. Local saved-evidence metadata is explicitly separate from packet-derived operational data and causes no station HTTP request.
