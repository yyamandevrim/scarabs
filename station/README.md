# Portable forest observation station

Offline smoke-suspicion prototype for the Green European Renaissance hackathon. Python 3.11+, `uv`, OpenCV headless, ONNX Runtime CPU, FastAPI, plain local HTML/CSS/JS, and SQLite. No PyTorch, GPU, Jetson, cloud inference, CDN, external fonts, LoRa, or solar implementation.

**The two-input requirement is applied.** Three cameras remain physically mounted: `left` −70°, `centre` 0°, `right` +70°. Each slot has an `active` flag. Any pair can be selected; the default is **left + centre**. Three active slots are rejected with `At most two camera slots may be active; the board has two usable inputs`. Only active slots create capture workers or receive inference. The inactive slot reads **“takılı, bağlı değil”**; a failed active source reads **“bağlantı koptu”**.

## Cold start on Mac

Run these from a terminal. Internet is required for initial dependency/model/media downloads only. Install `uv` first if needed using its [official installer](https://docs.astral.sh/uv/getting-started/installation/):

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
# Open a new terminal after installation.
cd station
uv sync --locked --python 3.11
uv run python scripts/fetch_model.py
uv run python scripts/fetch_footage.py
uv run --offline --frozen pytest -q
uv run --offline --frozen forest-station --config config.toml serve --port 8080
```

Open **http://127.0.0.1:8080**. The two default sources are actual recorded wildfire and fog videos, played at their original frame rates and analysed at a target of once per second per active camera. The right slot stays mounted/inactive. Stop with Ctrl+C. Saved decisions survive restart. All config paths resolve relative to the TOML file, independent of the shell's working directory.

The project has its own `.python-version`, `pyproject.toml`, `uv.lock`, and `.gitignore`. `models/`, `media/`, `data/`, virtual environments, and local config overrides are excluded from git. Nothing needs to be fetched while serving. A cold clone must run the fetch scripts before the real-video tests; those tests explicitly skip if assets are absent, rather than substituting generated footage.

## Cold start on UNO Q Linux

These are instructions for the board's **ARM64 Debian Linux side**, not its microcontroller. The hardware installation and performance remain unverified.

```sh
sudo apt-get update
sudo apt-get install -y curl ca-certificates v4l-utils libglib2.0-0
curl -LsSf https://astral.sh/uv/install.sh | sh
# Open a new shell, then enter the copy of this repository on the board:
cd /path/to/junction/station
uv sync --locked --python 3.11
uv run python scripts/fetch_model.py
uv run python scripts/fetch_footage.py
uv run --offline --frozen pytest -q
uv run --offline --frozen forest-station --config config.toml serve --host 0.0.0.0 --port 8080
```

Copy the downloaded `models/` and `media/` directories to the board instead of fetching again if desired. Install Linux dependencies on Linux: do not copy the Mac `.venv`. `--host 0.0.0.0` permits a browser on the station's local network to connect to `http://BOARD_LOCAL_IP:8080`; a local display can use `127.0.0.1`. The default host is loopback. The prototype has no authentication, so expose it only on the intended local demo network.

### Map USB cameras to mounted slots

```sh
v4l2-ctl --list-devices
ls -l /dev/v4l/by-path/ /dev/v4l/by-id/
# Inspect each persistent capture endpoint and its supported formats:
v4l2-ctl --device /dev/v4l/by-path/YOUR_CAMERA-video-index0 --list-formats-ext
sudo usermod -aG video "$USER"
# Log out and back in if group membership changed.
```

Copy `config.toml` to `usb.local.toml`. Set exactly the intended two slots to `active = true`. For each active USB slot, set:

```toml
kind = "usb"
source = "/dev/v4l/by-path/YOUR_PHYSICAL_PORT-video-index0"
width = 1280
height = 720
```

Use a real persistent path from `ls`, not the placeholder. `/dev/video0` and numeric indices are rejected. `by-path` binds a physical USB port and helps with identical cameras without serial numbers; `by-id` is also accepted when stable unique device IDs exist. Choose the capture endpoint, not a metadata endpoint. Physically label each camera/port and inspect its feed to verify that left/centre/right match the mounting. The application asks the driver for the configured resolution; hardware may negotiate another size, and the frame is resized to the configured working resolution.

```sh
uv run --offline --frozen forest-station --config usb.local.toml serve --host 0.0.0.0
```

Switching the active pair requires a config edit and restart. Yaw, tilt, horizontal/vertical FOV and resolution are mounting/configuration metadata, not measured calibration or geographic smoke coordinates. FOV defaults are placeholders to replace with the actual camera calibration.

## Detection and event behaviour

- Each active input has an independent capture thread, a single replaceable latest raw frame and no raw-frame queue. Files and USB inputs use the identical preprocessing, shared detector, alarm, evidence and storage path. File playback is paced in wall-clock time; live USB capture continuously drains frames.
- One model instance uses only `CPUExecutionProvider` and processes active cameras in turn. Default target: **1 analysis/second/camera**, 640 × 640 letterboxed RGB float32 input, confidence ≥ 0.35, two ORT CPU threads, NMS IoU 0.45. Rate, input size, confidence and CPU threads are configurable. The official dynamic export also accepts 1024 input, its training image size; 640 is the demonstrated starting setting.
- A candidate box must overlap a detection in at least **3 of the last 5 analyses on the same camera**. Overlap means normalized original-image box **IoU ≥ `similarity_iou`**, default 0.25, relative to the current candidate. Multiple boxes in one analysis count as one vote. Empty analyses count as misses. Three successes can open an event before the first five analyses are complete. Disconnection and long analysis gaps reset voting history.
- Subsequent overlapping detections extend that open event, updating `last_seen`, box and confidence while preserving the operator decision. Unrelated regions can open separate events. An event closes after `event_timeout` seconds without a matching detection, default 12 seconds. Smoke returning after closure can create a new event. Old open events are closed on process restart.
- Capture failure clears the latest frame, marks the active slot disconnected, and retries after `retry_seconds`, default 2 seconds. Frames older than `stale_seconds` are not analysed or displayed. The other active capture worker and shared inference loop continue. Inactive slots never attempt to open their sources.
- A bounded in-memory JPEG ring (default 640px wide, 5 fps) retains recent context; it is not written continuously. An event saves an annotated JPEG immediately and a short **MJPEG AVI**, normally up to 4 seconds before plus 4 seconds after opening. Early-start events have less pre-roll; loss/shutdown can shorten post-roll. Clip sampling uses capture timestamps. The clip captures initial event context; extensions update the event row, not an indefinitely growing movie. AVI is downloadable for playback in a compatible player; it is not presented as browser-native video.
- Event records live in `data/events.sqlite3` (SQLite WAL). Media lives in `data/events/`. Records include camera, opening/last-seen/closure timestamps, normalized `xyxy` box, confidence, media paths, operator decision and decision timestamp. Snapshot geometry corresponds to the opening detection; the row's box/confidence track the latest detection. Media failures appear in the event metadata. A single bounded encoder worker saves clips without blocking capture/inference; overload records an explicit missing-clip error.
- Retention, default 7 days since `last_seen`, removes expired event rows and imagery on startup and approximately once per minute. Old orphaned evidence from a crash is pruned too. The compressed context ring is memory-only and bounded; saved imagery is event-based.
- The panel polls local JPEGs and JSON once per second. The two active feeds share the observation area; the mounted inactive slot is a single status row. Pending **“Duman şüphesi”** records appear beside the feeds on desktop and above them on phones. The operational bar counts decisions still awaiting review, including closed observations. An open observation marks its source feed in amber. Recorded file sources are labelled **“Kayıtlı demo”**; actual runtime figures stay labelled **“Ölçülen”**. **Doğrula** and **Reddet** persist operator decisions; decided rows show the decision and time, with **Değiştir** to correct it. Camera loss raises a reduced-coverage warning. Server loss replaces stale frames, figures and the decision list with unavailable/loading states until recovery. A same-origin content-security policy prevents external panel assets and connections.

### Optional LED hook

`station/led.py` defines `LedHook.set_alarm(enabled)`. With no `led_path`, it is a no-op. If configured, it writes `1`/`0` to a Linux LED brightness file; a missing/unwritable path disables the hook without stopping detection. No UNO Q MCU bridge or physical LED control has been verified. A board-specific adapter can implement the same interface later. LoRa and solar are omitted.

## Model provenance and licence

The actual tested model is the ready-made **Pyronear YOLO11s wildfire-smoke detector**, current repository release **Tenacious Tiger v8.3.0** when inspected on 2026-11-13. It was not retrained, converted locally or replaced with another vendor's model.

- Model card: https://huggingface.co/pyronear/yolov11s
- Pinned repository revision: `de398b5192b2c1d5f8963aef56bf8df1f13c159e`
- **Exact downloaded export URL:** https://huggingface.co/pyronear/yolov11s/resolve/de398b5192b2c1d5f8963aef56bf8df1f13c159e/onnx_cpu.tar.gz
- Archive SHA-256: `31b00117575defe6ef2212ac747f1c24b7605211850cd7cf43f11bfd8ca22a7c`
- Archive member: `./best.onnx`; installed as `models/smoke.onnx`.
- **ONNX file SHA-256:** `5c17b5f917b3cd61bafd15b808cbe3c3b03e054e2e9f09ca72f6309d53d8e76b`
- **Licence: AGPL-3.0**, as stated in the current pinned repository, [licence file](https://huggingface.co/pyronear/yolov11s/blob/de398b5192b2c1d5f8963aef56bf8df1f13c159e/LICENSE). Its source-availability obligations apply to use/distribution; the current model card explains its Ultralytics ancestry. Older search-index claims of Apache-2.0 were not used.

`fetch_model.py` verifies the archive and extracted file, reads only the expected archive member, and never loads pickle/PyTorch. The tested export has dynamic input dimensions and a single-class `[1,5,anchors]` output; its class metadata says `item`. Letterboxing, RGB conversion, confidence filtering, NMS and original-frame coordinate mapping are implemented locally and tested.

An initially investigated `pyronear/yolov11n` CPU archive at revision `11bfef8c62f3f1c1f6ce6426a441b1208ba437b2` actually described COCO's 80 classes and `[1,84,anchors]`. It was rejected. The loader explicitly rejects multi-class exports, rather than silently labelling ordinary objects as smoke.

## Real footage, attribution and licences

All downloaded files are real videos, **not synthetic smoke**. `footage.json` contains direct download URLs, original file-page links, authors, licence links, SHA-256 hashes and change notes. The fetcher verifies all four hashes. The originals remain unmodified; capture ignores audio. Annotated snapshots and derived event clips inherit the applicable media attribution/share-alike obligations when redistributed.

| Local file | Source / author | Licence | Purpose |
|---|---|---|---|
| `media/smoke.ogv` | [Wildfire Near Monserrate](https://commons.wikimedia.org/wiki/File:Wildfire_Near_Monserrate.ogv), Peter Angritt / Mrtony77, 2015 | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) | Actual hillside wildfire smoke, about 54 seconds |
| `media/fog.webm` | [Fog covering mountain time lapse](https://commons.wikimedia.org/wiki/File:Fog_covering_mountain_time_lapse.webm), Athulvis | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) | Fog over mountains, about 46 seconds |
| `media/cloud.webm` | [Angeles National Forest from Mount Wilson](https://commons.wikimedia.org/wiki/File:Angeles_National_Forest_from_Mount_Wilson.webm), Tom Hawkins | [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) | Clouds across mountain landscape, about 33 seconds |
| `media/glare.webm` | [CostaRica Cow close up shot great lens flare](https://commons.wikimedia.org/wiki/File:072014_CostaRica_Cow_close_up_shot_great_lens_flare.webm), Michael Weinman | [CC BY-SA 2.0](https://creativecommons.org/licenses/by-sa/2.0/) | Sunlight/overexposure/lens-flare negative in a barn, about 41 seconds; not a forest-camera view |

The fog source page asserts the uploader's CC BY-SA 4.0 licence but also has a pending external licence-review notice; that provenance caveat is retained here. Wikimedia initially returned HTTP 429 for the glare video; a later retry succeeded and its actual bytes are now hash-pinned. Synthetic, uniformly coloured videos appear only in unit tests for capture mechanics, and are never reported as real smoke footage.

## Offline demo sequence

1. Complete dependency and model/media downloads. Keep `left` and `centre` active, `right` inactive. Stop any previous server.
2. Disconnect the station's internet uplink (Wi-Fi can remain on a local network if another device is viewing). Start with `uv run --offline --frozen forest-station --config config.toml serve` and open `http://127.0.0.1:8080`.
3. Show the **two** active feeds and the right mounted/inactive slot. The smoke source starts at a visible plume; an event should open after roughly three analyses. Show “Duman şüphesi,” the highlighted snapshot, the local clip and measured analysis times.
4. Choose **Doğrula** or **Reddet**. Restart the server and show that the decision remains. The repeating clip can produce another event after the first smoke disappears long enough to close; this is expected.
5. Fog is the default negative. To compare cloud or glare, stop the server, make a `negative.local.toml` copy, change only `cameras.centre.source` to `media/cloud.webm` or `media/glare.webm`, and restart with `--config negative.local.toml`. Keep only two active flags.
6. **On the board:** unplug one of the two active USB cameras. Its slot must say “bağlantı koptu”; the other active feed keeps processing, and the third remains “takılı, bağlı değil.” Reconnect the same port and watch retry recovery. This physical step has not been tested without the board.
7. **On the Mac:** the real-video integration test stops one capture worker and checks that the other continues. For an interactive unreadable-file/retry demonstration, rename `media/smoke.ogv` to `media/smoke.ogv.disabled` while serving. The already-open file can play until EOF (up to 54 seconds); after that, the left slot loses its source while fog continues. Rename it back to restore capture. Do not run the footage fetcher while it is renamed.

## Tests and measured Mac results

```sh
cd station
uv run --offline --frozen pytest -q
# Core/unit/API tests without large media:
uv run --offline --frozen pytest -q -m 'not integration'
# Real model + real videos, with socket connections forbidden by the test:
uv run --offline --frozen pytest -q -m integration
```

Panel state tests use Node 20+ and a development-only DOM implementation. They do not add any browser/runtime dependency or external panel requests. From `station/`, install once, then run offline:

```sh
npm ci --ignore-scripts
npm test
```

These tests cover loading, recorded/live labels, pending counts, source highlighting, both decisions and correction, failed writes, focus preservation during polling, camera/analysis failure, server loss and recovery, and different active pairs.

Verification on **Apple M5, ARM64 Mac, macOS 27.0.1, Python 3.11.15**, CPUExecutionProvider only. The suite includes 38 unit/API cases and 3 real-video integration cases: smoke paired separately with fog, cloud and glare. It covers three-of-five voting with misses and unrelated regions, configurable similarity, extension/expiry, latest-frame replacement, camera failure and retry, unaffected second camera, inactive slots, all active pairs, max-two validation, persistence of both decisions, retention of rows/media, preprocessing geometry/RGB/NMS, wrong-model rejection, local assets, and HTTP endpoints.

The actual uvicorn server was also run on this Mac with smoke + fog for 98 analyses per camera. A smoke event was observed, evidence downloaded over HTTP and decoded, and a confirmation persisted. The browser loaded both active feeds, three slot cards, the event list and the inactive message with **zero external resource requests and zero console errors**. Measured analysis rates near the end were 1.00/s left and 0.99/s centre. Internet was not physically disabled on the host; the end-to-end tests explicitly forbid socket connections, and the browser audit checks same-origin-only requests.

Benchmark the identical detector on either machine:

```sh
uv run --offline --frozen forest-station --config config.toml benchmark media/smoke.ogv --frames 60 --stride 25
uv run --offline --frozen forest-station --config config.toml benchmark media/fog.webm --frames 60 --stride 30
uv run --offline --frozen forest-station --config config.toml benchmark media/cloud.webm --frames 60 --stride 24
uv run --offline --frozen forest-station --config config.toml benchmark media/glare.webm --frames 60 --stride 30
```

`--stride` selects decoded frames; the values above sample approximately once per video second. Video decoding is outside the preprocessing timer. Three warm-up inferences are excluded. JSON output gives per-frame mean/p50/p95 preprocessing, inference and total analysis time, sample counts and detection/voting counts. `alarm_positive_frames` counts sampled analyses satisfying the three-of-five rule, not distinct events.

Measured smoke benchmark (640 input, confidence 0.35, two ORT threads, 54 samples): **preprocessing mean 0.61 ms**, **inference mean 57.74 ms / p50 59.22 ms / p95 65.56 ms**. These are **Mac measurements only** and establish nothing final about UNO Q throughput, thermals or power.

At approximately 1 Hz across each complete downloaded video: smoke detected in **24/54** samples with **19** analyses satisfying spatial three-of-five; fog **0/46**, cloud **0/34**, and glare **0/42** detections. The smoke clip produced a real local event. These small selected clips do not establish field sensitivity or false-alarm rates. The barn glare video is especially limited as a forest-domain negative. Raw measurements and local HTTP/browser audit notes from this run are under gitignored `data/verification/`.

## HTTP API

- `GET /api/status`: three slots, active/connected states, geometry and per-active-camera measurements.
- `GET /api/cameras/left/frame.jpg` (also `centre`, `right`): latest annotated frame; 503 when disconnected, 404 when inactive.
- `GET /api/events`: newest 200 events, title, timestamps, normalized box, confidence, media names, decision.
- `POST /api/events/EVENT_ID/decision` with JSON `{"decision":"confirmed"}` or `{"decision":"rejected"}`; invalid values return 422, unknown IDs 404.
- `GET /events/GENERATED_FILENAME.jpg` or `.avi`: local event evidence; arbitrary filesystem paths are not served.

## Known issues and unverified work

- No UNO Q or real USB cameras were available: ARM64 Debian installation, persistent-device mapping, physical unplug/replug, actual two-input bandwidth, measured board performance, memory/thermal limits and MCU/LED behaviour remain unverified. The same Python path is implemented for Linux USB capture, with a default no-op LED hook.
- The Mac camera-loss check is a software simulation. V4L2 driver-specific blocking/hanging behaviour cannot be established here; a frame-age watchdog marks stale feeds disconnected, but a driver stuck forever inside `read()` may need process/driver recovery on real hardware.
- No physical internet switch-off was performed. Runtime network independence is checked by denied-socket integration tests and the browser's local-only request audit. The initial downloads require internet.
- Event AVI clips are downloadable and OpenCV-decodable; browsers generally need a separate compatible player. Evidence can have shortened pre/post context at startup, loss or shutdown. No audio is saved.
- SQLite and media are local; abrupt power loss can leave incomplete evidence. Startup closes previously open events and retention eventually removes orphan files. There is no disk quota beyond age-based retention.
- The model/threshold and mounting FOV are demo settings. Detection is suspicion support requiring operator review, not a validated autonomous emergency system.
- The installed Starlette TestClient emits one upstream `httpx` deprecation warning; tests still pass. No failing test is hidden or filtered.
