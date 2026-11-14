# ACORN — live pitch deck script

**Nine slides / three minutes, followed by the live demo.** Allow 20 seconds per slide, including its transition. Speaker notes are an exact suggested read; rehearse to the time windows. Do not play the 114-second film inside these three minutes. Use it separately if the judging format permits.

Use the visual system in `VIDEO_SCRIPT.md`: dark mineral canvas, IBM Plex, restrained blue interaction accent, amber only for suspicion, map first. One main visual and one statement per slide; retain every app capture's provenance label. Slides 4–6 use the exact generic device frames from `MOCKUPS.md`, exported from the film compositions, with the same matte stage, silver diffuse light, screen aspect ratios and IBM Plex captions. No raw screenshots pasted on slides. All editorial copy is English; translate Station controls in an adjacent caption without altering the captured interface. Name treatment is plain **ACORN**; `[LOGO SLOT — undecided; leave empty]` on the layout master. No invented logo, sponsor logo or mock interface.

Evidence references below are production notes, not extra on-slide prose. Shot IDs refer to `SHOTLIST.md`. Place generated-image **Illustration** captions on the slide itself. Cover only existing header logo artwork with plain ACORN text, following its position, without hiding source/status labels. No app edits or proprietary device artwork. Phone frame is a responsive laptop-browser capture, not proof of physical iPhone deployment or tested AP mode. Source credits from `SHOTLIST.md` accompany any distributed deck.

## 1 · Earlier notice starts here · 00:00–00:20

**One thing:** The aim is to shorten the wait before someone notices smoke.

**Exact on-slide text:**

> ACORN
>
> Earlier notice starts here
>
> Aerial Canopy Observation and Reporting Node
>
> Scarabs · Junction 2026, Helsinki
>
> Illustration

**Visual:** G01 forest still, full-width and quiet; name in open sky/negative space. No plume, countdown, danger map or prevented-fire image.

**Speaker notes:** “A forest fire may begin before anyone notices smoke. We built ACORN to explore that gap: a portable station that watches locally and raises a smoke suspicion for a person to review. We are team Scarabs, building at Junction in Helsinki.”

**Evidence:** root `README.md` for identity and purpose; the time-to-notice framing is an ambition, not a measured response-time claim.

## 2 · Who can keep watch? · 00:20–00:40

**One thing:** Affordability and local operation could broaden who can maintain observation.

**Exact on-slide text:**

> Who can keep watch?
>
> Goal: affordable observation without an internet uplink
>
> Cost and field benefit not established
>
> Illustration

**Visual:** G03 empty ridge still. No price tag, customer count, connectivity heat map or fictional comparison with a competing system. Optional sourced cost figure belongs only in the placeholder list until supported.

**Speaker notes:** “A station that depends on sending camera video away also depends on that connection. We keep analysis local. Our goal is observation that more forest stewards could afford, including places without an internet uplink. We have not established a price or measured the field benefit.”

**Evidence:** `station/README.md` for local runtime and initial-download requirement. Affordability and audience here are proposed use, not validated demand. Real remote radio operation is not yet verified.

## 3 · A station that keeps analysis local · 00:40–01:00

**One thing:** The physical prototype uses both sides of the UNO Q for distinct jobs.

**Exact on-slide text:**

> A station that keeps analysis local
>
> Two USB cameras → UNO Q Linux → smoke suspicion
>
> MCU: local IR sensor + on-board status LED
>
> Actual hardware

**Visual:** Genuine shot 20 assembly photograph, large, caption Actual prototype · still photograph. Reuse a crop from the same original, keeping board, both cameras, sensor and on-board LED identifiable; no extra filming. Add two simple, static callout lines to the actual board: Linux analysis and MCU local sensing. Diagram describes the documented design; it is not a traced signal measurement. No external RGB LED, radio module or flight enclosure added.

