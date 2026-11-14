# Detection quality vs model input size

Measured 2026-11-14 to help choose `input_size`, `confidence` and `analysis_hz` for the UNO Q. The initial study was a measurement report only. The dated screen-demo follow-up in section 12 also records subsequent deployment diagnostics; analysis defaults were unchanged.

**Read this first.** The evidence is **one real smoke clip and three real negative clips**. The smoke clip shows a **large, nearby plume** that fills about half the frame. It contains no small, distant smoke, which is exactly the case input shrinking is expected to hurt. That case was tested only with a **synthetic proxy** (section 5). Every number here is indicative, not a benchmark.

Labels used throughout:

- **[Mac]**: measured on this Mac (Apple M5, macOS, CPUExecutionProvider, 2 ORT threads).
- **[Board, measured]**: taken from `../firmware/BOARD_NOTES.md`, measured on the UNO Q.
- **[Board, estimate]**: extrapolated here from those board measurements. Not measured.

## 1. What the application actually does at a smaller input

- The exported model (`models/smoke.onnx`, Pyronear YOLOv11s) has a **dynamic input shape**: `images [batch, 3, height, width]`. A smaller `input_size` therefore really runs the network at that resolution. Nothing is cropped or padded back up to 640. `SmokeDetector` rejects a mismatch only for fixed-shape exports.
- Path per analysis, as in `station/capture.py`, `station/detector.py` and `station/alarm.py`:
  1. File playback is resized to configured `width × height` with `cv2.resize`; a 16:9 file configured as 320×240 is squashed. The current live USB path preserves the actual negotiated camera pixels. The study below simulated working sizes explicitly; it did not capture a screen.
  2. `SmokeDetector.predict` letterboxes that frame into an `input_size × input_size` square (grey 114 padding), converts BGR→RGB, scales to float32 /255, runs ORT, filters by confidence and applies NMS at IoU 0.45.
  3. `EventTracker` / `AlarmRule` opens an event when a detection overlaps (IoU ≥ 0.25) a detection in at least 3 of the last 5 analyses. Events close after 12 s without a matching detection.
- In a 1280×720 frame at input 192, the frame is scaled by 0.15, so a plume 200 px wide reaches the network as about 30 px. At 640 the same plume is 100 px.

## 2. Method

- Clips were decoded with OpenCV and sampled by **video time** at 1 analysis/s (frames at t = 0, 1, 2 … s). The 0.5 Hz and 0.33 Hz results reuse every 2nd or 3rd of those samples, starting at phase 0. Frames were not wall-clock paced, so results are deterministic and every sample is analysed.
- Each sampled frame was resized to a working size, exactly as `capture.py` does, and passed to the real `SmokeDetector.predict` and `EventTracker.update` imported from `station/`. Working sizes:
  - **1280×720**: `config.toml` default; "native" below.
  - **320×240**: board camera setting; a squashed 16:9 clip.
  - **320×180**: board clip-trial setting; aspect preserved.
- Sizes tested: 640, 512, 416, 320, 256, 224, 192, 160. 512 was run only at native working size.
- **Confidence sweep.** Detections were collected once at a 0.10 floor and filtered afterwards at 0.20, 0.25, 0.35, 0.45 and 0.55. Greedy NMS keeps only boxes suppressed by higher-scoring kept boxes, so post-filtering gives the same detections as running at the higher threshold. Spot check: the 640/native result at 0.35 (24/54) matches the README's figure for the same clip.
- "Detection frames" means analyses with at least one detection at or above the threshold. "First alarm" is the video time of the analysis that opened the first event.
- Mac inference time is ORT `session.run` only, mean over all analysed frames after 3 warm-ups.
- Scripts were run from a temporary directory and are not committed (this report is the only added file). They import the unmodified `station` package.

## 3. Clips used (from `README.md` / `footage.json`)

