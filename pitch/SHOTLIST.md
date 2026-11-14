# ACORN — shot and sound package

**Current production:** English takes and the built deck supersede the earlier text-only capture plan below. See [capture index](captures/README.md), [film assembly](edit/README.md) and [deck](deck/README.md). Remaining picture gaps: 04, 13, 20.
Master: **20 shots / 114 seconds**. Sources: **13 MOCKUP / 6 GENERATED / 1 REAL**. Before: **6 REAL / 8 SCREEN / 6 GENERATED**. MOCKUP is a real running-app capture inside a generic device frame, never a recreated interface. No raw SCREEN shots remain. The social cut reuses 01, 06, 08, 10, 14, 04 and 20. This file gives later production instructions only; no media has been made.

## One visual family

All six generated scenes share overcast early dawn, fictional Finnish-looking spruce/birch forest, low granite ridges, cool mineral blue-grey shadows and muted greens. Diffuse silver sky, natural contrast, subtle fine 35 mm film grain and restrained 35 mm lens character. Deep enough focus to read the land; slow plausible camera motion, no dramatic swoops. 16:9. Reuse G01's approved style reference. It is fictional geography, never a measured site or Finnish data output.

Device shots use the same cool diffuse light on a matte dark stage (`#090e13`, tabletop `#0f161d`), neutral dark bezels and soft contact shadows. Do not put forest grain or a colour grade over the app. Generic Mac-style laptop/desktop and iPhone-style phone, no proprietary artwork or Apple logo. All device geometry, action, raw-take length, viewport and DPR are specified in **`MOCKUPS.md`**, the capture source of truth. Recommend a later coded composition with self-drawn CSS/SVG frames; no composition code is part of this task.

Add **Illustration** to every generated frame in the edit, and **Station concept · not deployed** to G04. No generated pixels in feed tiles, saved evidence, coverage map or result inset. Hard-cut from context into evidence. Name remains plain ACORN; cover only existing header logo artwork without obscuring status/provenance. No glow, radio waves or synthetic detection cue.

## Capture preparation and minimum hardware evidence

Follow `DEMO.md` A–B privately, Ground before Station, sustainable demo config and preserved duty ledger. Actual app output only. Record C1–C8 in `MOCKUPS.md` order, with all three interfaces in English. Wide screens 1440×810 CSS px/DPR2; phone 393×852/DPR3. Record native viewport, no terminal/credentials/browser bars. Check native output dimensions and phone expanded-card readability first. No main page needs a responsive fix at the chosen width by source inspection; dense wide workflows stay wide. A failed phone preflight switches to a genuine wide Station capture, never a compressed desktop phone mockup.

Station inputs are real recorded smoke/fog on the laptop; MCU and LoRa transport are simulated. Preserve source/host, simulated transport, Wi-Fi-only and map simulation labels, repeating important ones outside devices for legibility. Do not accelerate events or link waits into latency claims. C1/C2 paired scenes retain matching UUIDs and clock alignment; any removed wait cuts both tracks at once and carries Edited wait. Never inject an event. C4's 42-byte smoke size is a documented v2 schema caption, not Ground's changing last-packet metric.

**REAL minimum: shot 20 only, 3 seconds, one required genuine still photograph, zero filmed takes.** Photograph the actual powered board, hub/wiring, both connected USB cameras, KY-026 and on-board LED together at the venue. Landscape original ≥3840×2160, sharp, diffuse light, no flash/private screen. Keep original and log actual date/setup. Slow 100→103% crop move; no generative repair, added hardware, parallax or animated LED. It proves assembly, not operation or sensor response. Optional second detail still only if the required components are unreadable; no extra film shot. Reuse photo/crops on deck 3/7/8/9; no separate venue/team photo needed. Zero REAL shots would leave hardware judges without direct physical-prototype evidence.

## Shot rows

