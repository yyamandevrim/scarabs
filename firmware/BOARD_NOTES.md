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
7. Configure the panel password privately in `~/acorn/panel-secret`, mode 0600. The value is intentionally absent here. The launcher reads it into `ACORN_PANEL_SECRET`; no cloud account is needed for this local panel. The current launcher binds to `0.0.0.0:8080`. On the same trusted Wi-Fi, open `http://BOARD_LAN_IP:8080` and sign in; find the board’s current Wi-Fi address rather than assuming a fixed DHCP address. The original SSH forward is an optional fallback: `ssh -N -L 127.0.0.1:8080:127.0.0.1:8080 arduino@BOARD_NAME.local`, then open `http://127.0.0.1:8080`. USB forwarding with `adb -s SERIAL forward tcp:8080 tcp:8080` remains another fallback when ADB is available. A private temporary SSH credential helper/host-key file was used for this session; no password was committed or passed as a command-line password argument.

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
exec /usr/bin/flock -n -F "$HOME/acorn/station.lock" .venv/bin/forest-station --config board.local.toml serve --host 0.0.0.0 --port 8080
```

Append this single entry with `crontab -e`, preserving other entries:

```cron
@reboot /bin/sh -c 'exec "$HOME/acorn/start-station.sh" >> "$HOME/acorn/station.log" 2>&1' # ACORN station auto-start
```

The lock prevents duplicate instances. Manual startup is `~/acorn/start-station.sh`. Logs are in `~/acorn/station.log`. This is boot-time startup, not a crash-restarting supervisor. To undo only this addition, remove the marked cron line; the saved crontab can be restored with `crontab "$HOME/acorn/crontab.before-acorn"` only after checking no later unrelated entries would be lost. Keep the vendor's loader success flag intact; do not delete it as a generic reset step.

**Power-cycle confirmation: passed after the owner ran `sudo poweroff`, removed dongle power, waited a few seconds and reconnected power with both cameras in the same ports.** A changed kernel boot ID and reset uptime confirmed a new boot. Before starting anything manually, inspection found the station already running via cron, UVC parameter 128 active on both reprobed cameras, and the one-time loader service skipped (`ConditionResult=no`) because its genuine success flag existed. Both live JPEG endpoints returned HTTP 200, both analysis counters were already at 89, MCU protocol 1 was acknowledged, and fresh KY-026 telemetry was arriving. No reflash or manual station launch was needed.

The station process started at **14.3 seconds of Linux kernel uptime**. The first direct authenticated HTTP observation was successful at **111.4 seconds of kernel uptime**. This is an observed upper bound at the first probe, not the exact time the server became ready, and it excludes any power-on delay before kernel time zero. The physical power-on instant was not timestamped and readiness was not polled continuously during boot, so exact power-to-panel latency remains unmeasured. That power-cycle verification used the earlier loopback bind and SSH forward. The current direct-access bind is recorded below and has not been power-cycle tested. The SSH forward remains an optional fallback; reconnecting it does not start or repair anything on the board.

## Direct authenticated access on existing Wi-Fi

The normal-user launcher now binds to `0.0.0.0:8080`. From the same trusted local Wi-Fi, open `http://BOARD_LAN_IP:8080` and sign in with the existing station panel secret. The `panel-secret` file remains mode 0600; the launcher remains mode 0700 and exports `ACORN_PANEL_SECRET` privately. The same exclusive `flock`, `board.local.toml` and `@reboot` cron entry remain in use. Restarting the station invalidates existing panel sessions; sign in again after a restart. The default CLI bind remains loopback; this is a deployment choice.

Focused HTTP validation from the Mac succeeded through the board’s direct address: unauthenticated status, frames, events, evidence and MCU requests were rejected; existing-secret login succeeded; status and both intact 320×240 JPEGs, protected existing evidence and fresh MCU protocol-1 readings were retrieved; analysis counters advanced. Served login/API/image URLs were relative to the direct origin. This was HTTP and saved-frame validation, **not browser UI testing, a power-cycle test of the changed bind, or a new detection-accuracy measurement**.

