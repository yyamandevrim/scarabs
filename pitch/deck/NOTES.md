# ACORN — speaker notes

Nine slides / three minutes. Product stills: English laptop demo, recorded footage. Board measurements are separately sourced.

## 1 · Earlier notice starts here · 00:00–00:20

“A forest fire may begin before anyone notices smoke. We built ACORN to explore that gap: a portable station that watches locally and raises a smoke suspicion for a person to review. We are team Scarabs, building at Junction in Helsinki.”

Evidence: root `README.md` for identity and purpose; the time-to-notice framing is an ambition, not a measured response-time claim.


## 2 · Who can keep watch? · 00:20–00:40

“A station that depends on sending camera video away also depends on that connection. We keep analysis local. Our goal is observation that more forest stewards could afford, including places without an internet uplink. We have not established a price or measured the field benefit.”

Evidence: `station/README.md` for local runtime and initial-download requirement. Affordability and audience here are proposed use, not validated demand. Real remote radio operation is not yet verified.


## 3 · A station that keeps analysis local · 00:40–01:00

“On the UNO Q, Linux captures two USB cameras, runs the smoke model on CPU, and stores evidence locally. The microcontroller reads a short-range infrared sensor and controls the on-board status LED. That sensor is separate from camera smoke; it does not confirm a fire.”

Evidence: `docs/ARDUINO_UNO_Q.md`, `firmware/BOARD_NOTES.md`. Use Pyronear attribution in notes; the model was not trained by the team.


## 4 · A person makes the call · 01:00–01:20

“Consistent smoke observations create a suspicion with a snapshot and clip. An operator confirms or rejects that record, and can correct the decision. The demonstration uses real recorded smoke and fog footage on a laptop. A confirmed record is a human annotation, never automatic confirmation of fire.”

Evidence: `DEMO.md` C1–3; `station/README.md` Detection and event behaviour. Decision does not gate the initial outgoing suspicion packet.


## 5 · Send the suspicion, keep the imagery · 01:20–01:40

“The remote dashboard starts with packet data only. A current smoke alert is forty-two bytes; LoRa transport is simulated over UDP today. Images never travel on that path. Evidence uses a separate close-range Wi-Fi connection. Approximate direction comes from configured geometry, not a measured fire location.”

Evidence: `DEMO.md` C4–6, `station/README.md` Communication. Status is 40 bytes, flame/decision 37; do not substitute them for the smoke alert. Ground's optional Wi-Fi view can show imagery only when explicitly enabled; it is not the default remote packet view.


## 6 · Put the station where it can see · 01:40–02:00

“A working detector is only useful where its cameras can see. Our separate map tool estimates visible forest over real Finnish terrain and canopy data. Change the launch point, heading or connected pair. These are geometric estimates; they do not measure smoke-detection range or prove an airborne deployment.”

Evidence: root `README.md`, `placement/DESIGN.md`; actual controls and provenance from Placement's static interface. Planner heading is independent of the Ground demo's configured module heading; do not treat them as shared telemetry.


## 7 · Measured, simulated, still open · 02:00–02:20

“The board did respond live to dense daytime smoke filling a camera view: three screen-clip loops with the centre crop, peak scores from 0.62 to 0.76. Those are model scores, not accuracy. It does not respond to arbitrary news footage: the tested Guardian aerial clip failed. LoRa and coverage remain simulated. One real module is present, but its variant is unidentified and it has not carried an ACORN link. Field sensitivity and power endurance are still open.”

Evidence: `DEMO.md` live camera screen demonstration, `firmware/BOARD_NOTES.md` live screen-smoke fix, `station/DETECTION_VS_INPUT_SIZE.md` live-screen investigation and `station/LORA_HARDWARE.md`. Center camera filming the project smoke clip; opening scores 0.36/0.44/0.40 and peak scores 0.74/0.76/0.62 in three loops. The 240×240 centre crop discards the outer 40-pixel strips of a 320×240 input. Dense daytime smoke is the demonstrated input; no field accuracy, arbitrary-video reliability, night sensitivity or detection range follows. The new English laptop captures are separate evidence from that board run; English UI on the board still needs verification.


## 8 · Next proof: a forest trial · 02:20–02:40

“The next proof belongs in a supervised forest trial: real small-smoke evaluation on the board, real radio, and sustained power and thermal measurements. We also need a complete station cost. We are looking for a suitable test setting before claiming reliable coverage or a deployable service.”

Evidence: remaining-work limits in `docs/ARDUINO_UNO_Q.md`, `station/DETECTION_VS_INPUT_SIZE.md`, `station/README.md`. This is the team's proposed next step, not a scheduled or approved trial. No customer, budget, permission or agreement is implied.


## 9 · Built for these challenges · 02:40–03:00

“We enter Green European Renaissance, Best use of Arduino UNO Q, and Best Use of Codex. Codex agents wrote nearly all code and tests with bounded ownership; humans directed the work, and Claude also orchestrated, reviewed and contributed some implementation. The repository records that distinction. Now, the demo.”

Evidence: `placement/brand.json`, root `README.md`, `docs/ARDUINO_UNO_Q.md`, `docs/PROCESS.md`; entered side-challenge names also supplied in the brief. Do not credit every line, the independent detection study or all orchestration to Codex. Commits show work, not proof of model authorship; process sessions are available on request as recorded in PROCESS.

## Credits and visual provenance

Forest images: generated concept-illustration-station-medium-v2.png, hardware-free crops; context only. Film shots 04/13 use concept-illustration-station-ridge.png and concept-illustration-occluding-ridge.png. DECK.md assigns neither picture to a slide; slide visuals remain as specified. No hardware photograph is supplied.
Product stills: 2026-11-14 English running-app recordings, fresh origin/main; own generic device frames. Phone arrival may also appear in the film as a separately credited Screeny export. See ../captures/README.md for capture provenance and chronology.
Smoke footage inside the interface: “Wildfire Near Monserrate”, Peter Angritt / Mrtony77 (2015), CC BY-SA 4.0, https://commons.wikimedia.org/wiki/File:Wildfire_Near_Monserrate.ogv. Fog: “Fog covering mountain time lapse”, Athulvis, CC BY-SA 4.0 (Commons external licence review pending), https://commons.wikimedia.org/wiki/File:Fog_covering_mountain_time_lapse.webm. Annotated/edited screenshots retain these credits; https://creativecommons.org/licenses/by-sa/4.0/.
Map: NLS Finland / Syke / Luke, CC BY 4.0. Model: Pyronear YOLO11s ONNX, AGPL-3.0; not trained by the team. Type: IBM Plex Sans, SIL OFL (OFL-IBM-Plex-Sans.txt).
