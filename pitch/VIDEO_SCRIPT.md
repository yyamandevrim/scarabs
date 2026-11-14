# ACORN — promo script

## The idea

**Minutes spent waiting for someone to notice smoke are minutes we want to give back. Making a watch station affordable and independent of an internet uplink could let more people keep watch.** That is the design ambition, not a measured time saving or proven price advantage. No countdown, fire-growth statistic, cost or market claim appears in this film.

Master: **114 seconds, 16:9, 20 shots**. Sources: **13 MOCKUP / 6 GENERATED / 1 REAL** (previously 8 SCREEN / 6 GENERATED / 6 REAL). Quiet opening; real app output in devices in the middle; an authentic photograph of the prototype at the end. **One REAL shot, one required hardware photograph, zero filming**: hardware judges need to see the actual assembly; a generated substitute cannot establish its existence. Reuse that photo in the deck. A still is not proof of operation or a sensor response.

Shot numbers match `SHOTLIST.md`; capture IDs and exact recipes are in `MOCKUPS.md`. Times are editorial durations, never detection/delivery latency. Every MOCKUP uses real running-app captures; no painted UI. Read naturally with space around actions.

## Picture and type

Dark mineral background `#090e13`, panels `#0f161d`, text `#e3e9ee`, secondary `#a7b4bf`, blue `#8fc3e3`. Amber `#f2a93b` means smoke suspicion, red `#f0594e` faults; mint `#5aefb0` visible forest. IBM Plex Sans titles, IBM Plex Mono numeric labels. Generic Mac-style displays/laptop and iPhone-style portrait phone share matte edges, diffuse silver light and subtle shadows. Keep product pixels sharp, with no landscape grain or generative enhancement. No network waves, radar or decorative telemetry.

Use **ACORN as plain text**. `[LOGO SLOT — undecided; leave empty]` is not exported. Cover only existing header logo artwork in the composition, following its scroll position, with plain ACORN; never cover status/source labels. No app changes. Station is Turkish: retain it and add English translations outside the device. All editorial copy is English.

Every GENERATED frame carries **Illustration** on a dark backing; 04 adds **Station concept · not deployed**. Generated scenes are mood/context, never camera input, inference, map output or ACORN detecting a real fire. Hard-cut into product evidence. The physical photo is labelled **Actual prototype · still photograph**.

All Station and related Ground demo shots carry **Laptop demo · recorded footage**. Wherever LoRa appears, retain **LoRa transport simulated**. Phone mockups show the nearby ranger's intended panel use, not tested AP mode or a physical iPhone deployment. The remote desk receives no imagery with Wi-Fi demo off. Shot 12 is a separate Wi-Fi evidence demonstration.

## Master script

| Shot / time | Voice-over — exact read | On-screen text — editorial overlay | What is seen |
|---|---|---|---|
| 01 · 00:00–00:07 · 7 s | “The first minutes of a forest fire can pass without anyone noticing.” | `Before someone notices` / `Illustration` | GENERATED: quiet wide forest at dawn; no smoke/fire. |
| 02 · 00:07–00:13 · 6 s | “We want to make those minutes count.” | `Illustration` | GENERATED: slow canopy move. |
| 03 · 00:13–00:19 · 6 s | “But who can keep watch where there is no internet connection?” | `Observation without an internet uplink — the goal` / `Illustration` | GENERATED: remote ridge; no claimed outage. |
| 04 · 00:19–00:25 · 6 s | “Our goal is a station more people could afford to put there.” | `Cost not established` / `Illustration · Station concept · not deployed` | GENERATED: inert generic unbranded concept in landscape, never the team's actual assembly. |
| 05 · 00:25–00:30 · 5 s | “This is ACORN, built by team Scarabs.” | `ACORN` / `Aerial Canopy Observation and Reporting Node` / `Laptop demo · recorded footage` | MOCKUP: phone Station and laptop feed overview, stable prepared views, C1/C3. |
| 06 · 00:30–00:36 · 6 s | “The station runs smoke analysis locally. Here, the demo runs on a laptop.” | `Two active inputs · third mounted, inactive` / `Laptop demo · recorded footage` | MOCKUP: landscape laptop Station, genuine smoke/fog recorded feeds, C3. No board benchmark attached to laptop. |
| 07 · 00:36–00:43 · 7 s | “A nearby ranger can review a smoke suspicion on the local panel.” | `Smoke suspicion · needs human review` / `Laptop demo · recorded footage` | MOCKUP: portrait phone Station, actual new suspicion appears, C1. No OS notification. |
| 08 · 00:43–00:50 · 7 s | “That suspicion also reaches the remote desk. Today, LoRa transport is simulated.” | `LoRa transport simulated · no imagery` / `Laptop demo · recorded footage` / `Edited wait · not a latency measurement` | MOCKUP: same C1 event on phone and desktop Ground; packet arrives with Wi-Fi off. Joint time cut removes wait from both captures. |
| 09 · 00:50–00:55 · 5 s | “The ranger opens the saved evidence.” | `Full evidence · local panel` / `Laptop demo · recorded footage` | MOCKUP: phone Station, same suspicion's real saved clip plays, C2. |
| 10 · 00:55–01:03 · 8 s | “A person confirms or rejects the suspicion. That decision is an annotation, not confirmation of fire.” | `Confirm suspicion / Reject · human annotation` / `LoRa transport simulated · edited wait` / `Laptop demo · recorded footage` | MOCKUP: phone Doğrula, saved decision; Ground updates at its actual legal slot, C2. Initial packet already arrived in 08. |
| 11 · 01:03–01:09 · 6 s | “A smoke alert is forty-two bytes. Images stay off that link.” | `42-byte smoke alert · packet v2` / `LoRa transport simulated` / `Laptop demo · recorded footage` | MOCKUP: desktop Ground packet identity and calculated link details, C4. Size caption is from documented schema, not changing Last packet size. |
| 12 · 01:09–01:16 · 7 s | “Full evidence uses a separate, close-range Wi-Fi connection.” | `Wi-Fi evidence demo · separate from LoRa` / `LoRa transport simulated` / `Laptop demo · recorded footage` | MOCKUP: desktop Ground Wi-Fi demo on, labelled evidence, then off with imagery gone, C5. Edited sequence if load wait removed. |
| 13 · 01:16–01:21 · 5 s | “And where you put a station matters.” | `Illustration` | GENERATED: ridge blocks view across canopy. No synthetic coverage overlay. |
| 14 · 01:21–01:28 · 7 s | “Our map estimates visible forest using real Finnish terrain and forest data.” | `Simulated geometric visibility · not detection range` | MOCKUP: desktop Placement Compare, complete map and simulation-labelled results, C6. |
| 15 · 01:28–01:36 · 8 s | “Change the heading. Compare camera pairs. See what the terrain hides.” | `Planning estimate · edited sequence` / `Simulated geometric visibility` | MOCKUP: desktop Placement heading change/restoration and achievable pair selection, completed states only, C7. |
| 16 · 01:36–01:40 · 4 s | “Earlier notice is the aim.” | `Illustration` | GENERATED: unchanged opening forest. No implied prevented fire. |
| 17 · 01:40–01:44 · 4 s | “Board detection quality and real radio still need testing.” | `Unverified: board detection quality · real radio · AP · external RGB LED` / `LoRa transport simulated` / `Laptop demo · recorded footage · recap` | MOCKUP: paired phone/desk stable genuine C1 selects; limitations caption, no new event. |
| 18 · 01:44–01:48 · 4 s | “The short-range infrared sensor is separate from camera smoke.” | `Simulated sensor + logical LED` / `Does not confirm camera smoke` / `Laptop demo` | MOCKUP: phone Station local MCU section, simulated trigger/release C8. Not a physical LED response. |
| 19 · 01:48–01:51 · 3 s | “Next comes field testing.” | `Proposed work: supervised trial · radio · power · cost` / `Simulated geometric visibility` | MOCKUP: desktop Placement held real C6 map, no new result. |
| 20 · 01:51–01:54 · 3 s | “This is the prototype we built.” | `ACORN · Scarabs` / `Junction 2026 · Helsinki` / `Actual prototype · still photograph` | REAL: genuine assembly photo, slow 100→103% move, no invented LED response. Last image; no slogan outro. |