The existing cron entry uses this launcher, so direct access is expected after the board rejoins Wi-Fi on a later boot; that expectation has not been power-cycle verified. All-interface binding avoids depending on a fixed DHCP address. The address can change, and same-network reachability depends on Wi-Fi client isolation. The SSH tunnel remains an optional fallback; station starts independently of it. No AP, firewall, router, HTTPS or network discovery was configured in this change; **ranger AP mode remains untested**. HTTP is unencrypted. Detector, camera, preview, clip, UVC quirk and firmware settings were unchanged.

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
| input 192 | Not run standalone | See completed live run above | See completed live run above | Not measured |

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

## Preview-quality experiment — rolled back

The initial 640×480 YUYV trial returned truncated, green-padded images despite successful reads and matching dimensions. The user's visual report identified the failure; initial dimension-only validation was inadequate. Its apparent performance figures are INVALID. Both 640×480 YUYV sources also produced invalid pixels in the subsequent 30-fps probe; the new guard rejected them. Dual MJPG failed USB bandwidth admission at 1280×720 and 640×480. Mixed MJPG left + YUYV centre returned visually valid saved frames at 1024×768 and 1600×1200 on the left with the centre at 320×240, but the user reported reduced detection accuracy. The mixed mode was therefore rolled back too; throughput and intact images do not prove equivalent detection accuracy.

**Active recovery selection:** both original 320×240 USB sources, original model input 192, confidence 0.35, requested 1 analysis/s/camera, JPEG quality 80 and evidence JPEG quality 75. No model, inference interval, driver, firmware or boot-service setting was changed. Native-size/quality controls remain available in code, but higher-resolution settings are not active. The frame guard rejects malformed arrays and the observed zero-filled-YUV green footer before publishing to preview, inference or evidence, clears latest/ring and reports a camera fault. It is a specific corruption-signature check, not a universal integrity guarantee. The existing shared-checkout identity fix was deployed so `Arduino UnoQ` is recognised correctly.

Mac suite after the guard: **185 passed**. Board new picture/guard tests: **12 passed**. An earlier full board suite using its older integration tests had 156 passes, one skip and four failures: `test_removed_file_source_is_lost_live_and_recovers`, and `test_real_smoke_negative_pipeline_offline` for fog/cloud/glare. The file-recovery test passed on its isolated rerun; the three integration tests exceeded their fixed 16-second deadline while requesting eight input-640 analyses per source. No detection settings or test expectations were weakened to hide these failures. Only camera-quality hunks were deployed to board config/runtime; concurrent profile implementation was preserved in the shared checkout and not bundled into this deployment.

The original mixed-mode two-minute resource run measured 46.0% machine CPU / 161.6% station CPU, 250.8 MiB mean RSS (259.9 peak), at least 1085.4 MiB MemAvailable, 43.5–49.8°C. Browser payloads averaged 401,391 / 34,945 bytes at 0.871 fps and analysis 0.991 Hz each. These describe the **rejected mixed mode**, not the restored deployment or an accuracy improvement. The baseline was 45.2% / 163.0% CPU, 184.0 MiB RSS, 42.0–49.2°C; browser 0.876 fps, 8344 / 28431 bytes, analysis 0.980 / 0.991 Hz. Scenes changed during the work, so byte counts are payload observations, not controlled quality scores. Diagnostic data remains outside the repository under the board's measurements directory.


**Recovered deployment verification (after rollback):** both drivers report 320×240 YUYV at requested 30 fps; measured capture was 14.64 / 14.26 fps. The browser received correctly decoded 320×240 images at 0.875 fps each; counter-derived analysis was 0.983 / 0.996 Hz and last inference 269.3 / 262.8 ms. Mean payloads were 7645 / 8003 bytes (both views now show a wall, unlike the earlier scenes). A clean 60-second recovery resource run measured machine/station CPU **41.38% / 152.42%**, station RSS **173.8 MiB** (173.9 peak), MemAvailable ≥1157.0 MiB, and CPU temperature **41.3–47.6°C**. Both sources were connected and the panel identified Arduino UNO Q correctly through the existing SSH tunnel. Saved actual API frames were visually inspected from both sources: board and Mac temporary files `/tmp/acorn-recovered-left.jpg` and `/tmp/acorn-recovered-centre.jpg`. Recovery resource proof is `~/acorn/measurements/picture-quality/recovered-baseline.json` on the board. No further board mutations or quality tuning are pending in this task. Detection accuracy after rollback is not quantitatively validated by these wall views; throughput is healthy and the original model settings are restored.

