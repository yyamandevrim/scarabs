# ACORN English screen captures — 2026-11-14

Current takes were recorded on this Mac from a **fresh clone of pushed origin/main**, commit `ab2227499aed4a3a7fd6bf3402f34859b0969f85` (includes English UI `fe1f57f` and centre crop `8a05ecd`). Models/media and prepared map data were reused locally; app source came from the clone. Later main commits do not change that provenance. All three interfaces are English. These are laptop browser captures, not board/phone deployment evidence.

Old Turkish captures, raw frames, reviews and editable Screeny projects are preserved under `archive-2026-11-14-tr/`, with their original index there. No recording or third-party footage is committed. Current clips live in ignored `en/`; current device frames in ignored `mockups/clips/`.

## Method and conditions

Playwright Chromium, viewport-only timestamped JPEGs, matching the earlier capture method. Phone **393×852 CSS / DPR 3**, native 1179×2556; H.264 pads one black column to 1180. Ground/Placement **1440×810 / DPR 2** (2880×1620), Station overview **1152×648 / DPR 2** (2304×1296). Browser zoom 100%, background throttling disabled, concurrent paired contexts and a common wall clock. MP4 is 30 fps with repeated native samples at original timestamps, not 30 unique samples/s. No waits are accelerated.

Ground starts before Station. Station is stopped and its review records archived with the documented CLI before each arrival take; the duty ledger is preserved. Ground history is preserved. Starting the real recorded source triggers normal inference; no events, controls, values or media are injected into a product screen. Login takes place before recording and its generated private secret is never visible. Simulated local-sensor API actions follow DEMO.md D explicitly.

Station: demo profile, 192 input, threshold 0.35, 1 analysis/s/camera, recorded smoke/fog with inactive cloud slot, laptop full-frame inference (the board centre-crop measurement is separate). MCU simulated. UDP LoRa simulated, SF7/BW125/CR4/5, strict 1% duty, persistent ledger. App captures show actual source/host/status. Recording uses isolated task ports, all task-started servers stopped after capture.

## Accepted takes

| Take / local MP4 in `en/` | Use | Actual state |
|---|---|---|
| `C1-phone.mp4`, `C1-ground.mp4` | Screeny solo phone, shot 07 | First genuine new arrival; raw Ground keeps prior selected alert, so it is superseded for paired scenes. |
| `B1-phone.mp4`, `B1-ground.mp4` | 05/08/17, deck 5 | Second genuine arrival; matching alert selected using Show direction, Wi-Fi off. |
| `B2-phone.mp4`, `B2-ground.mp4` | 09/10, deck 4 | Native saved evidence plays (verified advancing), then first confirmation and matching received decision. |
| `C3-wide.mp4` | 05/06, deck 3/9 | Both complete feeds, profile and measured-on-Mac line together. |
| `C4-ground.mp4` | 11 | Earlier event's UUID and calculated link details; labelled separate details take. Latest packet can be 40-byte status. |
| `C5-ground.mp4` | 12 | Separate earlier-event Wi-Fi evidence; real off/on/off toggle, ending without imagery. |
| `C6-map.mp4` | 14/19, deck 6/8 | Completed Compare map and legend. |
| `C7-map.mp4` | 15 | Heading 180→0→180; left+right then left+centre, completed calculations only in the cut. |
| `C8-phone.mp4` | 18 | Authenticated simulated local IR trigger/release and logical LED; frame crops out adjoining camera imagery. |
| `C9-evidence-phone.mp4` | Spare | Earlier reviewed event reopened with Change; playback verified. Not used for the first-decision sequence. |

`C2-*` are superseded: their evidence control click landed on the timeline and did not play. Failed/aborted directories remain local and are excluded. All accepted native JPEGs are decoded/verified during encoding; every resulting video is fully decoded. Visual review includes each state, transition and one frame from every shot of both final films. Automated complete decoding is frame-by-frame integrity checking, not a claim that a human inspected every duplicate frame.

## Event chronology

First take UUID `7ba5d19a1f834b19a15c789b5c928d20`: Station arrival **2.731 s**, Ground receipt **13.581 s**, on Ground's recording clock. Phone starts **0.419 s** later. This is the Screeny solo arrival take, not paired with the second event.

Selected paired take UUID `4b19c5f90b084ad99e765653530fde7c`: Station arrival **5.526 s**, Ground receipt **7.344 s** on Ground's B1 clock. Phone starts **3.173 s** later; both tracks' in-points account for it. The seven-second master paired scene is one uninterrupted, real-time interval, Ground t=4.5–11.5 s. These are observed browser times in a simulated transport demo, not measured radio latency.

B2 first confirmation **6.432 s**, Ground decision receipt **11.304 s** after its recording starts (phone/Ground start difference 1 ms). The edit removes the same shared waiting interval from both tracks and says so. Native playback was running at t=1.188 s, paused=false. No local acknowledgement is presented as an operator decision.

Placement conditions: 600 m height; quick 120 m grid; smoke+canopy; Haukilahti 180°, Nuuksio 20°; left+centre; 12 km model limit; 50 m smoke target; reference/polygon off. C7 completed states: heading 0 at 12.048 s, heading 180 at 18.594 s, left+right at 25.653 s, restored left+centre at 32.232 s. Figures are geometric simulations, not flight altitude validation or detection range.

## Frames and Screeny accounting

Screeny MCP at local port 9410: checked **4 credits before**, **1 after**; a single video export cost 3. No purchase. Free preview inspected first. The existing ACORN phone project supplied the look. `mockups/C1-arrival-screeny.mp4` is the native export; `mockups/clips/C1-arrival-screeny.mp4` is its 1920×1080 / 30 fps version. **Only shot 07 uses Screeny.** Its separate-take label preserves the event distinction.

**Own frames:** shots **05–06, 08–12, 14–15, 17–19**, and all deck stills. `edit/frame_captures.py` draws plain, logo-free dark phone/laptop geometry with Pillow and composites unchanged capture pixels with ffmpeg. No proprietary device asset is reused. All framed clips are 1920×1080 / 30 fps. The sensor shot uses a disclosed static crop/pad to isolate the actual module; no UI value is repainted. No app header mask or translations are required in these English takes. The deck uses ACORN text for its name treatment.

Capture logs, clocks, rejected takes and full local integrity results remain beside the recordings. Credits for the real source footage, model, map and font accompany the films in `edit/README.md` and the deck in `deck/NOTES.md`.
