# ACORN · terminal-code capture manifest

Captured 2026-11-15 from commit `002761196c82e6ab2da9bcb60a1e7133ff58719f` — **working tree with uncommitted changes**. Source snapshots and hashes reflect the working tree at capture time. No tracked source was edited by this capture task.

23 unique clips / 46 MP4 files; 128 still PNG files. Unique footage duration: **319.900 seconds** (downscales duplicate the same timeline).

Folder: `/Users/yamandevrim/.t3/projects/junction/pitch/captures/broll/terminal-code`. Contact sheet: `/Users/yamandevrim/.t3/projects/junction/pitch/captures/broll/terminal-code/contact-sheet.png`.

## Method and conditions

All media is an offline engineering render. No screen, real terminal window, browser UI, OS chrome, cursor or audio was recorded. Headless Playwright Chromium uses a 1440×810 CSS viewport at DPR 2, repository IBM Plex Mono and #090e13. Browser-rendered source rasters are smoothly cropped at 30 fps; a separate offline terminal renderer replays untouched real PTY output. H.264, yuv420p, CRF 14, +faststart; every landscape clip also has a Lanczos 1920×1080 version. No phone assets. No server or port was used. All capture-started processes exited.

Code is unmodified file content, syntax-highlighted by Pygments, with visual wrapping only. Each source snapshot has its original SHA-256 in renderer/code-shots.json. Source viewport clips have 1 s start/end holds and cosine-eased continuous scrolling with 30 unique samples/s during movement (pixel rounding can repeat a frame near the eased endpoints). Whole-file PNGs are intentionally taller than 16:9; their 1920-wide companions preserve aspect ratio. Detector source is the unchanged L1–87 excerpt: the later Turkish annotation string is excluded from all frames.

Terminal command characters are revealed at 31 characters/s, with a 1 s opening hold. PTY chunk arrival timing is real; Station core output alone is compressed by the factor in the table below. Commands remain real argv, shell-quoted for display. The output is not rewritten or redacted. CRLF/ANSI interpretation is display formatting. After the real run completes, long transcripts pan for 5 s so their final lines remain legible, followed by a final hold. Full transcripts are also supplied as tall PNGs.

Codec vectors are explicitly labelled examples, not live detections or radio transmissions. CPU smoke inference uses the real existing local model and recorded clip. Placement calculations use real prepared local rasters and the current production analysis function; its generated cache is isolated inside this output folder. Performance results are true machine-under-load measurements, not isolated benchmarks or UNO Q claims. Artifact handoff is a dry run: no upload/download.

## Coverage and limitations

- Included: nine source clips; Station core, Ground and Placement Python tests; firmware host logic; all three Node suites; Station/Ground/benchmark help; 40-byte status and 42-byte smoke codec round trips with CRC rejection; smoke CPU benchmark; two-preset placement analysis; artifact dry run; tracked repository tree at depth two; header/smoke/status/airtime tables from PACKETS.md.
- Standard placement benchmark/report scripts were skipped because they write project files or select unassigned ephemeral ports. A real in-process isolated-cache analysis is supplied instead.
- The full Station suite initially passed 315 tests (one deselected). Its warning output contained a home path, so that take is excluded. The clean rerun timed out the cloud-video analysis-count integration test under concurrent load (314 passed, one failed); its traceback is also excluded. The isolated cloud integration subsequently passed (1 passed, 13.05 s pytest time). This is an observed timing limitation; no product fix or proven persistent defect is claimed.
- Station launcher tests and the UDP test are excluded because they bind ephemeral ports outside 8321–8329. The rendered Station core subset passes 96 tests, one deselected. Ground: 24; Placement: 89; Node: 45/13/23; firmware: 150 host checks.
- Board, radio, physical sensor, network/download and hardware-dependent commands are omitted. No app UI was evaluated or changed.
- Repo-tree stills explicitly show tracked source paths, excluding ignored local/runtime material and untracked files. Long full-page stills are extra formats, alongside the required 16:9 viewport stills.

## Command provenance and timing

| Clip | Actual command / relative working directory | PTY wall time | Output playback | Conditions |
|---|---|---:|---|---|
| terminal-code-10-station-core-tests | `uv run --offline --frozen pytest -q --disable-warnings tests/test_lora.py tests/test_detector.py tests/test_alarm.py -k 'not udp_exact_bytes_loss_and_serial_skeleton'` in `station` | 21.140 s | 1.815× real time | Station core regression suite |
| terminal-code-11-ground-tests | `uv run --offline --frozen pytest -q --color=no --disable-warnings` in `ground` | 3.797 s | 1.000× real time | Ground regression suite |
| terminal-code-12-placement-tests | `uv run --offline --frozen pytest -q --color=no --disable-warnings` in `placement` | 7.882 s | 1.000× real time | Placement regression suite |
| terminal-code-13-firmware-tests | `../../pitch/captures/broll/terminal-code/commands/acorn-test-logic vectors.txt` in `firmware/test` | 0.135 s | 1.000× real time | Host-compiled C++ logic only; no connected MCU. |
| terminal-code-14-station-node-tests | `node --test tests/panel.test.mjs` in `station` | 7.783 s | 1.000× real time | Station panel tests |
| terminal-code-15-ground-node-tests | `node --test tests/dashboard.test.mjs` in `ground` | 2.239 s | 1.000× real time | Ground dashboard tests |
| terminal-code-16-placement-node-tests | `node --test tests/ui_metrics.cjs tests/ui_charts.cjs tests/ui_map_display.cjs tests/ui_requests.cjs` in `placement` | 1.863 s | 1.000× real time | Placement request tests |
| terminal-code-17-station-help | `uv run --offline --frozen forest-station --help` in `station` | 0.285 s | 1.000× real time | Station command line |
| terminal-code-18-ground-help | `uv run --offline --frozen acorn-ground --help` in `ground` | 0.472 s | 1.000× real time | Ground command line |
| terminal-code-19-station-benchmark-help | `uv run --offline --frozen forest-station benchmark --help` in `station` | 0.289 s | 1.000× real time | Detector benchmark options |
| terminal-code-20-packet-roundtrip | `uv run --offline --frozen python ../pitch/captures/broll/terminal-code/commands/packet_roundtrip.py` in `station` | 0.159 s | 1.000× real time | Binary codec example vectors |
| terminal-code-21-detector-benchmark | `uv run --offline --frozen python ../pitch/captures/broll/terminal-code/commands/detector_benchmark.py` in `station` | 5.777 s | 1.000× real time | Actual recorded smoke clip; real model inference on this Mac, demo profile; not a board performance claim. |
| terminal-code-22-artifact-dry-run | `placement/.venv/bin/python tools/upload_artifacts.py --dry-run` in `.` | 0.177 s | 1.000× real time | Artifact handoff dry run |
| terminal-code-23-placement-benchmark | `uv run --offline --frozen python ../pitch/captures/broll/terminal-code/commands/placement_benchmark.py` in `placement` | 4.737 s | 1.000× real time | Prepared-raster geometric analysis |

## Delivered media