All MOCKUP rows inherit the stage/light above; `MOCKUPS.md` specifies each camera treatment and exact running-app recipe. Durations are used durations, not raw take lengths.

| No. | Used duration | Source | Exact instructions |
|---|---:|---|---|
| 01 | 7 s | GENERATED | G01 forest. Illustration. Deck 1 still. |
| 02 | 6 s | GENERATED | G02 canopy. Illustration. |
| 03 | 6 s | GENERATED | G03 empty ridge. Illustration. Deck 2 still; no connectivity proof. |
| 04 | 6 s | GENERATED | G04 generic inert concept. Illustration · Station concept · not deployed. No ACORN replica or actual deployment. |
| 05 | 5 s | MOCKUP | Portrait phone Station + landscape laptop feed overview, C1/C3 prepared states; static two-device introduction. Laptop demo · recorded footage. |
| 06 | 6 s | MOCKUP | Landscape laptop Station C3; two recorded feeds + inactive right slot, host/source intact, slow push-in. No laptop numbers attributed to board. |
| 07 | 7 s | MOCKUP | Portrait phone Station C1; actual new suspicion appears, pointer/focus outside queue. Static; human review + laptop recorded-demo labels. |
| 08 | 7 s | MOCKUP | Core moment: portrait phone suspicion + landscape desktop Ground C1 matching alert arrives, Wi-Fi off. Static paired frame; LoRa transport simulated · no imagery / Edited wait · not a latency measurement. |
| 09 | 5 s | MOCKUP | Portrait phone Station C2; same event's saved clip plays, honest panel scroll if needed. Local evidence, recorded-demo and source labels. Save pre-decision still for deck 4. |
| 10 | 8 s | MOCKUP | Paired phone/desktop C2: Doğrula persisted, Ground decision later at real legal slot. Human annotation / LoRa transport simulated / Edited wait. Initial suspicion already sent in 08. |
| 11 | 6 s | MOCKUP | Desktop Ground C4; Packet details identity and calculated Link details. 42-byte smoke alert · v2 is editorial schema fact; do not overwrite last-packet size. LoRa transport simulated. |
| 12 | 7 s | MOCKUP | Desktop Ground C5; saved evidence separately collected over Wi-Fi, demo on with bounded Wi-Fi-only label, then off and no imagery. Keep LoRa simulation label. Honest error/packet-only fallback if unavailable. |
| 13 | 5 s | GENERATED | G13 intervening ridge. Illustration; no synthetic coverage cells. |
| 14 | 7 s | MOCKUP | Desktop Placement C6 Compare; loaded Haukilahti/Nuuksio smoke + canopy, 600 m/quick 120 m/left+centre/180° Haukilahti, actual logged inputs. Map, legend, figures and simulation tags. Slow push-in. Deck 6 still. |
| 15 | 8 s | MOCKUP | Desktop Placement C7 heading 180°→0°→restored and achievable two-camera pair change/restoration. Completed results only; Planning estimate · edited sequence. Never three-camera reference as working hardware. |
| 16 | 4 s | GENERATED | G16 unchanged forest reprise. Illustration; no outcome implied. |
| 17 | 4 s | MOCKUP | Static C1 phone/desktop recap with limitations above devices: field smoke sensitivity and real radio still open; board screen-smoke response measured. LoRa simulated + laptop recorded-demo labels. No new event. |
| 18 | 4 s | MOCKUP | Portrait phone Station C8 local sensor section; authenticated runbook simulation of trigger/release, logical LED only. Simulated sensor + logical LED / Does not confirm camera smoke. No physical-response claim. |
| 19 | 3 s | MOCKUP | Desktop Placement C6 static real map; proposed field/radio/power/cost work outside device, no fresh result. Simulation caption retained. |
| 20 | 3 s | REAL | Genuine prototype still, slow crop move, Actual prototype · still photograph. Board/cameras/sensor/on-board LED visible. ACORN · Scarabs / Junction 2026 · Helsinki. End on actual assembly, no logo/slogan card. |

