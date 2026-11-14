# UNO Q board bring-up and measurement record

Work performed during the Junction 2026 ACORN bring-up. This is a borrowed team board. Firmware writes require its owner's agreement; never interrupt a firmware write. No Linux image reset or partition flashing was performed.

## Hardware and software identity

Measured target: device-tree model **Arduino UnoQ**, compatible strings `arduino,imola`, `qcom,qrb2210`, `qcom,qcm2290`; aarch64, Qualcomm QRB2210, nominal 2 GB RAM. Debian GNU/Linux 13.5 (trixie), kernel `7.0.0-g122c2c22d838`, glibc 2.41. The application's identity helper currently does not recognize the spelling `UnoQ` and can incorrectly display “not UNO Q”; the device-tree identity above establishes where these measurements ran. No application code was changed to hide this issue.

Python 3.11.18, uv 0.13.8 on Linux; ONNX Runtime 1.32.0, OpenCV headless 4.14.0.94, NumPy 2.4.6. Dependencies follow the copied `station/uv.lock` (SHA-256 `c7e65dcac8cf3e65515b3daa6e95cacd65bd41e62ff3f3afad50e3be20768436`). Other dependencies are listed in that lock and the on-board `~/acorn/measurements/python-packages.json`. The model is the project's Pyronear CPU ONNX export, SHA-256 `5c17b5f917b3cd61bafd15b808cbe3c3b03e054e2e9f09ca72f6309d53d8e76b`.

## Bring a stock/reset board to this state

