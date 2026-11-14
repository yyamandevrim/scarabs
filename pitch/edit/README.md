# ACORN English film assembly

From the repository root:

```sh
uv run pitch/edit/assemble.py
uv run pitch/edit/assemble.py --cut master
uv run pitch/edit/assemble.py --cut 30s
```

Requires Python 3.11+, uv, ffmpeg/libx264 and ffprobe. Inline dependencies supply Pillow and FontTools. No server or Screeny app is needed for assembly. Source paths in `assembly.json` are repository-relative. Captures, renders, raw footage and review frames remain ignored.

## Outputs

- `out/acorn-master-roughcut.mp4`: **114 seconds, 3,420 frames**.
- `out/acorn-30s-roughcut.mp4`: **30 seconds, 900 frames**.
- `out/review/<render-name>/`: one full-resolution midpoint from every shot, contact sheet and ffprobe results.
- `out/render-report.json`: shot order, source intervals, frame holds and explicit missing media.
- `out/work/`: regenerable intermediate clips, derived fonts and editorial overlays.

Both films: 1920×1080, square pixels, 16:9, 30 fps, H.264/yuv420p. They are silent, with English script subtitles. No voice-over or music has been supplied. Audio support remains in the JSON: name a repository-relative full-cut `voice_over` or `music`, with gain, to mix it; missing named audio fails explicitly. Source capture audio is discarded.

## Current edit and provenance

The master remains 20 shots. **17 are filled; 04, 13 and 20 are labelled placeholders.** In the social cut 04 and 20 remain placeholders. Replacement paths and required pictures:

| Shot | Local replacement | Needs |
|---|---|---|
| 04 | `pitch/edit/media/shot-04-station-concept.mp4` | Six-second inert generic station concept; Illustration / not deployed. Current generated flying/solar hardware does not fit. |
| 13 | `pitch/edit/media/shot-13-occluding-ridge.mp4` | Five-second view of a ridge visibly obscuring forest; Illustration. |
| 20 | `pitch/edit/media/shot-20-prototype.jpg` | Genuine landscape assembly photograph showing board, hub, both cameras and local sensor. Record date/setup; no generated substitute. |

Shots **01/02/03/16** use hardware-free forest/sky crops of `pitch/photos/concept-illustration-station-medium-v2.png`, with a restrained 100→103% push and persistent **Illustration** captions. The balloon, solar panels and generated enclosure are outside each crop; no deployment/energy claim is made. Other concept stills are preserved as context assets, not hardware evidence.

Every product moment is an English running-app recording from a fresh clone of pushed main. **Shot 07 alone uses the single new Screeny export**, marked as a separate arrival take. Every other device shot uses the plain, logo-free phone/laptop frames drawn by `frame_captures.py`. All deck stills use these own frames. The original Turkish takes and Screeny projects remain in the dated local archive. See `../captures/README.md` for credits, settings and exact event clocks.

The primary paired event is `4b19c5f90b084ad99e765653530fde7c`. Station appeared at Ground-clock t=5.526 s; Ground received it at 7.344 s. Phone recording started 3.173 s after Ground. Shot 08 plays one **uninterrupted seven-second shared interval**, t=4.5–11.5, accounting for that offset. No latency is claimed. Ground history is retained and the matching record is selected through the real Show direction control. Camera configuration may not have arrived yet: this is the real packet-only state, not a repaired compass.

B2's native evidence plays before the first confirmation (confirmed at t=6.432 s; Ground update t=11.304 s). Shot 10 removes the same waiting interval jointly, with an explicit edited-wait note. Ground's local acknowledgement is never substituted for Station's decision. Shot 11 is an explicitly separate earlier-event details take; the 42-byte caption describes the smoke-alert schema, while Last packet size may be a later 40-byte status. Shot 12 is a separate Wi-Fi off/on/off demonstration, ending without imagery. Shot 15 uses completed map results only (including the real recalculation waits in its untrimmed source). Shot 18 is a close-up of the genuine simulated local-sensor panel, with adjacent camera imagery cropped out; no physical LED is implied.

`assembly.json` contains each exact on-screen label, caption, subtitle and edit. Source intervals play at their original speed; short sources hold the final frame and never loop. Pair waits are cut jointly. `crop` removes exterior matte or provides a disclosed close-up, never stretches UI. The full native recordings remain intact. No header artwork or status value is repainted. ACORN is plain text in editorial titles and deck identity.

## Capture encoding and original frames

`frame_captures.py` converts ignored timestamped viewport JPEGs in `captures/en/_raw/` to 30-fps MP4 while retaining the native clock, verifies every JPEG, and draws original generic phone/laptop bezels with Pillow before ffmpeg compositing. It requires the local accepted raw takes; it neither starts apps nor triggers events. Phone capture is 393×852/DPR3; Ground/Placement 1440×810/DPR2; Station overview 1152×648/DPR2. The sensor source uses a disclosed static crop and matte pad, followed by a film close-up, preserving every module value and scope caption.

## Verification and remaining weaknesses

Every accepted framed clip was fully decoded. Both final films are checked for dimensions, fps, duration, frame count and missing audio; every shot has a midpoint extracted and visually reviewed. Arrival/playback/decision/toggle/map transitions receive additional state checks. PDF/HTML deck checks are in `../deck/README.md`. Verification artefacts stay local in ignored output directories.

The edit is still a rough cut: no narration/music, and three missing pictures. Shot 20 is the weakest because the physical prototype ending lacks its essential real photograph. Fine app text remains small in paired scenes; the exterior English captions carry the claims and the full-screen deck/demo supplies detail. Slide 3 is the weakest slide because its documented architecture is accompanied by a laptop capture, without a hardware photograph. No field accuracy/range, night response, complete cost, demand or endurance figure has been invented. Board centre-crop screen replay (0.62–0.76 peak scores) is separately documented evidence, not the laptop source used in these films.

## Credits to accompany both videos

ACORN by team Scarabs, Junction 2026, Helsinki. Current product screens are real running-app captures inside generic device frames. Missing station-concept, occluding-ridge and prototype shots are labelled cards. Forest crops are captioned Illustration. Generated context remains labelled Illustration; hardware evidence must be a genuine photograph. The laptop demonstration uses recorded footage, not a field deployment. LoRa transport is simulated.

Smoke source: “Wildfire Near Monserrate”, Peter Angritt / Mrtony77 (2015), CC BY-SA 4.0, <https://commons.wikimedia.org/wiki/File:Wildfire_Near_Monserrate.ogv>. Fog source: “Fog covering mountain time lapse”, Athulvis, CC BY-SA 4.0 (Commons external licence review pending), <https://commons.wikimedia.org/wiki/File:Fog_covering_mountain_time_lapse.webm>. Source videos appear inside ACORN with model annotations, edits and operator-review context. Licence: <https://creativecommons.org/licenses/by-sa/4.0/>. Keep these credits with redistributed annotated media and the social export.

Model: Pyronear YOLO11s, pinned export in `station/README.md`, AGPL-3.0. Map attribution: NLS Finland / Syke / Luke, CC BY 4.0; original map attribution remains visible. IBM Plex Sans: SIL Open Font License, `placement/static/fonts/OFL-IBM-Plex-Sans.txt`. Capture conditions and the event/clock log are documented in `pitch/captures/README.md`; source constraints in `pitch/SHOTLIST.md` and `pitch/MOCKUPS.md` still apply.