## 2026-11-14 live-camera input-size curve — measured on the UNO Q

The owner requested input 640 for field sensitivity after the [Mac detection-quality study](../station/DETECTION_VS_INPUT_SIZE.md). **192 remains the fast demo setting, not the field sensitivity recommendation.** This run measures speed and resource use, not smoke-detection accuracy.

All three tests used the same two physical live cameras, persistent paths above, negotiated **320×240 YUYV at 30 fps**, UVC quirk 128, the same ONNX model, CPUExecutionProvider, **2 ORT threads**, confidence **0.35**, and the unchanged on-board application snapshot. Only `input_size`, `analysis_hz` and `event_timeout` varied. The newly added repository field profile uses confidence 0.25; that threshold was **not** silently substituted into this controlled timing curve. On-board `detector.py` SHA-256: `96822a0a37057bd043ce44ec2557949f53b6ca7854afe984a816277ca5001317`; `capture.py`: `eca1a24a14e409d533090aedc4bc55878f16e42624d0752a0944b0587bf211b3`. No station source code was edited or updated on the board for these tests.

Method: short capacity probes followed by each selected configuration held for **30 seconds warm-up plus approximately 300 seconds of sampled steady running** (at least 5 minutes at each configuration overall). The 640 and 416 sample windows were 299.99/300.00 s after excluding first-request overhead; 320 was 300.00 s. There were 31 status/resource snapshots per long run, about 10 s apart. Analysis timers below are means of sampled completed-analysis metrics from the live station; they are **not** a second standalone benchmark, and do not include camera capture/decode time. Rates use completed-counter differences over monotonic elapsed time. The earlier standalone project benchmarks remain separate in the previous table. No inference/benchmark process ran alongside a measured station.

### Timing and sustained intervals

Each timing cell is **left / centre** in milliseconds; rate/count cells use the same order. The counter window can start/end between analyses, so an occasional one-count difference is expected.

| Input | Requested interval per camera | Measured rate per camera | Completed analyses | Preprocess mean | Inference mean | Total analysis mean | Event timeout |
|---|---:|---:|---:|---:|---:|---:|---:|
| 640 | 6 s | 0.167 / 0.167 Hz | 50 / 50 | 20.76 / 24.17 | 2719.54 / 2738.86 | 2740.66 / 2763.43 | 36 s |
| 416 | 3 s | 0.333 / 0.333 Hz | 100 / 100 | 15.51 / 8.47 | 1170.39 / 1163.29 | 1186.25 / 1172.10 | 18 s |
| 320 | 2 s | 0.500 / 0.497 Hz | 150 / 149 | 4.30 / 6.93 | 701.81 / 694.58 | 706.44 / 701.84 | 12 s |

**640: 6 seconds per camera is the shortest validated interval on the tested 0.5-second grid.** A 60-second boundary run at 5.5 s failed: observed mean periods were 5.729/5.742 s and p95 5.840/5.885 s. At 6 s, the full long-run mean periods were 6.011/6.010 s, p95 6.020/6.018 s, with 50/50 completed analyses. A one-second saturation request reached only about 0.20/0.18 Hz. This is not a proof of an exact mathematical minimum between 5.5 and 6 seconds, or a guarantee under every scene/event workload; 6 seconds is the validated practical setting. The 416/320 intervals are validated steady choices, not boundary-search minima.

A run was accepted only when both sources stayed connected without pipeline errors, sampled mean periods stayed within 2% of the requested interval, p95 within 5%, and counter rates met at least 93% of the scheduled rate (allowing integer-window phase). Event timeouts were `max(12, ceil(6 × interval))`, preserving the multi-analysis vote window at slower sampling; this does not shorten the separate sensor MCU debounce/heartbeat intervals.

### Resources, load and thermals

