# Verification report — 360° launch map

Verified 2026-11-14 on macOS, Python 3.12.10. **83 placement pytest tests pass**, zero failed/skipped. One upstream Starlette/httpx deprecation warning remains. The suite includes Node presentation and DOM request-sequencing checks. Playwright uses the locally cached Chromium 1255; its npm packages were installed in a temporary directory outside the repo.

## Current model

Three simultaneously active cameras on the faces of a triangular housing, yaw **0° / 120° / 240°**. Each camera is modelled as a **120° horizontal sector by product decision**, not a measured lens calibration. Half-open seams give every eligible azimuth exactly one camera. Common tilt and VFOV are evaluated in the radial vertical plane: heading rotates ownership without changing the union. The old rectilinear horizontal/vertical coupling, forward fan, pair/reference modes and heading sensitivity are superseded. Terrain/canopy LOS, target heights, curvature and raster weighting are unchanged.

Cache algorithm: `opaque-ray-half-cell-v8-360-sectors-en`. Tests reject old v7 cache entries and retired public camera modes. Default geometry is 600 m AGL, 10° down, 50° VFOV, 12 km maximum range and smoke 50 m above the local canopy/surface. Coast: 60.159 / 24.773, seam heading 180°; inland: 60.293 / 24.557, seam heading 20°. No priority polygon.

The annular guides solve the vertical boundaries, including curvature, on a level target plane through the launch cell. The inner blind disc is not filled by a camera wedge. Actual visibility masks use the local terrain/canopy target at every cell. Steeper settings can also reduce the outer guide radius below maximum range.

## Default sanity check against the retired three-camera reference

All values below are **simulated hectares** at 600 m. Historical values were read from the pre-change committed blind-audit.json before regeneration. The old reference used yaw −70°/0°/+70° and 80° rectilinear HFOV (nominal ~220° horizontal union; the task calls it the ~210° fan).

| Site | Grid | Old all-camera fan | New full circle |
| --- | ---: | ---: | ---: |
| Haukilahti | 120 m | 3,083.08 | 8,072.24 |
| Nuuksio | 120 m | 17,309.76 | 26,849.84 |
| Haukilahti | 40 m | 3,088.80 | 8,072.92 |
| Nuuksio | 40 m | 17,298.84 | 26,856.96 |

Both sites increase. Default quick headlines round to ≈8,070 and ≈26,850 simulated ha; water share is 43% and 8%. The 360° model still has a vertical blind disc, terrain/canopy occlusion and raster sampling effects. A larger height can reduce visible forest because the inner blind region grows; no monotonic-height claim is made.

## Height audit

`blind_forest_ha = outside_fov_forest_ha + occluded_forest_ha` within rounding ±0.003 ha. Each forest fraction is counted once; camera forest areas sum to the union within rounding. Overlap is zero. Outside FOV is vertical exclusion; low-height occlusion remains substantial. Unknown-elevation rays remain blind and the candid API uncertainty metadata is retained.

### Coarse canopy-smoke scenario

| Site | AGL m | Visible | Outside vertical FOV | Occluded | Blind total |
| --- | ---: | ---: | ---: | ---: | ---: |
| Coast · Haukilahti | 30 | 3,229.36 | 0.92 | 4,874.52 | 4,875.44 |
| Coast · Haukilahti | 100 | 8,100.56 | 0.12 | 4.12 | 4.24 |
| Coast · Haukilahti | 500 | 8,083.68 | 21.12 | 0.00 | 21.12 |
| Coast · Haukilahti | 600 | 8,072.24 | 32.56 | 0.00 | 32.56 |
| Coast · Haukilahti | 700 | 8,064.68 | 40.12 | 0.00 | 40.12 |
| Inland · Nuuksio | 30 | 5,319.20 | 0.64 | 21,614.36 | 21,615.00 |
| Inland · Nuuksio | 100 | 26,889.28 | 0.08 | 44.84 | 44.92 |
| Inland · Nuuksio | 500 | 26,885.76 | 48.44 | 0.00 | 48.44 |
| Inland · Nuuksio | 600 | 26,849.84 | 84.36 | 0.00 | 84.36 |
| Inland · Nuuksio | 700 | 26,792.68 | 141.52 | 0.00 | 141.52 |

### Detailed canopy-smoke scenario

| Site | AGL m | Visible | Outside vertical FOV | Occluded | Blind total |
| --- | ---: | ---: | ---: | ---: | ---: |
| Coast · Haukilahti | 30 | 4,544.32 | 0.68 | 3,560.60 | 3,561.28 |
| Coast · Haukilahti | 100 | 8,098.36 | 0.00 | 7.24 | 7.24 |
| Coast · Haukilahti | 500 | 8,084.20 | 21.36 | 0.04 | 21.40 |
| Coast · Haukilahti | 600 | 8,072.92 | 32.68 | 0.00 | 32.68 |
| Coast · Haukilahti | 700 | 8,064.52 | 41.08 | 0.00 | 41.08 |
| Inland · Nuuksio | 30 | 4,931.28 | 1.08 | 22,011.48 | 22,012.56 |
| Inland · Nuuksio | 100 | 26,815.40 | 0.20 | 128.24 | 128.44 |
| Inland · Nuuksio | 500 | 26,894.44 | 48.76 | 0.64 | 49.40 |
| Inland · Nuuksio | 600 | 26,856.96 | 86.52 | 0.36 | 86.88 |
| Inland · Nuuksio | 700 | 26,802.32 | 141.20 | 0.32 | 141.52 |

## UI and browser verification

- Compare: site A/B totals and verdict; selected-site height and detail; three per-camera forest bars. Shared tilt/VFOV, position, range and smoke height are in a disclosure. Breakdown includes scenario accounting and camera rows. Data keeps real data provenance, assumed-canopy percentage and CC BY 4.0 attribution.
- English is forced in the shared loader, saved preference is reset to en, dictionary loading is removed, and language controls are removed. URL language parameters do not affect rendering. The server strips the legacy Overview toggle without modifying its template.
- Playwright checks 1440×900 default, Breakdown, Data, site B, 100 m height, and 393×852 top/scrolled and each tab. All captures were visually inspected; the full ring, inner blind boundary, sector labels, balanced dock and mobile overflow were checked. Secondary place labels yield to camera/site labels. Zero console errors and external requests.
- `scripts/check_language.js` passes at every captured state after seeding localStorage language=tr and requesting ?lang=tr&language=tr. Tests include no obsolete pair/disconnected copy.
- Evidence: `browser-verification.json`; screenshots under `/private/tmp/claude-501/-Users-yamandevrim--t3-projects-junction/2d00c443-8aa2-4c2c-af46-792d4247fcf0/scratchpad/overview/map/`. Clean Overview capture: `map-preview-1440.png`. The owner copy review is one level up at `claims-for-owner-map.md`.
- Historical public browser evidence is explicitly marked superseded in `public-browser-verification.json`. No deployment was performed. The other agent owns the rebuilt Overview template/scripts/styles; its integration must supply the updated landing copy and preview.

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

Only this worktree uses the prepared-data symlink; writes go to its own results cache. The main server on 18787 and main checkout data were left alone. Overview-owned landing.html, landing.js and site.css were not changed. Shared integration points changed here: i18n.js and forest_placement/api.py. tokens.css and shell.js were not changed.
