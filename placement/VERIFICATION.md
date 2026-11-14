# Verification report — 360° launch map and Overview

Verified 2026-11-14 on macOS, Python 3.12.10. **85 placement pytest tests pass**, zero failed/skipped. One upstream Starlette/httpx deprecation warning remains. The suite includes Node presentation and DOM request-sequencing checks. Playwright uses the locally cached Chromium 1255; its npm packages were installed in a temporary directory outside the repo.

## Current model

Three simultaneously active cameras on the faces of a triangular housing, yaw **0° / 120° / 240°**. Each camera is modelled as a **120° horizontal sector by product decision**, not a measured lens calibration. Half-open seams give every eligible azimuth exactly one camera. Common tilt and VFOV are evaluated in the radial vertical plane: heading rotates ownership without changing the union. The old rectilinear horizontal/vertical coupling, forward fan, pair/reference modes and heading sensitivity are superseded. Terrain/canopy LOS, target heights, curvature and raster weighting are unchanged.

Cache algorithm: `opaque-ray-half-cell-v8-360-sectors-en`. Tests reject old v7 cache entries and retired public camera modes. Default geometry is 600 m AGL, 10° down, 50° VFOV, 12 km maximum range and smoke 50 m above the local canopy/surface. Default A is Sipoonkorpi at 60.320 / 25.190; B is Nuuksio at 60.293 / 24.557. Both use heading 0°. No priority polygon.

The annular guides solve the vertical boundaries, including curvature, on a level target plane through the launch cell. The inner blind disc is not filled by a camera wedge. Actual visibility masks use the local terrain/canopy target at every cell. Steeper settings can also reduce the outer guide radius below maximum range.

## Historical sanity check against the retired three-camera reference

All values below are **simulated hectares** at 600 m. Historical values were read from the pre-change committed blind-audit.json before regeneration. The old reference used yaw −70°/0°/+70° and 80° rectilinear HFOV (nominal ~220° horizontal union; the task calls it the ~210° fan).

| Site | Grid | Old all-camera fan | New full circle |
| --- | ---: | ---: | ---: |
| Haukilahti | 120 m | 3,083.08 | 8,072.24 |
| Nuuksio | 120 m | 17,309.76 | 26,849.84 |
| Haukilahti | 40 m | 3,088.80 | 8,072.92 |
| Nuuksio | 40 m | 17,298.84 | 26,856.96 |

Both historical sites increase. The round-two defaults are Sipoonkorpi (≈19,460 simulated ha; 6% water) and Nuuksio (≈26,850 simulated ha; 8% water). The 360° model still has a vertical blind disc, terrain/canopy occlusion and raster sampling effects. A larger height can reduce visible forest because the inner blind region grows; no monotonic-height claim is made.

## Height audit

`blind_forest_ha = outside_fov_forest_ha + occluded_forest_ha` within rounding ±0.003 ha. Each forest fraction is counted once; camera forest areas sum to the union within rounding. Overlap is zero. Outside FOV is vertical exclusion; low-height occlusion remains substantial. Unknown-elevation rays remain blind and the candid API uncertainty metadata is retained.

### Coarse canopy-smoke scenario

| Site | AGL m | Visible | Outside vertical FOV | Occluded | Blind total |
| --- | ---: | ---: | ---: | ---: | ---: |
| Forest · Sipoonkorpi | 30 | 8,863.52 | 5.24 | 10,763.84 | 10,769.08 |
| Forest · Sipoonkorpi | 100 | 19,630.92 | 1.16 | 0.52 | 1.68 |
| Forest · Sipoonkorpi | 500 | 19,518.32 | 114.28 | 0.00 | 114.28 |
| Forest · Sipoonkorpi | 600 | 19,461.96 | 170.64 | 0.00 | 170.64 |
| Forest · Sipoonkorpi | 700 | 19,399.36 | 233.24 | 0.00 | 233.24 |
| Inland · Nuuksio | 30 | 5,319.20 | 0.64 | 21,614.36 | 21,615.00 |
| Inland · Nuuksio | 100 | 26,889.28 | 0.08 | 44.84 | 44.92 |
| Inland · Nuuksio | 500 | 26,885.76 | 48.44 | 0.00 | 48.44 |
| Inland · Nuuksio | 600 | 26,849.84 | 84.36 | 0.00 | 84.36 |
| Inland · Nuuksio | 700 | 26,792.68 | 141.52 | 0.00 | 141.52 |