## Higgsfield prompts — paste each still prompt, then animate that result

### G01 — forest, 7 seconds

**Still prompt:** “Cinematic naturalistic landscape photograph, fictional Finnish-looking spruce and birch forest stretching across low granite ridges, broad unbroken canopy, no smoke or fire, distant horizon in the upper third, overcast early dawn, diffuse silver sky, mineral blue-grey shadows and subdued natural greens, realistic 35 mm full-frame lens, fine subtle 35 mm film grain, deep focus, restrained documentary mood, composition with quiet space at lower left for an editorial caption added later, aspect ratio 16:9, no text.”

**Animation prompt:** “Animate this fictional forest image for 7 seconds, 16:9. Very slow level forward dolly above the ridge, 35 mm lens perspective, stable horizon, only slight natural treetop movement. Preserve early-dawn diffuse light, cool mineral palette and subtle grain. Patient observational mood. No new subject, smoke, fire or overlays; no dramatic reveal.”

**Negative list:** smoke, flames, embers, scorched land, rescue crews, ACORN, camera output, detection box, map, HUD, words, watermark, orange glow, neon, oversaturated green, rapid drone motion, warped trees, time-lapse.

### G02 — canopy, 6 seconds

**Still prompt:** “Naturalistic cinematic view just above a fictional Finnish-looking spruce and birch canopy, layered tree crowns across gentle terrain, no smoke, overcast early dawn with soft silver light, muted natural greens and mineral blue-grey shadows, 35 mm full-frame lens at a shallow downward angle, fine subtle 35 mm film grain, realistic scale and deep focus, quiet documentary mood, 16:9 landscape, no lettering or technology.”

**Animation prompt:** “6 seconds, 16:9, slow level lateral camera slide just above the canopy, steady 35 mm lens perspective, gentle parallax only. Slight breeze in treetops, consistent diffuse early-dawn light, cool mineral colours and fine grain. Calm sustained watching; no new objects, overlays, smoke or changing weather.”

**Negative list:** smoke, fire, fog that resembles a plume, flames, alarm lights, detection UI, aerial targeting, thermal image, text, watermark, whip pan, fast fly-through, bending trunks, unreal vegetation, sunset orange.

### G03 — ridge without infrastructure, 6 seconds

**Still prompt:** “Wide naturalistic cinematic photograph of an empty low granite ridge overlooking a fictional Finnish-looking spruce and birch forest, no buildings or infrastructure in frame, overcast early dawn, diffuse silver sky, cool mineral blue-grey stone and subdued green canopy, 35 mm full-frame lens, realistic terrain, deep focus, fine subtle 35 mm film grain, quiet remote mood, ridge foreground left and broad landscape right, 16:9, no text.”

**Animation prompt:** “6 seconds, 16:9. Slow 35 mm lens push toward the empty granite ridge, very small camera travel, horizon stable. Preserve soft early-dawn light and cool mineral grade with fine grain. Gentle treetop breeze only. No station materialises; no smoke or communications graphics.”

**Negative list:** cell-signal symbols, coverage map, data streams, aircraft, station, smoke, fire, city, power lines, text, watermark, extreme mountains, science-fiction landscape, orange sunlight, fast zoom, terrain morphing.

### G04 — illustrative station concept, 6 seconds

**Still prompt:** “Concept illustration rendered as a naturalistic cinematic photograph: a generic small unbranded weatherproof observation enclosure on a simple short tripod on a low granite ridge, two passive camera-like apertures, no resemblance to a specific product and no visible electronics or status lights, fictional Finnish-looking spruce and birch forest beyond, no smoke or fire, overcast early dawn, diffuse silver sky, cool mineral blue-grey shadows and muted greens, 35 mm full-frame lens, fine subtle 35 mm grain, quiet contemplative mood, 16:9. This is an illustrative undeployed concept, not a product photograph; render no text.”