Packet-size conditions: current **v2 smoke alerts 42 bytes**, status 40, flame/decision 37 (`DEMO.md` C5). These are format sizes, not a measured radio transmission. Ground Packet details identifies an alert but does not display its byte size. Never change a captured 37/40 B last-packet metric to 42 B.

## Alternative social cut — exactly 30 seconds

Reuse master assets, 16:9, English subtitles, all source/illustration/simulation labels retained. No new vertical crop that loses provenance.

| Time / reused shot | Exact voice-over | Overlay and edit |
|---|---|---|
| 00:00–00:04 · 01 | “Who is watching before smoke is noticed?” | Illustration; forest, no fire. |
| 00:04–00:08 · 06 | “ACORN analyses smoke locally. This demo runs on a laptop.” | Laptop demo · recorded footage. |
| 00:08–00:13 · 08 | “A suspicion reaches the desk. LoRa transport is simulated.” | Paired real event, no imagery; Edited wait · not a latency measurement. |
| 00:13–00:18 · 10 | “A person reviews it and makes the call.” | Human annotation; LoRa transport simulated · edited wait; laptop/recorded label. |
| 00:18–00:23 · 14 | “The map estimates where to place it.” | Simulated visibility · not detection range. |
| 00:23–00:27 · 04 | “More affordable forest observation is our goal.” | Illustration · Station concept · not deployed / Cost not established. |
| 00:27–00:30 · 20 | “This is the prototype we built.” | Actual prototype · still photograph / ACORN · Scarabs. |

## Evidence and release notes

- Identity/ambition: root `README.md`, `placement/brand.json`; logo remains undecided despite supplied interface artwork.
- Hardware/runtime/limits: `DEMO.md` E, `docs/ARDUINO_UNO_Q.md`, `firmware/BOARD_NOTES.md`, `station/README.md`. Two live USB cameras, MCU/KY-026 and on-board LED have documented bring-up. These laptop captures and the photo establish no new validation. No flight, weatherproofing, endurance, solar, physical internet-disconnection test, tested AP, real radio or external RGB LED claim.
- Demo sequence/packet/Wi-Fi boundaries: `DEMO.md` C–D; capture and composition conditions: `MOCKUPS.md`. Initial suspicion transmission is independent of a human decision. Module heading 0° in demo is independent of Placement's candidate heading 180°.
- Placement interpretation: `placement/DESIGN.md` and actual interface; preserve simulation tags, map legend and data attribution. Log height/grid/heading/pair and other inputs with shown values. No fixed hectare promise.
- Quality: `station/DETECTION_VS_INPUT_SIZE.md`; throughput is not adequate small-smoke sensitivity. Optional statistics remain the marked placeholders in `DECK.md`; none is needed for this film.
- Carry `SHOTLIST.md` source credits with both exports and deck. Recorded wildfire/fog is third-party footage inside the app, never ACORN field camera footage.

Production fields: `[LOGO SLOT]`, `[CAPTURE DATE / ACTUAL TAKE CONDITIONS]`, `[LOCAL IR STIMULUS / OBSERVED DISTANCE]` (physical stimulus no longer required; mark not applicable for this simulated take). Record scratch reads before voice generation; fit pauses within these windows rather than accelerate UI events.
