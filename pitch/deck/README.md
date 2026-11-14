# ACORN pitch deck

Open `acorn-pitch.html` directly in a browser. It is one self-contained offline file: fonts, stills, notes, styles and navigation are embedded. It has nine 16:9 slides, scaled to fit the display. Use ←/→ (or Page Up/Down), Home/End, **F** for full screen and **N** for notes. `NOTES.md` also contains the reads, evidence and credits. `acorn-pitch.pdf` is the nine-page print version.

Rebuild after the English captures and frames exist:

```sh
uv run pitch/deck/build.py
# In a local environment with Playwright installed:
NODE_PATH=path/to/node_modules node pitch/deck/export.cjs
```

No server is needed. `build.py` reads the repository's IBM Plex font files, `DECK.md`, the named ignored clips and the concept forest crop. `export.cjs` creates the PDF and a 1920×1080 PNG of every slide under ignored `review/`, checks image/font loading, slide bounds, arrow navigation and notes, and writes `review/validation.json`. Inspect all nine images; automated bounds checks do not replace visual review. No network assets are loaded.

Product stills are real English laptop captures. The forest crops are captioned Illustration. The hardware photograph is still missing; documented architecture and actual app views are clearly distinguished. See `../DECK.md` and `../captures/README.md` for evidence limits and capture provenance.