**Animation prompt:** “6 seconds, 16:9, slow 35 mm lens lateral slide past the generic stationary enclosure on the ridge, slight landscape parallax, diffuse early-dawn light and cool mineral grade unchanged, fine film grain, calm concept-film mood. Enclosure remains inert; no lights, detection, transmission, scanning, moving lenses, screen or result. Do not add smoke or fire.”

**Negative list:** ACORN branding, Arduino branding, actual circuit board, logo, LEDs, blinking, screen, radio waves, smoke, flame, detection box, UI, evidence footage, drone or balloon deployment, text, watermark, futuristic casing, implausible wiring, glossy advertisement lighting.

### G13 — land blocks a view, 5 seconds

**Still prompt:** “Naturalistic cinematic landscape photograph across overlapping low granite ridges and dense spruce and birch canopy in a fictional Finnish-looking landscape, nearer ridge visibly obscuring the land behind it, no smoke or fire, overcast early dawn, silver diffuse sky, mineral blue-grey shadows and subdued greens, 35 mm full-frame lens, deep focus, realistic scale, fine subtle 35 mm film grain, restrained observational mood, 16:9, no diagram, no text.”

**Animation prompt:** “5 seconds, 16:9, slow level sideways dolly with 35 mm lens perspective so the nearer ridge gently shifts against the far canopy. Keep all terrain fixed, horizon stable, diffuse early-dawn lighting and fine grain consistent. Quiet geographic context only; no see-through land, visibility mask, scanning effect or data.”

**Negative list:** coverage cells, map labels, radar, x-ray terrain, transparent canopy, smoke, fire, model boxes, telemetry, arrows, measured range, text, watermark, alpine peaks, orange sunset, dramatic orbit, changing landforms.

### G16 — forest reprise, 4 seconds

**Still prompt:** “Return to the same fictional Finnish-looking spruce and birch forest and low granite ridge composition as the approved opening reference, unchanged conditions, no smoke or fire, overcast early dawn and diffuse silver sky, mineral blue-grey shadows, muted natural greens, 35 mm full-frame lens, deep focus, subtle fine 35 mm grain, quiet patient mood, 16:9, no people, technology, text or result.”

**Animation prompt:** “4 seconds, 16:9, almost locked 35 mm lens view with a barely perceptible slow forward drift and slight treetop breeze. Match the approved opening's geography, soft early-dawn lighting, cool mineral grade and fine grain. No clearing smoke, extinguished fire or before-and-after transformation; simply continue observing.”

**Negative list:** smoke, fire, burned trees, rescue, regrowth time-lapse, success symbol, ACORN deployment, detection UI, text, logo, watermark, colour-temperature change, fast zoom, warping horizon.

## Voice-over prompt

“English voice-over for a 114-second documentary-style prototype film. Warm, clear adult voice, neutral international English, measured and conversational, roughly 130–140 words per minute while speaking; respect the supplied scene windows and leave silence around actions. Precise consonants, low theatricality, no sales-announcer emphasis, urgency without panic. Say ACORN as the word ‘acorn’, UNO Q as ‘oo-no cue’, LoRa as ‘low-rah’, Wi-Fi as ‘why-fy’. Speak only the exact voice-over cells from VIDEO_SCRIPT.md; never read captions, times, instructions or placeholders. Keep ‘smoke suspicion’, ‘simulated today’ and ‘needs testing’ clear. Produce a clean dry voice without music, artificial room echo or alarm effects. For the social version use its separate exact text and 30-second scene windows.”

Generate scene phrases separately if required for accurate pauses. Do not clone any teammate's or public figure's voice. The last phrase ends over the real-device photograph. A photograph has no recorded sound; leave a quiet tail and do not fabricate venue room tone.

## Music-bed prompt