| File | Source / author | Licence | Content | Samples at 1 Hz |
|---|---|---|---|---|
| `media/smoke.ogv` 1280×720 | [Wildfire Near Monserrate](https://commons.wikimedia.org/wiki/File:Wildfire_Near_Monserrate.ogv), Peter Angritt / Mrtony77 | CC BY-SA 4.0 | Real hillside wildfire smoke, near and large; plume visible from the first frame | 54 |
| `media/fog.webm` 1920×1080 | [Fog covering mountain time lapse](https://commons.wikimedia.org/wiki/File:Fog_covering_mountain_time_lapse.webm), Athulvis | CC BY-SA 4.0 (Commons licence review pending) | Fog negative | 46 |
| `media/cloud.webm` 1280×720 | [Angeles National Forest from Mount Wilson](https://commons.wikimedia.org/wiki/File:Angeles_National_Forest_from_Mount_Wilson.webm), Tom Hawkins | CC BY-SA 3.0 | Cloud negative | 34 |
| `media/glare.webm` 1920×1080 | [CostaRica Cow close up shot great lens flare](https://commons.wikimedia.org/wiki/File:072014_CostaRica_Cow_close_up_shot_great_lens_flare.webm), Michael Weinman | CC BY-SA 2.0 | Sun glare / lens flare negative, barn interior, not a forest view | 42 |

## 4. Results on the real clips: confidence 0.35, 1 Hz [Mac]

### 4a. Smoke clip: alarm, first alarm, detection frames, confidence

Confidence columns are percentiles of each analysis's highest score; 0 means no box at or above 0.10.

| Input | Working | Alarm | First alarm (s) | Detection frames | Highest-score p10 / p50 / p90 | Peak |
|---|---|---|---|---|---|---|
| 640 | 1280×720 | yes | 2 | 24/54 (44%) | 0.16 / 0.33 / 0.51 | 0.63 |
| 512 | 1280×720 | **no** | – | 2/54 (4%) | 0.13 / 0.22 / 0.30 | 0.46 |
| 416 | 1280×720 | **no** | – | 3/54 (6%) | 0.11 / 0.22 / 0.34 | 0.40 |
| 320 | 1280×720 | yes | 4 | 17/54 (31%) | 0.18 / 0.29 / 0.42 | 0.46 |
| 256 | 1280×720 | **no** | – | 3/54 (6%) | 0.14 / 0.20 / 0.33 | 0.46 |
| 224 | 1280×720 | yes | 2 | 18/54 (33%) | 0.13 / 0.28 / 0.46 | 0.58 |
| 192 | 1280×720 | yes | 2 | 40/54 (74%) | 0.27 / 0.46 / 0.63 | 0.69 |
| 160 | 1280×720 | yes (2 events) | 8 | 12/54 (22%) | 0.00 / 0.17 / 0.48 | 0.65 |
| 640 | 320×240 | yes | 2 | 17/54 (31%) | 0.10 / 0.23 / 0.46 | 0.67 |
| 416 | 320×240 | **no** | – | 2/54 (4%) | 0.00 / 0.14 / 0.26 | 0.43 |
| 320 | 320×240 | **no** | – | 7/54 (13%) | 0.14 / 0.20 / 0.36 | 0.47 |
| 256 | 320×240 | yes | 20 | 31/54 (57%) | 0.24 / 0.37 / 0.50 | 0.55 |
| 224 | 320×240 | yes | 20 | 30/54 (56%) | 0.25 / 0.36 / 0.50 | 0.58 |
| **192** | **320×240** | **yes** | **3** | **45/54 (83%)** | **0.32 / 0.52 / 0.63** | **0.68** |
| 160 | 320×240 | yes | 4 | 47/54 (87%) | 0.32 / 0.62 / 0.77 | 0.80 |
| 640 | 320×180 | yes | 2 | 25/54 (46%) | 0.17 / 0.34 / 0.51 | 0.64 |
| 416 | 320×180 | no | – | 2/54 | – | 0.36 |
| 320 | 320×180 | yes | 4 | 17/54 | – | 0.46 |
| 256 | 320×180 | no | – | 3/54 | – | 0.45 |
| 224 | 320×180 | yes | 4 | 17/54 | – | 0.55 |
| 192 | 320×180 | yes | 2 | 40/54 | – | 0.69 |
| 160 | 320×180 | yes (2 events) | 18 | 11/54 | – | 0.60 |

The plume is visible from t = 0, so 2 s (the third analysis) is the fastest possible first alarm.

### 4b. Negatives: fog, cloud, glare

**No alarm at any input size, working size or threshold tested (0.20–0.55).** Detections at 0.35:

| Input / working | Fog detections | Cloud detections | Glare detections | Highest negative score seen |
|---|---|---|---|---|
| 320 / 1280×720 | 1/46 (0.37) | 0/34 | 0/42 | 0.37 fog |
| 320 / 320×180 | 1/46 (0.36) | 0/34 | 0/42 | 0.36 fog |
| All other size/working combinations | 0 | 0 | 0 | ≤ 0.34 (cloud at 512; fog at 256/320×240) |

At 192 the highest negative score was 0.11 (fog). Cloud and glare had no box at or above 0.10.

### 4c. Where the boxes land

Boxes were drawn and inspected on the smoke frames. At 640 the model boxes a single smoke column (mean box area 20% of the frame). At 320, 192 and 160 it boxes the **whole multi-column plume** as one object (mean area 43–49%). All of these are on real smoke. The small inputs score this clip highly because the plume is big enough to read as one coarse object at low resolution. That is not evidence that they would see a small plume.

## 5. Distant-smoke proxy (synthetic, labelled as such) [Mac]

The real smoke frames were shrunk by a factor k (plume width ÷ k, roughly k× farther away) and pasted, with feathered edges, in the centre of a background made from the same clip's forest strip. Then the normal pipeline ran at 0.35 and 1 Hz. As a control, the fog, cloud and glare clips were composited the same way at k = 3. **This is not real distant-smoke footage.** The pasted rectangle, the stretched background and the absence of real haze or atmospheric loss all differ from reality. Boxes at 640 were checked to fall on the pasted plume.

Results are smoke detection frames out of 54; ✓ = alarm.

| Input | k=1 native | k=2 native | k=3 native | k=4 native | k=1 320×240 | k=2 320×240 | k=3 320×240 | k=4 320×240 |
|---|---|---|---|---|---|---|---|---|
| 640 | 24 ✓ | 16 ✓ | 53 ✓ | 54 ✓ | 17 ✓ | 9 ✗ | 50 ✓ | 54 ✓ |
| 416 | 3 ✗ | 38 ✓ | 0 ✗ | 0 ✗ | 2 ✗ | 36 ✓ | 28 ✓ | 1 ✗ |
| 320 | 17 ✓ | 2 ✗ | 0 ✗ | 0 ✗ | 7 ✗ | 51 ✓ | 0 ✗ | 0 ✗ |
| 256 | 3 ✗ | 0 ✗ | 0 ✗ | 0 ✗ | 31 ✓ | 17 ✓ | 0 ✗ | 0 ✗ |
| 224 | 18 ✓ | 0 ✗ | 0 ✗ | 0 ✗ | 30 ✓ | 0 ✗ | 0 ✗ | 0 ✗ |
| **192** | 40 ✓ | **0 ✗** | **0 ✗** | **0 ✗** | **45 ✓** | **0 ✗** | **0 ✗** | **0 ✗** |
| 160 | 12 ✓ | 0 ✗ | 0 ✗ | 0 ✗ | 47 ✓ | 0 ✗ | 0 ✗ | 0 ✗ |

Composite negatives (k = 3, both working sizes, every input size): **0 detections, 0 alarms.**

In this proxy, **192 stops detecting completely once the plume is half its original size.** Only 640 alarms across all four scales. At native working size it is the only input that alarms at k = 3 and k = 4. It also catches k = 3 and k = 4 from 320×240 frames: upscaling the camera frame to 640 still helps the network. **Model input size, not the 320×240 camera resolution, is what loses the small plume.** Each smaller input has a narrow band of plume sizes it responds to; the band is not monotonic in size.

## 6. Does the confidence threshold need to move with size? [Mac]

Smoke-clip alarm and detection frames per threshold (native = 1280×720). "No" = no alarm. Negatives raised **no alarm at any cell**.

| Input / working | 0.20 | 0.25 | 0.35 (current) | 0.45 | 0.55 |
|---|---|---|---|---|---|
| 640 / native | yes, 45/54, 2 events | yes, 40/54 | yes, 24/54 | yes, 14/54 | no, 3/54 |
| 512 / native | yes, 32/54 | yes, 18/54 | **no**, 2/54 | no | no |
| 416 / native | yes, 32/54 | yes, 18/54 | **no**, 3/54 | no | no |
| 320 / native | yes, 43/54 | yes, 31/54 | yes, 17/54 | no | no |
| 256 / native | yes, 27/54 | yes, 16/54 | **no**, 3/54 | no | no |
| 192 / native | yes, 53/54 | yes, 49/54 | yes, 40/54 | yes (t=16 s), 28/54 | yes (t=16 s), 19/54 |
| 640 / 320×240 | yes, 35/54 | yes, 24/54 | yes, 17/54 | yes (t=17 s) | no |
| 320 / 320×240 | yes, 29/54 | yes, 22/54 | **no**, 7/54 | no | no |
| 192 / 320×240 | yes, 52/54 | yes, 51/54 | yes, 45/54 | yes (t=16 s), 34/54 | yes (t=18 s), 22/54 |
| 160 / 320×240 | yes | yes | yes, 47/54 | yes, 43/54 | yes, 35/54 |

Single detections on negatives at lower thresholds:

| Threshold | Negative detections (single analyses, never 3-of-5) |
|---|---|
| 0.25 | 512 / native: 1 fog, 1 cloud. 320 / native: 1 fog. 256 / 320×240: 1 fog. |
| 0.20 | Additionally 640 / 320×240: 1 fog. 416 / 320×240: 1 fog, 1 cloud. 416 / 320×180: 1 cloud. |

What the threshold sweep shows:

- Scores shift with input size, so the threshold is not size-independent. At 512, 416 and 256 the current 0.35 loses this smoke clip, and 0.25 restores it. Negative scores peaked at 0.37, so 0.25 would yield isolated single-frame negative detections. On this data the 3-of-5 rule still keeps them from becoming alarms.
- At 192 the current 0.35 has margin on this clip. Moving it does not fix the small-plume failure in section 5: that failure has no boxes even at the 0.10 floor.
- At 640, lowering to 0.25 nearly doubles smoke detection frames (24→40) with no negative detection.

## 7. Speed: Mac measured, board measured and board estimated

**Scaling assumption.** Inference time = a + b·s² (s = input side). Convolution work is proportional to pixel count, plus a fixed overhead. Fitted to the two standalone UNO Q benchmarks, 640 → 2545 ms and 320 → 665 ms, this gives a ≈ 38 ms, b ≈ 0.00612 ms/px². The fit predicts 264 ms at 192. The board measured about 277–279 ms there, under live two-camera capture, so the fit is within about 5%. Treat estimates as ±15%.

**Live-camera timing update:** the [board record](../firmware/BOARD_NOTES.md#2026-11-14-live-camera-input-size-curve--measured-on-the-uno-q) now measures 640, 416 and 320 with two live 320×240 YUYV cameras, UVC quirk 128, confidence 0.35 and two ORT threads. These replace the earlier ceiling estimates at those sizes. Pairs are left / centre; inference is the mean of sampled completed analyses, excluding capture/decode. The earlier 0.105 Hz result used recorded 1280×720 clips, not live cameras.

| Input | Mac inference mean [Mac] | UNO Q inference [Board, measured live] | Sustained rate per camera [Board, measured live] | Requested interval per camera |
|---|---|---|---|---|
| 640 | 68 ms | 2719.54 / 2738.86 ms | 0.167 / 0.167 Hz | 6 s |
| 416 | 28 ms | 1170.39 / 1163.29 ms | 0.333 / 0.333 Hz | 3 s |
| 320 | 17 ms | 701.81 / 694.58 ms | 0.500 / 0.497 Hz | 2 s |
| 192 | 9 ms | 279.32 / 276.53 ms | 0.990 / 0.990 Hz | 1 s |

640, 416 and 320 used 30 seconds warm-up plus approximately 300 seconds of sampled running each; 192 used the earlier 180.7-second window. Six seconds was the shortest validated 640 interval on the tested grid; 5.5 seconds failed. The 416/320 choices are not boundary-search minima. Other input sizes remain extrapolations from the scaling fit, not live-camera measurements.

Resource use was also measured: at 640, mean station RSS was 306.3 MiB, machine / station CPU 57.6% / 209.9%, and CPU temperatures 46.4–52.9°C. The board record includes the other sizes' resources and measurement limits. The exact repository field profile uses confidence 0.25 and remains unmeasured; this curve used 0.35. None of these timings validates detection quality on the board.

The board is about 32–40× slower than this Mac per inference. Mac times must never be quoted as board times.

**Board and Mac detections differ slightly.** The board benchmark found 28/54 positive frames at 640 and 21/54 at 320 on the same clip. The Mac found 24/54 and 17/54. These are differences near the threshold, probably from ARM ORT numerics. Detection on the board itself at other sizes is unmeasured.

## 8. Slower rate at a larger input (0.35 threshold) [Mac, sampled]

Smoke results by analysis rate. Negatives: no alarm at any rate.

| Input / working | 1 Hz | 0.5 Hz (every 2 s) | 0.33 Hz (every 3 s) |
|---|---|---|---|
| 640 / native | alarm t=2 s, 24/54 | alarm t=4 s, 11/27 | alarm t=21 s, 8/18 |
| 640 / 320×240 | alarm t=2 s, 17/54 | alarm t=4 s, 8/27 | alarm t=12 s, 6/18 |
| 320 / native | alarm t=4 s | alarm t=6 s | alarm t=27 s |
| 192 / 320×240 | alarm t=3 s, 45/54 | alarm t=16 s, 22/27 | alarm t=12 s, 16/18 |

Slowing down mainly delays the first alarm: the 3-of-5 window spans 5 analyses, so roughly 10–25 s at these rates. Here it never turned an alarm into a miss. For smoke that develops over minutes, a 5–20 s delay is small. Missing a small plume altogether, as 192 does in section 5, is not small.

**Config interaction.** If the interval grows toward the 12 s `event_timeout` (for example 640 at ~0.1 Hz), a single missed analysis can close an event and reopen it as a duplicate. `event_timeout` would need to be at least about 3 analysis intervals. This is a configuration value; it was not changed in the Mac study. The later board timing curve used 36 s at input 640 and a 6 s interval; the repository field profile now follows those values. Stale-frame reset uses `max(stale_seconds, 2/analysis_hz)`, so it scales with the rate already.

## 9. Plain-language reading

1. **Does 192 with 320×240 detect the smoke clip and stay quiet on the negatives?** Yes. It alarms at t = 3 s, detects in 83% of analyses with median top score 0.52, and gives zero detections at or above 0.35 on fog, cloud and glare (peak negative score 0.11). On this clip it outperforms 640.
2. **Why that is not reassuring.** This clip shows a near, frame-filling plume. When the same smoke is made 2–4× smaller (synthetic proxy), 192 detects nothing, even at a 0.10 score floor. 640 still alarms at every scale tested. Small, far smoke is what a ridge-top camera most needs to catch, and the evidence suggests 192 is blind to it.
3. **Camera resolution is a minor factor here.** With 320×240 frames fed at input 640, the proxy still alarms at k = 3–4. Shrinking the model input loses the small plume; the 320×240 cameras alone do not.
4. **Input sizes do not degrade smoothly.** 512, 416 and 256 miss the real clip at 0.35 but alarm at 0.25. Each size responds to a band of plume sizes. A size cannot be validated from one clip.
5. **False alarms:** none at any size, threshold or rate tested. The 3-of-5 rule absorbed every isolated negative detection.

## 10. Recommendation (a trade-off to choose from)

Detection-quality evidence in this table is from the Mac clips and synthetic proxy; board rates measure throughput only.

| Option | Setting | Board rate per camera, two cameras | Evidence for | Evidence against |
|---|---|---|---|---|
| A. Current | 192, 320×240, 0.35, 1 Hz | **0.99 Hz [measured]** | Real clip alarms at 3 s; quiet on all negatives | Detects nothing once the plume is ≥2× smaller (proxy) |
| B. Smallest "every real clip alarms, no false alarms" | 160–192 | 0.990 Hz at 192 [measured]; 160 unmeasured | Same as A | Same weakness as A; smallest setting is not the safest |
| C. Middle | 320 (0.35), or 416 at 0.25 | 0.500 / 0.497 Hz at 320; 0.333 Hz each at 416 [measured at 0.35; 416 at 0.25 unmeasured] | 320 alarms on the real clip at native working size; 416 at 0.25 does too | Each covers only one plume-size band in the proxy (320 misses the real clip from 320×240 frames at 0.35); neither is robust |
| **D. Recommended for smoke that develops over minutes** | **640, 320×240 cameras, 0.35 (0.25 is worth testing), one analysis every 6 s per camera, `event_timeout` 36 s** | **0.167 Hz each [measured at 0.35]**; exact field profile at 0.25 unmeasured | Only setting that alarms at every plume scale tested on the Mac, at both working sizes; no alarms on the tested negatives; board alarm latency unmeasured | Slower sampling; measured board CPU, RAM and thermals are in section 7; field sensitivity remains unverified |

A compromise between C and D is 416 at threshold 0.25, every 3 s (cadence measured only at 0.35); 512 remains unmeasured. It is cheaper than 640, but it covered fewer plume scales in the proxy, and its threshold change was tuned on one clip.

## 11. Limits of the evidence

- One real smoke clip (near, large, white plume against forest) and three negatives, one of which is not a forest view. This is no basis for sensitivity or false-alarm rates.
- The distant-smoke result is synthetic. It has hard-edged pasting, artificial background texture and no atmospheric haze. Real distant smoke is fainter as well as smaller, which would likely make small inputs worse, not better.
- The 320×240 test squashes a 16:9 clip. The real 4:3 cameras have a different field of view and optics, and USB YUYV sensor noise and compression were not modelled.
- Detection numbers are Mac ORT results. The board's ARM build gave slightly different counts at 640 and 320. Detection on the board at sizes other than 640 and 320 is unmeasured.
- Board live-camera timings and resources were measured at 192, 320, 416 and 640. Other sizes remain estimates. The exact field profile at confidence 0.25, longer hot-ambient operation and event-encoding load remain unmeasured; the controlled curve used 0.35.
- Slow-rate results use a single sampling phase. Different phases could shift first-alarm times by a few analyses.


## 12. Screen-demo diagnosis, 2026-11-14

**[Mac, measured]** The failed demo cannot be attributed to model input size alone. The Guardian's [Victoria/Buchan video](https://www.theguardian.com/australia-news/video/2020/jan/02/australia-fires-aerial-footage-wildfire-bushfire-victoria) (YouTube `NmyWqgBBhzY`) was identified from the owner's description and the visible “Buchan, Victoria” caption. Its exact URL still awaits owner confirmation. The initial camera evidence also contains Fire and Rescue NSW footage and later Sky News imagery; do not treat those mixed captures as a synchronized recording of one source file.

Using the production `SmokeDetector.predict`, CPUExecutionProvider, two ORT threads, all 85 one-second samples of the direct 1280×720 Guardian file were replayed at inputs 192, 320, 416 and 640. Collection floor 0.10; confidence sweep 0.10/0.20/0.25/0.35/0.45; production NMS 0.45 and spatial 3-of-5/IoU 0.25. No suspicion opened at 0.35 at **any** input, either native or resized to the board's 320×240 working size. Input 640's peak raw score was only **0.085 native / 0.077 at 320×240**. A larger input therefore does not repair this particular footage's model mismatch.

| Input | Direct Guardian: detections / 85, native / 320×240 | Direct project smoke: detections / 54, native / 320×240 | Project smoke first suspicion, native / 320×240 |
|---|---|---|---|
| 192 | 0 / 3 | 40 / 45 | 2 s / 3 s |
| 320 | 2 / 1 | 17 / 7 | 4 s / none |
| 416 | 1 / 0 | 3 / 2 | none / none |
| 640 | 0 / 0 | 24 / 17 | 2 s / 2 s |

At 0.35, all three full negative files remained free of suspicions at all four inputs and both working sizes (fog 46, cloud 34, glare 42 samples each). These are selected clips, not a false-alarm-rate estimate. Some lower-threshold Guardian replays open events; that is not justification to lower the deployed threshold. It remains **0.35**.

**[UNO Q capture, Mac inference]** A temporary wrapper saved **40 lossless PNGs per camera immediately before `CaptureWorker.latest.put`**, timestamp and pixel hash included, plus a separate exact PNG of each analysed frame and the raw top-five anchor outputs before confidence filtering. On the 40 publication samples per camera, input 192 peaked at **0.209 left / 0.161 centre**, with **0/40 detections at 0.35 on each**. At input 320, left had 4/40 detections and a replayed suspicion; 416 had only two left detections; 640 had none at 0.35. Those scores are on a mixture of paused browser footage, full-screen footage and hands crossing the view. The first 30 samples mostly show a small player inside the desktop, rather than a frame-filling plume. This is evidence against choosing input size from a single picture, not a latency comparison.

**[UNO Q and Mac, same pixels]** The first **40 exact analysed PNGs per camera** were replayed at input 192 on the Mac. Absolute raw maximum-score difference: **0.003002 maximum, 0.000205 mean**. Production capture/detector/runtime/alarm files on both hosts had matching SHA-256 hashes. The shared model path letterboxes BGR frames, converts to RGB CHW float32 /255 and uses the same NMS/tracker for file and USB. No live-only colour/normalisation defect was found. The alarm never receives a candidate below confidence, so no alarm-rule relaxation is justified.

**[UNO Q, measured]** Direct board file replay at input 192, 0.35, 320×240 and one sample per video second found **46/54 smoke detections**, first suspicion at **video t=3 s**, opening confidence **0.37051**. Fog **0/46**, cloud **0/34**, glare **0/42**: zero detections and zero suspicions. This was an offline replay while the live station remained running; it is neither physical screen validation nor a throughput measurement.

**Capture-integrity finding [UNO Q].** Displaced rectangular image blocks are present in lossless centre samples `centre-raw-1794641358.896942.png` and `centre-raw-1794641359.935038.png`, not just the preview JPEGs. The existing green-footer guard accepts these arrays. It detects the previously observed zero-filled YUV footer, **not arbitrary block displacement**. Do not call the live path corruption-free. An explicit 320×240 YUYV, 5-fps capture request was subsequently negotiated by both drivers to reduce USB load; its final validation is recorded in the board notes.

Reproduction evidence is private: the supplied `detection-frames/` folder now contains `lossless/smoke-live-20261114/`, manifests, hashes, timestamped PNGs and board traces. Mac replay reports and source frames are retained under `/tmp/acorn-*-20261114/`. `scripts/diagnose_smoke.py --save-inputs` now also saves exact raw ORT output tensors and reports uncensored maximum/top-five scores; production decisions remain unchanged. Temporary live instrumentation is removed before the final normal launch. No camera image or credential is committed.

**[UNO Q, capture-only trial]** With 5-fps requests accepted by both drivers, a 207.20-second stationary-screen window measured 267.89 / 266.65 ms mean inference, 274.23 / 269.78 ms total analysis and 1.00927 / 1.00936 s mean per-camera intervals. RSS mean 175.97 MiB, CPU thermal zones 45.1–48.2°C. These are instrumented baseline timings, **not live smoke success or hall-negative validation**.

**Status at the end of the initial investigation (superseded by the live result below):** physical camera positioning/readiness did not arrive during this investigation; the views remained the unrelated stationary screen. The 5-fps trial was not adopted without moving-scene validation. The original capture configuration and normal station launcher were restored, temporary live instrumentation stopped, and dated trial/rollback files retained. The procedure is documented, but **live project-clip latency, camera isolation and hall/ordinary-video negatives remain unverified**. Do not present the direct-file result or the timing trial as a live demonstration success.

## 13. Later live centre-crop verification, 2026-11-14

**[UNO Q, measured live]** Commit `8a05ecd` adds `detector_view = "center_crop"`: the central 240×240 square of a 320×240 capture reaches input 192 without full-frame letterbox padding; the outer 40-pixel side strips are excluded. Default `full` is unchanged. With the project smoke clip truly full screen and controls hidden, the centre camera raised three suspicions (peaks 0.743 / 0.759 / 0.621), about 3 s from first raw 0.20 response to suspicion, while the hall camera stayed silent. Confidence stayed 0.35 and spatial voting stayed 3-of-5 / IoU 0.25. The same screen with full-frame letterboxing scored about 0.00–0.05; player controls in view also defeated detection.

Across 513 analyses per camera, mean inference was 276 ms, total analysis 281 / 282 ms, intervals 1.012 / 1.011 s, RSS 180 MiB, with score logging active. See [the board record](../firmware/BOARD_NOTES.md) for conditions and the subsequent unexplained restart/network loss. The 5-fps capture request was active in this later test, superseding the earlier rollback snapshot.

**[Mac, saved board frames]** Grey-world/levels and CLAHE corrections were rejected because they lifted no-smoke, hall or fireplace negatives. The model responds to dense daytime smoke filling the view; arbitrary news footage is not a reliable positive. This controlled screen result closes the earlier blanket claim that live project-clip success was unverified. It does not establish left-only isolation, fixed-duration negative controls, the recommended Crane Fire clip live, field sensitivity or false-alarm rates. The Mac quality tables and synthetic distant-smoke proxy above remain separate evidence.
