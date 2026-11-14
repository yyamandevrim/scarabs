# Launch map — review round two

The GPT and Opus map sections were read in full. This pass addresses their map findings; the Overview agent owns its renderer, templates, scripts, styles and other media. No score is claimed without a new independent review.

| Finding | Resolution |
| --- | --- |
| GPT 1 / Opus 1 — preserve the useful comparison and mint subject | Two aligned site totals, one verdict and the per-camera bars remain primary. The default sites change as requested by Opus 3, so the real comparison is now ≈19,460 vs ≈26,850 simulated ha (1.4×), rather than the previous coast/inland contrast. |
| GPT 2 — basemap competes with coverage | Basemap display uses 35% saturation, 85% contrast, 32% brightness, 60% opacity and 0.6 px blur. Visibility has 85% layer opacity and the selected outline remains 1.5 px white. This is display styling only: masks, areas and data colours are unchanged. |
| GPT 3 / Opus 5 — phone labels and missing navigation | Below 480 px, the map shows site labels rather than camera/place labels. Camera names, bearings and bars remain in the panel. Overview and Launch map remain in the 48 px header with at least 44 px targets. |
| GPT 4 — editing state too weak | A 2 px accent rule selects the comparison column; the height block explicitly says “Editing A/B · site”. |
| GPT 5 — dense phone Breakdown | Three columns (Metric / A / B), units inside metric labels, 12 px values and 44 px rows. Secondary geometry, ground, priority and camera rows are in closed More metrics. |
| Opus 2 — repeated zero occlusion/ground rows | Rows which display measured zero at both sites are omitted. Missing or unknown values stay “—”; a DOM regression checks this distinction. Accounting legends omit zero segments, and the map's occlusion key appears only when the selected scenario has occluded forest. The 600 m default and all computations stay unchanged. Low-height controls still show large real occlusion in the regenerated audit. |
| Opus 3 — coast spends the first view over water | Default A is Sipoonkorpi (60.320, 25.190), B is Nuuksio (60.293, 24.557). Both are inland: water share is 5.701% and 8.161%, rather than 43% for the retired coast default. No simulated land-cover values were invented or relabelled. |
| Opus 4 — camera directions disagree with Overview | Both presets now use heading 0°. Camera 1 points grid north; Cameras 2/3 are 120°/240°. Panel rows show the actual bearings returned by the analysis. |
| Opus 5 — short map and repeated chips | Phone canvas is at least 400 px high, with an automatically measured compact legend. A single Simulated marker labels the comparison heading; per-site and verdict chips are removed. Height/detail controls and camera bars remain. |
| Owner — misleading Outside FOV category | The existing vertical exclusion metric is named Vertical blind area in the UI. The horizontal model stays 360°. No metric was reclassified or changed. |
| Owner — secondary ring looks broken | One continuous muted outer perimeter replaces the dashed, seamed secondary sectors. Both rings fit completely in the desktop default; only the selected site has a visibility raster. The secondary key is hidden when its marker is off-screen. Quarter-step zoom avoids clipping the two inland sites. |

## Evidence

`map-polish-verification.json` records the 13 desktop/phone browser states, language/overflow checks, real preset metrics and preview asset sizes. Screenshots are under:

`/private/tmp/claude-501/-Users-yamandevrim--t3-projects-junction/2d00c443-8aa2-4c2c-af46-792d4247fcf0/scratchpad/overview/round2-map/`

Desktop is 1440×900; phone is 393×852. The default, site B, 100 m height, Breakdown, More metrics, Data and scrolled phone comparison were inspected against the findings. English is forced despite old Turkish storage and URL parameters; no console errors, external requests or failed responses occurred.

The engine/core/LOS/raster algorithm remains v8. Only the Python preset locations/headings changed, so the main 18787 process must restart after integration. The prepared-data symlink remains read-only, with a separate results cache. Audit, live API benchmarks and production timings were regenerated for the new presets.

The Overview sources `static/demo/map-360-desktop.webp` and `map-360-phone.webp` are re-exported as WebP quality 78 / method 6 at the same 1280×800 and 393×852 dimensions. No Overview code or layout change is required. Their current sizes are in the verification JSON. The original owner-approved claims list is unchanged; no public disclaimers or accuracy claims were added.