1. Complete [Arduino's UNO Q onboarding](https://docs.arduino.cc/tutorials/uno-q/user-manual/) in App Lab; privately retain the board account credentials. Use a data-capable USB cable and suitable power supply. When a USB hub makes the board a USB host, ADB may disappear; use SSH over the configured local network. Verify the SSH host identity. Do not assume a USB disappearance means Linux has crashed.
2. On the Mac, follow [MAC_SETUP.md](MAC_SETUP.md) for CLI and libraries. The firmware pins **Zephyr 1.1.0**, **RouterBridge 0.4.4**. Align the board's own Arduino CLI core too before relying on power cycles:

   ```sh
   # In the board's Linux shell, as its normal user:
   arduino-cli core install arduino:zephyr@1.1.0 --additional-urls https://downloads.arduino.cc/packages/package_zephyr_index.json
   arduino-cli core list
   ```

   This changes related Arduino core/tool packages in the board user's `.arduino15`; it replaces the image's older 0.55.2 core. It does not flash the Linux OS. Library dependency resolution installed RouterBridge 0.4.4, RPClite 0.3.1, ArxContainer 0.7.0, ArxTypeTraits 0.3.2, DebugLog 0.8.4 and MsgPack 0.4.2 in the normal board user environment. Native tool dependencies were installed by the core package, including Zephyr SDK 1.0.1. Initial archive extraction took several minutes on this board.
3. With the owner-authorized firmware procedure and external parts disconnected, compile/upload on the Mac from the repository root:

   ```sh
   arduino-cli compile --fqbn arduino:zephyr:unoq --build-property 'compiler.cpp.extra_flags=-DLED_EXTERNAL=0' --build-path /tmp/acorn-unoq-onboard-build firmware/acorn_mcu
   arduino-cli board list
   arduino-cli upload --fqbn arduino:zephyr:unoq --port 'ACTUAL_ADDRESS_FROM_BOARD_LIST' --build-path /tmp/acorn-unoq-onboard-build firmware/acorn_mcu
   ```

   The upload used Arduino's remoteocd/OpenOCD recipe, including the matching MCU loader. It succeeded: **93,260 bytes flash, 38,264 bytes RAM**. No manual flash addresses were used. The firmware uses on-board LED4; external RGB outputs are disabled by the compiler flag. The checked-in firmware was not edited. Loader ELF SHA-256 on Mac and Linux both matched `ab51400731a80083979143dc764f1039c3d37853629108cbb77f958ee1a76960`. Firmware source SHA-256 was `eb30a7bc0f951f005e5e99092712cd258ff13f66b38e4fb762e36ee3cd69f61c`; `acorn_config.h` SHA-256 was `061406312282004fe2f03dfd59d7f0a0ddc1d1053571624ecec3fd52d4d864a8`.
4. Copy `station/` and `firmware/` into `~/acorn` on the board. Exclude Mac `.venv`, `node_modules`, event data, caches and `.git`. Existing `station/models` and `station/media` were copied; the model fetch script verified the existing model hash. One method from the local repository root is:

   ```sh
   tar -czf /tmp/acorn-source.tar.gz --exclude='station/.venv' --exclude='station/data' --exclude='station/node_modules' --exclude='__pycache__' --exclude='.pytest_cache' station firmware
   scp /tmp/acorn-source.tar.gz arduino@BOARD_NAME.local:/tmp/
   # In the board shell:
   mkdir -p "$HOME/acorn"
   tar -xzf /tmp/acorn-source.tar.gz -C "$HOME/acorn"
   ```

   Initial transfer here used `adb -s SERIAL push` followed by the same extraction. Mac provenance extended-header warnings were harmless. ADB serials, network addresses and hostnames are deliberately omitted from this public record.
5. Follow [station cold start](../station/README.md#cold-start-on-uno-q-linux). `curl`, `ca-certificates`, `v4l-utils`, `libglib2.0-0t64` were already installed; no apt packages were added during this work. If missing on a second board, the owner runs the README's apt commands with their own sudo approval. Commands actually used for the remaining setup:

   ```sh
   curl -LsSf https://astral.sh/uv/install.sh | sh
   cd "$HOME/acorn/station"
   "$HOME/.local/bin/uv" sync --locked --python 3.11
   "$HOME/.local/bin/uv" run --offline --frozen python scripts/fetch_model.py
   ```

   The installer put `uv`/`uvx` and environment helpers in `~/.local/bin`, Python in `~/.local/share/uv/python`, and caches in `~/.cache/uv`. It added the line `. "$HOME/.local/bin/env"` to the board user's `.profile` and `.bashrc`. No Mac shell profile was edited. Python dependencies were installed into `~/acorn/station/.venv` from the lock; the Mac environment was not copied.
6. On the board create `station/board.local.toml` from `config.toml`, changing its existing MCU mode to `router`, using separate `data-board-bringup`, and retaining the two recorded sources `media/smoke.ogv` and `media/fog.webm`. The tuned clip configuration sets `input_size = 192`, `analysis_hz = 1.0`, and both sources' working dimensions to 320×180. Other values: confidence 0.35, ORT threads 2, CPUExecutionProvider. The original configuration is retained as `station/board.before-performance.local.toml`. Never label these recorded sources as USB cameras.
7. Configure the panel password privately in `~/acorn/panel-secret`, mode 0600. The value is intentionally absent here. The launcher reads it into `ACORN_PANEL_SECRET`; no cloud account is needed for this local panel. The server binds only to board loopback. From the Mac, use either `adb -s SERIAL forward tcp:8080 tcp:8080` or `ssh -N -L 127.0.0.1:8080:127.0.0.1:8080 arduino@BOARD_NAME.local`, then open `http://127.0.0.1:8080` and sign in. A private temporary SSH credential helper/host-key file was used for this session; no password was committed or passed as a command-line password argument.

## Reboot diagnosis and automatic startup

There were **two separate issues**:

- `arduino-burn-bootloader.service` is Arduino's one-time **MCU loader initializer**, not the Linux OS bootloader. It runs as the normal board user, invokes `arduino-cli burn-bootloader -b arduino:zephyr:unoq -P jlink`, and on success creates `/var/lib/arduino-app-cli/bootloader_burned.flag`. Its `ConditionPathExists=!…` means it retries every boot while that flag is absent. Initially the board's CLI used core 0.55.2 while the project was uploaded with 1.1.0. Journal logs showed a flash-write timeout at the MCU loader region and no success flag; the RPC method was unavailable afterwards. The exact underlying cause of that original timeout was not established. Re-uploading the matching project restored MCU operation.
- Station had only been started manually with a detached process. No boot-time launch existed. After the later owner-authorized reconnection, core 1.1.0 was installed on the board; Arduino's service completed successfully and **created its own flag**. No service was disabled and no success flag was fabricated. ACORN's sketch survived this boot: once station was started, `mode=router`, `simulated=false`, MCU protocol 1, fresh sensor readings, acknowledgements and LED state reports returned. **No re-flash was needed after that boot.**

The owner's observation of a short blue flash every two seconds matched ACORN's `linux_silent` pattern: MCU code running without station heartbeats. A blank LED matrix is expected because this sketch does not use it. Those observations alone are insufficient to identify firmware; the successful protocol exchange above is the direct confirmation.

Station now has one normal-user cron `@reboot` entry. The existing `cron` system service was already active; no root service, sudo command, boot partition or Linux image was changed. Existing crontab contents were preserved in `~/acorn/crontab.before-acorn`; the old launcher was saved as `~/acorn/start-station.before-autostart.sh`. The new `~/acorn/start-station.sh` (mode 0700) is:

```sh
#!/bin/sh
set -eu
umask 077
cd "$HOME/acorn/station"
ACORN_PANEL_SECRET=$(cat "$HOME/acorn/panel-secret")
export ACORN_PANEL_SECRET
exec /usr/bin/flock -n -F "$HOME/acorn/station.lock" .venv/bin/forest-station --config board.local.toml serve --host 127.0.0.1 --port 8080
```

Append this single entry with `crontab -e`, preserving other entries:

```cron
@reboot /bin/sh -c 'exec "$HOME/acorn/start-station.sh" >> "$HOME/acorn/station.log" 2>&1' # ACORN station auto-start
```

The lock prevents duplicate instances. Manual startup is `~/acorn/start-station.sh`. Logs are in `~/acorn/station.log`. This is boot-time startup, not a crash-restarting supervisor. To undo only this addition, remove the marked cron line; the saved crontab can be restored with `crontab "$HOME/acorn/crontab.before-acorn"` only after checking no later unrelated entries would be lost. Keep the vendor's loader success flag intact; do not delete it as a generic reset step.

**Power-cycle confirmation: pending explicit owner-approved test after this auto-start change.** No claim of automatic recovery is made yet.

## Measurements — measured on the UNO Q

The recorded-video sources were measured separately from USB cameras. Each steady-state run uses a 30-second warm-up followed by 19 snapshots about 10 seconds apart (approximately three minutes). Per-source rates are differences in completed-analysis counters divided by monotonic elapsed time, not just the last displayed rate. Process CPU uses `/proc/PID/stat` with `CLK_TCK=100` (100% = one core); machine busy time uses `/proc/stat` across four cores, treating idle/iowait as idle. RSS and free/available memory come from procfs. Thermal readings are the board's named thermal zones, not an external ambient measurement. No GUI/browser polling was deliberately added as benchmark load.

The project benchmark ran with the station server stopped:

```sh
cd "$HOME/acorn/station"
"$HOME/.local/bin/uv" run --offline --frozen forest-station --config board.local.toml benchmark media/smoke.ogv --frames 60 --stride 25
```

For each input size use the matching saved local configuration. There are 54 sampled frames and three warm-up inferences in the completed 640 and 320 runs. Preprocessing/inference timers exclude video decoding; steady two-source measurements include the live station pipeline. The CLI's generic JSON note says “not a UNO Q performance claim”; hardware identity was independently verified above, so these particular results **are UNO Q measurements**, not Mac results.

| Run / configuration | Sources and interval | Analysis rate left / centre | CPU machine / process | Station RSS mean (range) | MemAvailable mean (range) | MemFree mean (range) | CPU thermal range |
|---|---|---|---|---|---|---|---|
| Baseline: input 640; working 1280×720; requested 1 Hz; 2 ORT threads | smoke + fog clips; 181.3 s | 0.105 / 0.105 Hz | 98.85% / 381.8% | 392.4 (383.7–397.4) MiB | 945.1 (932.3–956.3) MiB | 40.3 (31.5–51.2) MiB | cpuss0 58.0–63.3°C; cpuss1 58.3–63.6°C |
| Tuned clip trial: input 192; working 320×180; requested 1 Hz | smoke + fog clips; interrupted after 130.9 s | 0.986 / 0.993 Hz | Not summarized as a full run | 276.1 MiB mean | Not summarized | Not summarized | Not summarized |
| Two live cameras: input 192; working 320×240; requested 1 Hz; 2 ORT threads; UVC quirk 128 | two UVC cameras; 180.7 s / 19 snapshots | **0.990 / 0.990 Hz** (179 analyses each) | **42.42% / 156.5%** | **179.8 (179.2–180.1) MiB** | **1118.8 (1113.8–1124.9) MiB** | **403.9 (398.9–410.2) MiB** | **cpuss0/cpuss1 41.7–47.0°C** |

Baseline final 1/5/15-minute load averages: 8.88 / 5.85 / 4.07. Total Linux-visible RAM is approximately 1.7 GiB; nominal board RAM is 2 GB.

| Standalone smoke benchmark | Preprocess mean / p95 | Inference mean / p95 | Total analysis mean / p95 | Positive sampled frames / total |
|---|---|---|---|---|
| input 640 | 17.90 / 19.75 ms | 2545.33 / 2571.81 ms | 2563.79 / 2591.55 ms | 28 / 54 |
| input 320 | 5.53 / 7.06 ms | 665.11 / 680.96 ms | 671.10 / 687.01 ms | 21 / 54 |
| input 192 | Pending | Pending | Pending | Pending |

Exploratory input 256 with working 640×360 produced about 0.6 Hz per source and did not hold the target. The first 192 run was interrupted by an owner-initiated power removal; it is not counted as a completed steady run or a power fault. A smaller model input changes detections: already, 320 differed from 640 on the same smoke samples. Hitting 1 Hz does not establish equivalent sensitivity or field accuracy. Do not treat reduced-resolution speed as an accuracy validation.

Raw JSON/logs remain privately on the board in `~/acorn/measurements`; paths, hostnames and credentials from raw logs are not copied into this public document. Measurement helper scripts were placed in the board's `/tmp`; these are not application-code changes. Benchmark/server runs were sequential. Earlier full tests had 149 passes, one skip and three fixed-16-second real-video integration timeouts while another benchmark was running; that earlier overlap is not used as a clean performance measurement.

## USB camera status and fallback

After the owner's camera-priority change, clip measurements were stopped deliberately. The last 192 clip run contains **130.9 seconds / 14 snapshots**, with counter rates **0.986 / 0.993 Hz** and mean RSS **276.1 MiB**; it is shorter than the planned three minutes and is not promoted to a completed long steady test.

USB inspection initially found one HHWei `1c45:6200` UVC camera, two `343c:0210` hub devices and a Realtek `0bda:8152` Ethernet adapter. A downstream port failed enumeration with error `-71`. After the owner reseated/swapped camera plugs, both identical HHWei cameras enumerated. Their serial-based links collide, so physical `by-path` links are required:

- `/dev/v4l/by-path/platform-xhci-hcd.2.auto-usb-0:1.1:1.0-video-index0`
- `/dev/v4l/by-path/platform-xhci-hcd.2.auto-usb-0:1.4.4:1.0-video-index0`

Do not use the matching `video-index1` metadata endpoints, or the Qualcomm Venus encoder/decoder nodes, as cameras. Both cameras offer MJPEG from 320×240 through high resolutions (including 640×480 and 1280×720); raw YUYV is offered at 320×240 and 640×480. Each returned a valid JPEG independently through `v4l2-ctl`; the second was decoded as 320×240, the first as 640×480. The board user already belongs to `video`.

Opening both at once failed independently of the station: kernel messages explicitly say **“Not enough bandwidth for new device state” / “altsetting 6”**; V4L2 STREAMON returned ENOSPC. OpenCV V4L2 opened both device handles but returned frames from only the first. Raw YUYV at 320×240 and even a verified 5 fps request did not fix simultaneous capture. The camera's selected high-bandwidth USB alternate setting, rather than a Python memory error, is the established immediate failure. This does not prove the cameras physically require that bandwidth; their firmware may overstate it.

The board did not reset during the reported panel disappearance: uptime and boot history continued, SSH stayed connected, and station logs show the deliberate clean shutdown for independent camera tests. No undervoltage/over-current indication was found in kernel logs. The Type-C port reports `power_operation_mode=default` and role `sink`, not a negotiated USB-PD operating mode. Adapter capacity and voltage/current were not supplied, and board telemetry does not measure the actual power headroom; adequate power remains unverified. Avoid diagnosing every USB bandwidth error as a brownout.

During diagnosis `board.local.toml` selected **one real camera** in the left slot at 320×240 plus the **smoke clip** in the centre slot at 320×180, model input 192, requested 1 Hz. This mixed fallback was verified with increasing analysis counters, JPEG HTTP 200 responses from both slots and fresh MCU protocol-1 sensor data. Example observed rates were 0.985 / 0.994 Hz, live capture about 14.8 fps. These are short functional observations, not a new three-minute live-camera benchmark.

Saved configurations: `board.clips.local.toml` (two clips), `board.live-one.local.toml` (one live + smoke clip), `board.two-live.local.toml` (two physical paths, working with UVC quirk 128). `board.local.toml` is the launcher's active selection and now contains **both live USB sources**, each 320×240, input 192, requested 1 Hz. No application capture code was changed.

A possible reversible driver diagnostic is Linux's `UVC_QUIRK_FIX_BANDWIDTH` flag (128), whose [upstream implementation](https://github.com/torvalds/linux/blob/master/drivers/media/usb/uvc/uvc_video.c) recalculates bandwidth for uncompressed formats. The existing module value is 4294967295 (use device defaults). Writing this root-owned sysfs parameter requires the owner to run `sudo sh -c 'printf 128 > /sys/module/uvcvideo/parameters/quirks'` and replug **only camera USB connections** so they reprobe. It does not flash firmware, change a disk configuration, or survive a reboot. The owner applied the temporary setting and replugged only the cameras. The kernel confirmed the quirk on both devices. Both then streamed concurrently through `v4l2-ctl` at 320×240 YUYV, requested 10 fps, 60 frames each, with exit 0 for each stream. The initial system-tool streams dropped 2/3 startup buffers respectively but each completed, reporting about 9.8 fps. The station subsequently negotiated **YUYV 320×240 at 30 fps** on both devices without the previous bandwidth error. MJPEG or alternating-capture application changes were therefore unnecessary.

Both live panel endpoints returned JPEG HTTP 200; both analysis counters advanced; MCU protocol 1 and fresh sensor data remained available. The completed 180.7-second live measurement had both sources connected in all 19 snapshots, zero kernel log entries during the window (no resets, disconnects, bandwidth, undervoltage or over-current errors), and final 1/5/15-minute load averages 1.68 / 1.99 / 2.06. Mean sampled live preprocessing/inference/total time was **2.52 / 279.32 / 282.21 ms (left)** and **5.65 / 276.53 / 282.55 ms (centre)**. These are snapshots of completed live analyses under simultaneous capture, not a standalone benchmark distribution or accuracy validation.

The owner confirmed this is already the Arduino kit hub. USB topology shows two cascaded `343c:0210` hubs at **480 Mb/s**: camera A at `1-1.1`, camera B at `1-1.4.4`; the Ethernet adapter is at `1-1.4.1`. A separate 5000 Mb/s root bus exists but has no enumerated downstream hub/device. No identified physical camera port offers a separate data bus. Moving these USB-2 cameras cannot make them SuperSpeed devices; no different-hub branch was pursued after the owner clarified the kit hardware.

After the successful temporary test the owner installed the prepared file with:

```sh
sudo install -m 0644 "$HOME/acorn/acorn-uvc.conf" /etc/modprobe.d/acorn-uvc.conf
```

The exact staged/persistent contents are:

```text
# ACORN: correct overstated raw UVC bandwidth for these two cameras
options uvcvideo quirks=128
```

This is the only root-owned configuration added in this work; the **owner**, not the agent, ran sudo. File mode/owner were verified as 0644 root:root, and `modprobe -c` includes the option. The driver is a loadable `uvcvideo.ko`, so this option applies at module load before camera probing. It does not alter MCU firmware, Linux boot partitions or initramfs. Its scope is all UVC cameras on this board; if future devices need different quirks, reevaluate it. To undo this added setting, the owner can remove only `/etc/modprobe.d/acorn-uvc.conf` and restart at an agreed time; merely deleting the file does not change the already-loaded module. The existing temporary value was 128 when persistence was installed.

For reproduction, after creating the two physical-path configuration, activate it with `cp "$HOME/acorn/station/board.two-live.local.toml" "$HOME/acorn/station/board.local.toml"`; retain the separate mixed and clip configs. Use the launcher/cron setup above. Do not manually start another station while the boot-launched one holds the lock. The nominal 1-Hz target is sustained to scheduling tolerance (0.990 measured on each source) in this short run, with substantially reduced model input. Equivalent smoke-detection quality at input 192 remains unverified.

## Sensor result and remaining hardware work

- KY-026 is powered at 3.3 V, AO → A0, DO → D2, common ground; physical wiring was done by the owner with power removed. No voltage measurement by the agent is claimed.
- Working sketch setting: **`FLAME_DIGITAL_ACTIVE_HIGH=1`**. The owner confirmed changing sensor values and an actual trigger. Live MCU telemetry and heartbeat recovery were verified. This is a local IR response, not proof of a fire or validation of camera smoke detection.
- IR source and measured distance: **to be filled in by the team**. No quantitative detection range is established.
- Still unverified: live capture beyond the measured three-minute window and supply electrical headroom; access-point mode; external RGB LED wiring/polarity/PWM; LoRa radio hardware; unexpected power-loss data recovery; long-duration thermals; detection sensitivity/false positives at tuned input size. The matrix is unused by design.