### Detailed canopy-smoke scenario

| Site | AGL m | Visible | Outside vertical FOV | Occluded | Blind total |
| --- | ---: | ---: | ---: | ---: | ---: |
| Forest · Sipoonkorpi | 30 | 7,473.88 | 4.40 | 12,153.36 | 12,157.76 |
| Forest · Sipoonkorpi | 100 | 19,627.32 | 0.96 | 3.36 | 4.32 |
| Forest · Sipoonkorpi | 500 | 19,517.84 | 113.80 | 0.00 | 113.80 |
| Forest · Sipoonkorpi | 600 | 19,458.84 | 172.80 | 0.00 | 172.80 |
| Forest · Sipoonkorpi | 700 | 19,398.76 | 232.88 | 0.00 | 232.88 |
| Inland · Nuuksio | 30 | 4,931.28 | 1.08 | 22,011.48 | 22,012.56 |
| Inland · Nuuksio | 100 | 26,815.40 | 0.20 | 128.24 | 128.44 |
| Inland · Nuuksio | 500 | 26,894.44 | 48.76 | 0.64 | 49.40 |
| Inland · Nuuksio | 600 | 26,856.96 | 86.52 | 0.36 | 86.88 |
| Inland · Nuuksio | 700 | 26,802.32 | 141.20 | 0.32 | 141.52 |

## UI and browser verification

- Compare: site A/B totals and verdict; selected-site height and detail; three per-camera forest bars. Shared tilt/VFOV, position, range and smoke height are in a disclosure. Breakdown includes scenario accounting and camera rows. Data keeps real data provenance, assumed-canopy percentage and CC BY 4.0 attribution.
- English is forced in the shared loader, saved preference is reset to en, dictionary loading is removed, and language controls are removed. URL language parameters do not affect rendering. Overview and map templates have no language control; the server also strips any legacy toggle.
- Playwright checks 1440×900 default, Breakdown, Data, site B, 100 m height, and 393×852 top/scrolled and each tab. All captures were visually inspected; the full ring, inner blind boundary, sector labels, balanced dock and mobile overflow were checked. Secondary place labels yield to camera/site labels. Zero console errors and external requests.
- `scripts/check_language.js` passes at every captured state after seeding localStorage language=tr and requesting ?lang=tr&language=tr. Tests include no obsolete pair/disconnected copy.
- Evidence: `browser-verification.json`; screenshots under `/private/tmp/claude-501/-Users-yamandevrim--t3-projects-junction/2d00c443-8aa2-4c2c-af46-792d4247fcf0/scratchpad/overview/map/`. Clean Overview capture: `map-preview-1440.png`. The owner copy review is one level up at `claims-for-owner-map.md`.
- Historical public browser evidence is explicitly marked superseded in `public-browser-verification.json`. No cloud deployment was performed. Overview and map are now integrated, and the Overview map section uses responsive captures of the 360° default view.

## Reproduce

```sh
uv run --offline --frozen pytest
uv run --offline --frozen python scripts/blind_audit.py
uv run --offline --frozen python scripts/benchmark.py --url http://127.0.0.1:56232 --fresh
uv run --offline --frozen python scripts/production_benchmark.py
uv run --offline --frozen python scripts/write_report.py
```

`blind-audit.json` has 20 current analyses (2 sites × 5 heights × 2 grids), including every scenario and per-camera breakdown. `benchmark-results.json` contains the fresh-engine/live-HTTP verification at 500/600/700 m. `production-timings.json` was regenerated against this model, in isolated temporary caches. Timing measurements are local Mac observations, not cloud/cold-network measurements. `comparison-chart.html` is regenerated from the current audit.