**Speaker notes:** “On the UNO Q, Linux captures two USB cameras, runs the smoke model on CPU, and stores evidence locally. The microcontroller reads a short-range infrared sensor and controls the on-board status LED. That sensor is separate from camera smoke; it does not confirm a fire.”

**Evidence:** `docs/ARDUINO_UNO_Q.md`, `firmware/BOARD_NOTES.md`. Use Pyronear attribution in notes; the model was not trained by the team.

## 4 · A person makes the call · 01:00–01:20

**One thing:** The product's output is a reviewable suspicion.

**Exact on-slide text:**

> A person makes the call
>
> Smoke suspicion → evidence → operator decision
>
> Laptop demo · recorded footage
>
> Confirm suspicion / Reject

**Visual:** Portrait iPhone-style Station mockup from shot 09/C2, showing the complete genuine saved clip frame and its source; an adjacent second state from shot 10 may show actual decision controls if the phone needs a panel scroll. Both are clearly labelled separate states of the same event, not one invented screen. Small English translations beside Doğrula / Reddet outside the phone. Use the film's front-on phone, matte background and soft silver light. Amber belongs to suspicion; no fire-detected banner or accuracy badge.

**Speaker notes:** “Consistent smoke observations create a suspicion with a snapshot and clip. An operator confirms or rejects that record, and can correct the decision. The demonstration uses real recorded smoke and fog footage on a laptop. A confirmed record is a human annotation, never automatic confirmation of fire.”

**Evidence:** `DEMO.md` C1–3; `station/README.md` Detection and event behaviour. Decision does not gate the initial outgoing suspicion packet.

## 5 · Send the suspicion, keep the imagery · 01:20–01:40

**One thing:** Remote packets and local imagery are separate paths.

**Exact on-slide text:**

> Send the suspicion, keep the imagery
>
> 42-byte smoke alert · packet v2
>
> LoRa transport simulated today
>
> No imagery over LoRa
>
> Evidence: separate close-range Wi-Fi
>
> Laptop demo · recorded footage

**Visual:** Shot 08/C1 paired mockup: portrait Station phone with a suspicion at left, landscape Mac-style desktop Ground with its matching received packet, Wi-Fi demo off, at right. This is the core film moment frozen after real receipt; retain laptop/recorded-footage and simulated-transport captions outside devices. Tiny static path labels: Station → packet → Ground (LoRa transport simulated); Station → local Wi-Fi → evidence. Same source event UUID in both underlying captures, not a collage of unrelated alerts. No image thumbnail on the LoRa path, radio waves or measured fire location. The 42-byte caption is a v2 schema fact from DEMO C5; Packet details shows identity, not byte size, and Last packet size may refer to a later heartbeat/decision.

**Speaker notes:** “The remote dashboard starts with packet data only. A current smoke alert is forty-two bytes; LoRa transport is simulated over UDP today. Images never travel on that path. Evidence uses a separate close-range Wi-Fi connection. Approximate direction comes from configured geometry, not a measured fire location.”

**Evidence:** `DEMO.md` C4–6, `station/README.md` Communication. Status is 40 bytes, flame/decision 37; do not substitute them for the smoke alert. Ground's optional Wi-Fi view can show imagery only when explicitly enabled; it is not the default remote packet view.

## 6 · Put the station where it can see · 01:40–02:00

**One thing:** Placement makes terrain and canopy obstruction visible before deployment.

**Exact on-slide text:**

> Put the station where it can see
>
> Real Finnish terrain and forest data
>
> Compare sites · headings · camera pairs
>
> Simulated geometric visibility, not detection range

**Visual:** Landscape Mac-style desktop mockup exported from shot 14/C6; device fills most of the slide, with map dominating the screen and the actual Compare panel alongside it. Preserve mint visible forest, grey outside field of view, rust occlusion and the legend. Retain simulation labels beside hectare figures. Use one captured setup, not a new collage of incompatible results. Do not pre-write any hectare number. Keep an adjacent readable modelling-conditions line: captured 600 m height, quick 120 m grid, smoke + canopy, Haukilahti heading 180°, left+centre; log max-range and smoke-target height too (verify actual take). These are simulation inputs, not validated flight height/detection range. Use the same screen/frame/light as the film, no unframed screenshot or synthetic visibility overlay.

