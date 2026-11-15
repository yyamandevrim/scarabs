# ACORN for Arduino App Lab

ACORN is a two-camera wildfire smoke observation station for the Arduino UNO Q. This package contains the complete Python station: CPU ONNX inference, centre crop, spatial voting, authenticated local web panel, human decisions, SQLite, JPEG/video evidence, retention, and the KY-026/LED bridge. Camera results are smoke suspicions for human review. It is not a validated emergency system. The firmware independently reads the local flame sensor and drives on-board LED4.

**Board status:** this packaging has been compiled and exercised on a Mac and in Arduino's Linux arm64 container. The UNO Q was unplugged throughout; App Lab import, live USB capture inside App Lab, physical bridge/LED and board performance remain unverified. Earlier standalone board measurements do not establish App Lab behavior.

## Build and share

Use the [ACORN repository](https://github.com/yyamandevrim/scarabs), Python 3.11+ and the source checkout. From the repository root:

```sh
python3 station/scripts/fetch_model.py
python3 applab/build.py
```

The fetcher downloads the pinned Pyronear export and verifies both archive and model SHA-256. The builder reuses those constants, verifies the model again, copies the real `station/station/` package including local panel assets, and generates:

```text
applab/dist/acorn/
  app.yaml
  README.md
  BUILD.json
  sketch/
    sketch.ino
    sketch.yaml
    acorn_config.h
    acorn_logic.h
  python/
    main.py
    requirements.txt
    config.toml
    settings.example.toml
    fetch_model.py
    models/smoke.onnx
    station/...
applab/dist/acorn.zip
```

`app.yaml` is at the ZIP root. `applab/dist/` is git-ignored. Rebuilding replaces the generated app completely: keep development data outside that folder. Only metadata/configuration templates and a thin launcher are maintained under `applab/`; firmware and station remain authoritative. Requirements are generated from `station/pyproject.toml`, with the image-provided OpenCV exception described below. `BUILD.json` records every assembled input's SHA-256. The sketch is the source sketch with a generated `LED_EXTERNAL=0` override, so only LED4 is assumed; headers are copied unchanged. Its isolated profile pins Zephyr 1.1.0, RouterBridge 0.4.4 and all six libraries, including transitive dependencies.

**Weights choice:** bundle the verified ONNX file only in the ignored generated app/ZIP; never in git. Serving needs no model download. The model is 38,155,661 bytes; the ZIP is approximately **32.9 MB (31.4 MiB)**; the build prints the exact current size. Model SHA-256: `5c17b5f917b3cd61bafd15b808cbe3c3b03e054e2e9f09ca72f6309d53d8e76b`. The source is [Pyronear's pinned CPU export](https://huggingface.co/pyronear/yolov11s/resolve/de398b5192b2c1d5f8963aef56bf8df1f13c159e/onnx_cpu.tar.gz), licensed AGPL-3.0 according to the existing fetcher and [model repository](https://huggingface.co/pyronear/yolov11s). Preserve model attribution/license obligations when sharing. No source footage is included.

In App Lab choose **Import app**, select `applab/dist/acorn.zip`, then complete the board setup below before running. The ZIP can be shared as the App Lab project attachment on Project Hub. Arduino also documents **Publish on Project Hub → Upload as draft**; completing/publishing that draft is a separate manual step. Neither import nor Project Hub upload was performed here. See the official [app management guide](https://docs.arduino.cc/software/app-lab/apps/manage-apps/) and [ZIP layout validator](https://github.com/arduino/arduino-app-cli/blob/d3c4df1ac01cadf885e85fc6355a1c989e810221/internal/orchestrator/archive.go).

## Configure after import — board steps unverified

Stop the previous standalone ACORN station and disable its ACORN-only boot launcher before starting the App Lab copy. Both otherwise compete for cameras, port 8080 and the `acorn_reading` route. Retain its old data and configuration for rollback. Do not run two stations against one MCU.

In a normal-user local/SSH shell on the board, change to the imported app's actual folder. App Lab mounts this directory at `/app` in the container. Do not assume a fixed host installation path.

```sh
mkdir -p data
cp python/settings.example.toml data/settings.toml
ls -l /dev/v4l/by-path/ /dev/v4l/by-id/
# Edit data/settings.toml: set left and centre to the actual capture endpoints.
python3 python/main.py --set-password
```

The password command uses hidden terminal prompts, requires matching passwords of at least 16 characters, creates `data/panel-secret` exclusively with mode 0600 and never prints the secret. It runs using only the standard library; it does not start inference. There is no default password or secret in YAML/configuration/build output. Missing, short or group/world-readable secret files prevent startup. To rotate it, stop the app, remove the private secret file, rerun the command and restart; existing sessions expire on restart. `ACORN_PANEL_SECRET` is also accepted when supplied privately by a local development launcher, but no undocumented App Lab environment-setting feature is assumed.

Start the app using App Lab. The launcher defaults to real USB cameras and `arduino.app_utils.Bridge`; it refuses placeholder camera paths and never falls back to recorded media or simulation. Cameras request **320×240 YUYV at 5 capture fps**, the final board screen-demo capture request in the existing board record. Actual negotiated format/fps must be checked. Keep physical ports labelled: identical cameras previously had colliding IDs, so `/dev/v4l/by-path/` is preferred; `/dev/v4l/by-id/` is also accepted. Numeric indexes and `/dev/video0` are rejected by the existing station configuration.

The default detector is the board **demo** profile: **192**, confidence **0.35**, **1 analysis/s/camera**, **3 of 5** spatial voting with **IoU 0.25**, `detector_view="center_crop"`, 12-second event timeout, two ORT threads. The crop excludes the outer 40-pixel strips of a 320×240 frame. Profile values come from the canonical station configuration, with no detection/event injection. Set `profile="field"` in `data/settings.toml` for the existing **640 / 0.25 / six-second interval** profile; its exact board performance remains unmeasured. Both profiles use centre crop in this launcher. Radio code is included, but radio remains disabled by the canonical board package defaults; no real LoRa claim is made.

On the same trusted Wi-Fi, open `http://BOARD_LAN_IP:8080` and sign in. `ports: [8080]` plus Uvicorn's `0.0.0.0:8080` bind is the intended published-port route. Wi-Fi isolation, firewall rules, DHCP address changes and actual App Lab reachability still require testing. HTTP is unencrypted; do not expose this port publicly. This package does not configure a Wi-Fi access point.

Persistent files live in `/app/data/`: private password and settings, then `station/` for SQLite/evidence/lock files. Recorded verification uses a separate `recorded/` subdirectory. App restarts preserve host-backed data; deleting the app or disk failure may not. `.cache/` is disposable. When sharing an App Lab export, leave **Include data** unchecked; otherwise it can disclose the password, settings and evidence. The repository builder always reconstructs from an allowlist and never includes any runtime data, `.env`, local configuration, `.DS_Store`, footage or caches. See Arduino's [app structure and persistent data documentation](https://docs.arduino.cc/software/app-lab/apps/about-apps/) and [app format specification](https://github.com/arduino/arduino-app-cli/blob/d3c4df1ac01cadf885e85fc6355a1c989e810221/docs/app-specification.md).

## Runtime decisions and sources

Research checked official sources on 2026-11-15. CLI references below are pinned to `d3c4df1`; runner/Bridge references are the released **bricks/0.13.2** source (`a603efee`). A board with an older App Lab image may differ; inspect its installed versions before assuming equivalence.

- **Manifest:** `name`, `description`, a single emoji `icon`, integer `ports`, and `bricks: []`. A brick entry can be an ID or a single-key map with `model`, string `variables`, and `devices`. There is no invented generic camera/volume/secret field. ACORN runs its own pipeline and panel, so it needs no inference or web brick. Sources: [specification](https://github.com/arduino/arduino-app-cli/blob/d3c4df1ac01cadf885e85fc6355a1c989e810221/docs/app-specification.md), [parser and emoji validation](https://github.com/arduino/arduino-app-cli/blob/d3c4df1ac01cadf885e85fc6355a1c989e810221/internal/orchestrator/app/parser.go).
- **Bridge:** `AppLabLink` implements the station's existing `McuLink` contract with `Bridge.provide("acorn_reading", callback)` and `Bridge.call("acorn_state", state, seq, timeout=...)`. Telemetry callback arguments become the unchanged protocol list. Calls and registration failures are reported without fabricating readings; subsequent heartbeats retry registration. The SDK handles reconnect/re-registration. The adapter unregisters its callback on stop, without shutting down App Lab's process-wide Bridge. Its status reports registration and last MCU acknowledgment; it does not pretend to have SDK socket-health data. The original Unix-socket `RouterLink` remains selectable with `bridge="router"` behind the same interface; the image must mount its socket. `bridge="off"` explicitly disables hardware. Sources: [released Bridge implementation](https://github.com/arduino/app-bricks-py/blob/a603efee8696e8d2dcbda1415b2f6e32abeed517/src/arduino/app_utils/bridge.py), official [Python call example](https://github.com/arduino/app-bricks-examples/blob/a95f8ac6a42753311d73dc8908a823d023c0234c/core-and-foundational/03-bridge-basics/01-call-sketch-function-from-python/python/main.py), [MCU callback example](https://github.com/arduino/app-bricks-examples/blob/a95f8ac6a42753311d73dc8908a823d023c0234c/core-and-foundational/03-bridge-basics/02-send-data-to-python/python/main.py). This entry point uses Uvicorn's existing station lifecycle; Bridge does not require `App.run()`.
- **USB cameras:** the researched CLI binds host `/dev` into the Python service, adds the `video` group and `video4linux` device cgroup rules; a camera brick is unnecessary for direct OpenCV UVC capture. The same generator mounts runtime sockets and publishes each manifest port as `p:p`. Source: [Compose generator](https://github.com/arduino/arduino-app-cli/blob/d3c4df1ac01cadf885e85fc6355a1c989e810221/internal/orchestrator/compose_template.go). **Unconfirmed on this board:** device visibility, persistent symlinks, permissions, dual-camera bandwidth and hotplug inside App Lab. The earlier standalone station needed host `uvcvideo quirks=128`; a container cannot repair the host USB power/bandwidth setup. The reported [“Python sees 0 devices” hub case](https://forum.arduino.cc/t/arduino-uno-q-app-lab-as-a-usb-host-to-an-uno-r3-python-environment-sees-0-devices/1433482) concerns CDC communication to an external Uno R3, not a demonstrated blanket ban on UVC. A separate [camera troubleshooting report](https://forum.arduino.cc/t/howw-to-trouble-shoot-python-provisioning-missing-required-device-no-camera-found/1411432) improved after hub connections changed. Forum reports are supporting observations, not verified guarantees.
- **Container and installation:** researched CLI defaults to `ghcr.io/arduino/app-bricks/python-apps-base:0.13.2`. The verified image is **Linux arm64, Python 3.13.18, Debian trixie/glibc 2.41**. `/run.sh` creates `/app/.cache/.venv` with system site packages, installs `python/requirements.txt` with `uv pip install`, and caches successful requirement contents. Initial image/dependency installation requires internet; this ZIP does not vendor wheels. Sources: [CLI runner selection](https://github.com/arduino/arduino-app-cli/blob/d3c4df1ac01cadf885e85fc6355a1c989e810221/internal/orchestrator/config/config.go), [released entrypoint](https://github.com/arduino/app-bricks-py/blob/a603efee8696e8d2dcbda1415b2f6e32abeed517/containers/bricks/python-apps-base/scripts/run.sh), [base Dockerfile](https://github.com/arduino/app-bricks-py/blob/a603efee8696e8d2dcbda1415b2f6e32abeed517/containers/base/python-base/Dockerfile).
- **OpenCV compatibility found by execution:** this image supplies `opencv-python-headless 4.13.0+1ddb20b` and constrains that private version. Explicitly listing the normal OpenCV requirement causes `uv` to search PyPI for the private version and fail. Generated requirements therefore record it as an image-provided dependency in a comment. Do not replace the custom build: it supplies Arduino camera support. Its `cv2.dnn` module is absent. ACORN now uses a small equivalent NMS fallback only when that module is absent; the ONNX model, score threshold and voting are unchanged. Fallback results were compared with native OpenCV across empty/duplicate/disjoint boxes and 100 seeded random cases. Standard [OpenCV aarch64 wheels](https://pypi.org/pypi/opencv-python-headless/json) also exist, but were not installed over Arduino's image. ONNX Runtime **1.32.0** installed successfully as an arm64 wheel in this Python environment (older [1.20.1 cp313/aarch64 metadata](https://pypi.org/pypi/onnxruntime/1.20.1/json) also confirms support).

## Verification reproduced without the board

From repository root:

```sh
uv run --offline --frozen --project station pytest -q station/tests applab/tests
npm --prefix station test
arduino-cli compile --fqbn arduino:zephyr:unoq --build-path /tmp/acorn-applab-source-build firmware/acorn_mcu
arduino-cli compile --fqbn arduino:zephyr:unoq --build-path /tmp/acorn-applab-generated-build applab/dist/acorn/sketch
uv run --offline --frozen --project station python applab/verify_recorded.py \
  --app applab/dist/acorn --media station/media
```

Fetch the existing model and footage first (`station/scripts/fetch_model.py`, `station/scripts/fetch_footage.py`). Footage attribution remains in the canonical [station documentation](https://github.com/yyamandevrim/scarabs/blob/main/station/README.md#real-footage-attribution-and-licences); footage is external to the export. No generated or injected detections are used. The verifier generates a temporary in-memory panel secret, starts the real exported `python/main.py --recorded`, checks authenticated HTTP and evidence, and cleans up its temporary data. Recorded sources retain the station's **Recorded demo** label; MCU/LED state is explicitly **simulated**, with no flame trigger injected. A second clean process launch against the same directory checks persisted smoke events. The verifier requires process shutdown within the researched App CLI **five-second** stop grace period; this is a local test after evidence becomes available, not proof of board shutdown during a slow encode. Source: [Compose stop timeout](https://github.com/arduino/arduino-app-cli/blob/d3c4df1ac01cadf885e85fc6355a1c989e810221/internal/dockerhelper/compose.go).

With Docker/OrbStack running, use the actual image:

```sh
docker pull --platform linux/arm64 ghcr.io/arduino/app-bricks/python-apps-base:0.13.2
docker run --rm --platform linux/arm64 --entrypoint /bin/sh \
  -v "$PWD/applab/dist/acorn:/app" \
  ghcr.io/arduino/app-bricks/python-apps-base:0.13.2 -c '/run.sh prepare'
docker run --rm --platform linux/arm64 --entrypoint /bin/sh \
  -v "$PWD/applab/dist/acorn:/app" \
  -v "$PWD/station/media:/media:ro" \
  -v "$PWD/applab/verify_recorded.py:/verify_recorded.py:ro" \
  ghcr.io/arduino/app-bricks/python-apps-base:0.13.2 \
  -c '/app/.cache/.venv/bin/python /verify_recorded.py --app /app --media /media'
```

Verified image digest: `sha256:3e374c96d3366a07ad143290522387e3bf6132db691af96489fbc3897b87644a`. Preparation succeeded, including NumPy 2.5.4, ONNX Runtime 1.32.0, FastAPI 0.163.0 and Uvicorn 0.54.0. The public Bridge API imports and call/provide signatures were checked inside that image. Both Mac Python 3.11 and arm64 Python 3.13 runs served the panel, advanced both 320×240 file cameras through at least six analyses, created a real smoke event and served its JPEG and encoded clip. Unauthenticated `/api/status` returned 401. Both clean process restarts retained prior smoke events; measured shutdown after evidence availability was 0.230 s on Mac and 0.228 s in arm64, within five seconds. Stop during slow board evidence encoding remains unverified. No board network address was contacted. Container timings are Mac-hosted, not UNO Q speed measurements.

Regression results: **330 Python tests passed** (324 existing station tests plus six new packaging/glue tests), with one existing Starlette/httpx deprecation warning; **45 panel JavaScript tests passed**.

The original sketch compiled at **94,492 bytes flash / 38,924 bytes RAM**; the generated LED4-only sketch compiled at **93,260 / 38,264**. Packaging tests compare copied source bytes and hashes, check profile/transport/password handling, registration/retry/error/shutdown behavior, compare NMS results and rebuild over planted private state to confirm it cannot enter the ZIP. The final ZIP is rebuilt after verification so it contains no `.cache`, passwords, SQLite or evidence. No browser UI or physical hardware verification was performed.

## Ordered real-board acceptance checklist — all pending

1. Record installed App Lab/App CLI/runner/core versions and free storage; preserve the previous station deployment and stop its process/ACORN boot launcher. Confirm adequate hub power and the existing UVC setting. Do not run competing bridge clients.
2. Import the generated ZIP in App Lab. Confirm manifest recognition, dependencies, isolated sketch build, normal upload/vendor-loader startup and no missing symbols. Record any change from the verified 0.13.2 image.
3. In the imported app directory, configure two real persistent camera paths and create the private password. From its Python container, confirm both `/dev/video*` capture endpoints and persistent symlinks exist and are accessible; check port-to-camera mapping, actual 320×240 YUYV format/fps, simultaneous moving capture and physical unplug/replug.
4. Start with `bridge="applab"`; check fresh non-simulated KY-026 telemetry, protocol 1 acknowledgments and no route conflict. Stop/restart the app and verify SDK reconnection. Confirm the local sensor remains separate from smoke events.
5. Observe LED4: normal, camera fault, pending smoke, permitted local sensor trigger, and Linux-silent timeout. Confirm the red local response works independently and heartbeats restore station control. External RGB is disabled and untested.
6. From a second device on the board's Wi-Fi, open the board's actual IP on port 8080. Check login, unauthorized API rejection, both feeds, evidence playback and human confirm/reject decisions. Check App Lab stop/restart both while idle and during evidence encoding (the CLI may force-kill after five seconds), private file permissions and persisted events/decisions/evidence. Re-export without data and inspect for secrets before sharing.
7. Check input 192 / 0.35 / one analysis/s/camera / 3-of-5 / IoU 0.25 / centre crop in authenticated status. After warm-up, measure at least three minutes of analysis timings/rates, RSS, CPU, thermals, disk growth and evidence encoding. Compare with the earlier standalone **about 282 ms per analysis** only under equivalent conditions; App Lab parity is unconfirmed. Do not substitute Mac/container timings.
8. Rehearse the documented live-camera screen-smoke positive and dedicated hall/ordinary-video controls with unchanged thresholds. Identify any file-source fallback as **Recorded demo**. Field accuracy, calibrated sensor range, AP mode, real LoRa, long-duration stability and unexpected-power-loss recovery remain unverified.