CPU machine is percent of the whole four-core machine; station CPU uses 100% per core. Memory is MiB. Free and available RAM are different quantities and are both reported.

| Input | Station RSS mean (range) | MemAvailable mean (range) | MemFree mean (range) | CPU machine / station | Final load average 1/5/15 min | CPU thermal min–max | First / last minute CPU thermal mean |
|---|---:|---:|---:|---:|---|---:|---:|
| 640 | 306.3 (302.4–307.6) | 1014.2 (1009.3–1020.7) | 465.3 (460.0–472.8) | 57.6% / 209.9% | 2.64 / 2.31 / 1.42 | 46.4–52.9°C | 51.75 / 50.98°C |
| 416 | 227.5 (224.7–228.1) | 1082.8 (1075.0–1084.6) | 532.7 (524.6–534.8) | 50.8% / 187.1% | 2.35 / 2.31 / 1.74 | 45.1–51.7°C | 50.02 / 48.52°C |
| 320 | 203.8 (199.2–205.5) | 1101.2 (1091.7–1109.1) | 550.1 (540.6–558.4) | 49.2% / 178.3% | 2.06 / 2.29 / 1.96 | 47.6–50.7°C | 49.25 / 49.38°C |

No kernel entries occurred in any of the three long-run windows: **no USB disconnect, reset, bandwidth, UVC, undervoltage or over-current errors**. Both sources stayed connected in every snapshot and their counters advanced. Absence of logged voltage errors is not an electrical measurement or proof of supply headroom.

Temperature did not keep climbing: 640 cooled slightly between first/last minute, 416 cooled, and 320 was effectively flat. There is **no evidence of progressive thermal throttling in these windows**. Instantaneous CPU frequencies varied with DVFS (614.4–2016 MHz observed during 640); this is not alone proof of thermal throttling. The 640 first-to-last-minute sampled inference means increased about 4% left / 8% centre while CPU temperature decreased, so that variation cannot be assigned to heat from this evidence; the 6-second schedule still held throughout. Longer hot-ambient/event-encoding tests remain unverified.

### Saved configurations and final state

The board-local files are:

| File under `~/acorn/station` | Input | Interval per camera | Timeout | Use |
|---|---:|---:|---:|---|
| `board.local.toml` and `board.demo192.local.toml` | 192 | 1 s | 12 s | **Active after measurement**, two live cameras |
| `board.field640.local.toml` | 640 | 6 s | 36 s | Measured field-size configuration |
| `board.curve416.local.toml` | 416 | 3 s | 18 s | Measured curve point |
| `board.curve320.local.toml` | 320 | 2 s | 12 s | Measured curve point |

To switch at an agreed interruption, stop the current station first; either run the CLI with the chosen file and `ACORN_PANEL_SECRET` set privately from the existing secret file, or copy the chosen file to `board.local.toml` and run `~/acorn/start-station.sh`. The cron launcher always reads `board.local.toml`, so copying to that file also selects the next boot's configuration. For example, **after stopping the running station**:

```sh
cp "$HOME/acorn/station/board.field640.local.toml" "$HOME/acorn/station/board.local.toml"
"$HOME/acorn/start-station.sh"
# To restore the demonstrated two-live fast mode, again stop station first:
cp "$HOME/acorn/station/board.demo192.local.toml" "$HOME/acorn/station/board.local.toml"
"$HOME/acorn/start-station.sh"
```

The measurement driver used separate `curve-*.local.toml` files, a private runtime secret, and the same exclusive station lock; it left the boot-time demo selection intact throughout and restored it in a `finally` step. Diagnostic driver script: `/tmp/acorn-profile-curve.py` on the board. Raw samples, summaries, probe logs and per-run kernel logs are retained in `~/acorn/measurements/curve`; these are outside the public repository. The active input 192, two live JPEG endpoints (HTTP 200), increasing analysis counters, MCU protocol 1, no bridge error and fresh sensor telemetry were rechecked after restoration.

The repository field profile now follows the measured six-second interval and 36-second timeout. Its confidence threshold is 0.25, while this controlled timing curve used 0.35. The station README keeps exact field-profile performance explicitly pending; this curve does not validate the exact new profile.