**Speaker notes:** “A working detector is only useful where its cameras can see. Our separate map tool estimates visible forest over real Finnish terrain and canopy data. Change the launch point, heading or connected pair. These are geometric estimates; they do not measure smoke-detection range or prove an airborne deployment.”

**Evidence:** root `README.md`, `placement/DESIGN.md`; actual controls and provenance from Placement's static interface. Planner heading is independent of the Ground demo's configured module heading; do not treat them as shared telemetry.

## 7 · Measured, simulated, still open · 02:00–02:20

**One thing:** The prototype has hardware evidence with clear limits.

**Exact on-slide text:**

> Measured, simulated, still open
>
> Measured: 0.990 analyses/s per camera on UNO Q
>
> Simulated: LoRa transport; geometric coverage
>
> Unverified: board detection quality; real radio; AP; external RGB LED
>
> Speed only · input 192 · confidence 0.35 · two live 320×240 YUYV cameras
>
> CPU · 2 ORT threads · UVC quirk 128 · 30 s warm-up + 180.7 s sample

**Visual:** Crop of the actual shot 20 photograph, caption Still photograph, plus three calm text rows, no success score or chart equating speed with accuracy. The conditions are a readable footer, not hidden speaker-only qualification. If projection makes them unreadable, enlarge the footer and reduce the photo.

**Speaker notes:** “The board sustained nearly one analysis per second per camera in the documented short speed test under the settings shown. That is throughput, not detection quality. LoRa transport and map coverage are simulations. Real radio, access-point mode, the external LED and board detection quality remain unverified.”

**Evidence:** `docs/ARDUINO_UNO_Q.md`, `firmware/BOARD_NOTES.md`. Use the 192 run only with the conditions printed here. The broader quality study used an Apple M5 Mac, one real smoke clip, three negatives and a synthetic distant-smoke proxy. Never call it a field accuracy test.

## 8 · Next proof: a forest trial · 02:20–02:40

**One thing:** The next work must establish field usefulness, rather than add claims.

**Exact on-slide text:**

> Next proof: a forest trial
>
> Validate board sensitivity
>
> Verify real radio + power endurance
>
> Cost the complete station
>
> Seeking a supervised test setting

**Visual:** REAL shot 20 photograph, caption Actual prototype · still photograph, using the same crop, cool neutral treatment and name typography as the closing film frame. Three short labels next to the actual assembly, no rendered deployment, invented customer logo or rollout map. These labels are proposed work.

**Speaker notes:** “The next proof belongs in a supervised forest trial: real small-smoke evaluation on the board, real radio, and sustained power and thermal measurements. We also need a complete station cost. We are looking for a suitable test setting before claiming reliable coverage or a deployable service.”

**Evidence:** remaining-work limits in `docs/ARDUINO_UNO_Q.md`, `station/DETECTION_VS_INPUT_SIZE.md`, `station/README.md`. This is the team's proposed next step, not a scheduled or approved trial. No customer, budget, permission or agreement is implied.

## 9 · Built for these challenges · 02:40–03:00

**One thing:** Each entered challenge has a concrete, inspectable contribution.

**Exact on-slide text:**

> Built for these challenges
>
> Green European Renaissance — forest observation
>
> Best use of Arduino UNO Q — Linux + MCU working together
>
> Best Use of Codex — implementation, tests and board bring-up
>
> Scarabs · Junction 2026, Helsinki
>
> Next: live demo

**Visual:** Reuse the same genuine shot 20 assembly photograph with plain challenge names. No separate team photo is required; no invented sponsor marks. Keep actual device and Still photograph caption visible. Small evidence pointers in distributed notes: `docs/ARDUINO_UNO_Q.md` and `docs/PROCESS.md`.