| File | Duration | Resolution | FPS | Source / state |
|---|---:|---|---:|---|
| [video/terminal-code-01-mcu-sketch-1080.mp4](video/terminal-code-01-mcu-sketch-1080.mp4) | 14.000 s | 1920×1080 | 30 | Unmodified `firmware/acorn_mcu/acorn_mcu.ino`; slow source scroll |
| [video/terminal-code-01-mcu-sketch.mp4](video/terminal-code-01-mcu-sketch.mp4) | 14.000 s | 2880×1620 | 30 | Unmodified `firmware/acorn_mcu/acorn_mcu.ino`; slow source scroll |
| [video/terminal-code-02-flame-logic-1080.mp4](video/terminal-code-02-flame-logic-1080.mp4) | 14.000 s | 1920×1080 | 30 | Unmodified `firmware/acorn_mcu/acorn_logic.h`; slow source scroll |
| [video/terminal-code-02-flame-logic.mp4](video/terminal-code-02-flame-logic.mp4) | 14.000 s | 2880×1620 | 30 | Unmodified `firmware/acorn_mcu/acorn_logic.h`; slow source scroll |
| [video/terminal-code-03-smoke-detector-1080.mp4](video/terminal-code-03-smoke-detector-1080.mp4) | 14.000 s | 1920×1080 | 30 | Unmodified `station/station/detector.py`; slow source scroll |
| [video/terminal-code-03-smoke-detector.mp4](video/terminal-code-03-smoke-detector.mp4) | 14.000 s | 2880×1620 | 30 | Unmodified `station/station/detector.py`; slow source scroll |
| [video/terminal-code-04-packet-codec-1080.mp4](video/terminal-code-04-packet-codec-1080.mp4) | 14.000 s | 1920×1080 | 30 | Unmodified `station/station/lora/protocol.py`; slow source scroll |
| [video/terminal-code-04-packet-codec.mp4](video/terminal-code-04-packet-codec.mp4) | 14.000 s | 2880×1620 | 30 | Unmodified `station/station/lora/protocol.py`; slow source scroll |
| [video/terminal-code-05-placement-engine-1080.mp4](video/terminal-code-05-placement-engine-1080.mp4) | 14.000 s | 1920×1080 | 30 | Unmodified `placement/forest_placement/engine.py`; slow source scroll |
| [video/terminal-code-05-placement-engine.mp4](video/terminal-code-05-placement-engine.mp4) | 14.000 s | 2880×1620 | 30 | Unmodified `placement/forest_placement/engine.py`; slow source scroll |
| [video/terminal-code-06-spatial-voting-1080.mp4](video/terminal-code-06-spatial-voting-1080.mp4) | 14.000 s | 1920×1080 | 30 | Unmodified `station/station/alarm.py`; slow source scroll |
| [video/terminal-code-06-spatial-voting.mp4](video/terminal-code-06-spatial-voting.mp4) | 14.000 s | 2880×1620 | 30 | Unmodified `station/station/alarm.py`; slow source scroll |
| [video/terminal-code-07-terrain-sightlines-1080.mp4](video/terminal-code-07-terrain-sightlines-1080.mp4) | 14.000 s | 1920×1080 | 30 | Unmodified `placement/forest_placement/core.py`; slow source scroll |
| [video/terminal-code-07-terrain-sightlines.mp4](video/terminal-code-07-terrain-sightlines.mp4) | 14.000 s | 2880×1620 | 30 | Unmodified `placement/forest_placement/core.py`; slow source scroll |
| [video/terminal-code-08-packet-receiver-1080.mp4](video/terminal-code-08-packet-receiver-1080.mp4) | 14.000 s | 1920×1080 | 30 | Unmodified `ground/ground/receiver.py`; slow source scroll |
| [video/terminal-code-08-packet-receiver.mp4](video/terminal-code-08-packet-receiver.mp4) | 14.000 s | 2880×1620 | 30 | Unmodified `ground/ground/receiver.py`; slow source scroll |
| [video/terminal-code-09-airtime-budget-1080.mp4](video/terminal-code-09-airtime-budget-1080.mp4) | 14.000 s | 1920×1080 | 30 | Unmodified `station/station/lora/radio.py`; slow source scroll |
| [video/terminal-code-09-airtime-budget.mp4](video/terminal-code-09-airtime-budget.mp4) | 14.000 s | 2880×1620 | 30 | Unmodified `station/station/lora/radio.py`; slow source scroll |
| [video/terminal-code-10-station-core-tests-1080.mp4](video/terminal-code-10-station-core-tests-1080.mp4) | 25.000 s | 1920×1080 | 30 | Station core regression suite; real output; timed command replay |
| [video/terminal-code-10-station-core-tests.mp4](video/terminal-code-10-station-core-tests.mp4) | 25.000 s | 2880×1620 | 30 | Station core regression suite; real output; timed command replay |
| [video/terminal-code-11-ground-tests-1080.mp4](video/terminal-code-11-ground-tests-1080.mp4) | 13.900 s | 1920×1080 | 30 | Ground regression suite; real output; timed command replay |
| [video/terminal-code-11-ground-tests.mp4](video/terminal-code-11-ground-tests.mp4) | 13.900 s | 2880×1620 | 30 | Ground regression suite; real output; timed command replay |
| [video/terminal-code-12-placement-tests-1080.mp4](video/terminal-code-12-placement-tests-1080.mp4) | 18.000 s | 1920×1080 | 30 | Placement regression suite; real output; timed command replay |
| [video/terminal-code-12-placement-tests.mp4](video/terminal-code-12-placement-tests.mp4) | 18.000 s | 2880×1620 | 30 | Placement regression suite; real output; timed command replay |
| [video/terminal-code-13-firmware-tests-1080.mp4](video/terminal-code-13-firmware-tests-1080.mp4) | 10.667 s | 1920×1080 | 30 | Firmware host logic; real output; timed command replay |
| [video/terminal-code-13-firmware-tests.mp4](video/terminal-code-13-firmware-tests.mp4) | 10.667 s | 2880×1620 | 30 | Firmware host logic; real output; timed command replay |
| [video/terminal-code-14-station-node-tests-1080.mp4](video/terminal-code-14-station-node-tests-1080.mp4) | 17.000 s | 1920×1080 | 30 | Station panel tests; real output; timed command replay |
| [video/terminal-code-14-station-node-tests.mp4](video/terminal-code-14-station-node-tests.mp4) | 17.000 s | 2880×1620 | 30 | Station panel tests; real output; timed command replay |
| [video/terminal-code-15-ground-node-tests-1080.mp4](video/terminal-code-15-ground-node-tests-1080.mp4) | 11.467 s | 1920×1080 | 30 | Ground dashboard tests; real output; timed command replay |
| [video/terminal-code-15-ground-node-tests.mp4](video/terminal-code-15-ground-node-tests.mp4) | 11.467 s | 2880×1620 | 30 | Ground dashboard tests; real output; timed command replay |
| [video/terminal-code-16-placement-node-tests-1080.mp4](video/terminal-code-16-placement-node-tests-1080.mp4) | 13.067 s | 1920×1080 | 30 | Placement request tests; real output; timed command replay |
| [video/terminal-code-16-placement-node-tests.mp4](video/terminal-code-16-placement-node-tests.mp4) | 13.067 s | 2880×1620 | 30 | Placement request tests; real output; timed command replay |
| [video/terminal-code-17-station-help-1080.mp4](video/terminal-code-17-station-help-1080.mp4) | 10.000 s | 1920×1080 | 30 | Station command line; real output; timed command replay |
| [video/terminal-code-17-station-help.mp4](video/terminal-code-17-station-help.mp4) | 10.000 s | 2880×1620 | 30 | Station command line; real output; timed command replay |
| [video/terminal-code-18-ground-help-1080.mp4](video/terminal-code-18-ground-help-1080.mp4) | 10.000 s | 1920×1080 | 30 | Ground command line; real output; timed command replay |
| [video/terminal-code-18-ground-help.mp4](video/terminal-code-18-ground-help.mp4) | 10.000 s | 2880×1620 | 30 | Ground command line; real output; timed command replay |
| [video/terminal-code-19-station-benchmark-help-1080.mp4](video/terminal-code-19-station-benchmark-help-1080.mp4) | 10.133 s | 1920×1080 | 30 | Detector benchmark options; real output; timed command replay |
| [video/terminal-code-19-station-benchmark-help.mp4](video/terminal-code-19-station-benchmark-help.mp4) | 10.133 s | 2880×1620 | 30 | Detector benchmark options; real output; timed command replay |
| [video/terminal-code-20-packet-roundtrip-1080.mp4](video/terminal-code-20-packet-roundtrip-1080.mp4) | 11.367 s | 1920×1080 | 30 | Binary codec example vectors; real output; timed command replay |
| [video/terminal-code-20-packet-roundtrip.mp4](video/terminal-code-20-packet-roundtrip.mp4) | 11.367 s | 2880×1620 | 30 | Binary codec example vectors; real output; timed command replay |
| [video/terminal-code-21-detector-benchmark-1080.mp4](video/terminal-code-21-detector-benchmark-1080.mp4) | 17.067 s | 1920×1080 | 30 | Recorded-smoke CPU benchmark; real output; timed command replay |
| [video/terminal-code-21-detector-benchmark.mp4](video/terminal-code-21-detector-benchmark.mp4) | 17.067 s | 2880×1620 | 30 | Recorded-smoke CPU benchmark; real output; timed command replay |
| [video/terminal-code-22-artifact-dry-run-1080.mp4](video/terminal-code-22-artifact-dry-run-1080.mp4) | 10.200 s | 1920×1080 | 30 | Artifact handoff dry run; real output; timed command replay |
| [video/terminal-code-22-artifact-dry-run.mp4](video/terminal-code-22-artifact-dry-run.mp4) | 10.200 s | 2880×1620 | 30 | Artifact handoff dry run; real output; timed command replay |
| [video/terminal-code-23-placement-benchmark-1080.mp4](video/terminal-code-23-placement-benchmark-1080.mp4) | 16.033 s | 1920×1080 | 30 | Prepared-raster geometric analysis; real output; timed command replay |
| [video/terminal-code-23-placement-benchmark.mp4](video/terminal-code-23-placement-benchmark.mp4) | 16.033 s | 2880×1620 | 30 | Prepared-raster geometric analysis; real output; timed command replay |
| [stills/terminal-code-01-mcu-sketch-end-1080.png](stills/terminal-code-01-mcu-sketch-end-1080.png) | — | 1920×1080 | — | Unmodified `firmware/acorn_mcu/acorn_mcu.ino`; scroll end |
| [stills/terminal-code-01-mcu-sketch-end.png](stills/terminal-code-01-mcu-sketch-end.png) | — | 2880×1620 | — | Unmodified `firmware/acorn_mcu/acorn_mcu.ino`; scroll end |
| [stills/terminal-code-01-mcu-sketch-full-1080.png](stills/terminal-code-01-mcu-sketch-full-1080.png) | — | 1920×7939 | — | Unmodified `firmware/acorn_mcu/acorn_mcu.ino`; full source |
| [stills/terminal-code-01-mcu-sketch-full.png](stills/terminal-code-01-mcu-sketch-full.png) | — | 2880×11908 | — | Unmodified `firmware/acorn_mcu/acorn_mcu.ino`; full source |
| [stills/terminal-code-01-mcu-sketch-start-1080.png](stills/terminal-code-01-mcu-sketch-start-1080.png) | — | 1920×1080 | — | Unmodified `firmware/acorn_mcu/acorn_mcu.ino`; scroll start |
| [stills/terminal-code-01-mcu-sketch-start.png](stills/terminal-code-01-mcu-sketch-start.png) | — | 2880×1620 | — | Unmodified `firmware/acorn_mcu/acorn_mcu.ino`; scroll start |
| [stills/terminal-code-02-flame-logic-end-1080.png](stills/terminal-code-02-flame-logic-end-1080.png) | — | 1920×1080 | — | Unmodified `firmware/acorn_mcu/acorn_logic.h`; scroll end |
| [stills/terminal-code-02-flame-logic-end.png](stills/terminal-code-02-flame-logic-end.png) | — | 2880×1620 | — | Unmodified `firmware/acorn_mcu/acorn_logic.h`; scroll end |
| [stills/terminal-code-02-flame-logic-full-1080.png](stills/terminal-code-02-flame-logic-full-1080.png) | — | 1920×9048 | — | Unmodified `firmware/acorn_mcu/acorn_logic.h`; full source |
| [stills/terminal-code-02-flame-logic-full.png](stills/terminal-code-02-flame-logic-full.png) | — | 2880×13572 | — | Unmodified `firmware/acorn_mcu/acorn_logic.h`; full source |
| [stills/terminal-code-02-flame-logic-start-1080.png](stills/terminal-code-02-flame-logic-start-1080.png) | — | 1920×1080 | — | Unmodified `firmware/acorn_mcu/acorn_logic.h`; scroll start |
| [stills/terminal-code-02-flame-logic-start.png](stills/terminal-code-02-flame-logic-start.png) | — | 2880×1620 | — | Unmodified `firmware/acorn_mcu/acorn_logic.h`; scroll start |
| [stills/terminal-code-03-smoke-detector-end-1080.png](stills/terminal-code-03-smoke-detector-end-1080.png) | — | 1920×1080 | — | Unmodified `station/station/detector.py`; scroll end |
| [stills/terminal-code-03-smoke-detector-end.png](stills/terminal-code-03-smoke-detector-end.png) | — | 2880×1620 | — | Unmodified `station/station/detector.py`; scroll end |
| [stills/terminal-code-03-smoke-detector-full-1080.png](stills/terminal-code-03-smoke-detector-full-1080.png) | — | 1920×4269 | — | Unmodified `station/station/detector.py`; full source excerpt L1–87 |
| [stills/terminal-code-03-smoke-detector-full.png](stills/terminal-code-03-smoke-detector-full.png) | — | 2880×6404 | — | Unmodified `station/station/detector.py`; full source excerpt L1–87 |
| [stills/terminal-code-03-smoke-detector-start-1080.png](stills/terminal-code-03-smoke-detector-start-1080.png) | — | 1920×1080 | — | Unmodified `station/station/detector.py`; scroll start |
| [stills/terminal-code-03-smoke-detector-start.png](stills/terminal-code-03-smoke-detector-start.png) | — | 2880×1620 | — | Unmodified `station/station/detector.py`; scroll start |
| [stills/terminal-code-04-packet-codec-end-1080.png](stills/terminal-code-04-packet-codec-end-1080.png) | — | 1920×1080 | — | Unmodified `station/station/lora/protocol.py`; scroll end |
| [stills/terminal-code-04-packet-codec-end.png](stills/terminal-code-04-packet-codec-end.png) | — | 2880×1620 | — | Unmodified `station/station/lora/protocol.py`; scroll end |
| [stills/terminal-code-04-packet-codec-full-1080.png](stills/terminal-code-04-packet-codec-full-1080.png) | — | 1920×5165 | — | Unmodified `station/station/lora/protocol.py`; full source |
| [stills/terminal-code-04-packet-codec-full.png](stills/terminal-code-04-packet-codec-full.png) | — | 2880×7748 | — | Unmodified `station/station/lora/protocol.py`; full source |
| [stills/terminal-code-04-packet-codec-start-1080.png](stills/terminal-code-04-packet-codec-start-1080.png) | — | 1920×1080 | — | Unmodified `station/station/lora/protocol.py`; scroll start |
| [stills/terminal-code-04-packet-codec-start.png](stills/terminal-code-04-packet-codec-start.png) | — | 2880×1620 | — | Unmodified `station/station/lora/protocol.py`; scroll start |
| [stills/terminal-code-05-placement-engine-end-1080.png](stills/terminal-code-05-placement-engine-end-1080.png) | — | 1920×1080 | — | Unmodified `placement/forest_placement/engine.py`; scroll end |
| [stills/terminal-code-05-placement-engine-end.png](stills/terminal-code-05-placement-engine-end.png) | — | 2880×1620 | — | Unmodified `placement/forest_placement/engine.py`; scroll end |
| [stills/terminal-code-05-placement-engine-full-1080.png](stills/terminal-code-05-placement-engine-full-1080.png) | — | 1920×7043 | — | Unmodified `placement/forest_placement/engine.py`; full source |
| [stills/terminal-code-05-placement-engine-full.png](stills/terminal-code-05-placement-engine-full.png) | — | 2880×10564 | — | Unmodified `placement/forest_placement/engine.py`; full source |
| [stills/terminal-code-05-placement-engine-start-1080.png](stills/terminal-code-05-placement-engine-start-1080.png) | — | 1920×1080 | — | Unmodified `placement/forest_placement/engine.py`; scroll start |
| [stills/terminal-code-05-placement-engine-start.png](stills/terminal-code-05-placement-engine-start.png) | — | 2880×1620 | — | Unmodified `placement/forest_placement/engine.py`; scroll start |
| [stills/terminal-code-06-spatial-voting-end-1080.png](stills/terminal-code-06-spatial-voting-end-1080.png) | — | 1920×1080 | — | Unmodified `station/station/alarm.py`; scroll end |
| [stills/terminal-code-06-spatial-voting-end.png](stills/terminal-code-06-spatial-voting-end.png) | — | 2880×1620 | — | Unmodified `station/station/alarm.py`; scroll end |
| [stills/terminal-code-06-spatial-voting-full-1080.png](stills/terminal-code-06-spatial-voting-full-1080.png) | — | 1920×3331 | — | Unmodified `station/station/alarm.py`; full source |
| [stills/terminal-code-06-spatial-voting-full.png](stills/terminal-code-06-spatial-voting-full.png) | — | 2880×4996 | — | Unmodified `station/station/alarm.py`; full source |
| [stills/terminal-code-06-spatial-voting-start-1080.png](stills/terminal-code-06-spatial-voting-start-1080.png) | — | 1920×1080 | — | Unmodified `station/station/alarm.py`; scroll start |
| [stills/terminal-code-06-spatial-voting-start.png](stills/terminal-code-06-spatial-voting-start.png) | — | 2880×1620 | — | Unmodified `station/station/alarm.py`; scroll start |
| [stills/terminal-code-07-terrain-sightlines-end-1080.png](stills/terminal-code-07-terrain-sightlines-end-1080.png) | — | 1920×1080 | — | Unmodified `placement/forest_placement/core.py`; scroll end |
| [stills/terminal-code-07-terrain-sightlines-end.png](stills/terminal-code-07-terrain-sightlines-end.png) | — | 2880×1620 | — | Unmodified `placement/forest_placement/core.py`; scroll end |
| [stills/terminal-code-07-terrain-sightlines-full-1080.png](stills/terminal-code-07-terrain-sightlines-full-1080.png) | — | 1920×5379 | — | Unmodified `placement/forest_placement/core.py`; full source |
| [stills/terminal-code-07-terrain-sightlines-full.png](stills/terminal-code-07-terrain-sightlines-full.png) | — | 2880×8068 | — | Unmodified `placement/forest_placement/core.py`; full source |
| [stills/terminal-code-07-terrain-sightlines-start-1080.png](stills/terminal-code-07-terrain-sightlines-start-1080.png) | — | 1920×1080 | — | Unmodified `placement/forest_placement/core.py`; scroll start |
| [stills/terminal-code-07-terrain-sightlines-start.png](stills/terminal-code-07-terrain-sightlines-start.png) | — | 2880×1620 | — | Unmodified `placement/forest_placement/core.py`; scroll start |
| [stills/terminal-code-08-packet-receiver-end-1080.png](stills/terminal-code-08-packet-receiver-end-1080.png) | — | 1920×1080 | — | Unmodified `ground/ground/receiver.py`; scroll end |
| [stills/terminal-code-08-packet-receiver-end.png](stills/terminal-code-08-packet-receiver-end.png) | — | 2880×1620 | — | Unmodified `ground/ground/receiver.py`; scroll end |
| [stills/terminal-code-08-packet-receiver-full-1080.png](stills/terminal-code-08-packet-receiver-full-1080.png) | — | 1920×9261 | — | Unmodified `ground/ground/receiver.py`; full source |
| [stills/terminal-code-08-packet-receiver-full.png](stills/terminal-code-08-packet-receiver-full.png) | — | 2880×13892 | — | Unmodified `ground/ground/receiver.py`; full source |
| [stills/terminal-code-08-packet-receiver-start-1080.png](stills/terminal-code-08-packet-receiver-start-1080.png) | — | 1920×1080 | — | Unmodified `ground/ground/receiver.py`; scroll start |
| [stills/terminal-code-08-packet-receiver-start.png](stills/terminal-code-08-packet-receiver-start.png) | — | 2880×1620 | — | Unmodified `ground/ground/receiver.py`; scroll start |
| [stills/terminal-code-09-airtime-budget-end-1080.png](stills/terminal-code-09-airtime-budget-end-1080.png) | — | 1920×1080 | — | Unmodified `station/station/lora/radio.py`; scroll end |
| [stills/terminal-code-09-airtime-budget-end.png](stills/terminal-code-09-airtime-budget-end.png) | — | 2880×1620 | — | Unmodified `station/station/lora/radio.py`; scroll end |
| [stills/terminal-code-09-airtime-budget-full-1080.png](stills/terminal-code-09-airtime-budget-full-1080.png) | — | 1920×5720 | — | Unmodified `station/station/lora/radio.py`; full source |
| [stills/terminal-code-09-airtime-budget-full.png](stills/terminal-code-09-airtime-budget-full.png) | — | 2880×8580 | — | Unmodified `station/station/lora/radio.py`; full source |
| [stills/terminal-code-09-airtime-budget-start-1080.png](stills/terminal-code-09-airtime-budget-start-1080.png) | — | 1920×1080 | — | Unmodified `station/station/lora/radio.py`; scroll start |
| [stills/terminal-code-09-airtime-budget-start.png](stills/terminal-code-09-airtime-budget-start.png) | — | 2880×1620 | — | Unmodified `station/station/lora/radio.py`; scroll start |
| [stills/terminal-code-10-station-core-tests-1080.png](stills/terminal-code-10-station-core-tests-1080.png) | — | 1920×1080 | — | Station core regression suite; real output; final output |
| [stills/terminal-code-10-station-core-tests-transcript-full-1080.png](stills/terminal-code-10-station-core-tests-transcript-full-1080.png) | — | 1920×1080 | — | Station core regression suite; real output; full transcript |
| [stills/terminal-code-10-station-core-tests-transcript-full.png](stills/terminal-code-10-station-core-tests-transcript-full.png) | — | 2880×1620 | — | Station core regression suite; real output; full transcript |
| [stills/terminal-code-10-station-core-tests.png](stills/terminal-code-10-station-core-tests.png) | — | 2880×1620 | — | Station core regression suite; real output; final output |
| [stills/terminal-code-11-ground-tests-1080.png](stills/terminal-code-11-ground-tests-1080.png) | — | 1920×1080 | — | Ground regression suite; real output; final output |
| [stills/terminal-code-11-ground-tests-transcript-full-1080.png](stills/terminal-code-11-ground-tests-transcript-full-1080.png) | — | 1920×1080 | — | Ground regression suite; real output; full transcript |
| [stills/terminal-code-11-ground-tests-transcript-full.png](stills/terminal-code-11-ground-tests-transcript-full.png) | — | 2880×1620 | — | Ground regression suite; real output; full transcript |
| [stills/terminal-code-11-ground-tests.png](stills/terminal-code-11-ground-tests.png) | — | 2880×1620 | — | Ground regression suite; real output; final output |
| [stills/terminal-code-12-placement-tests-1080.png](stills/terminal-code-12-placement-tests-1080.png) | — | 1920×1080 | — | Placement regression suite; real output; final output |
| [stills/terminal-code-12-placement-tests-transcript-full-1080.png](stills/terminal-code-12-placement-tests-transcript-full-1080.png) | — | 1920×1080 | — | Placement regression suite; real output; full transcript |
| [stills/terminal-code-12-placement-tests-transcript-full.png](stills/terminal-code-12-placement-tests-transcript-full.png) | — | 2880×1620 | — | Placement regression suite; real output; full transcript |
| [stills/terminal-code-12-placement-tests.png](stills/terminal-code-12-placement-tests.png) | — | 2880×1620 | — | Placement regression suite; real output; final output |
| [stills/terminal-code-13-firmware-tests-1080.png](stills/terminal-code-13-firmware-tests-1080.png) | — | 1920×1080 | — | Firmware host logic; real output; final output |
| [stills/terminal-code-13-firmware-tests-transcript-full-1080.png](stills/terminal-code-13-firmware-tests-transcript-full-1080.png) | — | 1920×1080 | — | Firmware host logic; real output; full transcript |
| [stills/terminal-code-13-firmware-tests-transcript-full.png](stills/terminal-code-13-firmware-tests-transcript-full.png) | — | 2880×1620 | — | Firmware host logic; real output; full transcript |
| [stills/terminal-code-13-firmware-tests.png](stills/terminal-code-13-firmware-tests.png) | — | 2880×1620 | — | Firmware host logic; real output; final output |
| [stills/terminal-code-14-station-node-tests-1080.png](stills/terminal-code-14-station-node-tests-1080.png) | — | 1920×1080 | — | Station panel tests; real output; final output |
| [stills/terminal-code-14-station-node-tests-transcript-full-1080.png](stills/terminal-code-14-station-node-tests-transcript-full-1080.png) | — | 1920×3048 | — | Station panel tests; real output; full transcript |
| [stills/terminal-code-14-station-node-tests-transcript-full.png](stills/terminal-code-14-station-node-tests-transcript-full.png) | — | 2880×4572 | — | Station panel tests; real output; full transcript |
| [stills/terminal-code-14-station-node-tests.png](stills/terminal-code-14-station-node-tests.png) | — | 2880×1620 | — | Station panel tests; real output; final output |
| [stills/terminal-code-15-ground-node-tests-1080.png](stills/terminal-code-15-ground-node-tests-1080.png) | — | 1920×1080 | — | Ground dashboard tests; real output; final output |
| [stills/terminal-code-15-ground-node-tests-transcript-full-1080.png](stills/terminal-code-15-ground-node-tests-transcript-full-1080.png) | — | 1920×1213 | — | Ground dashboard tests; real output; full transcript |
| [stills/terminal-code-15-ground-node-tests-transcript-full.png](stills/terminal-code-15-ground-node-tests-transcript-full.png) | — | 2880×1820 | — | Ground dashboard tests; real output; full transcript |
| [stills/terminal-code-15-ground-node-tests.png](stills/terminal-code-15-ground-node-tests.png) | — | 2880×1620 | — | Ground dashboard tests; real output; final output |
| [stills/terminal-code-16-placement-node-tests-1080.png](stills/terminal-code-16-placement-node-tests-1080.png) | — | 1920×1080 | — | Placement request tests; real output; final output |
| [stills/terminal-code-16-placement-node-tests-transcript-full-1080.png](stills/terminal-code-16-placement-node-tests-transcript-full-1080.png) | — | 1920×1725 | — | Placement request tests; real output; full transcript |
| [stills/terminal-code-16-placement-node-tests-transcript-full.png](stills/terminal-code-16-placement-node-tests-transcript-full.png) | — | 2880×2588 | — | Placement request tests; real output; full transcript |
| [stills/terminal-code-16-placement-node-tests.png](stills/terminal-code-16-placement-node-tests.png) | — | 2880×1620 | — | Placement request tests; real output; final output |
| [stills/terminal-code-17-station-help-1080.png](stills/terminal-code-17-station-help-1080.png) | — | 1920×1080 | — | Station command line; real output; final output |
| [stills/terminal-code-17-station-help-transcript-full-1080.png](stills/terminal-code-17-station-help-transcript-full-1080.png) | — | 1920×1080 | — | Station command line; real output; full transcript |
| [stills/terminal-code-17-station-help-transcript-full.png](stills/terminal-code-17-station-help-transcript-full.png) | — | 2880×1620 | — | Station command line; real output; full transcript |
| [stills/terminal-code-17-station-help.png](stills/terminal-code-17-station-help.png) | — | 2880×1620 | — | Station command line; real output; final output |
| [stills/terminal-code-18-ground-help-1080.png](stills/terminal-code-18-ground-help-1080.png) | — | 1920×1080 | — | Ground command line; real output; final output |
| [stills/terminal-code-18-ground-help-transcript-full-1080.png](stills/terminal-code-18-ground-help-transcript-full-1080.png) | — | 1920×1427 | — | Ground command line; real output; full transcript |
| [stills/terminal-code-18-ground-help-transcript-full.png](stills/terminal-code-18-ground-help-transcript-full.png) | — | 2880×2140 | — | Ground command line; real output; full transcript |
| [stills/terminal-code-18-ground-help.png](stills/terminal-code-18-ground-help.png) | — | 2880×1620 | — | Ground command line; real output; final output |
| [stills/terminal-code-19-station-benchmark-help-1080.png](stills/terminal-code-19-station-benchmark-help-1080.png) | — | 1920×1080 | — | Detector benchmark options; real output; final output |
| [stills/terminal-code-19-station-benchmark-help-transcript-full-1080.png](stills/terminal-code-19-station-benchmark-help-transcript-full-1080.png) | — | 1920×1080 | — | Detector benchmark options; real output; full transcript |
| [stills/terminal-code-19-station-benchmark-help-transcript-full.png](stills/terminal-code-19-station-benchmark-help-transcript-full.png) | — | 2880×1620 | — | Detector benchmark options; real output; full transcript |
| [stills/terminal-code-19-station-benchmark-help.png](stills/terminal-code-19-station-benchmark-help.png) | — | 2880×1620 | — | Detector benchmark options; real output; final output |
| [stills/terminal-code-20-packet-roundtrip-1080.png](stills/terminal-code-20-packet-roundtrip-1080.png) | — | 1920×1080 | — | Binary codec example vectors; real output; final output |
| [stills/terminal-code-20-packet-roundtrip-transcript-full-1080.png](stills/terminal-code-20-packet-roundtrip-transcript-full-1080.png) | — | 1920×1080 | — | Binary codec example vectors; real output; full transcript |
| [stills/terminal-code-20-packet-roundtrip-transcript-full.png](stills/terminal-code-20-packet-roundtrip-transcript-full.png) | — | 2880×1620 | — | Binary codec example vectors; real output; full transcript |
| [stills/terminal-code-20-packet-roundtrip.png](stills/terminal-code-20-packet-roundtrip.png) | — | 2880×1620 | — | Binary codec example vectors; real output; final output |
| [stills/terminal-code-21-detector-benchmark-1080.png](stills/terminal-code-21-detector-benchmark-1080.png) | — | 1920×1080 | — | Recorded-smoke CPU benchmark; real output; final output |
| [stills/terminal-code-21-detector-benchmark-transcript-full-1080.png](stills/terminal-code-21-detector-benchmark-transcript-full-1080.png) | — | 1920×1640 | — | Recorded-smoke CPU benchmark; real output; full transcript |
| [stills/terminal-code-21-detector-benchmark-transcript-full.png](stills/terminal-code-21-detector-benchmark-transcript-full.png) | — | 2880×2460 | — | Recorded-smoke CPU benchmark; real output; full transcript |
| [stills/terminal-code-21-detector-benchmark.png](stills/terminal-code-21-detector-benchmark.png) | — | 2880×1620 | — | Recorded-smoke CPU benchmark; real output; final output |
| [stills/terminal-code-22-artifact-dry-run-1080.png](stills/terminal-code-22-artifact-dry-run-1080.png) | — | 1920×1080 | — | Artifact handoff dry run; real output; final output |
| [stills/terminal-code-22-artifact-dry-run-transcript-full-1080.png](stills/terminal-code-22-artifact-dry-run-transcript-full-1080.png) | — | 1920×1555 | — | Artifact handoff dry run; real output; full transcript |
| [stills/terminal-code-22-artifact-dry-run-transcript-full.png](stills/terminal-code-22-artifact-dry-run-transcript-full.png) | — | 2880×2332 | — | Artifact handoff dry run; real output; full transcript |
| [stills/terminal-code-22-artifact-dry-run.png](stills/terminal-code-22-artifact-dry-run.png) | — | 2880×1620 | — | Artifact handoff dry run; real output; final output |
| [stills/terminal-code-23-placement-benchmark-1080.png](stills/terminal-code-23-placement-benchmark-1080.png) | — | 1920×1080 | — | Prepared-raster geometric analysis; real output; final output |
| [stills/terminal-code-23-placement-benchmark-transcript-full-1080.png](stills/terminal-code-23-placement-benchmark-transcript-full-1080.png) | — | 1920×1171 | — | Prepared-raster geometric analysis; real output; full transcript |
| [stills/terminal-code-23-placement-benchmark-transcript-full.png](stills/terminal-code-23-placement-benchmark-transcript-full.png) | — | 2880×1756 | — | Prepared-raster geometric analysis; real output; full transcript |
| [stills/terminal-code-23-placement-benchmark.png](stills/terminal-code-23-placement-benchmark.png) | — | 2880×1620 | — | Prepared-raster geometric analysis; real output; final output |
| [stills/terminal-code-24-repository-tree-1080.png](stills/terminal-code-24-repository-tree-1080.png) | — | 1920×1080 | — | Tracked source · top two levels · 1 / 2; git ls-files, grouped by actual tracked path at depth 1–2 |
| [stills/terminal-code-24-repository-tree-continued-1080.png](stills/terminal-code-24-repository-tree-continued-1080.png) | — | 1920×1080 | — | Tracked source · top two levels · 2 / 2; git ls-files, continuation |
| [stills/terminal-code-24-repository-tree-continued.png](stills/terminal-code-24-repository-tree-continued.png) | — | 2880×1620 | — | Tracked source · top two levels · 2 / 2; git ls-files, continuation |
| [stills/terminal-code-24-repository-tree-full-1080.png](stills/terminal-code-24-repository-tree-full-1080.png) | — | 1920×1468 | — | Tracked source · top two levels · 1 / 2; git ls-files, grouped by actual tracked path at depth 1–2 |
| [stills/terminal-code-24-repository-tree-full.png](stills/terminal-code-24-repository-tree-full.png) | — | 2880×2202 | — | Tracked source · top two levels · 1 / 2; git ls-files, grouped by actual tracked path at depth 1–2 |
| [stills/terminal-code-24-repository-tree.png](stills/terminal-code-24-repository-tree.png) | — | 2880×1620 | — | Tracked source · top two levels · 1 / 2; git ls-files, grouped by actual tracked path at depth 1–2 |
| [stills/terminal-code-25-packet-header-1080.png](stills/terminal-code-25-packet-header-1080.png) | — | 1920×1080 | — | Binary layout · version 2 header; Unchanged Markdown table contents from station/station/lora/PACKETS.md |
| [stills/terminal-code-25-packet-header.png](stills/terminal-code-25-packet-header.png) | — | 2880×1620 | — | Binary layout · version 2 header; Unchanged Markdown table contents from station/station/lora/PACKETS.md |
| [stills/terminal-code-26-smoke-packet-1080.png](stills/terminal-code-26-smoke-packet-1080.png) | — | 1920×1080 | — | Smoke suspicion · 42 bytes total; Unchanged Markdown table contents from station/station/lora/PACKETS.md |
| [stills/terminal-code-26-smoke-packet-detail-2x-1080.png](stills/terminal-code-26-smoke-packet-detail-2x-1080.png) | — | 1920×1080 | — | Smoke suspicion · 42 bytes total; Unchanged Markdown table contents from station/station/lora/PACKETS.md; 2× detail crop |
| [stills/terminal-code-26-smoke-packet-detail-2x.png](stills/terminal-code-26-smoke-packet-detail-2x.png) | — | 2880×1620 | — | Smoke suspicion · 42 bytes total; Unchanged Markdown table contents from station/station/lora/PACKETS.md; 2× detail crop |
| [stills/terminal-code-26-smoke-packet.png](stills/terminal-code-26-smoke-packet.png) | — | 2880×1620 | — | Smoke suspicion · 42 bytes total; Unchanged Markdown table contents from station/station/lora/PACKETS.md |
| [stills/terminal-code-27-status-packet-1080.png](stills/terminal-code-27-status-packet-1080.png) | — | 1920×1080 | — | Status · 40 bytes total; Unchanged Markdown table contents from station/station/lora/PACKETS.md |
| [stills/terminal-code-27-status-packet.png](stills/terminal-code-27-status-packet.png) | — | 2880×1620 | — | Status · 40 bytes total; Unchanged Markdown table contents from station/station/lora/PACKETS.md |
| [stills/terminal-code-28-packet-airtime-1080.png](stills/terminal-code-28-packet-airtime-1080.png) | — | 1920×1080 | — | Version-2 packet airtime · calculated; Unchanged Markdown table contents from station/station/lora/PACKETS.md |
| [stills/terminal-code-28-packet-airtime-detail-2x-1080.png](stills/terminal-code-28-packet-airtime-detail-2x-1080.png) | — | 1920×1080 | — | Version-2 packet airtime · calculated; Unchanged Markdown table contents from station/station/lora/PACKETS.md; 2× detail crop |
| [stills/terminal-code-28-packet-airtime-detail-2x.png](stills/terminal-code-28-packet-airtime-detail-2x.png) | — | 2880×1620 | — | Version-2 packet airtime · calculated; Unchanged Markdown table contents from station/station/lora/PACKETS.md; 2× detail crop |
| [stills/terminal-code-28-packet-airtime.png](stills/terminal-code-28-packet-airtime.png) | — | 2880×1620 | — | Version-2 packet airtime · calculated; Unchanged Markdown table contents from station/station/lora/PACKETS.md |

