# Overview media

`event-frame.webp` and `event-clip.mp4` come from the same archived event, `af27f33e9e244d9db8f18eb4276fd1ad`. The H.264 / 15fps clip is a native 640px-wide crop from y=80 to y=360. The still comes from one second into that same clip, so smoke reads clearly. Cropping omits legacy in-frame annotation text without repainting pixels. Reproduce with `scripts/prepare_overview_media.py SOURCE_EVENT.webm OUTPUT_DIRECTORY` (ffmpeg and Pillow).

The record's opening time and score (13:47:51 UTC; 59% after packet quantization) drive the report and review context. Camera choice changes the displayed camera and bearing only. Every choice retains that one real UUID, time, score and media; no case identifier is generated. The archive is unchanged. The phone uses real DOM playback and decision controls: moving video, a saved frame, then review. Both players have neutral labels and pause off-screen/hidden. The desktop evidence dialog keeps the source video at or below its native 640px width.

`map-overview-desktop.webp` is a direct 1312×820 capture from port 18787 after the round-three map integration (`be92393`), encoded at WebP quality 78 / method 6. It is shown at that width without letterboxing. `map-360-phone.webp` is the map agent's current 393×852 export, shown at full phone width. The original map agent's desktop export remains available but is no longer the Overview's selected source. No map controls, parameters or pixels were edited for these captures. Sources show Sipoonkorpi and Nuuksio.

See `pitch/captures/README.md` and `pitch/captures/apple-screens/README.md` for the source archive, and `../vendor/README.md` for runtime/build instructions.

Smoke footage: [Wildfire Near Monserrate](https://commons.wikimedia.org/wiki/File:Wildfire_Near_Monserrate.ogv), Peter Angritt (Mrtony77), [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Changes: app detection overlays, crop, WebP and H.264 re-encoding. These derivatives remain available under CC BY-SA 4.0. Underlying map data: NLS Finland, Syke and Luke, CC BY 4.0, with dataset details supplied by `/api/config`. Credits are retained on the Overview.
