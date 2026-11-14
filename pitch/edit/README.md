# ACORN rough-cut assembly

From the repository root:

```sh
uv run pitch/edit/assemble.py
# Optional: render just one timeline
uv run pitch/edit/assemble.py --cut master
uv run pitch/edit/assemble.py --cut 30s
```

Requires Python 3.11+, `uv`, `ffmpeg` with libx264, and `ffprobe` on PATH. `uv` supplies Pillow and FontTools from the script's inline dependency list. No running app, Screeny project, browser, server or port is used. The supplied MP4 mockups are read only.

Outputs (local and ignored):

- `out/acorn-master-roughcut.mp4`: 114.000 seconds / 3,420 frames.
- `out/acorn-30s-roughcut.mp4`: 30.000 seconds / 900 frames.
- `out/review/<render-name>/`: one full-resolution midpoint PNG per shot, contact sheet and complete ffprobe result.
- `out/render-report.json`: shot order, fill/gap state, source intervals, held durations and missing paths.
- `out/work/`: intermediate shot parts and editorial overlays; safe to delete and regenerate.

Both exports are 1920×1080, square pixels, 16:9, 30 fps, H.264/yuv420p. Straight cuts preserve the exact script windows. Without named audio files they have **no audio stream**. Burnt English subtitles contain the exact script voice-over reads, including the separate social reads, so the silent film can be reviewed end to end. The social cut retains the master editorial/provenance labels.

## Edit data

`assembly.json` is the only edit decision file. `shots` lists all 20 master shots in order, source type, description, duration, exact `on_screen_text`, `caption`, script `subtitle`, and source `edits`. `cuts` lists each ordered timeline and optional subtitle/edit overrides. All paths are relative to the repository root; the command works from any working directory.

Each edit names its duration and one source or a paired phone/desk view. `in_seconds` is inclusive; `out_seconds` is exclusive. Each interval plays at its original speed; an interval longer than the edit is trimmed, and a shorter interval holds its last frame. Clips never loop. Multi-part edits cut between real states. Shot 10 uses identical source intervals on both tracks, removing the same wait jointly. The 30-second version has its own shorter paired intervals.

`crop` is `[x, y, width, height]` in the original mockup. It removes outer matte and the lower monitor stand, preserving the entire screen and bezel; media is then fitted proportionally, never stretched. Titles/captions occupy the top band, devices the middle band, subtitles the bottom band. Translations sit beside the solo phone or at upper right for pairs. `wordmark_rect` masks only the verified existing header artwork with plain ACORN; scrolled shots 11 and 18 have no mask. No app controls, source labels or values are repainted. If you change a source's geometry or scroll position, review its crop and header mask too.

The single type family is the repository's IBM Plex Sans; Latin and Latin Extended subsets supply Turkish glyphs. Derived TTFs stay in `out/`. `placement/brand.json` supplies ACORN's identity but currently contains **no palette tokens**. The JSON therefore records the exact mineral colours from `VIDEO_SCRIPT.md`'s “Picture and type” section and identifies that source explicitly.

## Replace the seven gaps

Create `pitch/edit/media/` and add approved assets at these names. The next run replaces the cards automatically; no code/data change is needed. GENERATED files are context only, always captioned Illustration. Missing paired mockup components also produce an explicit card.

| Shot | Type | Agreed repository-relative file | Required picture |
|---|---|---|---|
| 01 | GENERATED | `pitch/edit/media/shot-01-forest-dawn.mp4` | Quiet forest at dawn, no smoke/fire; 7 s |
| 02 | GENERATED | `pitch/edit/media/shot-02-canopy.mp4` | Slow canopy move; 6 s |
| 03 | GENERATED | `pitch/edit/media/shot-03-remote-ridge.mp4` | Empty remote ridge; 6 s |
| 04 | GENERATED | `pitch/edit/media/shot-04-station-concept.mp4` | Generic inert enclosure, not deployed; 6 s |
| 13 | GENERATED | `pitch/edit/media/shot-13-occluding-ridge.mp4` | Ridge obscuring forest; 5 s |
| 16 | GENERATED | `pitch/edit/media/shot-16-forest-reprise.mp4` | Opening forest unchanged; 4 s |
| 20 | REAL | `pitch/edit/media/shot-20-prototype.jpg` | Genuine landscape assembly photograph, ideally ≥3840×2160 |

Shot 20 gets a restrained 100→103% crop move when its actual photograph arrives. Record its capture date/setup separately; the still proves assembly, not operation. No generated hardware substitute is accepted for this shot.