## Verification

`renderer/verification.json` records fresh ffprobe stream metadata, SHA-256, full successful decode and the three review-frame positions for every MP4. 46 MP4 files verified. Start/middle/end frames for each resolution were inspected in `review/qa-*.jpg`; source/code and documentation stills were checked for readability, provenance and privacy. Motion checks are recorded in `renderer/motion-check.json`. No completion claim covers an excluded raw take.

## Supporting files

| File | Duration | Resolution | FPS | Purpose |
|---|---:|---|---:|---|
| `commands/README.md` | — | — | — | Reproduction script, source render raster or capture metadata |
| `commands/acorn-test-logic` | — | — | — | Reproduction script, source render raster or capture metadata |
| `commands/capture.py` | — | — | — | Reproduction script, source render raster or capture metadata |
| `commands/detector_benchmark.py` | — | — | — | Reproduction script, source render raster or capture metadata |
| `commands/packet_roundtrip.py` | — | — | — | Reproduction script, source render raster or capture metadata |
| `commands/placement-cache/868286401f89947b13bdf5e6.json` | — | — | — | Generated isolated placement analysis cache; not a media deliverable |
| `commands/placement-cache/868286401f89947b13bdf5e6_bare_ground.png` | — | 212×213 | — | Generated isolated placement analysis cache; not a media deliverable |
| `commands/placement-cache/868286401f89947b13bdf5e6_bare_smoke.png` | — | 212×213 | — | Generated isolated placement analysis cache; not a media deliverable |
| `commands/placement-cache/868286401f89947b13bdf5e6_canopy_ground.png` | — | 212×213 | — | Generated isolated placement analysis cache; not a media deliverable |
| `commands/placement-cache/868286401f89947b13bdf5e6_canopy_smoke.png` | — | 212×213 | — | Generated isolated placement analysis cache; not a media deliverable |
| `commands/placement-cache/f60c68c0e4bde9395a339ae4.json` | — | — | — | Generated isolated placement analysis cache; not a media deliverable |
| `commands/placement-cache/f60c68c0e4bde9395a339ae4_bare_ground.png` | — | 210×211 | — | Generated isolated placement analysis cache; not a media deliverable |
| `commands/placement-cache/f60c68c0e4bde9395a339ae4_bare_smoke.png` | — | 210×211 | — | Generated isolated placement analysis cache; not a media deliverable |
| `commands/placement-cache/f60c68c0e4bde9395a339ae4_canopy_ground.png` | — | 210×211 | — | Generated isolated placement analysis cache; not a media deliverable |
| `commands/placement-cache/f60c68c0e4bde9395a339ae4_canopy_smoke.png` | — | 210×211 | — | Generated isolated placement analysis cache; not a media deliverable |
| `commands/placement_benchmark.py` | — | — | — | Reproduction script, source render raster or capture metadata |
| `commands/run_all.py` | — | — | — | Reproduction script, source render raster or capture metadata |
| `contact-sheet.png` | — | 2100×9590 | — | One labelled representative tile per delivered video and still |
| `raw/artifact-dry-run.json` | — | — | — | Untouched timed PTY evidence; consult raw/index.json safe_to_render flag before any use |
| `raw/artifact-dry-run.txt` | — | — | — | Untouched timed PTY evidence; consult raw/index.json safe_to_render flag before any use |
| `raw/detector-benchmark.json` | — | — | — | Untouched timed PTY evidence; consult raw/index.json safe_to_render flag before any use |
| `raw/detector-benchmark.txt` | — | — | — | Untouched timed PTY evidence; consult raw/index.json safe_to_render flag before any use |
| `raw/firmware-compile.json` | — | — | — | Untouched timed PTY evidence; consult raw/index.json safe_to_render flag before any use |
| `raw/firmware-compile.txt` | — | — | — | Untouched timed PTY evidence; consult raw/index.json safe_to_render flag before any use |
| `raw/firmware-tests.json` | — | — | — | Untouched timed PTY evidence; consult raw/index.json safe_to_render flag before any use |
| `raw/firmware-tests.txt` | — | — | — | Untouched timed PTY evidence; consult raw/index.json safe_to_render flag before any use |
| `raw/ground-help.json` | — | — | — | Untouched timed PTY evidence; consult raw/index.json safe_to_render flag before any use |
| `raw/ground-help.txt` | — | — | — | Untouched timed PTY evidence; consult raw/index.json safe_to_render flag before any use |
| `raw/ground-node-tests.json` | — | — | — | Untouched timed PTY evidence; consult raw/index.json safe_to_render flag before any use |
| `raw/ground-node-tests.txt` | — | — | — | Untouched timed PTY evidence; consult raw/index.json safe_to_render flag before any use |
| `raw/ground-tests-clean.json` | — | — | — | Untouched timed PTY evidence; consult raw/index.json safe_to_render flag before any use |
| `raw/ground-tests-clean.txt` | — | — | — | Untouched timed PTY evidence; consult raw/index.json safe_to_render flag before any use |
| `raw/ground-tests.json` | — | — | — | Untouched timed PTY evidence; consult raw/index.json safe_to_render flag before any use |
| `raw/ground-tests.txt` | — | — | — | Untouched timed PTY evidence; consult raw/index.json safe_to_render flag before any use |
| `raw/index.json` | — | — | — | Untouched timed PTY evidence; consult raw/index.json safe_to_render flag before any use |
| `raw/packet-roundtrip.json` | — | — | — | Untouched timed PTY evidence; consult raw/index.json safe_to_render flag before any use |
| `raw/packet-roundtrip.txt` | — | — | — | Untouched timed PTY evidence; consult raw/index.json safe_to_render flag before any use |
| `raw/placement-benchmark.json` | — | — | — | Untouched timed PTY evidence; consult raw/index.json safe_to_render flag before any use |
| `raw/placement-benchmark.txt` | — | — | — | Untouched timed PTY evidence; consult raw/index.json safe_to_render flag before any use |
| `raw/placement-node-tests.json` | — | — | — | Untouched timed PTY evidence; consult raw/index.json safe_to_render flag before any use |
| `raw/placement-node-tests.txt` | — | — | — | Untouched timed PTY evidence; consult raw/index.json safe_to_render flag before any use |
| `raw/placement-tests-clean.json` | — | — | — | Untouched timed PTY evidence; consult raw/index.json safe_to_render flag before any use |
| `raw/placement-tests-clean.txt` | — | — | — | Untouched timed PTY evidence; consult raw/index.json safe_to_render flag before any use |
| `raw/placement-tests.json` | — | — | — | Untouched timed PTY evidence; consult raw/index.json safe_to_render flag before any use |
| `raw/placement-tests.txt` | — | — | — | Untouched timed PTY evidence; consult raw/index.json safe_to_render flag before any use |
| `raw/station-benchmark-help.json` | — | — | — | Untouched timed PTY evidence; consult raw/index.json safe_to_render flag before any use |
| `raw/station-benchmark-help.txt` | — | — | — | Untouched timed PTY evidence; consult raw/index.json safe_to_render flag before any use |
| `raw/station-cloud-integration.json` | — | — | — | Untouched timed PTY evidence; consult raw/index.json safe_to_render flag before any use |
| `raw/station-cloud-integration.txt` | — | — | — | Untouched timed PTY evidence; consult raw/index.json safe_to_render flag before any use |
| `raw/station-core-tests.json` | — | — | — | Untouched timed PTY evidence; consult raw/index.json safe_to_render flag before any use |
| `raw/station-core-tests.txt` | — | — | — | Untouched timed PTY evidence; consult raw/index.json safe_to_render flag before any use |
| `raw/station-help.json` | — | — | — | Untouched timed PTY evidence; consult raw/index.json safe_to_render flag before any use |
| `raw/station-help.txt` | — | — | — | Untouched timed PTY evidence; consult raw/index.json safe_to_render flag before any use |
| `raw/station-node-tests.json` | — | — | — | Untouched timed PTY evidence; consult raw/index.json safe_to_render flag before any use |
| `raw/station-node-tests.txt` | — | — | — | Untouched timed PTY evidence; consult raw/index.json safe_to_render flag before any use |
| `raw/station-tests-clean.json` | — | — | — | Untouched timed PTY evidence; consult raw/index.json safe_to_render flag before any use |
| `raw/station-tests-clean.txt` | — | — | — | Untouched timed PTY evidence; consult raw/index.json safe_to_render flag before any use |
| `raw/station-tests.json` | — | — | — | Untouched timed PTY evidence; consult raw/index.json safe_to_render flag before any use |
| `raw/station-tests.txt` | — | — | — | Untouched timed PTY evidence; consult raw/index.json safe_to_render flag before any use |
| `renderer/check_containers.py` | — | — | — | Reproduction script, source render raster or capture metadata |
| `renderer/check_motion.py` | — | — | — | Reproduction script, source render raster or capture metadata |
| `renderer/code-shots.json` | — | — | — | Reproduction script, source render raster or capture metadata |
| `renderer/container-check.json` | — | — | — | Reproduction script, source render raster or capture metadata |
| `renderer/doc-shots.json` | — | — | — | Reproduction script, source render raster or capture metadata |
| `renderer/encode_sources.py` | — | — | — | Reproduction script, source render raster or capture metadata |
| `renderer/extras/index.json` | — | — | — | Reproduction script, source render raster or capture metadata |
| `renderer/extras/render_extras.cjs` | — | — | — | Reproduction script, source render raster or capture metadata |
| `renderer/extras/terminal-code-10-station-core-tests-transcript-full.html` | — | — | — | Reproduction script, source render raster or capture metadata |
| `renderer/extras/terminal-code-11-ground-tests-transcript-full.html` | — | — | — | Reproduction script, source render raster or capture metadata |
| `renderer/extras/terminal-code-12-placement-tests-transcript-full.html` | — | — | — | Reproduction script, source render raster or capture metadata |
| `renderer/extras/terminal-code-13-firmware-tests-transcript-full.html` | — | — | — | Reproduction script, source render raster or capture metadata |
| `renderer/extras/terminal-code-14-station-node-tests-transcript-full.html` | — | — | — | Reproduction script, source render raster or capture metadata |
| `renderer/extras/terminal-code-15-ground-node-tests-transcript-full.html` | — | — | — | Reproduction script, source render raster or capture metadata |
| `renderer/extras/terminal-code-16-placement-node-tests-transcript-full.html` | — | — | — | Reproduction script, source render raster or capture metadata |
| `renderer/extras/terminal-code-17-station-help-transcript-full.html` | — | — | — | Reproduction script, source render raster or capture metadata |
| `renderer/extras/terminal-code-18-ground-help-transcript-full.html` | — | — | — | Reproduction script, source render raster or capture metadata |
| `renderer/extras/terminal-code-19-station-benchmark-help-transcript-full.html` | — | — | — | Reproduction script, source render raster or capture metadata |
| `renderer/extras/terminal-code-20-packet-roundtrip-transcript-full.html` | — | — | — | Reproduction script, source render raster or capture metadata |
| `renderer/extras/terminal-code-21-detector-benchmark-transcript-full.html` | — | — | — | Reproduction script, source render raster or capture metadata |
| `renderer/extras/terminal-code-22-artifact-dry-run-transcript-full.html` | — | — | — | Reproduction script, source render raster or capture metadata |
| `renderer/extras/terminal-code-23-placement-benchmark-transcript-full.html` | — | — | — | Reproduction script, source render raster or capture metadata |
| `renderer/extras/verification.json` | — | — | — | Reproduction script, source render raster or capture metadata |
| `renderer/finalize.py` | — | — | — | Reproduction script, source render raster or capture metadata |
| `renderer/finish_manifest.py` | — | — | — | Reproduction script, source render raster or capture metadata |
| `renderer/make_review.py` | — | — | — | Reproduction script, source render raster or capture metadata |
| `renderer/motion-check.json` | — | — | — | Reproduction script, source render raster or capture metadata |
| `renderer/prepare_sources.py` | — | — | — | Reproduction script, source render raster or capture metadata |
| `renderer/provenance.json` | — | — | — | Reproduction script, source render raster or capture metadata |
| `renderer/render_docs.cjs` | — | — | — | Reproduction script, source render raster or capture metadata |
| `renderer/render_sources.cjs` | — | — | — | Reproduction script, source render raster or capture metadata |
| `renderer/render_terminal.cjs` | — | — | — | Reproduction script, source render raster or capture metadata |
| `renderer/sources.json` | — | — | — | Reproduction script, source render raster or capture metadata |
| `renderer/terminal-code-01-mcu-sketch-header.png` | — | 2880×148 | — | Reproduction script, source render raster or capture metadata |
| `renderer/terminal-code-01-mcu-sketch-source.png` | — | 2880×11760 | — | Reproduction script, source render raster or capture metadata |
| `renderer/terminal-code-02-flame-logic-header.png` | — | 2880×148 | — | Reproduction script, source render raster or capture metadata |
| `renderer/terminal-code-02-flame-logic-source.png` | — | 2880×13424 | — | Reproduction script, source render raster or capture metadata |
| `renderer/terminal-code-03-smoke-detector-header.png` | — | 2880×148 | — | Reproduction script, source render raster or capture metadata |
| `renderer/terminal-code-03-smoke-detector-source.png` | — | 2880×6256 | — | Reproduction script, source render raster or capture metadata |
| `renderer/terminal-code-04-packet-codec-header.png` | — | 2880×148 | — | Reproduction script, source render raster or capture metadata |
| `renderer/terminal-code-04-packet-codec-source.png` | — | 2880×7600 | — | Reproduction script, source render raster or capture metadata |
| `renderer/terminal-code-05-placement-engine-header.png` | — | 2880×148 | — | Reproduction script, source render raster or capture metadata |
| `renderer/terminal-code-05-placement-engine-source.png` | — | 2880×10416 | — | Reproduction script, source render raster or capture metadata |
| `renderer/terminal-code-06-spatial-voting-header.png` | — | 2880×148 | — | Reproduction script, source render raster or capture metadata |
| `renderer/terminal-code-06-spatial-voting-source.png` | — | 2880×4848 | — | Reproduction script, source render raster or capture metadata |
| `renderer/terminal-code-07-terrain-sightlines-header.png` | — | 2880×148 | — | Reproduction script, source render raster or capture metadata |
| `renderer/terminal-code-07-terrain-sightlines-source.png` | — | 2880×7920 | — | Reproduction script, source render raster or capture metadata |
| `renderer/terminal-code-08-packet-receiver-header.png` | — | 2880×148 | — | Reproduction script, source render raster or capture metadata |
| `renderer/terminal-code-08-packet-receiver-source.png` | — | 2880×13744 | — | Reproduction script, source render raster or capture metadata |
| `renderer/terminal-code-09-airtime-budget-header.png` | — | 2880×148 | — | Reproduction script, source render raster or capture metadata |
| `renderer/terminal-code-09-airtime-budget-source.png` | — | 2880×8432 | — | Reproduction script, source render raster or capture metadata |
| `renderer/terminal-shots.json` | — | — | — | Reproduction script, source render raster or capture metadata |
| `renderer/tracked-tree.json` | — | — | — | Reproduction script, source render raster or capture metadata |
| `renderer/verification.json` | — | — | — | Reproduction script, source render raster or capture metadata |
| `review/qa-01.jpg` | — | 1440×1788 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/qa-02.jpg` | — | 1440×1788 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/qa-03.jpg` | — | 1440×1788 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/qa-04.jpg` | — | 1440×1788 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/qa-05.jpg` | — | 1440×1788 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/qa-06.jpg` | — | 1440×1788 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/qa-07.jpg` | — | 1440×1788 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/qa-08.jpg` | — | 1440×1192 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-01-mcu-sketch-1080-end.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-01-mcu-sketch-1080-middle.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-01-mcu-sketch-1080-start.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-01-mcu-sketch-end.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-01-mcu-sketch-middle.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-01-mcu-sketch-start.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-02-flame-logic-1080-end.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-02-flame-logic-1080-middle.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-02-flame-logic-1080-start.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-02-flame-logic-end.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-02-flame-logic-middle.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-02-flame-logic-start.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-03-smoke-detector-1080-end.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-03-smoke-detector-1080-middle.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-03-smoke-detector-1080-start.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-03-smoke-detector-end.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-03-smoke-detector-middle.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-03-smoke-detector-start.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-04-packet-codec-1080-end.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-04-packet-codec-1080-middle.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-04-packet-codec-1080-start.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-04-packet-codec-end.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-04-packet-codec-middle.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-04-packet-codec-start.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-05-placement-engine-1080-end.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-05-placement-engine-1080-middle.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-05-placement-engine-1080-start.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-05-placement-engine-end.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-05-placement-engine-middle.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-05-placement-engine-start.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-06-spatial-voting-1080-end.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-06-spatial-voting-1080-middle.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-06-spatial-voting-1080-start.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-06-spatial-voting-end.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-06-spatial-voting-middle.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-06-spatial-voting-start.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-07-terrain-sightlines-1080-end.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-07-terrain-sightlines-1080-middle.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-07-terrain-sightlines-1080-start.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-07-terrain-sightlines-end.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-07-terrain-sightlines-middle.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-07-terrain-sightlines-start.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-08-packet-receiver-1080-end.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-08-packet-receiver-1080-middle.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-08-packet-receiver-1080-start.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-08-packet-receiver-end.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-08-packet-receiver-middle.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-08-packet-receiver-start.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-09-airtime-budget-1080-end.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-09-airtime-budget-1080-middle.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-09-airtime-budget-1080-start.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-09-airtime-budget-end.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-09-airtime-budget-middle.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-09-airtime-budget-start.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-10-station-core-tests-1080-end.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-10-station-core-tests-1080-middle.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-10-station-core-tests-1080-start.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-10-station-core-tests-end.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-10-station-core-tests-middle.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-10-station-core-tests-start.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-11-ground-tests-1080-end.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-11-ground-tests-1080-middle.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-11-ground-tests-1080-start.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-11-ground-tests-end.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-11-ground-tests-middle.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-11-ground-tests-start.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-12-placement-tests-1080-end.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-12-placement-tests-1080-middle.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-12-placement-tests-1080-start.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-12-placement-tests-end.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-12-placement-tests-middle.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-12-placement-tests-start.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-13-firmware-tests-1080-end.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-13-firmware-tests-1080-middle.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-13-firmware-tests-1080-start.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-13-firmware-tests-end.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-13-firmware-tests-middle.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-13-firmware-tests-start.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-14-station-node-tests-1080-end.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-14-station-node-tests-1080-middle.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-14-station-node-tests-1080-start.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-14-station-node-tests-end.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-14-station-node-tests-middle.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-14-station-node-tests-start.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-15-ground-node-tests-1080-end.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-15-ground-node-tests-1080-middle.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-15-ground-node-tests-1080-start.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-15-ground-node-tests-end.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-15-ground-node-tests-middle.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-15-ground-node-tests-start.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-16-placement-node-tests-1080-end.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-16-placement-node-tests-1080-middle.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-16-placement-node-tests-1080-start.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-16-placement-node-tests-end.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-16-placement-node-tests-middle.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-16-placement-node-tests-start.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-17-station-help-1080-end.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-17-station-help-1080-middle.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-17-station-help-1080-start.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-17-station-help-end.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-17-station-help-middle.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-17-station-help-start.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-18-ground-help-1080-end.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-18-ground-help-1080-middle.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-18-ground-help-1080-start.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-18-ground-help-end.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-18-ground-help-middle.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-18-ground-help-start.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-19-station-benchmark-help-1080-end.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-19-station-benchmark-help-1080-middle.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-19-station-benchmark-help-1080-start.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-19-station-benchmark-help-end.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-19-station-benchmark-help-middle.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-19-station-benchmark-help-start.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-20-packet-roundtrip-1080-end.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-20-packet-roundtrip-1080-middle.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-20-packet-roundtrip-1080-start.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-20-packet-roundtrip-end.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-20-packet-roundtrip-middle.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-20-packet-roundtrip-start.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-21-detector-benchmark-1080-end.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-21-detector-benchmark-1080-middle.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-21-detector-benchmark-1080-start.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-21-detector-benchmark-end.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-21-detector-benchmark-middle.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-21-detector-benchmark-start.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-22-artifact-dry-run-1080-end.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-22-artifact-dry-run-1080-middle.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-22-artifact-dry-run-1080-start.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-22-artifact-dry-run-end.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-22-artifact-dry-run-middle.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-22-artifact-dry-run-start.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-23-placement-benchmark-1080-end.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-23-placement-benchmark-1080-middle.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-23-placement-benchmark-1080-start.png` | — | 1920×1080 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-23-placement-benchmark-end.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-23-placement-benchmark-middle.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `review/terminal-code-23-placement-benchmark-start.png` | — | 2880×1620 | — | Extracted QA frame or review sheet; not a separate b-roll deliverable |
| `manifest.md` | — | — | — | This complete capture index |
| `renderer/summary.json` | — | — | — | Final media counts and unique footage duration |
