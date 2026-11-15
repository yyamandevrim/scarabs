# Station b-roll manifest — 2026-11-15

23 distinct takes / 215 s, plus 14 landscape 1080p copies; 37 MP4 files / 349 s including copies. 34 PNG stills, plus contact-sheet.png.

Commit `0027611` — working tree with uncommitted changes. Captured the existing station source without tracked edits; other surfaces had ongoing changes. `git diff -- station` was empty.

## Conditions and method

- Local station only, HTTP 8191. Ignored `station/broll-station.local.toml` copied from `demo-lora.toml`, with separate data/state under this output folder and unused UDP destination 19191. MCU simulated; physical board unplugged. No ground receiver started. Config and private secret deleted and station stopped after capture. Isolated persistent duty ledger retained in `state/`; no existing config records or ledgers touched.
- Real local `models/smoke.onnx`, demo profile, input 192, confidence threshold 0.35, 1 analysis/s/camera, unchanged spatial 3-of-5 / IoU 0.25, 12 s timeout, full-frame detector. Left: `media/smoke.ogv`; Center: `media/fog.webm`; right cloud mounting inactive. No events, UI values or media injected. Only the runbook’s explicit MCU simulation endpoint was used for take 17.
- Headless Playwright Chromium; viewport content only. Landscape 1440×810 CSS / DPR 2, 2880×1620 native; phone 393×852 CSS / DPR 3, 1179×2556 native PNG and one black right column padded to 1180 for H.264. No display, keyboard or foreground app takeover. No browser chrome or cursor. English UI. Authentication used the real local auth endpoint before app takes; login takes contain only an empty form and no secret was typed.
- Native rendered viewport samples requested at 30 Hz, pipelined for actual sampling throughput; samples retained individually and encoded at 30 fps without motion interpolation or intentional time compression. Capture timestamps retained in `takes.json`; sampling timestamps and per-take elapsed times are recorded, with no intentional frame duplication or interpolation. PNGs made during a take share its quality-95 JPEG sample; standalone/full-page PNGs use native screenshots. No content pixels repainted.
- MP4: libx264 CRF 14, yuv420p, 30 fps CFR, no audio, +faststart. Every landscape take has a Lanczos 1920×1080 copy. All MP4s ffprobed and fully decoded once; start/middle/end frames inspected. QA evidence is in `validation.json` and `work/qa/`.
- The application itself refreshes live preview JPEGs once per second; saved event clips use its configured 5 fps. Those genuine source limits remain visible, including stepped smoke/fog motion. Scrolls and controls are captured at 30 Hz. This is laptop recorded-footage demonstration, not airborne/live-board footage or a radio range/latency measurement.
- Smoke footage: “Wildfire Near Monserrate”, Peter Angritt / Mrtony77, CC BY-SA 4.0. Fog footage: “Fog covering mountain time lapse”, Athulvis, CC BY-SA 4.0 (repository provenance notes a pending external licence-review notice). Source/credit details remain in `station/footage.json`. Model provenance: Pyronear YOLO11s. No footage downloads or substitutions were made.

## Real event continuity

- Phone arrival/decision takes 03, 05–08 and landscape history/correction takes 09–13 use `1fe6a2ce3d844d92a933353cd61e531c`: first confirmed, then corrected to rejected through Change. The phone confirmation still shows the open saved record; the video briefly also covers the collapsed history disclosure.
- Landscape arrival/confirmation takes 14 and 16, native overflow-menu take 22 and saved-frame take 20 use `bb9f56cb40d447888d427a12e7e70afb`. This is a separate genuine event after a station restart; the first event and ledger were preserved.
- Evidence takes 04 and 15 were replaced after QA using a later genuine pending event; they are separate takes from the earlier arrival/confirmation sequence. One original smoke source loop and the later verification restart produced further real records; no old decisions were rewritten for the retake. Original rejected captures remain under `work/rejected/`. Take 13 was also recaptured after allowing the headless compositor to settle. All final first/middle/end frames were checked again.
- Local sensor take 17 uses the documented MCU simulation; event `dce79d179b2d4560a683fa59d8db6373`. The sensor releases before its read LED hold ends; take 17 preserves that distinction. Still 24 deliberately shows normal sensor, red read LED and normal requested LED during that hold.
- Queue take 21 and media take 23 follow five further process restarts, each yielding a genuine detector suspicion without changing thresholds or inserting records. Pending IDs are in `events-provenance.json`; newest is `5f835c9e65c54ae2b136adf5ef14ef38`. Earlier restarted events can have shortened post-roll, as documented by the app. These takes demonstrate real UI queue navigation, not uninterrupted five-event field incidence.
- Initial calibration records in this isolated config were archived using the supported CLI while the station was stopped. The ledger was preserved. This did not archive anyone else’s records.

