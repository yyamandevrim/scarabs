# ACORN screen captures

Local Screeny handoff, recorded 2026-11-14 from the running apps on an Apple M5 Mac. Files below are ignored and stay on this machine. Plain screen videos: no device frame or editorial captions baked in. All wide viewports are **16:9** for the 1920×1080 film.

Viewport is CSS pixels; `@2`/`@3` means DPR. Original wide video: 2880×1620; the preferred Station fit take is 2304×1296. Phone native frames: 1179×2556; H.264 MP4 adds **one black column at the right** (1180×2556) for decoder compatibility, without scaling/cropping the UI. Timestamped JPEG originals and action logs are in `_raw/`; reviewed stills are alongside the videos and in `review/`. MP4 is 30 fps with repeated frames at original timing; actual sampling was approximately 7–20 fps, not 30 distinct frames/s. No event or wait was accelerated.

| File | Shots | Viewport | Duration | State |
|---|---|---|---|---|
| `shot-05-07-08-17-station-phone.mp4` | 05/07/08/17 | 393×852 @3 | 15.1 s | Existing pending smoke suspicion; stable fallback, **no new arrival**. |
| `shot-08-17-ground.mp4` | 08/17 | 1440×810 @2 | 15.1 s | Matching received suspicion; Wi-Fi off; stable fallback. |
| `shot-09-station-phone.mp4` | 09 | 393×852 @3 | 45.3 s | Native saved clip plays, then initial confirmation. |
| `shot-10-station-phone.mp4` | 10 | 393×852 @3 | 45.3 s | Genuine annotation correction: Değiştir → Doğrula; rejected → confirmed. |
| `shot-10-ground.mp4` | 10 | 1440×810 @2 | 45.2 s | Same correction arrives at real legal slot; Wi-Fi off. |
| `shot-05-06-station-wide-fit.mp4` | 05/06 | 1152×648 @2 | 25.1 s | Preferred new take: both complete feeds together, source/profile/host visible. |
| `shot-05-06-station-wide.mp4` | 05/06 | 1440×810 @2 | 25.3 s | Smoke feed, fog feed, inactive right slot and host; honest scrolling. |
| `shot-11-ground-details.mp4` | 11 | 1440×810 @2 | 25.3 s | Packet UUID and calculated link details; last packet is 40 B. |
| `shot-12-ground-wifi.mp4` | 12 | 1440×810 @2 | 35.1 s | Off → saved Wi-Fi evidence plays → off; imagery disappears. |
| `shot-14-19-placement.mp4` | 14/19 | 1440×810 @2 | 25.4 s | Complete Haukilahti/Nuuksio Compare map, legend and simulation labels. |
| `shot-15-placement-changes.mp4` | 15 | 1440×810 @2 | 90.4 s | Heading 180°→0°→180°; left+right pair, then left+centre restored. |
| `shot-18-sensor-phone.mp4` | 18 | 393×852 @3 | 25.3 s | Authenticated simulated trigger/release and logical LED; no adjoining camera image. |

C1 new-arrival action failed: the same suspicion stayed open for the entire 180-second wait. Its fallback cannot establish arrival chronology. Initial C2 Ground footage was rejected because Wi-Fi was on; shot 10 shows a genuine **correction**, not a first decision. Those paired tracks start together: confirm 5.098 s, Ground update 13.522 s. Cut waits jointly; retain simulated/edited-wait labels. Event UUID: `83fae61ea28842dfa627eb1d2f66ce1a`.

Placement: 600 m, quick 120 m grid, smoke+canopy, 12 km model range, 50 m smoke target; Haukilahti 180°, Nuuksio 20°, left+centre, reference/polygon off. Station: demo, input 192, confidence 0.35, recorded smoke/fog, simulated MCU/UDP LoRa; duty ledger preserved.

Every accepted take was visually checked. The original wide Station take scrolls; the preferred fit take shows both feeds together. Dense Ground/map text still needs close framing. Retain captions, translations and credits from [MOCKUPS](../MOCKUPS.md) and [SHOTLIST](../SHOTLIST.md). Apps stopped; no Remotion remains.

## Screeny mockups — corrected framing

Device-framed outputs are now available locally in `mockups/clips/`: **11 H.264 MP4s, 1920×1080, 30 fps**, with the raw capture's name followed by `-mockup.mp4`. Station uses `shot-05-06-station-wide-fit-mockup.mp4`. The old scrolling Station take is superseded for mockups.

Phone shots focus on the genuine review/evidence or MCU section; unrelated lower-page content is cropped out, with safe space for the notch. The original recordings remain intact. Shot 09 uses the first 12 seconds of its take. Wide shots use a matching **16:9 Studio Display** frame; the mismatched MacBook frame was replaced. The Station overview additionally excludes the unrelated hardware strip below the complete feeds and host line. No interface controls or values were recreated.

- `mockups/alpha/`: the same 11 clips as transparent HEVC-alpha MOV elements for compatible editors.
- `mockups/acorn-phone-shots.screeny`: editable Screeny project, four phone items.
- `mockups/acorn-monitor-shots.screeny`: editable Screeny project, seven monitor items.
- Screeny app: **ACORN promo** folder, **ACORN — Phone video mockups** and **ACORN — Desktop video mockups**. A separate **ACORN — Station overview** project is retained.
- `mockups/review/`: inspected stills; `mockups/verification.json`: all 11 MP4s decoded fully. HEVC-alpha MOVs need an alpha-capable Apple/editor pipeline; the MP4s are opaque on the film's mineral background.

These are reusable mockup elements with recording handles. Film timing, paired-device assembly, subtitles and editorial provenance labels remain part of the film edit. Existing C1/decision limitations above still apply. For shot 18, the clean trigger/release select is approximately 5.3–11.3 seconds into its mockup; the longer clip retains handles.
