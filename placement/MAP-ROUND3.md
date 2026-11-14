# Map round-three acceptance — 2026-11-14

Supersedes round-two **UI** evidence in MAP-POLISH.md. Numeric audits and the v8 full-circle engine are unchanged. No Python/backend, physics, raster, token, shared shell or Overview implementation changes.

| Review finding | Resolution and evidence |
| --- | --- |
| Opus N-3: unfair height/detail comparison | Height and detail apply to both sites. The verdict remains “Updating the comparison…” until both results are current at the same height and grid. Superseded responses cannot restore an obsolete verdict. Unit and browser tests cover the partial-result interval. |
| GPT 2: Finish area contrast | Explicit neutral light finish button; enabled contrast exceeds 7:1. Disabled until three points; all toolbar actions are 44 px. Start, drawing, finish, cancel and clear are covered by the desktop/pointer and phone/touch tests. |
| GPT 4: dead comparison column | Each whole site card is an accessible pressed-state button. Clicking the large B figure selects B, including its camera breakdown and geometry context. |
| GPT 8 / Opus map figure-ground | Restore the requested 48% brightness, 70% opacity and no blur while preserving the quiet colour treatment. Actual coverage at both sites is drawn; secondary raster opacity is 45%, with a quiet continuous perimeter. Mint cells remain dominant. |
| GPT 8 / Opus N-14: priority area | Guidance is short, uses Tap on touch, and hides after finish/cancel/clear. A solid accent outline/fill has a dark under-stroke. Finish returns to Compare and scrolls the comparison into view. |
| GPT 9: scale ghost | Remove Leaflet's white text-shadow, use 11 px Plex / 1.4 line-height. |
| GPT phone verdict / Opus N-14 | Fit both site markers initially; show three 12 px camera labels with clamped positions, recomputed on pan/zoom. Keep navigation reachable, move phone zoom/layers to bottom-left, reduce map/legend region to 340–390 px. Verdict fits the initial 393×852 screen. |
| Opus height trade-off | Closed Compare heights table computes the five supported heights for both current sites using the actual engine, current detail/scenario/priority. Missing cells remain uncomputed. Samples are bounded and invalidated when config changes. |
| Opus disclosure/filler | Separate Editing context from the disclosure name, retain its native arrow, remove filler footer/dead space. Status is an accessible live region. |
| Owner: feedback/recovery | Settings mark previous figures/coverage as updating immediately; no blocking map overlay. Requests have deadlines, serialized analysis transport and capped exponential retries. Reconnection refetches config/presets and recalculates both sites. Network failures, timeout, changed schema/config and obsolete responses have DOM request tests. |

## Verification

- `uv run --offline --frozen pytest`: **85 passed**, one upstream Starlette/httpx deprecation warning. This includes eight DOM request/recovery cases.
- `scripts/check_map.mjs`: **25 captured desktop/phone states** at 1440×900 / 393×852; `check_language.js` evaluated throughout with Turkish storage/URL preferences seeded. No Turkish, obsolete camera copy, horizontal overflow, external requests, ordinary console errors or failed responses.
- The browser suite starts an additional server on its own random port, kills that owned uvicorn process mid-request, then restarts it. The same open page resumes without a navigation. A response fixture changes preset names, default height and the data fingerprint after restart, proving config/preset refresh and rejection of stale figures. All numerical analyses still use the actual engine. Evidence records multiple config reads, one navigation and automatic recovery. Expected network console messages from this intentional outage are separated from ordinary errors.
- Captures inspected for map context/coverage balance, label placement, touch controls, enabled finish contrast, priority outline/help removal, shared 30 m/detail updates, each tab, heights table and reconnection. Default figures remain **≈19,460 / ≈26,850 simulated ha**, both at 600 m and Quick · 120 m.

Screenshots and raw checks: `/private/tmp/claude-501/-Users-yamandevrim--t3-projects-junction/2d00c443-8aa2-4c2c-af46-792d4247fcf0/scratchpad/overview/round3-map/`. Committed evidence: `map-round3-verification.json`.

Reproduce from the repo root: copy `placement/scripts/check_map.mjs` into a temporary directory with Playwright installed, then run `node TEMP/check_map.mjs BASE_URL CHROMIUM_BINARY OUTPUT_DIRECTORY`. Use the cached Chromium under `~/Library/Caches/ms-playwright`. The suite cleans up its own recovery server, leaving the supplied test URL and main port 18787 alone.

The unchanged Overview also passes its full `check_overview.mjs` suite (Chromium, Firefox and WebKit at both widths; full interaction path, context recovery and no-WebGL fallback). Those captures and measurements are in `overview-regression/` under the same screenshot directory. This verifies the committed Overview version; the concurrent Overview edits are outside this round’s ownership.

## Preview and ownership

Fresh `preview-desktop.png` and `preview-phone.png` export the existing map-owned WebPs at unchanged filenames/dimensions: `map-360-desktop.webp` 1280×800 / 96,776 B; `map-360-phone.webp` 393×852 / 39,096 B (quality 78, method 6). The concurrently edited Overview desktop source `map-overview-desktop.webp` is owned by the Overview agent and is not overwritten here; the fresh desktop PNG is available for its export. No landing template, script or stylesheet was edited.

The main server needs no restart for these static changes. No removed claims were restored and no new public caveats or performance/accuracy claims were added.