**Speaker notes:** “We enter Green European Renaissance, Best use of Arduino UNO Q, and Best Use of Codex. Codex agents wrote nearly all code and tests with bounded ownership; humans directed the work, and Claude also orchestrated, reviewed and contributed some implementation. The repository records that distinction. Now, the demo.”

**Evidence:** `placement/brand.json`, root `README.md`, `docs/ARDUINO_UNO_Q.md`, `docs/PROCESS.md`; entered side-challenge names also supplied in the brief. Do not credit every line, the independent detection study or all orchestration to Codex. Commits show work, not proof of model authorship; process sessions are available on request as recorded in PROCESS.

## Handoff into the live demo

Open Station already authenticated and Ground already running, with downloads/preparation complete. Follow `DEMO.md` C in order: recorded feeds → suspicion clip → a decision → packet-only Ground → calculated link details → explicitly separate Wi-Fi demo → Placement → Haukilahti heading change and camera-pair comparison. Say which host each screen runs on. Allow actual calculation/contact waits; use prepared genuine screenshots if needed and label them as earlier captures. Do not reset duty accounting or claim immediate delivery. Keep all terminals and private access details off the projector.

## Judge questions — short, honest answers

| Likely question | Answer |
|---|---|
| Does it actually work on the UNO Q? | Two live USB cameras, CPU inference, the MCU bridge, KY-026 response and on-board LED have run on the board. The stage runbook is a separate recorded-footage laptop demo. Board speed measurements do not validate smoke-detection quality. |
| How fast is it? | At input 192, confidence 0.35, two live 320×240 YUYV cameras, CPU/two ORT threads and UVC quirk 128, mean total analysis was 282.21/282.55 ms left/centre, excluding capture/decode; both sustained 0.990 analyses/s after 30 s warm-up over 180.7 s. Those are speed observations, not alert latency. |
| Why use 640 input if 192 is fast? | In the Mac study, the fast setting missed smoke shrunk two to four times in a synthetic proxy. Input 640 retained detections across those scales. That proxy is not real distant smoke. We need board quality evaluation, not a speed-only choice. |
| Can the board sustain the larger input? | With two live 320×240 YUYV cameras, confidence 0.35, CPU/two ORT threads and UVC quirk 128, input 640 sustained 0.167 analyses/s per camera after 30 s warm-up over about 300 s. Mean total analysis was 2740.66/2763.43 ms, excluding capture/decode. Exact field profile at confidence 0.25 and final camera settings remains unmeasured. |
| What are accuracy, range and false-alarm rate? | Not established. The broader quality study used one near-smoke clip, three negative clips and a synthetic distant-smoke proxy on an Apple M5 Mac. No field sensitivity, calibrated optical detection range or general false-alarm rate follows from that. |
| Is this your model? | No. It is the pinned Pyronear YOLO11s ONNX smoke detector, not retrained by us. We built capture, event handling, evidence, review, interfaces and communication around it. Its documented licence is AGPL-3.0. |
| Does confirm mean a fire is confirmed? | It is the operator's annotation on a smoke-suspicion record. The system does not establish a confirmed fire or dispatch emergency services. A suspicion can be sent before an operator decides. |
| Does LoRa work, and how far? | The packet format, scheduling and Ground dashboard work with simulated UDP transport. No real LoRa hardware or range is verified. Current v2 smoke alerts are 42 bytes; 40 bytes describes status. |
| How long until Ground receives an alert? | In the runbook's simulated SF7/BW125/CR4/5, strict 1% setting, calculated slots are 12 seconds; an alert may wait up to about 12 seconds without backlog, plus event creation. At SF12 the calculated slot is 241 seconds. These are simulation/calculation conditions, not measured radio delivery, and overload can queue alerts. |
| Why can I see video on Ground? | Only the explicitly enabled Wi-Fi demo fetches imagery separately. With it off, the remote packet view shows no imagery. It does not travel over LoRa. Saved evidence is collected over Wi-Fi for a particular received alert. |
| Does it work without internet? | Runtime uses local models, assets and storage after initial preparation; denied-socket integration tests and local-only browser audits support that. No physical internet-switch-off test was performed. Remote real-radio operation and UNO Q AP mode are still unverified. |
| Is the sensor looking for flames across the forest? | No. KY-026 is a short-range local IR sensor. Its response is separate from camera smoke. The original trigger's source and distance were undocumented; we must record any new capture conditions without calling them calibrated range. |
| Why only two cameras? | The station supports at most two active inputs; its configuration has three mounted slots and lets us choose a pair. Three-camera mode in Placement is a comparison reference, not a supported three-input runtime. |
| Does the coverage map prove detection at that distance or height? | No. It estimates line of sight over real terrain/canopy with configured geometry and assumptions. It is not optical detection range, a tested flight height or a deployed station result. Field access, site use and permissions need checks. |
| Has it flown? What about weather and power? | No airborne field validation is established by these records. Battery life, weather resistance, long hot operation and supply headroom are not established; no solar implementation is claimed. |
| Does it recover after losing power? | An orderly owner-run power-off and reconnection recovered station, cameras and MCU telemetry automatically. That does not verify unexpected-power-loss data recovery. The later direct Wi-Fi bind was not power-cycle tested. |
| How much does it cost? Who will buy it? | We do not have a sourced complete-station cost or validated customer demand in this repository. Affordability is a goal. Complete the bill of materials and speak to prospective users before giving a price or market claim. |
| What did Codex contribute? | Nearly all code/tests, including station, placement, communication, interfaces and board bring-up, under bounded briefs and human direction. Claude handled much orchestration/review, some interim implementation and the independent quality study. PROCESS names those limits; combined review acceptance is still pending. |
| Why these side challenges? | UNO Q gives a concrete Linux/MCU split with observed hardware response. Codex has an inspectable implementation and iteration trail. The main challenge motivation is forest observation; environmental impact is an aim, not a quantified result. |