## Coverage and limitations

- Captured: empty login at both sizes; genuine phone and landscape arrivals; native clip playback; saved annotated frame; confidence/box; Confirm, Reject, Change and Cancel; reviewed history; both moving feeds; inactive slot; MCU and sensor scope; LED/alarm trigger/release; camera configuration; full-page views; multi-record Newest/Oldest/older-record controls; native overflow and playback-speed menus; native 2x detail crops.
- No maintenance page or editable settings dialog exists on this station surface. The read-only Camera configuration disclosure is captured. Pagination beyond 200 pending events was not manufactured, and native Picture-in-Picture outside the viewport was excluded. Fullscreen evidence was attempted but excluded: the headless capture resized/exited fullscreen or returned a tiled surface, so no clean fullscreen clip is delivered. No hardware-camera outage was induced because the media sources are shared with concurrent agents.
- Product observations: full landscape feeds and hardware cannot fit together at 1440×810; honest scrolling and a full-page still cover them. Preview cadence is only 1 Hz, and the real saved evidence is 5 fps. No other visual defect was observed in the accepted takes. Arrival takes show the normal “Preparing event clip…” interval; later evidence takes show the completed playable clip.

## Files

| File | Duration | Resolution | FPS | View / actual state |
|---|---:|---:|---:|---|
| [video/station-01-login-landscape-1080.mp4](video/station-01-login-landscape-1080.mp4) | 6.00 s | 1920×1080 | 30 CFR | 1080p copy. Empty login page; unauthenticated. |
| [video/station-01-login-landscape.mp4](video/station-01-login-landscape.mp4) | 6.00 s | 2880×1620 | 30 CFR | Empty login page; unauthenticated. |
| [video/station-02-login-phone.mp4](video/station-02-login-phone.mp4) | 6.00 s | 1180×2556 | 30 CFR | Phone login empty form. |
| [video/station-03-arrival-phone.mp4](video/station-03-arrival-phone.mp4) | 9.00 s | 1180×2556 | 30 CFR | New genuine smoke suspicion from recorded smoke through real detector; MCU and UDP simulated. |
| [video/station-04-evidence-phone.mp4](video/station-04-evidence-phone.mp4) | 10.00 s | 1180×2556 | 30 CFR | Retake on latest genuine pending suspicion after QA; native saved evidence playback, separate event from initial confirmation take. |
| [video/station-05-confirm-phone.mp4](video/station-05-confirm-phone.mp4) | 8.00 s | 1180×2556 | 30 CFR | Confirm suspicion persists the operator decision and moves it to reviewed records. |
| [video/station-06-change-reject-phone.mp4](video/station-06-change-reject-phone.mp4) | 10.00 s | 1180×2556 | 30 CFR | Change reopens saved evidence; Reject corrects the original confirmation. |
| [video/station-07-history-phone.mp4](video/station-07-history-phone.mp4) | 8.00 s | 1180×2556 | 30 CFR | Reviewed-record disclosure collapses and opens; persisted rejected decision. |
| [video/station-08-camera-scroll-phone.mp4](video/station-08-camera-scroll-phone.mp4) | 14.00 s | 1180×2556 | 30 CFR | Ranger phone layout scrolling through real smoke and fog feeds to inactive slot, simulated MCU and configuration. |
| [video/station-09-overview-landscape-1080.mp4](video/station-09-overview-landscape-1080.mp4) | 12.00 s | 1920×1080 | 30 CFR | 1080p copy. Landscape overview with moving recorded feeds, measured analysis and native queue. |
| [video/station-09-overview-landscape.mp4](video/station-09-overview-landscape.mp4) | 12.00 s | 2880×1620 | 30 CFR | Landscape overview with moving recorded feeds, measured analysis and native queue. |
| [video/station-10-hardware-landscape-1080.mp4](video/station-10-hardware-landscape-1080.mp4) | 12.00 s | 1920×1080 | 30 CFR | 1080p copy. Scroll from feeds to inactive mounting, MCU simulation, status LED and hardware strip. |
| [video/station-10-hardware-landscape.mp4](video/station-10-hardware-landscape.mp4) | 12.00 s | 2880×1620 | 30 CFR | Scroll from feeds to inactive mounting, MCU simulation, status LED and hardware strip. |
| [video/station-11-sensor-scope-landscape-1080.mp4](video/station-11-sensor-scope-landscape-1080.mp4) | 9.00 s | 1920×1080 | 30 CFR | 1080p copy. Open Local sensor scope disclosure: relative uncalibrated IR level and requested/read LED distinction. |
| [video/station-11-sensor-scope-landscape.mp4](video/station-11-sensor-scope-landscape.mp4) | 9.00 s | 2880×1620 | 30 CFR | Open Local sensor scope disclosure: relative uncalibrated IR level and requested/read LED distinction. |
| [video/station-12-configuration-landscape-1080.mp4](video/station-12-configuration-landscape-1080.mp4) | 10.00 s | 1920×1080 | 30 CFR | 1080p copy. Camera configuration disclosure expanded: active pair geometry and unchanged detector rules. |
| [video/station-12-configuration-landscape.mp4](video/station-12-configuration-landscape.mp4) | 10.00 s | 2880×1620 | 30 CFR | Camera configuration disclosure expanded: active pair geometry and unchanged detector rules. |
| [video/station-13-change-cancel-landscape-1080.mp4](video/station-13-change-cancel-landscape-1080.mp4) | 10.00 s | 1920×1080 | 30 CFR | 1080p copy. Retake: original reviewed rejection, Change exposes saved evidence and Cancel preserves the existing decision. |
| [video/station-13-change-cancel-landscape.mp4](video/station-13-change-cancel-landscape.mp4) | 10.00 s | 2880×1620 | 30 CFR | Retake: original reviewed rejection, Change exposes saved evidence and Cancel preserves the existing decision. |
| [video/station-14-arrival-landscape-1080.mp4](video/station-14-arrival-landscape-1080.mp4) | 9.00 s | 1920×1080 | 30 CFR | 1080p copy. Second genuine suspicion opens after process restart; earlier reviewed history preserved. |
| [video/station-14-arrival-landscape.mp4](video/station-14-arrival-landscape.mp4) | 9.00 s | 2880×1620 | 30 CFR | Second genuine suspicion opens after process restart; earlier reviewed history preserved. |
| [video/station-15-evidence-landscape-1080.mp4](video/station-15-evidence-landscape-1080.mp4) | 10.00 s | 1920×1080 | 30 CFR | 1080p copy. Retake: completed native saved evidence on latest genuine pending event; separate from the earlier confirmation take. |
| [video/station-15-evidence-landscape.mp4](video/station-15-evidence-landscape.mp4) | 10.00 s | 2880×1620 | 30 CFR | Retake: completed native saved evidence on latest genuine pending event; separate from the earlier confirmation take. |
| [video/station-16-confirm-landscape-1080.mp4](video/station-16-confirm-landscape-1080.mp4) | 8.00 s | 1920×1080 | 30 CFR | 1080p copy. Confirm genuine pending suspicion; reviewed history gains second decision. |
| [video/station-16-confirm-landscape.mp4](video/station-16-confirm-landscape.mp4) | 8.00 s | 2880×1620 | 30 CFR | Confirm genuine pending suspicion; reviewed history gains second decision. |
| [video/station-17-simulated-sensor-alarm-1080.mp4](video/station-17-simulated-sensor-alarm-1080.mp4) | 14.00 s | 1920×1080 | 30 CFR | 1080p copy. Documented local MCU simulation trigger and release: normal → triggered red LED → release; never a physical board claim. |
| [video/station-17-simulated-sensor-alarm.mp4](video/station-17-simulated-sensor-alarm.mp4) | 14.00 s | 2880×1620 | 30 CFR | Documented local MCU simulation trigger and release: normal → triggered red LED → release; never a physical board claim. |
| [video/station-18-configuration-phone.mp4](video/station-18-configuration-phone.mp4) | 8.00 s | 1180×2556 | 30 CFR | Phone camera configuration geometry and detector settings. |
| [video/station-19-sensor-scope-phone.mp4](video/station-19-sensor-scope-phone.mp4) | 8.00 s | 1180×2556 | 30 CFR | Phone local sensor scope disclosure and simulated status LED. |
| [video/station-20-saved-frame-landscape-1080.mp4](video/station-20-saved-frame-landscape-1080.mp4) | 6.00 s | 1920×1080 | 30 CFR | 1080p copy. Original saved annotated event image with opening confidence and box. |
| [video/station-20-saved-frame-landscape.mp4](video/station-20-saved-frame-landscape.mp4) | 6.00 s | 2880×1620 | 30 CFR | Original saved annotated event image with opening confidence and box. |
| [video/station-21-queue-navigation-landscape-1080.mp4](video/station-21-queue-navigation-landscape-1080.mp4) | 14.00 s | 1920×1080 | 30 CFR | 1080p copy. Multiple real suspicion records: Newest, Oldest awaiting review, expanded older rows; event identities and duty ledger preserved. |
| [video/station-21-queue-navigation-landscape.mp4](video/station-21-queue-navigation-landscape.mp4) | 14.00 s | 2880×1620 | 30 CFR | Multiple real suspicion records: Newest, Oldest awaiting review, expanded older rows; event identities and duty ledger preserved. |
| [video/station-22-video-controls-menu-1080.mp4](video/station-22-video-controls-menu-1080.mp4) | 7.00 s | 1920×1080 | 30 CFR | 1080p copy. Native saved-video overflow menu and dismissal. |
| [video/station-22-video-controls-menu.mp4](video/station-22-video-controls-menu.mp4) | 7.00 s | 2880×1620 | 30 CFR | Native saved-video overflow menu and dismissal. |
| [video/station-23-playback-speed-menu-1080.mp4](video/station-23-playback-speed-menu-1080.mp4) | 7.00 s | 1920×1080 | 30 CFR | 1080p copy. Native playback speed submenu and dismissal; no rate changes. |
| [video/station-23-playback-speed-menu.mp4](video/station-23-playback-speed-menu.mp4) | 7.00 s | 2880×1620 | 30 CFR | Native playback speed submenu and dismissal; no rate changes. |
| [stills/station-01-login-landscape.png](stills/station-01-login-landscape.png) | — | 2880×1620 | — | Empty login form; secret never entered. |
| [stills/station-02-login-phone.png](stills/station-02-login-phone.png) | — | 1179×2556 | — | Empty responsive login. |
| [stills/station-03-arrival-phone.png](stills/station-03-arrival-phone.png) | — | 1179×2556 | — | Genuine newly opened smoke suspicion; awaiting decision. |
| [stills/station-04-evidence-phone.png](stills/station-04-evidence-phone.png) | — | 1179×2556 | — | Retake: latest genuine pending event, completed saved evidence ready to play; separate event from first confirmation take. |
| [stills/station-05-playing-phone.png](stills/station-05-playing-phone.png) | — | 1179×2556 | — | Retake: native saved clip actually playing. |
| [stills/station-06-confirmed-phone.png](stills/station-06-confirmed-phone.png) | — | 1179×2556 | — | Confirmed suspicion in open reviewed records. |
| [stills/station-07-change-phone.png](stills/station-07-change-phone.png) | — | 1179×2556 | — | Change decision: evidence, Confirm, Reject and Cancel. |
| [stills/station-08-rejected-phone.png](stills/station-08-rejected-phone.png) | — | 1179×2556 | — | Saved rejected decision. |
| [stills/station-09-feeds-phone.png](stills/station-09-feeds-phone.png) | — | 1179×2556 | — | Phone camera feeds and recorded-source labels. |
| [stills/station-10-hardware-phone.png](stills/station-10-hardware-phone.png) | — | 1179×2556 | — | Phone hardware strip and configuration disclosure. |
| [stills/station-11-full-page-phone.png](stills/station-11-full-page-phone.png) | — | 3537×7668 | — | Complete responsive page with saved reviewed decision, both feeds and hardware. |
| [stills/station-12-overview-landscape.png](stills/station-12-overview-landscape.png) | — | 2880×1620 | — | Landscape top overview: smoke feed and reviewed/pending records. |
| [stills/station-13-both-feeds-landscape.png](stills/station-13-both-feeds-landscape.png) | — | 2880×1620 | — | Both active file feeds in landscape. |
| [stills/station-14-hardware-landscape.png](stills/station-14-hardware-landscape.png) | — | 2880×1620 | — | Inactive slot, measured-on-Mac line, simulated sensor and LED strip. |
| [stills/station-15-sensor-scope-landscape.png](stills/station-15-sensor-scope-landscape.png) | — | 2880×1620 | — | Sensor scope expanded. |
| [stills/station-16-configuration-landscape.png](stills/station-16-configuration-landscape.png) | — | 2880×1620 | — | Read-only configuration expanded; actual source geometries. |
| [stills/station-17-full-page-landscape.png](stills/station-17-full-page-landscape.png) | — | 5760×6610 | — | Full landscape page: real feeds, hardware and expanded configuration. |
| [stills/station-18-event-landscape.png](stills/station-18-event-landscape.png) | — | 2880×1620 | — | Retake: original reviewed event opened for change with genuine saved evidence. |
| [stills/station-19-history-landscape.png](stills/station-19-history-landscape.png) | — | 2880×1620 | — | Reviewed records with persisted rejection. |
| [stills/station-20-arrival-landscape.png](stills/station-20-arrival-landscape.png) | — | 2880×1620 | — | New pending suspicion with retained reviewed history. |
| [stills/station-21-playing-landscape.png](stills/station-21-playing-landscape.png) | — | 2880×1620 | — | Retake: actual native saved clip playback. |
| [stills/station-22-confirmed-landscape.png](stills/station-22-confirmed-landscape.png) | — | 2880×1620 | — | Confirmed and rejected records in history. |
| [stills/station-23-sensor-triggered-landscape.png](stills/station-23-sensor-triggered-landscape.png) | — | 2880×1620 | — | Simulated local sensor triggered and red logical LED. |
| [stills/station-24-sensor-released-landscape.png](stills/station-24-sensor-released-landscape.png) | — | 2880×1620 | — | Simulated local sensor released; read LED still red during its hold while requested station LED has returned to normal. |
| [stills/station-25-configuration-phone.png](stills/station-25-configuration-phone.png) | — | 1179×2556 | — | Phone read-only camera configuration. |
| [stills/station-26-sensor-scope-phone.png](stills/station-26-sensor-scope-phone.png) | — | 1179×2556 | — | Phone sensor scope and simulation labels. |
| [stills/station-27-saved-frame-landscape.png](stills/station-27-saved-frame-landscape.png) | — | 2880×1620 | — | Original saved annotated JPEG viewed directly from real event endpoint; no replacement pixels. |
| [stills/station-28-queue-landscape.png](stills/station-28-queue-landscape.png) | — | 2880×1620 | — | Five genuine suspicions accumulated across five documented restarts; earlier history retained. |
| [stills/station-29-queue-expanded-landscape.png](stills/station-29-queue-expanded-landscape.png) | — | 2880×1620 | — | Expanded multiple-record review queue. |
| [stills/station-30-video-menu-landscape.png](stills/station-30-video-menu-landscape.png) | — | 2880×1620 | — | Native saved-video overflow menu. |
| [stills/station-31-playback-speed-landscape.png](stills/station-31-playback-speed-landscape.png) | — | 2880×1620 | — | Native playback speed submenu; normal speed unchanged. |
| [stills/station-32-evidence-detail-2x.png](stills/station-32-evidence-detail-2x.png) | — | 800×1394 | — | Unaltered 2x crop of actual event review panel: evidence, detection box, confidence and correction controls. |
| [stills/station-33-hardware-detail-2x.png](stills/station-33-hardware-detail-2x.png) | — | 1452×650 | — | Unaltered 2x detail crop of local sensor and LED panel. |
| [stills/station-34-configuration-detail-2x.png](stills/station-34-configuration-detail-2x.png) | — | 2040×350 | — | Unaltered 2x detail crop of camera configuration. |
| [contact-sheet.png](contact-sheet.png) | — | 1600×5040 | — | Representative frame from every exported video and PNG still, labelled by filename. |

Support files: `conditions.toml` is the non-secret configuration snapshot; `takes.json` contains action/capture timing and descriptions; `events-provenance.json` contains the actual isolated event records; `validation.json` records every MP4 decode/probe. `state/` contains the isolated runtime evidence and retained ledger. `work/` contains capture/verification scripts, logs and QA frames, not additional accepted b-roll. No media committed, pushed, deployed or uploaded.

Motion QA: one-second eased-scroll samples in phone take 08 and landscape take 09 each decode to 30 distinct rendered frames (30/30), recorded in `work/motion-sampling.json`.
