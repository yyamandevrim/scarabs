# ACORN — Aerial Canopy Observation and Reporting Node

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../assets/brand/acorn-wordmark-white.png">
  <img src="../assets/brand/acorn-wordmark-black.png" width="144" height="50" alt="ACORN">
</picture>

Offline smoke-suspicion prototype for the Green European Renaissance challenge at Junction 2026 in Helsinki. Python 3.11+, `uv`, OpenCV headless, ONNX Runtime CPU, FastAPI, plain local HTML/CSS/JS, and SQLite. No PyTorch, GPU, Jetson, cloud inference, CDN, external fonts, or solar implementation. Communication now includes a compact LoRa packet layer with a simulated transport; no real radio has been tested.

The panel's English product name is defined once in `station/identity.py`. It supplies the accessible product name and page title, including alarm and connection-loss states. The panel uses Yaman’s supplied compact white wordmark; ranger sign-in uses the complete stacked logo. Both are bundled locally. See [asset provenance and usage](../assets/brand/README.md).

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
# macOS zsh; choose a local secret before starting the server.
read -s 'ACORN_PANEL_SECRET?Station secret: '; export ACORN_PANEL_SECRET; echo
uv run --offline --frozen forest-station --config config.toml serve --port 8080
```

Without a configured secret all panel data/API access fails closed; see [Communication](#communication). Open **http://127.0.0.1:8080** and sign in. The two default sources are actual recorded wildfire and fog videos, played at their original frame rates. The default **field** profile analyses each active camera at a target interval of six seconds. For a nearby-screen stage demo select `profile = "demo"` in the local configuration (or use `demo-lora.toml`). The right slot stays mounted/inactive. Stop with Ctrl+C. Saved decisions survive restart. All config paths resolve relative to the TOML file, independent of the shell's working directory.

The project has its own `.python-version`, `pyproject.toml`, `uv.lock`, and `.gitignore`. `models/`, `media/`, `data/`, virtual environments, and local config overrides are excluded from git. Nothing needs to be fetched while serving. A cold clone must run the fetch scripts before the real-video tests; those tests explicitly skip if assets are absent, rather than substituting generated footage.

## Cold start on UNO Q Linux

These are instructions for the board's **ARM64 Debian Linux side**, not its microcontroller. The station has been run on a real Arduino UNO Q using recorded clips, with the microcontroller bridge, the KY-026 responding and the on-board status LED following station state. Two live USB cameras at input 192 were measured on the board at about 278 ms inference and 0.990 analyses/s per camera; that is a throughput measurement, not a quality validation. Access-point mode, the external RGB LED and real LoRa radio remain unverified for this demo. See [the dated board bring-up record](../firmware/BOARD_NOTES.md) for ongoing hardware work and measurements; this document does not turn Mac timings into board claims.

```sh
sudo apt-get update
sudo apt-get install -y curl ca-certificates v4l-utils libglib2.0-0
curl -LsSf https://astral.sh/uv/install.sh | sh
# Open a new shell, then enter the copy of this repository on the board:
cd station
uv sync --locked --python 3.11
uv run python scripts/fetch_model.py
uv run python scripts/fetch_footage.py
uv run --offline --frozen pytest -q
# bash on the board; local secret, never committed.
read -rs -p 'Station secret: ' ACORN_PANEL_SECRET; export ACORN_PANEL_SECRET; echo
uv run --offline --frozen forest-station --config config.toml serve --host 0.0.0.0 --port 8080
```

Copy the downloaded `models/` and `media/` directories to the board instead of fetching again if desired. Install Linux dependencies on Linux: do not copy the Mac `.venv`. `--host 0.0.0.0` permits a browser on the station's local network to connect to `http://BOARD_LOCAL_IP:8080`; a local display can use `127.0.0.1`. The default host is loopback. The panel and all data APIs require the shared-secret login described under [Communication](#communication); configure it before exposing the service.