## Placeholders — production handoff, never export bracketed text

- `[LOGO SLOT]`: identity is undecided. Leave blank and use ACORN text; no logo is required to pitch.
- `[CAPTURE DATE / ACTUAL TAKE CONDITIONS]`: fill from the hardware photograph and running-app browser takes; record host, source, setup, viewport/DPR, paired UUID/timing, and Placement's actual height/grid/heading/pair/max-range/smoke-target height if figures appear.
- `[LOCAL IR STIMULUS / OBSERVED DISTANCE]`: not applicable for this plan's simulated local-sensor capture; no new physical stimulus/response is filmed. Preserve the placeholder for a future genuine test and never infer a range from the simulation.
- `[OPTIONAL SOURCED CONTEXT FIGURE]`: if adding scale to slide 1, obtain a relevant wildfire/detection-delay figure with geography, period, definition and an authoritative cited source. Otherwise keep the qualitative opening.
- `[OPTIONAL COMPLETE-STATION COST]`: a dated bill of materials, including board, cameras, power, enclosure, mounting and real communication hardware; currency and exclusions explicit. Required before adding a cost or price advantage to slide 2.
- `[OPTIONAL CUSTOMER / MARKET EVIDENCE]`: named user interviews or a sourced, defined market figure with geography/date before adding any demand claim. No market-size graphic in this version.
- `[PENDING VALIDATION]`: future dated board detection-quality results, exact field-profile performance, real radio, AP, external LED and power/endurance work. Until evidence exists, retain unverified labels; these are open work, not numbers to fill from guesses.

The film needs one REAL photograph shot and no live-action filming; slides 3/7/8/9 reuse it. It proves the prototype exists; documented board operation comes from the cited repository records, not animation of that photo. App layout verdicts and the phone fallback are in `MOCKUPS.md`; no planned phone page requires a responsive fix by source inspection, subject to capture preflight.

No new external statistics were researched or used. All factual claims and figures above come from the requested repository sources; proposed audience, trial and affordability goals are explicitly proposals.