## Engineering limitations and ownership

No measured lens calibration, field detection accuracy, smoke transport, weather, refraction or balloon/tether motion model. No building-height dataset; positive canopy cover is opaque, Luke mean height is not maximum treetop height, 5.47% of forest cells use assumed 20 m canopy, and raster years differ (NLS 2019 / CORINE 2024 / Luke 2023). Land launch validation is approximate; permission/access/tether suitability remain field checks. No physical Wi-Fi-off test or cloud deployment was performed. Investor-facing limitations text removed from the map is recorded verbatim for the owner; no replacement accuracy/range claims were added.

Integration combines the Overview renderer, link/Wi-Fi demos, English-only brand hydration and root-only WebAssembly CSP with the 360° map. The landing map section has a real responsive WebP preview and height-based copy. Its layout and all other Overview sections are retained. Prepared rasters are read-only in this worktree; analyses write only its own results cache. The approved claims list remains in the owner scratch directory. tokens.css and shell.js are unchanged.

## Merged Overview acceptance

The complete `scripts/check_overview.mjs` interaction suite was rerun after integration. It retains the Overview agent’s WebGL, CAD selection, all-camera view, assembly, packet codec, LoRa/evidence, video, touch/scroll, fallback/context recovery and idle-render checks. The page-specific language/title assertions and map obsolete-copy assertions are combined in `scripts/check_language.js`.

Measured initial transfer: **1,050,571 B**; full scroll + phone walkthrough: **1,241,968 B**. The previous full-scroll baseline was 1,184,230 B. The increase is **57,738 B**, within the requested ~150 KB budget. These CDP development-server measurements include HTTP headers and exclude later explicit evidence collection.

Initial integration preview assets (superseded by the round-two refresh): desktop 1280×800 / 119,632 B; phone 393×852 / 41,208 B; WebP quality 78, method 6. Only the matching responsive source loads, lazily, with declared dimensions. The retired source was 61,062 B. The map-section layout and style are retained.

Fresh `/` and `/map` desktop/393px checks pass with zero console errors, external requests, failed responses or horizontal overflow, and English despite Turkish storage/URL preferences. Screenshots and measurements: `/private/tmp/claude-501/-Users-yamandevrim--t3-projects-junction/2d00c443-8aa2-4c2c-af46-792d4247fcf0/scratchpad/overview/merged/`. Overview implementation/build methods remain documented in `static/vendor/README.md`.

Reproduce the full Overview suite from the repository root by copying `placement/scripts/check_overview.mjs` into the temporary npm directory and running `node TEMP/check_overview.mjs BASE_URL CHROMIUM_BINARY SCREENSHOT_DIRECTORY`. It evaluates `check_language.js` in the browser; that file is not a standalone Node CLI.

## Round-two map polish

All compatible map findings from the GPT and Opus reviews were addressed. See `MAP-POLISH.md` for the per-finding decisions and `map-polish-verification.json` for desktop/393px checks and current preset metrics. This is presentation and preset selection only: camera-sector physics, LOS, numeric rasters and algorithm version remain unchanged.

The desktop view shows both complete ring perimeters; the selected raster is mint over a quieter basemap. Mobile keeps navigation and uses A/B labels on a larger canvas. The active site has an accent rule and explicit Editing label. One simulation label covers the comparison group. Breakdown has three columns, 44 px rows, More metrics and no shared measured-zero rows. Vertical exclusion is called Vertical blind area.

The height audit, live benchmark and production timings were regenerated for Sipoonkorpi and Nuuksio. The 600 m default is retained; the zero high-altitude smoke occlusion is expected from the unchanged model, and low-height controls still show strong occlusion. No numbers were invented and no new public caveats were added.

The Overview preview sources were re-exported at the same 1280×800 / 393×852 dimensions and filenames. Overview templates, scripts and styles were not edited during this polish round. Evidence screenshots are under `/private/tmp/claude-501/-Users-yamandevrim--t3-projects-junction/2d00c443-8aa2-4c2c-af46-792d4247fcf0/scratchpad/overview/round2-map/`.