## 2026-11-14 screen-demo smoke investigation — UNO Q and Mac evidence

The board was handed over after the whole-system test with source snapshot **4436f38**, its prior station directory retained as `~/acorn/station.backup-20261114-0925`. Active settings were two live 320×240 YUYV sources, DEMO input 192, confidence 0.35, requested 1 analysis/s/camera. At takeover, `capture.py`, `detector.py`, `runtime.py` and `alarm.py` matched this Mac's source hashes exactly. No model, firmware, kernel, boot setting, package, serial port or LoRa implementation was changed for this investigation.

**[UNO Q, capture and inference]** A temporary `/tmp/acorn-live-diagnostic.py` wrapper launched the unmodified CLI under the same exclusive station lock, private panel secret and existing config. It captured 40 timestamped lossless PNG arrays per source **immediately before `CaptureWorker.latest.put`**, plus each exact analysed BGR array, pixel hashes, pre-threshold top-five raw model outputs, tensor shapes/ranges, post-NMS boxes, timings and actual event openings. These are genuine inference results; nothing was injected into the tracker or event store. The original launch/config were saved under the UTC-dated `~/acorn/measurements/smoke-diagnosis-*` directory before the brief restart. The wrapper is diagnostic only; the final normal launch must use the original launcher.

**[Mac, replay of UNO Q pixels]** All 40 publication PNGs per camera were run through the production detector at 192/320/416/640 and thresholds 0.10/0.20/0.25/0.35/0.45. At 192, highest raw scores were **0.209 left / 0.161 centre**, with zero 0.35 detections or suspicions. The first 40 exact analysed PNGs per camera were also compared at 192: Mac vs UNO Q maximum-score absolute differences **≤0.003002**, mean **0.000205**. This does not support a live-only RGB/normalisation bug. Mixed captures include a small paused browser player, full-screen fire footage and hands; they are not synchronized to the direct source file.

**[Mac, direct-file controls]** The Guardian Victoria/Buchan video, candidate identified from the caption (`NmyWqgBBhzY`; exact owner URL still awaiting confirmation), produces **no suspicion at 0.35 at any of 192/320/416/640**, for either native 1280×720 or working 320×240 pixels, across 85 one-second samples. At 640 peak raw score is **0.085 / 0.077**. This is a model/content limitation even before screen recapture. The project's daylight smoke clip still alarms; increasing model input does not reliably repair the Guardian clip. Details and the retained threshold sweeps are in [the quality report](../station/DETECTION_VS_INPUT_SIZE.md#12-screen-demo-diagnosis-2026-11-14).

**[UNO Q, direct-file controls]** Using the same detector and tracker at 192/0.35 with 320×240 working frames and video-time 1-Hz samples: smoke **46/54** detections, one suspicion opening at **video 3 s**, confidence **0.3705104**; fog **0/46**, cloud **0/34**, glare **0/42** detections, no suspicions. All clips were decoded to completion. This separate offline replay ran while the station remained live, so neither its wall-clock duration nor concurrently sampled station timings are a standalone speed measurement. Results are retained as `~/acorn/measurements/smoke-live-20261114/file-check.json`.

**[UNO Q, image integrity]** Displaced rectangular blocks are visible in lossless centre publication samples at Unix timestamps **1794641358.896942** and **1794641359.935038**, as well as the other tester's JPEG previews. Thus at least some malformed image content reaches the model path. The existing zero-filled-YUV green-footer guard **accepts** these arrays; it does not test arbitrary geometric rearrangement. The precise underlying USB/driver/camera cause is unproven. No generic visual “corruption detector” was added that could reject legitimate smoke scenes.

