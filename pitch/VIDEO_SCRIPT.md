# ACORN — promo script

## The idea

**Minutes spent waiting for someone to notice smoke are minutes we want to give back. Making a watch station affordable and independent of an internet uplink could let more people keep watch.** That is the design ambition, not a measured time saving or a proven price advantage. No countdown, fire-growth statistic, cost or market claim appears in this film.

Master: **114 seconds, 16:9**. Quiet opening; tangible proof in the middle; the actual powered device at the end. Shot numbers match `SHOTLIST.md`. Read the voice-over naturally, leaving the remaining space for looking and listening. Times are editorial durations, never detection or delivery latency.

## Picture and type

Use the product's dark mineral canvas, restrained typography and large map area: background `#090e13`, panels `#0f161d`, text `#e3e9ee`, secondary `#a7b4bf`, interaction blue `#8fc3e3`. Amber `#f2a93b` belongs to smoke suspicion, red `#f0594e` to faults; mint `#5aefb0` belongs to visible forest on the map. IBM Plex Sans for titles, IBM Plex Mono for numeric labels. No glowing network lines, animated radar or decorative telemetry.

Use **ACORN as plain text**. `[LOGO SLOT — undecided; leave empty]` is a production placeholder, not a title to export. Existing interface logos do not settle the identity: crop only their header artwork or cover that artwork with plain ACORN text in the edit, preserving status and source labels. Do not modify the apps.

Every GENERATED shot carries a small, readable **“Illustration”** caption throughout, bottom left in a dark backing strip. Shot 04 adds **“Station concept · not deployed”**. Hard-cut into product evidence; never match a generated plume to a model box. All voice-over and editorial captions are English. Station currently uses Turkish controls: preserve the actual UI and add English translations beside the relevant action.

## Master script

| Shot / time | Voice-over — exact read | On-screen text — editorial overlay | What is seen |
|---|---|---|---|
| 01 · 00:00–00:07 · 7 s | “The first minutes of a forest fire can pass without anyone noticing.” | `Before someone notices` + `Illustration` | GENERATED: still, wide Finnish-looking forest at dawn. No fire or smoke. |
| 02 · 00:07–00:13 · 6 s | “We want to make those minutes count.” | `Illustration` | GENERATED: slow move just above the canopy; patient, not threatening. |
| 03 · 00:13–00:19 · 6 s | “But who can keep watch where there is no internet connection?” | `Observation without an internet uplink — the goal` + `Illustration` | GENERATED: remote ridge, forest extending beyond it. No signal bars or invented outage. |
| 04 · 00:19–00:25 · 6 s | “Our goal is a station more people could afford to put there.” | `Affordability is a design goal · cost not established` + `Illustration · Station concept · not deployed` | GENERATED: generic, unbranded observation-station concept on the ridge. No detection, transmission or ACORN replica. |
| 05 · 00:25–00:30 · 5 s | “This is ACORN, built by team Scarabs.” | `ACORN` / `Aerial Canopy Observation and Reporting Node` | REAL: hands place the actual assembly on the venue table. |
| 06 · 00:30–00:36 · 6 s | “Two USB cameras. Smoke analysis on the Arduino UNO Q.” | `Actual UNO Q hardware` | REAL: board, hub and cameras in one readable composition; no laptop benchmark number. |
| 07 · 00:36–00:43 · 7 s | “For this demonstration, recorded footage goes through the working pipeline on a laptop.” | `Laptop demo · real recorded footage` / `Not live forest cameras` | SCREEN: Station's two active recorded feeds and inactive mounted slot. Preserve the measured-host and recorded-source labels. |
| 08 · 00:43–00:50 · 7 s | “A smoke suspicion opens with evidence for a person to review.” | `Smoke suspicion · needs human review` / `Recorded-footage demonstration` | SCREEN: open one specific suspicion and play its saved clip. Never replace the source image. |
| 09 · 00:50–00:55 · 5 s | “They confirm or reject that suspicion.” | `Confirm suspicion / Reject` / `Operator annotation` | SCREEN: choose Doğrula on the same record; show the saved decision. |
| 10 · 00:55–01:03 · 8 s | “The remote view receives compact packets. LoRa transport is simulated today.” | `LoRa link · simulated transport` / `Packet-only view · no imagery` | SCREEN: Ground, Wi-Fi demo off, received alert selected. This packet can arrive before the operator decides; do not imply confirmation gates transmission. |
| 11 · 01:03–01:09 · 6 s | “A smoke alert is forty-two bytes. Images stay off that link.” | `42-byte smoke alert · packet v2` / `LoRa transport simulated` | SCREEN: Ground link details; keep calculated-radio wording visible. No implied real radio range. |
| 12 · 01:09–01:16 · 7 s | “Full evidence is a separate, close-range Wi-Fi connection.” | `Wi-Fi evidence demo · separate from LoRa` / `LoRa transport simulated` | SCREEN: enable Show Wi-Fi demo, show its built-in Wi-Fi-only label, then disable it and let the imagery disappear. |
| 13 · 01:16–01:21 · 5 s | “And where you put a station matters.” | `Illustration` | GENERATED: lateral view of canopy and intervening ridge. No visibility overlay. |
| 14 · 01:21–01:28 · 7 s | “Our map estimates visible forest using real Finnish terrain and forest data.” | `Simulated geometric visibility` / `Not a detection range` | SCREEN: Placement Launch map, loaded comparison with simulation labels beside the figures. |
| 15 · 01:28–01:36 · 8 s | “Change the heading. Compare camera pairs. See what the terrain hides.” | `Planning estimate · not field validation` | SCREEN: Haukilahti heading change, restore, then select an achievable camera pair. Do not rush an unfinished calculation. |
| 16 · 01:36–01:40 · 4 s | “Earlier notice is the aim.” | `Illustration` | GENERATED: return to the opening forest. No fire, rescue or before/after result. |
| 17 · 01:40–01:44 · 4 s | “Board detection quality still needs testing.” | `Actual board · two live USB cameras` / `Detection quality unverified` | REAL: both physical cameras connected to the powered board at the venue. |
| 18 · 01:44–01:48 · 4 s | “The local infrared sensor is separate.” | `Short-range local IR sensor` / `Does not confirm camera smoke` | REAL: KY-026 and a controlled nearby IR stimulus in one honest shot; no forest-fire intercut. |
| 19 · 01:48–01:51 · 3 s | “Its status is visible here.” | `On-board status LED · actual response` | REAL: continuation of the sensor take, reframed to LED4's observed response. Never use the unverified external RGB LED. |
| 20 · 01:51–01:54 · 3 s | “Here is ACORN, running.” | `ACORN · Scarabs` / `Junction 2026 · Helsinki` | REAL: hold on the actual powered assembly, cameras and visible on-board LED. Keep its real current state. Cut to black after this shot; no slogan or logo end card. |

