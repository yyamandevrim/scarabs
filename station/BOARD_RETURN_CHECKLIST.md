# UNO Q return checklist — after the 2026-11-14 drop-off

The board restarted for an unknown reason, then left the network and was unplugged (see [board record](../firmware/BOARD_NOTES.md#2026-11-14-live-screen-smoke-fix--center-crop)). Work through these steps in order when it is plugged in again. Each step says what to run or look at and what you should see. Stop and investigate at the first unexpected result. **Do not reboot or power-off without the owner's agreement.**

Conventions: `B` is your private SSH wrapper or `ssh arduino@BOARD_NAME.local`; the board address and panel secret stay out of this file. When selecting the station process, use the bracket pattern `[f]orest-station` so the search cannot match the shell running it (a plain pattern killed the operator's own SSH shell twice).

## 1. Boot, configuration, disk, cameras, analysis

1. Reachability and boot: `B 'uptime; journalctl --list-boots --no-pager | tail -3'`. Expected: answers; one new boot since the drop-off.
2. Why it went away: `B 'journalctl -k -b -1 --no-pager | tail -80'` (previous boot, if the journal is persistent) and `B 'dmesg | grep -iE "usb|uvc|voltage|over-current|thermal|wlan|brcm|ath" | tail -40'`. Look for undervoltage, USB resets or disconnects, hub errors, Wi-Fi firmware crashes and thermal trips. Record what you find in the board notes, including "nothing found".
3. Station started by cron with the board config: `B 'ps -eo pid,etime,args | grep "[f]orest-station"; grep -E "^(profile|input_size|detector_view|confidence|analysis_hz)" ~/acorn/station/board.local.toml'`. Expected: one process, `--config board.local.toml serve --host 0.0.0.0 --port 8080`; `profile = "demo"`, `input_size = 192`, `detector_view = "center_crop"`, `confidence = 0.35`, `analysis_hz = 1.0`.
4. Disk: `B 'df -h ~ | tail -1; du -sh ~/acorn/measurements/* | sort -h | tail -5'`. Expected: at least 600 MB free. Delete only diagnostic PNG folders you created (`live-colour-*` holds up to 1200 PNGs), never `data-board-bringup`.
5. Cameras: `B 'ls -l /dev/v4l/by-path/ | grep index0; cat /sys/module/uvcvideo/parameters/quirks'`. Expected: both `usb-0:1.1:1.0` and `usb-0:1.4.4:1.0` `video-index0` links; quirks `128`.
6. Panel: open the panel and sign in. Expected: Left and Center previews, both connected, analysis counters rising, no "Analysis unavailable" message. In `/api/status`: `runtime.state = running`, `analysis_profile.detector_view = center_crop`, both `pipeline_error = null`, `analysis_hz` ≈ 1.0 each.

## 2. Deploy the current code (English panel, centre views)

From the repository root on the Mac, after `git pull --rebase`:

```sh
TS=$(date -u +%Y%m%dT%H%M%SZ)
COPYFILE_DISABLE=1 tar -czf /tmp/acorn-station-$TS.tgz station/station station/tests station/pyproject.toml station/uv.lock \
  --exclude='__pycache__' --exclude='.pytest_cache'
scp /tmp/acorn-station-$TS.tgz arduino@BOARD_NAME.local:/tmp/
B "set -e; D=~/acorn/measurements/deploy-$TS; mkdir -p \$D /tmp/acorn-new
   cd ~/acorn/station; cp -a station tests pyproject.toml uv.lock board.local.toml \$D/
   tar -xzf /tmp/acorn-station-$TS.tgz -C /tmp/acorn-new
   cp -a /tmp/acorn-new/station/station/. station/; cp -a /tmp/acorn-new/station/tests/. tests/
   cmp -s /tmp/acorn-new/station/uv.lock uv.lock || echo 'LOCK CHANGED: stop, run uv sync --locked first'"
```

This keeps `board.local.toml`, `data-board-bringup/`, `.venv`, `models/` and `media/` untouched. Then:

1. Focused tests on the board with the station still running: `B 'cd ~/acorn/station && .venv/bin/python -m pytest -q tests/test_detector_crop.py tests/test_centre_views.py tests/test_profiles.py'`. Expected: all pass.
2. Restart the documented way: `B 'P=$(pgrep -f "[f]orest-station --config"); kill $P; while kill -0 $P 2>/dev/null; do sleep 0.5; done; setsid nohup ~/acorn/start-station.sh >> ~/acorn/station.log 2>&1 < /dev/null &'`.
3. Expected within 20 s: the panel login page and panel text are **English** ("Smoke suspicion", "Left", "Center"). Both cameras analysing, `detector_view = center_crop`, no pipeline error.
4. To roll back, copy `~/acorn/measurements/deploy-$TS/station` and `tests` back and restart the same way.

## 3. Live confirmation: Crane loop, center_crop

1. Laptop plays `LOOP_01_crane_fire_22-39s_x10.mp4` **truly full screen**, looping, mouse off the screen (no player bar or taskbar). The screen fills the **Center** camera's whole view with the plume tops in frame. **Left** looks at the hall.
2. Record two minutes of per-analysis raw scores. Either use a score-only logger (no images, or a hard cap with a free-space stop), or poll `/api/status` and the event list once a second.
3. Record time from plume in view to the new **Smoke suspicion** card, camera, opening and peak confidence. Expected: suspicion on Center within about 3–5 s; Left silent.
4. Swap roles (screen on Left, Center on the hall) and repeat. Left has not fired live yet.

## 4. Same on centre_zoom, then choose

1. Set `detector_view = "centre_zoom"` in `board.local.toml` (dated copy first), restart as in 2.2, and repeat step 3 for two minutes on each camera.
2. Read `analysis_ms` and `analysis_hz` from `/api/status` for both cameras. It runs two inferences per analysis (about 0.55–0.6 s estimated on this board, unmeasured).
3. **Rule:** keep `center_crop` unless `centre_zoom` is clearly better live (more frames over 0.35 *and* suspicions at least as fast on both cameras) **and** still gives about one analysis per second per camera (≥ 0.9 Hz each with two cameras). Otherwise restore the `center_crop` line and restart.

## 5. Negatives, on the chosen view

1. Three minutes of the empty hall on both cameras. Expected: no new suspicion.
2. Three minutes of an ordinary non-smoke video (the fireplace video was used before) full screen in front of the camera that saw the smoke. Expected: no new suspicion.
3. Fog, cloud and glare files: the board replay at 192 gave 0 detections and 0 suspicions with the full view. Re-run with the chosen view using the offline replay, not the live station: `B 'cd ~/acorn/station && .venv/bin/forest-station --config board.local.toml benchmark media/fog.webm --frames 40 --stride 25'` (and `cloud.webm`, `glare.webm`). Expected: `positive_frames` and `alarm_positive_frames` 0. This loads the CPU, so do it when no live measurement is running.

## 6. Flame sensor and LED

`/api/status` → `mcu.link.mcu_protocol = 1`, `router_connected = true`, fresh `mcu.flame_sensor.last_update`. Bring a small IR source (lighter flame) within about 1 m of the KY-026. Expected: `triggered = true` and a separate local flame-sensor event (not a camera suspicion), and the LED state changes. Remove it and the state returns to normal. Measured distance is still to be recorded by the team.

## 7. Camera unplug

Unplug the Left camera's USB cable only. Expected: Left shows "connection lost" within a few seconds; Center keeps analysing; no runtime error. Replug into the **same** port. Expected: the same `by-path` link returns and Left reconnects within a few seconds with counters rising. Check `B 'dmesg | tail -20'` for a clean re-enumeration with quirk 0x80.

## 8. Direct Wi-Fi URL

`B 'ip -4 -o addr show wlan0'` gives the current address (DHCP, may change after a reboot). From a phone or laptop on the same Wi-Fi open `http://<that address>:8080`. Expected: login page. Without signing in, `/api/status` returns 401. After signing in, the panel works without any SSH tunnel. The tunnel remains a fallback.

## If the board drops off the network again

- Power first: the board's USB-C supply, the dongle/hub power and cables. Check that cameras and hub are seated. The kit hub carries both cameras and Ethernet at USB 2 speed.
- Ask what changed physically (cable moved, something plugged into the hub) before touching anything.
- After it reconnects, read the kernel log of the previous boot (step 1.2) and the station log tail (`~/acorn/station.log`) before restarting anything.
- Never use diagnostic loggers that write unbounded images. The disk-full outage on 2026-11-14 stopped analysis for 18 minutes.