A reversible capture-only trial explicitly requests **YUYV 320×240 at 5 fps on both cameras**, preserving input 192, confidence 0.35 and the complete alarm rule. Both drivers reported **5.000 fps** after restart. The previous active TOML is retained as `board.before-smoke-lowfps-<UTC timestamp>.local.toml`; the normal launcher was not edited. Initial 40 publication PNGs per source at the lower rate have no visually obvious displaced blocks, **but they show a nearly stationary screen**; this is not proof that moving-image corruption is eliminated. Final acceptance requires the live moving-smoke and hall/ordinary-video controls in [DEMO.md](../DEMO.md#live-camera-screen-demonstration--2026-11-14-diagnosis).

Evidence: `~/acorn/measurements/smoke-live-20261114/` and `smoke-lowfps-20261114/` on the board; copies under the supplied Mac `detection-frames/lossless/` directory. PNGs, exact timestamps, manifests, raw score traces and local resource records remain private. The offline `diagnose_smoke.py` improvement retains exact output tensors with `--save-inputs` and uncensored top-score summaries; it does not alter service decisions. **[Mac validation]** full station suite **248 passed**, panel suite **36 passed**, one existing upstream TestClient deprecation warning. Physical left-only smoke latency and hall/ordinary-video negative windows remain pending until the owner positions the hardware.

**[UNO Q, 5-fps capture trial, measured]** A **207.20-second** steady window (42 status/resource snapshots, no concurrent file inference) completed **206 left / 205 centre** analyses. Mean ORT inference **267.89 / 266.65 ms**, total analysis **274.23 / 269.78 ms**, mean start-to-start interval **1.00927 / 1.00936 s**. Station RSS mean **175.97 MiB**, range **175.84–176.06 MiB**; CPU thermal zones **45.1–48.2°C**. Actual decoded USB capture was approximately **3.1 / 3.3 fps**, despite the accepted 5-fps request. The temporary PNG/score instrumentation was active and no event encoder ran. Both views still showed the stationary Sky News screen; **zero suspicions in this window is not a hall or ordinary-video negative test**. These figures describe the capture-only trial, not a validated smoke-on-screen setting.

**Final handback state, 2026-11-14:** physical camera positioning was requested repeatedly, but no readiness confirmation or view of the project clip arrived. The nearly stationary Sky News screen therefore cannot count as the required positive or negative validation. The 5-fps trial was **not adopted** without moving-scene evidence: its TOML was retained as `board.smoke-lowfps-trial-<UTC timestamp>.local.toml`, and `board.local.toml` was restored from `board.before-smoke-lowfps-20261114T073934Z.local.toml`. The temporary wrapper and resource sampler were stopped, and the original `~/acorn/start-station.sh` restarted the normal service. No live instrumentation is imported by that launch. The offline diagnostic script/test changes remain deployed with dated copies of replaced files. **The live screen-demo fix remains unproven; no time-to-suspicion or camera-isolation result is claimed.** The next required action is the owner's left-only moving-smoke rehearsal, followed by 3-minute hall and 3-minute ordinary-video controls. The 207-second trial figures above remain trial measurements, not final-deployment measurements.

**[UNO Q, final restoration check]** Authenticated status after the normal launch reports DEMO 192 / 0.35 / 1 Hz, both live 320×240 YUYV sources connected, increasing counters and no pipeline/runtime/retention error. Latest sampled inference was 288.1 / 293.9 ms, total analysis 290.5 / 301.0 ms; these are individual restoration samples, not a new sustained benchmark. MCU telemetry was fresh. `smoke-final-restoration.json` retains the check.


## 2026-11-14 live screen smoke fix — center crop

Times are UTC (local = UTC+2). **[UNO Q]** unless marked otherwise.

**State at takeover (08:26).** The board had booted at about 07:19. The station ran the previous agent's *uncommitted* strip-displacement frame guard and the 5-fps capture trial configuration (`capture_format = "YUYV"`, `capture_fps = 5.0` on both cameras), re-applied at 08:21 despite the earlier rollback note. Both cameras were connected and streaming; no USB, UVC or bandwidth kernel messages since boot. The owner's “only one camera” observation matched that agent's single-camera trials (several restarts 07:2x–08:21). Its guard had flagged 0 of about 11,000 frames in its own 5/10/30-fps trials. At 08:31 the guard was replaced by the committed capture code (dated copy in `~/acorn/measurements/restore-head-20261114T083124Z`). The 5-fps request is still active (measured capture about 3.1 fps; analysis held 1 Hz); no displaced blocks were seen in moving frames at that rate, which does not prove they cannot occur.

**Regression check.** Between the owner's “it worked around 03:00 local” and the takeover, the detector was byte-identical, the alarm/runtime changes did not alter the decision path at 1 Hz, and input 192 / 0.35 / 1 Hz were unchanged. The event store showed only **one** live-camera suspicion before today's work: left camera, 01:30:28, peak 0.708, full-frame box, a frame-filling ground-level crown-fire video on a screen (the video itself is not recorded). The earlier 23:46–00:21 suspicions came from the `smoke.ogv` **file** source. Replaying the 01:30 event clip through the current code still scored 0.44–0.66. The failures were footage and framing, not a code regression.

**Screen recapture loss.** Filmed at input 192 with the full-frame letterbox, the project clip on a laptop scored 0.00–0.05 where the same clip as a file scores 0.37–0.67. Both cameras render a screen blue and flat (blue/red ≈ 1.59 left, 1.50 centre, ≈ 1.32 in the file; left's darkest decile ≈ 40 levels higher than centre's). V4L2 controls (manual white balance 4500/6500 K, exposure 100–600, contrast, brightness, saturation, gamma) reached at most 0.14 and were reset to defaults. [Mac, on saved board frames] Software corrections were rejected: grey-world + levels lifted a Pyronear no-smoke photo to 0.55 and barely helped centre; CLAHE lifted hall and fireplace frames past 0.35.

**Center crop.** `detector_view = "center_crop"` (commit `8a05ecd`) analyses the centred 240×240 square of each 320×240 frame at input 192 instead of letterboxing. Deployed 09:41 with dated copies in `~/acorn/measurements/center-crop-deploy-20261114T094130Z`; `board.local.toml` gained that one line. Live, with the project clip full screen and the player controls hidden, the **Center camera raised suspicions at 10:00:45, 10:01:39 and 10:02:36** (one per loop; peaks 0.743 / 0.759 / 0.621; 3 s from first raw 0.20 to the suspicion), while Left on the hall stayed silent. With the player bar in view, both cameras scored ≤ 0.08. Measured over 513 analyses per camera at this setting: mean start-to-start interval 1.012 / 1.011 s (p95 1.020), ORT inference 276 ms, total analysis 281 / 282 ms, station RSS 180 MiB, MemAvailable 1115 MiB, CPU thermal 49.8 / 50.4 °C, load average about 1.5. These timings were taken with the score logger running.

**Disk-full outage, caused by the diagnostic logger.** A temporary wrapper saved a PNG of every analysed frame and filled the home partition (823 MB of PNGs). From about **09:21 to 09:39** analysis failed with `OSError: [Errno 28] No space left on device` on both cameras while previews kept arriving. The PNGs were deleted (96 kept), the normal launcher restarted, and the event database passed `integrity_check` with all 36 events. Later logging kept scores only, or at most 600 PNGs per camera and stopped below 400 MB free. Two further short gaps (about 1 min at 09:43 and 30 s at 10:10) came from a `kill` whose pattern matched the operator's own shell; select the station by PID from `ps` output, never by a pattern that appears in the command being run.

**Direct Wi-Fi access.** The launcher already binds all interfaces on port 8080, and the cron `@reboot` entry uses the same launcher. From the Mac over the venue Wi-Fi (no tunnel), the login page and a camera image both answered **401** without a session: the panel is reachable on the board's DHCP address and requires the panel secret. The address can change after a reboot. No bind or network setting was changed.

**Unexplained restart, then off the network.** At about 10:50 the station was found running as a low PID started by cron and `/tmp` was empty: the board had restarted, not by any command in this work. Within minutes it stopped answering ping, SSH and HTTP for more than four minutes, with no USB/ADB connection either; the owner then unplugged it. The kernel log for that restart has not been read. At that point `board.local.toml` contained `center_crop` and the 5-fps capture request, and the board still ran the **Turkish** panel: the English panel (commit `fe1f57f`) is **not deployed**. Steps for return are in [`station/BOARD_RETURN_CHECKLIST.md`](../station/BOARD_RETURN_CHECKLIST.md).