The packet size follows current `DEMO.md`: v2 smoke alerts are **42 bytes**, status packets **40 bytes**, flame/decision packets **37 bytes**. Do not copy the brief's older “40-byte alert” shorthand into the edit. No packet-size claim implies measured radio transmission.

## Alternative social cut — exactly 30 seconds

Reuse master takes; no extra shot assets. Deliver 16:9 with English subtitles. The same source and illustration labels remain readable. Do not vertically crop away provenance if a different format is made later.

| Time / reused shot | Exact voice-over | Overlay and edit |
|---|---|---|
| 00:00–00:04 · 01 | “Who is watching before smoke is noticed?” | `Illustration`. Forest, no fire. |
| 00:04–00:08 · 06 | “ACORN runs smoke analysis on an Arduino UNO Q.” | `Actual hardware · detection quality unverified`. |
| 00:08–00:13 · 08 | “This laptop demo raises a suspicion for human review.” | `Laptop · recorded footage` / `Smoke suspicion`. Keep the recorded-source label. |
| 00:13–00:18 · 10 | “The remote link carries packets. LoRa is simulated today.” | `LoRa transport simulated · no imagery`. Wi-Fi switch off. |
| 00:18–00:23 · 14 | “The map estimates where to place it.” | `Simulated visibility · not detection range`. |
| 00:23–00:27 · 04 | “More affordable forest observation is our goal.” | `Illustration · station concept, not deployed` / `Cost not established`. |
| 00:27–00:30 · 20 | “This is ACORN, running.” | `ACORN · Scarabs`. Actual device is the last image. |

## Editorial evidence and release notes

- Concept and identity: root `README.md`, `placement/brand.json`. The brief overrides the repository's supplied logo choice: this package reserves an empty logo slot.
- Device operation, local sensor/LED and limits: `docs/ARDUINO_UNO_Q.md`, `firmware/BOARD_NOTES.md`, `station/README.md`. Do not imply a flown station, weatherproof enclosure, measured autonomy, solar supply, physical internet-disconnection test, working access point or real radio.
- Product sequence, packet sizes and separate Wi-Fi path: `DEMO.md`, sections C and E. Runtime is designed to operate locally after preparation; remote radio operation without a network remains a goal until hardware is verified.
- Placement interpretation and visual system: `placement/DESIGN.md`, plus the three apps' static HTML/CSS. All coverage figures remain simulation outputs with their assumptions visible.
- Quality caveat: `station/DETECTION_VS_INPUT_SIZE.md`. Fast throughput is not evidence of adequate small-smoke sensitivity.
- Use the source-credit copy in `SHOTLIST.md` with both exports and deck handoff. No third-party recorded footage should be relabelled as captured by ACORN in the field.

Production placeholders: `[LOGO SLOT]`, `[CAPTURE DATE / ACTUAL TAKE CONDITIONS]`, `[LOCAL IR STIMULUS / OBSERVED DISTANCE]`. Optional future proof points are in `DECK.md`; none is needed to export this script as written. Timing is a paper edit; record a scratch read and adjust pauses within the fixed scene windows before final voice generation.