Filled today: **05–12, 14–15, 17–19** (all 13 MOCKUP shots, using all 11 device-framed clips). Placeholders: **01–04, 13, 16, 20**. The existing `pitch/photos/*concept-illustration*` stills show balloon hardware and do not match the scripted empty forests/ridges or inert ridge-mounted station. They are deliberately unused; none is evidence or a prototype photograph. A suitable still can later be named in the relevant JSON source instead of MP4; supported still extensions are JPG/JPEG/PNG/WebP.

## Later voice-over and music

Under each cut's `audio`, set `voice_over` and/or `music` to repository-relative files, for example:

```json
"audio": {
  "voice_over": "pitch/edit/media/acorn-master-vo.wav",
  "music": "pitch/edit/media/acorn-master-music.wav",
  "voice_gain": 1.0,
  "music_gain": 0.16
}
```

Use `acorn-30s-vo.wav` and `acorn-30s-music.wav` for the social cut. Each file starts at timeline zero: supply an already timed full-cut voice track using the exact script windows. Missing named audio fails explicitly. Audio is resampled to 48 kHz, padded/trimmed to the cut, mixed with the chosen gains and a limiter, then encoded as AAC. Music has a three-second tail fade and defaults to a low bed; there is no automatic speech ducking. Original capture audio is always discarded. No audio is generated by this assembly.

## Review and known weaknesses

The renderer extracts a midpoint from **every shot of both final exports**, rejects black midpoints and overflowing editorial blocks, and checks codec, dimensions, fps, frame counts, silent default and total lengths with ffprobe. Open all midpoint PNGs after edits; inspect additional frames around actions and cuts when source intervals change. The first delivery was visually inspected shot by shot, including the Wi-Fi off/on/off and completed Placement selections. Both full exports were decoded without errors. Midpoints alone cannot prove a UI transition or establish event timing.

- The 25-second opening is still four dark cards; pacing cannot be judged cinematically until the landscapes arrive. Seven gaps occupy 37 seconds of the master.
- 07/08 use the matching held suspicion fallback: **no new arrival was captured**. An amber note stays visible; the exact script read remains a planned narration, not evidence of arrival. 17 is a held recap.
- 10 is the genuine rejected→confirmed **correction**, not a first decision. The paired cut retains the real order, packet-only Ground and simulated/edited-wait labels. The correction note stays visible.
- 11's 42-byte caption describes the documented smoke schema. The captured “Last packet size” is 40 B and remains unchanged, with an exterior clarification.
- 12 cuts off→saved Wi-Fi clip→off, preserving a final imagery-free state. 15 cuts only completed heading/pair results; it does not show calculations as completed before they are.
- Ground, packet details, translations and map fine print are dense at projection size; the editorial labels are readable, but this remains a rough cut. The four-second limitations beat (17) and three-second proposed-work beat (19) are particularly text-heavy.
- No voice or music exists yet, and the missing final photograph weakens the ending. Do not treat this assembly as release-ready proof of field operation.

## Credits to accompany both videos

ACORN by team Scarabs, Junction 2026, Helsinki. Current product screens are real running-app captures inside generic device frames. Missing forest/concept and prototype shots are labelled cards. Future forest/concept assets must remain labelled generated illustrations; future hardware must be a genuine still photograph. The laptop demonstration uses recorded footage, not a field deployment. LoRa transport is simulated.

Smoke source: “Wildfire Near Monserrate”, Peter Angritt / Mrtony77 (2015), CC BY-SA 4.0, <https://commons.wikimedia.org/wiki/File:Wildfire_Near_Monserrate.ogv>. Fog source: “Fog covering mountain time lapse”, Athulvis, CC BY-SA 4.0 (Commons external licence review pending), <https://commons.wikimedia.org/wiki/File:Fog_covering_mountain_time_lapse.webm>. Source videos appear inside ACORN with model annotations, edits and operator-review context. Licence: <https://creativecommons.org/licenses/by-sa/4.0/>. Keep these credits with redistributed annotated media and the social export.

Model: Pyronear YOLO11s, pinned export in `station/README.md`, AGPL-3.0. Map attribution: NLS Finland / Syke / Luke, CC BY 4.0; original map attribution remains visible. IBM Plex Sans: SIL Open Font License, `placement/static/fonts/OFL-IBM-Plex-Sans.txt`. Capture conditions and the event/clock log are documented in `pitch/captures/README.md`; source constraints in `pitch/SHOTLIST.md` and `pitch/MOCKUPS.md` still apply.