“114-second instrumental bed for a restrained forest-observation prototype film, cool dawn atmosphere, soft felt-piano fragments, sparse low sustained strings and very gentle organic pulse, no vocals. Begin with space and quiet curiosity; modest forward movement as the product mockups appear around 25 seconds; remain unobtrusive beneath technical speech and screen actions. Ease down from 100 seconds, resolve softly by 111 seconds, leave the final three seconds for voice and a quiet tail over the hardware photograph. No heroic climax, trailer hits, ticking countdown, sirens, radio chatter, digital alarm or triumph suggesting a fire was prevented. Clean, understated, patient. Also provide a 30-second edit with a quiet opening, restrained middle and fade before its final hardware-photograph phrase.”

Duck music beneath voice; do not add transmission beeps or synthetic LED sounds as if recorded from the product. Optional generated upscaling applies to context footage only. Preserve authentic app captures, text, camera pixels and photographed LED states without generative enhancement.

## Credits to carry with the exports and deck handoff

Copy the following into the accompanying video description/credits and the deck's distributed notes; keep source badges in the picture too:

> ACORN by team Scarabs, Junction 2026, Helsinki. Forest/concept sequences are generated illustrations; product screens are real running-app captures in generic device frames, and hardware is a genuine still photograph. The laptop demonstration uses recorded footage, not a field deployment. LoRa transport is simulated. Smoke source: “Wildfire Near Monserrate”, Peter Angritt / Mrtony77 (2015), CC BY-SA 4.0, https://commons.wikimedia.org/wiki/File:Wildfire_Near_Monserrate.ogv . Fog source: “Fog covering mountain time lapse”, Athulvis, CC BY-SA 4.0 (Commons external licence review pending), https://commons.wikimedia.org/wiki/File:Fog_covering_mountain_time_lapse.webm . Source videos are shown inside the ACORN interface, with model annotations, edits and operator-review context. Licence: https://creativecommons.org/licenses/by-sa/4.0/ . Model: Pyronear YOLO11s, pinned export documented in station/README.md, AGPL-3.0. Map attribution: NLS Finland / Syke / Luke, CC BY 4.0; retain the map's attribution.

If a fallback capture includes cloud or glare rather than the default fog, copy its exact attribution and licence from `station/README.md`'s Real footage table too. Keep the source and licence information with redistributed annotated media; do not strip it when making the social cut.

Asset log fields: shot ID, capture date, actual host, live/recorded source, profile and camera settings if any performance figure is visible, chosen event, Wi-Fi toggle state, simulation state, viewport/DPR, raw output dimensions, paired-track clock/action times, Placement model inputs, and sensor simulation state. Physical IR stimulus/distance is not applicable to this simulated sensor take. These are capture notes, not new validation results.


## English production refresh — 2026-11-14

All current product takes are English, recorded from a fresh clone of pushed `origin/main`; dated Turkish clips are kept under `captures/archive-2026-11-14-tr/`. See `captures/README.md` for accepted takes, matching arrival UUID/times, device-frame provenance and Screeny accounting. Translation overlays are retired. Events remain smoke suspicions. LoRa transport remains simulated; smoke alerts are 42 bytes (status 40, decision/local-sensor 37). A physical radio module exists but is unidentified and unused for an ACORN link.

Detection claims follow `DEMO.md`: dense daytime smoke filling the camera view worked live on UNO Q with centre crop, three loops and peak scores 0.62–0.76; arbitrary news footage is not a reliable trigger. The new film's file-source inference is a laptop demonstration, separate from that board run. No accuracy/range/endurance claim is added.

Current production overrides earlier text-only handoff language. Hardware-free crops from the existing concept illustration supply forest context in shots 01/02/03/16, with Illustration captions and slow push-ins. Shots 04 and 13 retain labelled cards because the flying/solar concepts do not fit an inert ridge station or a clearly occluding ridge. Shot 20 still needs a genuine assembly photograph. Never substitute the generated hardware. Film renders remain silent with English script subtitles pending recorded narration/music.
