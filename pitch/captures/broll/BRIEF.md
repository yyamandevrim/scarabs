# B-roll capture brief (shared by all capture agents) — 2026-11-15

Goal: clean screen recordings (MP4) and stills (PNG) of ACORN, to be placed inside device mockups and used as b-roll in the pitch film. Yaman (owner) wants every UI covered, plus stills from everywhere. Each agent owns ONE surface and writes only into its own folder `pitch/captures/broll/<surface>/` (git-ignored; do not commit media).

Repo: /Users/yamandevrim/.t3/projects/junction. Read first: `pitch/captures/README.md` (previous capture method and conditions), `pitch/MOCKUPS.md` (device geometry, truthful-input rules), `DEMO.md` (how to run the apps), and the README of your app.

## Output spec
- Video: MP4, H.264, yuv420p, `+faststart`, no audio, 30 fps constant minimum (60 if you can get real unique frames), high quality (CRF <= 16 or equivalent). Motion must be smooth: real unique frames, not a 5 fps slideshow padded to 30. Check with ffprobe and by looking at extracted frames.
- Landscape: 1440x810 CSS viewport, DPR 2 -> 2880x1620 native (16:9). Also deliver a 1920x1080 downscale of every landscape clip (`*-1080.mp4`).
- Phone (only where the UI is meant for phone or is responsive and looks good): 393x852 CSS, DPR 3 -> 1179x2556 (pad to even width for H.264 as before).
- Viewport content only: no browser chrome, no OS desktop, no terminal, no notifications, no scrollbar flashes if avoidable. Produce each interaction clip without a visible cursor; a cursor version is optional (`*-cursor.mp4`).
- Clips: 6-25 s each, one idea per clip, 1 s of still hold at start and end, slow smooth moves (eased scrolls, unhurried clicks). Many short clips beat one long one. Cover every screen, state, panel, dialog, tab, hover/expanded state and animation the surface has. Aim for full coverage, not a sample.
- Stills: PNG at the same native sizes, of every distinct screen/state, plus full-page stills for long pages and a few tight crops of good-looking details (2x). 
- Naming: `<surface>-<nn>-<short-slug>.mp4|png`, in `video/` and `stills/` subfolders.
- `manifest.md` in your folder: table of every file with duration, resolution, fps, and one line on what it shows and the app state/conditions (source, port, commit `git rev-parse --short HEAD` + "working tree with uncommitted changes" if so).
- `contact-sheet.png`: one image tiling a representative frame from every clip and still, with filenames, so the owner can scan everything at once.

## Rules
- Capture the working tree as it is. Do NOT edit tracked source files, do not commit, do not push, do not deploy, do not touch the Vercel project. Scripts you write go in your output folder (or the scratch area), not in app folders.
- Do not record the real screen and do not take over the user's display, keyboard, mouse or foreground apps: use headless/offscreen browser capture (Playwright Chromium is installed in ~/Library/Caches/ms-playwright; ffmpeg at /opt/homebrew/bin/ffmpeg). Several agents run at the same time on this Mac.
- Truthful pixels: everything on screen comes from the real running app with its real inputs. No DOM edits to change content, no injected events or values, no fake detections, no replaced media. Driving real controls and scrolling is fine. Hiding the cursor or a scrollbar via capture settings is fine.
- English UI only. If any Turkish text shows, switch the UI to English by its own control; if it cannot be removed, do not use that take and note it.
- Never show secrets, login passwords, tokens, private addresses or personal data. Log in before recording starts.
- No paid or external services (no Higgsfield, Screeny, image generators, uploads). Everything local.
- Use only your assigned ports. Stop every server/process you started when done. Do not stop processes you did not start.
- You may start as many further GPT (codex gpt-6.1-sol) subagents as helps you, e.g. one per clip group or for an independent quality check; they follow this same brief.
- Before reporting done: ffprobe every MP4, fully decode each once, look at frames from start/middle/end of every clip yourself (blank frames, loading spinners, half-loaded maps, clipped text, Turkish text, stutter are failures: retake). Report honestly what is missing or weak.

## Final report (short)
Count of clips and stills, total duration, absolute path of your folder and contact sheet, anything you could not capture and why, anything that looked wrong in the product itself (list it, do not fix it).