Before judging board speed, stop the server and run the smoke `benchmark` command in [Tests and measured Mac results](#tests-and-measured-mac-results) **on the UNO Q**. Published timings below are Apple M5 Mac measurements only. For the KY-026, RGB LED, sketch upload and real bridge config, follow the [complete hardware installation checklist](../firmware/README.md#install-on-the-arduino-uno-q--first-time-checklist). The checked-in `[mcu] mode = "simulated"` is a hardware-free demo; switch your board config to `router` before presenting it as hardware telemetry.

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

Use a real persistent path from `ls`, not the placeholder. `/dev/video0` and numeric indices are rejected. `by-path` binds a physical USB port and helps with identical cameras without serial numbers; `by-id` is also accepted when stable unique device IDs exist. Choose the capture endpoint, not a metadata endpoint. Physically label each camera/port and inspect its feed to verify that left/centre/right match the mounting. The application asks the driver for the configured resolution; hardware may negotiate another size. USB frames retain that actual size; file playback uses the configured working resolution.

```sh
uv run --offline --frozen forest-station --config usb.local.toml serve --host 0.0.0.0
```

Switching the active pair requires a config edit and restart. Yaw, tilt, horizontal/vertical FOV and resolution are mounting/configuration metadata, not measured calibration or geographic smoke coordinates. FOV defaults are placeholders to replace with the actual camera calibration.

### Picture quality and USB negotiation

The panel requests a new JPEG about once per second, independently of analysis.
Preview uses native capture pixels by default (`preview_width = 0`) and JPEG quality
95. A positive `preview_width` is an optional maximum; preview never upscales.
The detector creates its own letterboxed `input_size` tensor from the raw frame;
preview compression and evidence settings do not change model input or analysis cadence.

For USB cameras, `width`/`height` request capture size, `capture_format = "MJPG"`
requests camera-side JPEG compression (`"YUYV"` requests raw video), and
`capture_fps = 5` requests a low capture rate to leave CPU time for analysis.
The format/rate defaults are an empty string/zero, preserving driver defaults.
USB frames retain their actual negotiated dimensions, without artificial enlargement
or aspect-ratio changes. `/api/status` reports actual `capture_width`,
`capture_height`, `capture_format`, and measured `capture_fps`; requested dimensions
alone do not establish that the hardware accepted them. Test **both cameras together**
before selecting a format: compressed MJPG does not guarantee USB bandwidth admission.
The existing UVC quirk 128 specifically helps raw capture on the tested hub.
Negotiation and successful reads alone do not prove usable pixels: the tested
cameras returned truncated green-padded 640×480 YUYV images despite reporting that
size. Inspect saved frames from **each** source before adopting a new mode.
Capture rejects malformed arrays and the observed zero-filled-YUV green footer
before publishing frames to preview, analysis or evidence. Rejection clears the
latest frame/ring, reports a camera fault, and retries normally. This signature
guard does not detect every possible kind of image corruption.

Optional quality settings in `[station]`:

```toml
preview_width = 0
preview_jpeg_quality = 95 # integer 1–100
evidence_jpeg_quality = 95 # snapshots and compressed context-ring samples
clip_width = 1280 # maximum; never enlarges a smaller source
clip_fps = 2.0 # lower temporal rate can offset larger evidence frames
```

`clip_width`/`clip_fps` retain their general defaults of 640/5 unless overridden.
WebM clips still use the existing lossy VP8 encoder; JPEG quality governs its source
ring and snapshots, not VP8 bitrate. Larger rings and clips cost memory and encode
time. The board notes record tested settings and limits separately from Mac tests.

## Analysis profiles

Profiles are selected in the station TOML and take effect on restart. The panel reports the active configuration; it has no profile-switch button or API. `config.toml` selects `field`; `demo-lora.toml` selects `demo`.

| Profile | Model input | Confidence threshold | Target per camera | Event timeout default | Purpose |
|---|---:|---:|---:|---:|---|
| `field` (default) | 640 | 0.25 | 1/6 Hz · every 6 s | 36 s | Retain sensitivity to small, distant smoke, accepting slower analysis |
| `demo` | 192 | 0.35 | 1 Hz · every 1 s | 12 s | Nearby smoke, such as a camera looking at a screen |

The six-second field interval is within the **5–10 s** recommendation in [the input-size quality study](DETECTION_VS_INPUT_SIZE.md), option D, and now follows the validated six-second live-camera timing point in the board record. Its input-640 confidence sweep found 40/54 native smoke detections at 0.25 versus 24/54 at 0.35, with no negative detections at 0.25 on those samples. At input 192, 0.35 already had margin on the near plume, but the same smoke shrunk two to four times yielded no detections even at a 0.10 floor. Input 640 retained distant-proxy detections. No setting produced an alarm on the tested fog, cloud or glare clips. These observations support separate thresholds; they do not establish field accuracy or a false-alarm rate.

**Limits:** one real smoke clip; distant smoke was a synthetic shrinking/compositing test. Quality was measured on an **Apple M5 Mac**, not the UNO Q. The [board record](../firmware/BOARD_NOTES.md) measured input 192 with two live 320×240 USB cameras at 279.32/276.53 ms mean sampled inference and 0.990 analyses/s each over 180.7 s. These are separate speed observations, not small-smoke validation. Profiles do not alter capture sources or frame sizes.

**Board timing update, 2026-11-14:** the parallel board measurement now documents two live **320×240 YUYV** cameras at input 640 and confidence **0.35**, with 2719.54 / 2738.86 ms mean sampled inference and **0.167 / 0.167 analyses/s** over approximately 300 sampled seconds, after 30 seconds of warm-up. Six seconds per camera held the target; a 5.5-second boundary run did not. The default cadence and 36-second timeout follow that measured configuration. This is a timing result on that capture configuration, not a field sensitivity or smoke-quality validation. See [the full input-size curve and its limits](../firmware/BOARD_NOTES.md#2026-11-14-live-camera-input-size-curve--measured-on-the-uno-q).

**Pending exact field-profile validation — input 640, confidence 0.25, final camera-quality settings:** mean inference **not measured yet**; sustained per-camera analysis rate **not measured yet**. Fill these entries with a dated run and negotiated camera formats/resolutions. The controlled timing curve used 0.35 and the earlier capture snapshot; do not present it as a measurement of the exact new profile or generalise it to larger camera frames.

```toml
[station]
profile = "field" # or "demo"
# Every profile value can be explicitly overridden:
# input_size = 640
# confidence = 0.25
# analysis_hz = 0.16666666666666666
# event_timeout = 36.0
```

The spatial **3-of-5 analyses** rule is unchanged. Without an explicit override, event timeout is `max(12, 6 / analysis_hz)` seconds, matching the board curve’s six-interval timeout and retaining an open event across the full five-analysis voting window. Votes reset after a gap longer than `max(stale_seconds, 2 / analysis_hz)`; camera loss and analysis errors still reset votes. Changing the interval changes the default timeout and vote-gap limit. An explicit `event_timeout` wins; keep it at least three intervals to avoid splitting an event across two missed analyses. Actual inference may run slower than the configured target; unusually long interruptions intentionally restart voting. Shorter explicit timeouts remain supported for tests and short clips.

`GET /api/status` includes `analysis_profile` with name, effective input size, confidence, rate, interval, timeout, vote-gap limit and the 3-of-5 counts, alongside existing timing fields. Measured rates and milliseconds remain labelled with machine identity. LoRa v2 status packets stay unchanged: their fixed 40-byte layout has no profile field. Although eight bytes remain under the 48-byte ceiling, adding a field would break existing v2 length checks; the remote dashboard therefore makes no profile claim.

## Detection and event behaviour

- Each active input has an independent capture thread, a single replaceable latest raw frame and no raw-frame queue. Files and USB inputs use the identical preprocessing, shared detector, alarm, evidence and storage path. File playback is paced in wall-clock time; live USB capture continuously drains frames.
- One model instance uses only `CPUExecutionProvider` and processes active cameras in turn. Default **field** target: **one analysis every six seconds/camera**, 640 × 640 letterboxed RGB float32 input, confidence ≥ 0.25, two ORT CPU threads, NMS IoU 0.45. Rate, input size, confidence and CPU threads are configurable. The official dynamic export also accepts 1024 input, its training image size; 640 is the demonstrated starting setting.
- A candidate box must overlap a detection in at least **3 of the last 5 analyses on the same camera**. Overlap means normalized original-image box **IoU ≥ `similarity_iou`**, default 0.25, relative to the current candidate. Multiple boxes in one analysis count as one vote. Empty analyses count as misses. Three successes can open an event before the first five analyses are complete. Disconnection and long analysis gaps reset voting history.
- Subsequent overlapping detections extend that open event, updating `last_seen`, box and confidence while preserving the operator decision. Unrelated regions can open separate events. An event closes after `event_timeout` seconds without a matching detection (field default 36 seconds; demo default 12 seconds). Smoke returning after closure can create a new event. Old open events are closed on process restart.
- Capture failure clears the latest frame, marks the active slot disconnected, and retries after `retry_seconds`, default 2 seconds. Frames older than `stale_seconds` are not analysed or displayed. The other active capture worker and shared inference loop continue. Inactive slots never attempt to open their sources.
- A bounded in-memory JPEG ring (default 640px wide, 5 fps) retains recent context; it is not written continuously. An event saves an annotated JPEG immediately and a short **WebM/VP8 clip**, normally up to 4 seconds before plus 4 seconds after opening, with the opening detection box drawn on every frame. Early-start events have less pre-roll; loss/shutdown can shorten post-roll. Clip sampling uses capture timestamps. The clip captures initial event context; extensions update the event row, not an indefinitely growing movie. See **Event clip format** below.
- Event records live in `data/events.sqlite3` (SQLite WAL). Media lives in `data/events/`. Records include camera, opening/last-seen/closure timestamps, normalized `xyxy` box, confidence, media paths, operator decision and decision timestamp. Snapshot geometry corresponds to the opening detection; the row's box/confidence track the latest detection. Media failures appear in the event metadata. A single bounded encoder worker saves clips without blocking capture/inference; overload records an explicit missing-clip error.
- Retention, default 7 days since `last_seen`, removes expired event rows and imagery on startup and approximately once per minute. Old orphaned evidence from a crash is pruned too. The compressed context ring is memory-only and bounded; saved imagery is event-based.
- The panel polls local JPEGs and JSON once per second. The two active feeds share the observation area; the mounted inactive slot is a single status row. Pending **“Duman şüphesi”** records appear beside the feeds on desktop and above them on phones. The operational bar counts decisions still awaiting review, including closed observations. An open observation marks its source feed in amber. Recorded file sources are labelled **“Kayıtlı demo”**; actual runtime figures stay labelled **“Ölçülen”**. **Doğrula** and **Reddet** persist operator decisions; decided rows show the decision and time, with **Değiştir** to correct it. Camera loss raises a reduced-coverage warning. Server loss replaces stale frames, figures and the decision list with unavailable/loading states until recovery. A same-origin content-security policy prevents external panel assets and connections.

### Event clip format

Clips play inline in the panel: an HTML `<video>` with native controls, the annotated snapshot as its poster and an **İndir** download link. The label reads **“Kayıtlı demo · olay klibi”** for file sources.

- **Why WebM/VP8.** The pinned `opencv-python-headless` 4.14 wheels bundle FFmpeg with libvpx on both macOS ARM64 and **Linux ARM64**. VP8 therefore needs no system `ffmpeg` binary and no extra package, and works fully offline. H.264/MP4 was rejected: the Mac wheel bundles x264, but inspection of the `manylinux_2_28_aarch64` wheel's libavcodec found no x264 or OpenH264 encoder. The only H.264 encoder there is `h264_v4l2m2m`, which needs a hardware codec driver that has not been verified on the UNO Q. VP9 and AV1 cost several times to ~50× more CPU than VP8. No `ffmpeg` binary is used or required.
- **Browsers.** Clips were confirmed playing inline on this Mac in **Safari 27.0.1** and **Playwright Chromium 156**: playback ran past 1.5 s, `readyState` reached 4, the frame was 640×360, there were no media errors and no external requests. Firefox has documented VP8 WebM support, but it was **not tested** here because Playwright's Firefox build would not launch on this macOS. Google Chrome-branded builds and iOS/iPadOS Safari were not tested either.
- **CPU cost.** One evidence thread encodes at most one clip at a time from the already-compressed 640px/5 fps ring, so detection never waits on it. On Linux that thread is reniced to +10 so capture and inference win any contention. Overload records an explicit missing-clip error instead of queuing. Measured on the **Mac (Apple M5)** with real smoke footage: 0.43–0.82 s wall time per event (6 real smoke events, 31–40 frames at 640×360, measured while both cameras were being analysed; includes JPEG decode, box drawing and a decode check of the output). The UNO Q figure is **unmeasured**; measure encode time and its effect on sustained inference on the actual board before making a performance claim.
- **Fallback without the encoder.** If the VP8 writer cannot open, or its output does not decode, the same event is written as an **MJPEG AVI** with OpenCV's built-in writer, which needs no FFmpeg. The panel then shows the annotated snapshot, the download link and the message *“Bu klip tarayıcıda oynatılamaz (.avi) · işaretli görüntü gösteriliyor, klip indirilip yerel oynatıcıda açılabilir”*. A browser that reports no VP8 support, or fails to decode the clip, gets the same snapshot-plus-download view with *“Bu tarayıcı klibi oynatamıyor”*. If both writers fail, the event keeps its snapshot and records the error, and the panel shows **“Klip kaydedilemedi”**.
- **Legacy events.** Events recorded before this change keep their `.avi` clips. They stay listed and decidable, and show the AVI fallback view. The server log line `Event clip …: WebM/VP8, N frames, encoded in X ms` reports each event's format and encode time. OpenCV prints a harmless `tag … 'VP80' is not supported … webm` notice when it opens the VP8 writer.

### Optional LED hook

The MCU status LED and local KY-026 now use the implemented RouterBridge client (`station/mcu_bridge.py`, `mcu_link.py`), with a tested in-process simulation. See the [panel API contract](#microcontroller-and-local-flame-sensor-api-for-the-panel-designer) and [hardware guide/LED table](../firmware/README.md#led-state-table). The sketch compiles for UNO Q; the real bridge, KY-026 response and on-board status LED were observed on the UNO Q with recorded clips; the external RGB LED remains unverified.

The separate legacy `station/led.py` interface, `LedHook.set_alarm(enabled)`, is still available: no `led_path` means no-op; a configured Linux LED brightness file receives `1`/`0`, with missing/unwritable paths disabling this hook without stopping detection. It is a binary smoke-alarm hook, not the MCU's multi-state RGB driver. Leave it unset when using the MCU scheme, avoiding another writer to the same LED. Solar is omitted. LoRa communication uses the simulated transport described below; real radio hardware remains unverified.

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

1. Complete dependency and model/media downloads on reliable internet before the venue demo. Keep `left` and `centre` active, `right` inactive. Stop any previous server; if you want a clean panel, use [archive-events](#start-with-a-clean-event-list) below. The footage fetcher retries HTTP 429/503 up to five attempts with exponential backoff (30/60/120/240 s), honours a longer Retry-After, and preserves verified finished files. If all attempts fail, retry later.
2. Disconnect the station's internet uplink (Wi-Fi can remain on a local network if another device is viewing). Start with `uv run --offline --frozen forest-station --config config.toml serve` and open `http://127.0.0.1:8080`.
3. Show the **two** active feeds and the right mounted/inactive slot. The smoke source starts at a visible plume; an event should open after roughly three analyses. Show “Duman şüphesi,” the highlighted snapshot, the local clip and measured analysis times. Say “measured on this Apple M5 Mac, not on the UNO Q” for the laptop demo; `/api/status.measured_on` identifies the running host. Label simulated MCU data as simulated.
4. Choose **Doğrula** or **Reddet**. Restart the server and show that the decision remains. The repeating clip can produce another event after the first smoke disappears long enough to close; this is expected.
5. Fog is the default negative. To compare cloud or glare, stop the server, make a `negative.local.toml` copy, change only `cameras.centre.source` to `media/cloud.webm` or `media/glare.webm`, and restart with `--config negative.local.toml`. Keep only two active flags.
6. **On the board:** unplug one of the two active USB cameras. Its slot must say “bağlantı koptu”; the other active feed keeps processing, and the third remains “takılı, bağlı değil.” Reconnect the same port and watch retry recovery. This physical step has not been tested without the board.
7. **On the Mac, live file dropout:** keep the server running. In another terminal in `station/`, run `uv run --offline --frozen forest-station --config config.toml unplug centre`. It renames the centre source to `.unplugged`; capture checks path existence every 0.5 s, so allow about 1–2 s for the panel to show “bağlantı koptu” while left continues and right stays inactive. Run `uv run --offline --frozen forest-station --config config.toml replug centre` to restore it; allow the default 2 s retry plus a panel poll. Use the same config as the server. These commands only accept active **file** sources; they do not detach USB hardware. Always replug before running the footage fetcher. A looping file also reopens its path at EOF, rather than keeping an old file handle forever.

### Start with a clean event list

Stop the server with Ctrl+C first. From `station/`, use the config whose event directory you intend to reset:

```sh
uv run --offline --frozen forest-station --config config.toml archive-events
# Inspect the summary, then type ARCHIVE at the prompt.
```

This moves the event database (including any WAL/SHM files) and evidence directory into `data/archive/<UTC timestamp>/`, under that config's `data_dir`. It preserves the records on disk while the next server starts with an empty event list. It includes **both smoke and flame-sensor records**, and refuses if a station server holds that data directory. Prior archives, model and footage are kept. Do not delete the whole data directory to clear the panel.

For intentional permanent removal, `archive-events --delete` requires typing `DELETE`; adding `--yes` skips the respective confirmation, so use it only in an intentional scripted reset. Start the server again after archiving. The repeating smoke clip can create fresh pending records within seconds; this is not a failed reset.

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

The panel regression suite covers loading, recorded/live labels, pending counts, source highlighting, both decisions and correction, failed writes, focus preservation during polling, camera/analysis failure, server loss and recovery, different active pairs, clip playback/fallback, large queues, machine/confidence labels and separate local-flame/LED states.

Verification on **Apple M5, ARM64 Mac, macOS 27.0.1, Python 3.11.15**, CPUExecutionProvider only: the full Python suite passes, including three real-video integration cases, smoke paired separately with fog, cloud and glare. This includes WebM/VP8 encoding, AVI fallback, no-encoder failure and legacy AVI events; MCU simulation/protocol, fake-router reconnect/timeout, storage migration and flame-event separation; live file dropout/recovery, Turkish overlays, opening/peak/latest confidence, host identity and archive safety. It also covers three-of-five voting with misses and unrelated regions, configurable similarity, extension/expiry, latest-frame replacement, unaffected second camera, inactive slots, all active pairs, max-two validation, decisions, retention, preprocessing/RGB/NMS, wrong-model rejection, local assets and HTTP endpoints. Real-video tests skip explicitly when model/media are missing.

The pure C++ firmware suite passes **150 checks** and its shared vectors are also tested against the Python simulation. Run it independently from `firmware/test/` with `c++ -std=c++17 -Wall -Wextra -I../acorn_mcu test_logic.cpp -o /tmp/acorn-test-logic` then `/tmp/acorn-test-logic vectors.txt`. The sketch also compiles with Arduino CLI 1.6.0, Zephyr core 1.1.0 and RouterBridge 0.4.4; the sketch has since been flashed and exercised on the UNO Q, as recorded in [BOARD_NOTES.md](../firmware/BOARD_NOTES.md).

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

- `GET /api/status`: three slots, active/connected states, geometry, per-active-camera measurements, `measured_on` host identity and the `mcu` object described below.
- `GET /api/cameras/left/frame.jpg` (also `centre`, `right`): latest annotated frame; 503 when disconnected, 404 when inactive.
- `GET /api/events`: newest 200 **smoke** events by default, title, timestamps, normalized box, confidence fields, media names, decision. `?kind=smoke|flame_sensor|all` selects kinds; invalid kinds return 422. Existing camera-only clients can retain the default.
- `POST /api/events/EVENT_ID/decision` with JSON `{"decision":"confirmed"}` or `{"decision":"rejected"}`; invalid values return 422, unknown IDs 404.
- `GET /events/GENERATED_FILENAME.jpg`, `.webm` or legacy `.avi`: local event evidence. WebM is served inline as `video/webm` with HTTP Range support; AVI is served as a download. Arbitrary filesystem paths are not served.

Smoke records have `alarm_confidence` (opening detection, matching snapshot/clip overlays), `peak_confidence` (highest recorded confidence) and `latest_confidence` (same as legacy `confidence`). All are model scores on `0..1`, not proof of fire. Label them **opening / peak / latest**, rather than presenting mismatched values as the same measurement. Old rows retain `null` for opening/peak values that were not recorded; do not infer an opening score from the latest one. Row box coordinates still track the latest detection; evidence retains the opening box.

`/api/status.measured_on` contains `system`, `os_release`, `architecture`, `cpu_model`, `board_model`, `is_uno_q` and display `label`. Show the host next to measured inference figures. No hostname or username is included. UNO Q identification accepts the recorded device-tree spelling “Arduino UnoQ” as well as “Arduino UNO Q”; see the board bring-up record. No Mac timings become board timings by connecting a board to the laptop.

## Microcontroller and local flame sensor API for the panel designer

**Implemented backend contract; UI integration is separate.** `GET /api/mcu` returns the same MCU object included at `/api/status.mcu`. Poll either once per second. `[mcu] mode` is `off`, `simulated` or `router`; the checked-in config is `simulated`. Wiring, voltage limits, upload, config switch and the full LED table are in [firmware/README.md](../firmware/README.md).

| Object / fields | Meaning and display rule |
|---|---|
| `mode`, `simulated` | Always show a **simulation** badge when true, including LED state and sensor events. `off` is unconfigured, not normal. |
| `link` in router mode | `transport`, `socket`, `router_connected`, `registered`, `mcu_acknowledged_at`, `mcu_protocol`, `unanswered_requests`, `last_error`; also `rejected_readings` and `mcu_uptime_ms`. Distinguish router connection from actual fresh MCU telemetry. |
| `link` in simulated/off mode | Simulation has `transport: "simulated"`, `linux_messages_ignored`; off has `transport: "off"`. Do not assume router-only keys exist. |
| `flame_sensor` identity | `kind: "local_flame_sensor"`, `model: "Joy-IT KY-026"`, `scope: "station_local_short_range"`, `note`, `simulated`. Keep the local/short-range note visible; it never confirms a camera suspicion. |
| Sensor availability | `configured`, `connected`, `status_text`, `last_update` (Unix seconds), `open_event_id`. `connected` means telemetry arrived within `reading_timeout` (default 3 s), **not** electrical presence of the module. |
| Sensor readings | `raw`, `smoothed_raw`, `adc_bits`, `level_permille` (`0..1000`), `level` (`0..1`), `level_note`, `digital_active`, `triggered`. `digital_active` is polarity-normalized; `triggered` includes debounce. Intensity is uncalibrated, not probability, range or fire size. |
| Missing/stale readings | Reading values and `led.shown` become `null` when unavailable; `triggered` becomes false. Render **unavailable**, not “no flame”, zero intensity or green. `last_update` can remain the old timestamp. |
| `led.requested` | Station's requested `{code,name,colour,pattern,text}`, initially nullable. This is an instruction, not hardware feedback. |
| `led.shown` | Last state **reported by the MCU** in the same descriptor shape, nullable when stale. It is a logical state, not optical verification that the LED lights. On-board LED4 uses yellow for the descriptor's PWM amber state. |
| `led.mcu_hears_station`, `led.simulated` | MCU heartbeat judgement (nullable when stale), and whether the LED report is simulated. Local trigger/hold or missing heartbeat can override the request. |

LED codes are `0 boot`, `1 normal`, `2 smoke_pending`, `3 degraded`, `4 flame_sensor`, `5 linux_silent`. Use the returned name/pattern/text as well as colour. Priority is local flame/hold, then Linux silence, then station request. Within station requests, fresh flame outranks pending smoke, which outranks camera degradation, then normal. An unreviewed, closed smoke event still requests `smoke_pending`.

`GET /api/events?kind=flame_sensor` returns independent rows titled **“Alev sensörü tetiklendi”**, with `kind: "flame_sensor"`, `camera: null`, `box: null`, all confidence fields `null`, and no fabricated camera media. Use `details.source` (`"simulated"` or `"hardware"`) for the simulation badge. `details` includes `sensor`, `trigger_reading`, `peak_level_permille`, `peak_level`; on closure it adds `closed_reason` (`sensor_cleared`, `sensor_disconnected` or `station_stopped`) and, when supplied, `last_reading`. Reading details include sequence, uptime, raw/smoothed/relative level, ADC bits and digital/trigger flags. One sensor activation creates one event; release, lost telemetry or station stop closes it. Ordinary pending/confirmed/rejected operator annotations use the existing decision endpoint; **confirmed is an operator annotation, never an automatic confirmed-fire claim**. Smoke feed highlighting and smoke counts must remain smoke-only. SQLite migrations add the kind/details/confidence columns without deleting legacy smoke rows.

For the hardware-free demo, `POST /api/mcu/simulate` accepts optional JSON booleans `flame` and `linux_silent`. It returns immediately with `{ok:true, simulated:true, flame:…, linux_silent:…}` (omitted inputs appear as null); poll for the debounced result. It returns **409** outside simulated mode. Examples while the demo server is running:

```sh
# macOS zsh; use the same secret as the running station. Change only this URL if needed.
ACORN_BASE_URL=http://127.0.0.1:8091
read -s 'ACORN_PANEL_SECRET?Station secret: '; export ACORN_PANEL_SECRET; echo
ACORN_COOKIE_JAR=$(mktemp); chmod 600 "$ACORN_COOKIE_JAR"
uv run --offline --frozen python -c 'import json,os; print(json.dumps({"secret":os.environ["ACORN_PANEL_SECRET"]}))' | \
  curl --fail-with-body -sS -c "$ACORN_COOKIE_JAR" -X POST "$ACORN_BASE_URL/api/auth/login" \
    -H 'Content-Type: application/json' --data-binary @-
curl --fail-with-body -sS -b "$ACORN_COOKIE_JAR" "$ACORN_BASE_URL/api/mcu"
curl --fail-with-body -sS -b "$ACORN_COOKIE_JAR" -X POST "$ACORN_BASE_URL/api/mcu/simulate" -H 'Content-Type: application/json' -d '{"flame":true}'
# Wait at least one second, then read the independent sensor event list.
curl --fail-with-body -sS -b "$ACORN_COOKIE_JAR" "$ACORN_BASE_URL/api/events?kind=flame_sensor"
curl --fail-with-body -sS -b "$ACORN_COOKIE_JAR" -X POST "$ACORN_BASE_URL/api/mcu/simulate" -H 'Content-Type: application/json' -d '{"flame":false}'
# Trigger release takes about 1 s; red LED state holds another 3 s.
curl --fail-with-body -sS -b "$ACORN_COOKIE_JAR" -X POST "$ACORN_BASE_URL/api/mcu/simulate" -H 'Content-Type: application/json' -d '{"linux_silent":true}'
# Allow 5 s, then restore normal heartbeats.
curl --fail-with-body -sS -b "$ACORN_COOKIE_JAR" -X POST "$ACORN_BASE_URL/api/mcu/simulate" -H 'Content-Type: application/json' -d '{"linux_silent":false}'
rm "$ACORN_COOKIE_JAR"
```

Simulation applies no signal to the board. Keep titles distinct: cameras **“Duman şüphesi”**, local sensor **“Alev sensörü tetiklendi”**. The KY-026 responds to nearby IR, including sunlight/other IR sources; its approximate metre-scale scope is not a guaranteed detection range. Never fuse these two event kinds into a claim of confirmed fire.

## Known issues and unverified work

- The station has been run on a real Arduino UNO Q using recorded clips, with the microcontroller bridge, the KY-026 responding and the on-board status LED following station state. Two live USB cameras at input 192 were measured on the board at about 278 ms inference and 0.990 analyses/s per camera; that is a throughput measurement, not a quality validation. Access-point mode, the external RGB LED and real LoRa radio remain unverified for this demo. See [the dated board bring-up record](../firmware/BOARD_NOTES.md) for ongoing hardware work and measurements; this document does not turn Mac timings into board claims.
- The Mac camera-loss check is a software simulation. V4L2 driver-specific blocking/hanging behaviour cannot be established here; a frame-age watchdog marks stale feeds disconnected, but a driver stuck forever inside `read()` may need process/driver recovery on real hardware.
- No physical internet switch-off was performed. Runtime network independence is checked by denied-socket integration tests and the browser's local-only request audit. The initial downloads require internet.
- WebM/VP8 encoding on the UNO Q itself, its per-event CPU time, and iOS Safari playback are unverified. Legacy or fallback AVI clips still need a separate player. Evidence can have shortened pre/post context at startup, loss or shutdown. No audio is saved.
- SQLite and media are local; abrupt power loss can leave incomplete evidence. Startup closes previously open events and retention eventually removes orphan files. There is no disk quota beyond age-based retention.
- The model/threshold and mounting FOV are demo settings. Detection is suspicion support requiring operator review, not a validated autonomous emergency system.
- The installed Starlette TestClient emits one upstream `httpx` deprecation warning; tests still pass. No failing test is hidden or filtered.

## Communication

ACORN has two distinct access paths. The **original remote dashboard** in [`ground/`](../ground/README.md) receives only compact binary alert/status/decision packets over **LoRa link (simulated transport)**. The **ranger Wi-Fi panel** here is the full-detail interface for someone close to the station: feeds, snapshots, clips and authenticated operator decisions. Wi-Fi is a permanent close-range feature. The remote dashboard's optional Wi-Fi imagery is an explicitly labelled demo aid and is off by default. No image/video is carried by LoRa.

### Configure the link

Copy `config.toml` to an ignored `communication.local.toml`. Enable `[lora] enabled = true`; set a unique `station_id`, actual configured `heading` and the ground laptop's `peer_host`/`peer_port`. The default UDP destination is loopback port 9901, SF10/BW125/CR4/5, sub-band 868.0–868.6 MHz at 868.3 MHz, calculated 1% duty limit, one replaceable heartbeat every 300 s, and two alert/decision repeats 30 s apart. Start ground first, then:

```sh
# From station/, macOS zsh: input is hidden and not written into shell history.
read -s 'ACORN_PANEL_SECRET?Choose a strong station secret: '; export ACORN_PANEL_SECRET; echo
uv run --offline --frozen forest-station --config communication.local.toml serve --port 8091
```

For bash on the UNO Q use `read -rs -p 'Choose a strong station secret: ' ACORN_PANEL_SECRET; export ACORN_PANEL_SECRET; echo`. For a persistent local setting, put `panel_secret` under `[station]` in an ignored, owner-readable `*.local.toml` (`chmod 600`). Never use the checked-in config for secrets. `ACORN_PANEL_SECRET` overrides the local TOML value. There is no default password, development bypass or unauthenticated data API. Missing configuration returns HTTP 503 instead of exposing the panel. Choose a long random secret and share it with authorised rangers separately from public demo materials.

The shared-secret login compares using `hmac.compare_digest`, limits failed logins to five per five-minute window per source and globally, and limits login body size. The global limit intentionally trades availability for resistance to source rotation: a ranger may need to wait five minutes after repeated failures. Successful logins set an opaque random HttpOnly, SameSite=Strict cookie for eight hours. Sessions survive reload but expire on server restart or logout (`POST /api/auth/logout`). Only local static assets and the login page/endpoint are public; status, frames, all events, evidence and MCU routes require a session. Mutating requests must be same-origin. HTTP runs without transport encryption on the local AP; use a strong WPA2/WPA3 AP password, a trusted local network and HTTPS if that network is not trusted. Do not forward the panel from a public router.

The [`packet specification`](station/lora/PACKETS.md) contains byte layouts, projection assumptions, airtime tables, CEPT primary sources, exact queue policy and unimplemented modem integration points. The bridge works independently of capture/inference and never waits for radio airtime. New alerts take priority; repeats are bounded; heartbeats yield; `data/lora-duty.json` persists the rolling sub-band budget. Lost simulated packets still consume airtime. Never erase that ledger to increase a real transmitter's allowance. `loss`, `seed`, `airtime_delay`, `payload_limit`, stricter `duty_fraction` and heartbeat/repeat intervals can exercise constraints without changing packets or UIs. There is no battery sensor: the status packet explicitly says **not measured**.

The serial adapter is a documented **unimplemented/untested skeleton** and refuses startup when selected. No modem command set, wiring, serial device, e.r.p., range, RSSI or SNR is invented. The station ID is configured identity, not an authenticated radio identity. CRC protects against accidental corruption, not an attacker. New events opened during the current process session are scanned into a bounded in-memory outbox; unsent work is not durable across shutdown. See the specification for these prototype limits.

### Direct panel access on an existing Wi-Fi network

For an already configured station, persist `--host 0.0.0.0 --port 8080` in its existing normal-user launcher, preserving private secret loading, `board.local.toml`, the exclusive `flock` and the existing cron entry. Open `http://BOARD_LAN_IP:8080` on the same trusted Wi-Fi and sign in with the existing panel secret. Find the board’s current Wi-Fi address; DHCP and client isolation can affect reachability. The default CLI bind remains loopback; this is a deployment choice. The SSH tunnel is an optional fallback, and station starts independently of it. HTTP is unencrypted.

Direct board-address HTTP validation succeeded for authentication, protected APIs, both intact 320×240 frames, existing evidence, advancing analysis counters and fresh MCU readings. **The bind change was not power-cycle or browser tested.** The secret/configuration/lock/cron and camera/model settings were otherwise preserved. Direct access on an existing Wi-Fi network does not establish or test ranger AP mode, which remains untested. See the [board access record](../firmware/BOARD_NOTES.md#direct-authenticated-access-on-existing-wi-fi).

### UNO Q as a ranger Wi-Fi access point — all board steps unverified

Arduino's [UNO Q Debian Linux Basics](https://docs.arduino.cc/tutorials/uno-q/debian-guide/) documents the board's NetworkManager **`nmcli`** Wi-Fi management and USB ADB recovery. The [UNO Q user manual](https://docs.arduino.cc/tutorials/uno-q/user-manual/) also uses `nmcli`. The following AP procedure uses [NetworkManager's own hotspot command](https://networkmanager.pages.freedesktop.org/NetworkManager/NetworkManager/nmcli.html), rather than assuming Raspberry Pi tools or preinstalled `hostapd`. **None of these steps has been run on the UNO Q; AP mode, driver capabilities, DHCP sharing and phone interoperability are unverified.**

Use a local SBC console or USB ADB shell first; switching the only Wi-Fi interface to AP mode can disconnect its existing network/App Lab connection. Keep that recovery shell open. Replace the interface placeholder with the actual name reported on the board:

```sh
# UNVERIFIED ON BOARD: inspect shipped network tools, interface and AP capability.
command -v nmcli
nmcli device status
nmcli -f GENERAL.DEVICE,WIFI-PROPERTIES.AP device show WIFI_INTERFACE
# If AP is unavailable, stop here: a verified supported Wi-Fi adapter/AP is needed.

# UNVERIFIED ON BOARD: prompt separately for a strong AP password (bash).
read -rs -p 'Ranger AP password: ' ACORN_AP_PASSWORD; echo
sudo nmcli device wifi hotspot ifname WIFI_INTERFACE con-name acorn-ranger \
  ssid ACORN-Ranger password "$ACORN_AP_PASSWORD"
unset ACORN_AP_PASSWORD
# UNVERIFIED ON BOARD: explicit shared IPv4 network and WPA2-capable configuration.
sudo nmcli connection modify acorn-ranger ipv4.method shared \
  ipv4.addresses 10.42.0.1/24 wifi-sec.key-mgmt wpa-psk wifi-sec.proto rsn
sudo nmcli connection up acorn-ranger
nmcli -g IP4.ADDRESS device show WIFI_INTERFACE
```

These password arguments are passed to the local `nmcli` process; do this only on the trusted board console. The password is not a literal in shell history or this repository. Verify that the resulting AP is protected and a ranger receives an address on 10.42.0.0/24. Do not assume internet connectivity, concurrent client/AP mode or a captive portal. If the interface cannot provide AP mode, the procedure is incomplete until a supported AP/adapter is tested; do not call the UNO Q hotspot tested.

**UNVERIFIED ON BOARD:** configure `ACORN_PANEL_SECRET` as above, then start station with `serve --host 0.0.0.0 --port 8091` on the board's Linux side. Join **ACORN-Ranger** from the ranger phone/laptop using its AP password, open **http://10.42.0.1:8091**, and sign in with the separate station panel secret. Confirm the address with `nmcli` rather than assuming the requested address succeeded. The full local panel is then the Wi-Fi evidence/decision view. Keep unrelated services off this field AP and restrict access to the intended network; no firewall configuration is claimed as applied here.

**UNVERIFIED ON BOARD recovery:** from the retained local/ADB shell, run `sudo nmcli connection down acorn-ranger`, then `sudo nmcli connection up YOUR_PREVIOUS_CONNECTION`. Use `nmcli connection show` to identify that saved connection. Remove the AP profile with `sudo nmcli connection delete acorn-ranger` if no longer wanted. Refer to Arduino's ADB recovery instructions if normal network access is lost.

### Collect evidence when in range

The ranger can inspect the full panel directly. On a ground laptop that already received LoRa alerts, join the station AP, start ground with `--station-url http://10.42.0.1:8091` and `ACORN_STATION_SECRET` set to the station's panel secret, then use **Collect evidence over Wi-Fi** on the received alert. Ground checks the station ID and requests that alert's full original UUID via the protected API. It saves snapshot/clip locally under `ground/data/evidence/STATION_ID/EVENT_UUID/`. A later station outage or retention cleanup does not remove those copies. Enable the clearly marked Wi-Fi demo area to view them in ground; with the switch off, no imagery is shown. Collection works independently of that viewing switch and does not create radio alerts or station decisions.

### Sustained demo scheduling (rehearsal 2 fix)

Use the checked-in `demo-lora.toml`: recorded inputs, simulated transport, SF7/BW125/CR4/5, a requested four-second heartbeat and a strict 1% rolling-hour allowance. Every transmission is paced into a calculated 12-second slot; alerts pre-empt queued heartbeats, decisions then repeats follow, and a heartbeat replaces rather than queues another heartbeat. This is a sustainable demo setting, not a range claim. At SF10 the slot is 61 seconds; at SF12 it is 241 seconds. Full alerts cannot arrive every few seconds at those long-range settings within 1% duty.

The ledger always refilled one hour after earlier transmissions. The former failure was spending that whole allowance in the first few minutes. Pacing and its next-allowed timestamp now persist too. Do not reset or delete a ledger: a pre-fix exhausted ledger must wait for the already-used airtime to expire; `/api/communication.calculated_next_tx_at` reports the earliest legal opportunity. `archive-events` archives imagery/decisions and intentionally preserves radio accounting. No “start one minute before going on” workaround is needed for the new sustainable configuration.

Packet version 2 adds a CRC-protected calculated next-contact window to every message (37–42 bytes total). Ground still reads version-1 journals. It displays a calculated duty-cycle wait within that window, then stale/lost if the bounded deadline is missed; it cannot infer the cause of silence from unannounced legacy packets. Its configured stale threshold is a minimum: the effective threshold is at least the announced window plus five seconds. A ten-second threshold cannot override a physically required 241-second interval. Under overload, alerts queue and repeats/heartbeats yield; arbitrary alert rates or packet loss cannot be guaranteed.

Three-hour clock-driven tests at SF7, SF10 and SF12 check every rolling hour, ongoing contact and restart persistence. The root [DEMO.md](../DEMO.md) is the single runbook. New arrivals in the station review queue wait while pointer or keyboard focus is inside it, with a new-record notice; they are applied after leaving the queue.
