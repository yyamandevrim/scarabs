# Held-frame smoke diagnosis

Use `scripts/diagnose_smoke.py` to compare **the same frozen, unannotated images**
across model input sizes and confidence thresholds. This is an offline diagnostic;
it does not open cameras, contact hardware, run the station, or alter configuration.
It imports the production detector and spatial event tracker. No extra dependency
is needed.

Keep camera imagery, manifests, model inputs and reports outside the repository.
Label footage by operator observation and retain clip author/licence provenance.
A camera watching a video display is a different input domain from the original
clip; neither demonstrates physical field accuracy.

## Input

Create a JSON manifest with one series for each camera and uninterrupted trial.
Do not combine frames from different cameras into one voting history. Each sample
needs an image path (relative to the manifest), strictly increasing time in seconds,
label (`positive`, `negative`, or `unknown`) and provenance. Use the actual analysis
sample timestamp when available. Capture timestamps at a higher rate do not imply
those frames were analysed by the running station.

```json
{
  "series": [{
    "name": "held-screen-trial",
    "samples": [
      {"image": "raw-000.png", "time": 0, "label": "unknown",
       "provenance": "Operator to record source, clip stage, camera and capture method"},
      {"image": "raw-001.png", "time": 1, "label": "unknown",
       "provenance": "Same uninterrupted trial; operator to label visible smoke"}
    ]
  }]
}
```

Use raw BGR camera frames saved before annotation where possible. The station JPEG
endpoint is annotated and compressed: mark that provenance explicitly and never
feed an image containing drawn smoke boxes or labels back into the detector.
Opening a second capture process can steal a USB camera from the station. This
script deliberately accepts files only; it provides no unauthenticated route or
live frame export.

## Run

From `station/`, with existing downloaded model and installed environment:

```sh
uv run python scripts/diagnose_smoke.py /tmp/smoke-debug/manifest.json \
  --model models/smoke.onnx --output /tmp/smoke-debug/replay --save-inputs
uv run pytest tests/test_smoke_diagnostic.py tests/test_alarm.py tests/test_detector.py
```

The output directory must be new. Defaults compare input 192/320/416/640 and
thresholds 0.25/0.35/0.45. Detections are collected once at a 0.10 floor per size,
then filtered for each threshold; scores below that floor are unknown. Thresholds
below 0.10 are rejected. The regression test checks post-filtering against direct
inference on a held licensed smoke frame.

`report.json` records source/pixel/model SHA-256, provenance, unique image counts,
boxes, timings and every spatial vote, event opening and closure. `--save-inputs`
saves the **actual float32 RGB tensor handed to ORT** as `.npy` plus a letterboxed
PNG view, using an observer around the existing session. It does not reimplement
preprocessing or alter the source images. Pixel enlargement changes the network's
scale response; it cannot restore detail lost in capture.

The tracker uses spatial IoU 0.25, NMS IoU 0.45, a 3-of-5 window, a 12-second timeout
and a 3-second history gap. Set `--timeout` and `--history-gap` to the effective
configuration for the trial. Each series starts with an empty history. Supplied
times are replay times, not measured inference cadence. The report's final event
closure uses a labelled synthetic drain after the timeout; it is not an observed
negative frame. Per-image timings include cold inference and must not be quoted
as sustained throughput. Repeated copies of one frozen image test persistence,
not additional independent smoke examples.

## Interpret and validate

A box is a per-analysis candidate. An event needs three spatially overlapping
candidate analyses in the last five. An already-open event survives missed boxes
until its last matching detection exceeds the timeout. Multiple boxes in one
analysis contribute one vote. Long interruptions reset the vote history.

First compare the original clip with camera-seen versions of the same paused
stage; keep framing, glare and focus fixed. Inspect both raw pixels and exact
network inputs, then compare a different stage with only that variable changed.
Include fog, cloud, glare and the current empty scene as negatives. Missing boxes
at the collection floor cannot be repaired by a smaller threshold sweep.

A local replay cannot establish the live operating configuration. Hardware
acceptance still requires a coordinated board test: one station process; unchanged
capture mode on both cameras; visually intact current frames; advancing analyses
and measured cadence; fresh MCU data; authenticated panel; and held positive /
negative replay through the real event/evidence path. Coordinate any heavy
inference with the station workload and restore its backed-up baseline afterward.
