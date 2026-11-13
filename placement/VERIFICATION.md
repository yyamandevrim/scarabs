# Verification report

Run on 2026-11-13 on this Mac. **36 pytest tests passed; zero failed or skipped.** One upstream Starlette/httpx deprecation warning. Real data preparation completed, live server/API calls completed, and browser/resource checks completed.

All area figures below are **simulated hectares**, not optical detection range. Baseline: **left + centre active**, yaw −70°/0°/+70°, tilt 10° down, HFOV 80°, VFOV 50°, range 12 km, smoke target 50 m above canopy. Coast: Haukilahti, lat 60.159/lon 24.773, heading 180°. Inland: Nuuksio, lat 60.293/lon 24.557, heading 20°. No priority polygon in these tables.

## Canopy-obstructed smoke target

| Resolution | Preset | AGL m | Visible forest (simulation ha) | Blind forest (simulation ha) | ≥2 camera forest (simulation ha) | Water view (simulation ha) | Water share (simulation %) | Compute s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| coarse (120 m) | Kıyı · Haukilahti | 500 | 770.92 | 7,333.88 | 5.84 | 15,715.56 | 83.63 | 0.058 |
| coarse (120 m) | Kıyı · Haukilahti | 600 | 769.56 | 7,335.24 | 5.88 | 15,713.48 | 83.66 | 0.074 |
| coarse (120 m) | Kıyı · Haukilahti | 700 | 770.32 | 7,334.48 | 5.88 | 15,704.16 | 83.66 | 0.063 |
| coarse (120 m) | İç kesim · Nuuksio | 500 | 12,519.76 | 14,414.44 | 826.64 | 1,361.36 | 7.25 | 0.059 |
| coarse (120 m) | İç kesim · Nuuksio | 600 | 12,523.56 | 14,410.64 | 843.76 | 1,357.28 | 7.23 | 0.059 |
| coarse (120 m) | İç kesim · Nuuksio | 700 | 12,518.04 | 14,416.16 | 860.64 | 1,362.44 | 7.25 | 0.057 |
| detailed (40 m) | Kıyı · Haukilahti | 500 | 771.84 | 7,333.76 | 6.08 | 15,719.24 | 83.64 | 0.490 |
| detailed (40 m) | Kıyı · Haukilahti | 600 | 771.12 | 7,334.48 | 6.24 | 15,711.00 | 83.64 | 0.492 |
| detailed (40 m) | Kıyı · Haukilahti | 700 | 771.92 | 7,333.68 | 6.40 | 15,702.64 | 83.66 | 0.396 |
| detailed (40 m) | İç kesim · Nuuksio | 500 | 12,514.04 | 14,429.80 | 827.24 | 1,358.00 | 7.25 | 0.401 |
| detailed (40 m) | İç kesim · Nuuksio | 600 | 12,511.80 | 14,432.04 | 845.32 | 1,360.28 | 7.25 | 0.409 |
| detailed (40 m) | İç kesim · Nuuksio | 700 | 12,502.88 | 14,440.96 | 859.12 | 1,362.88 | 7.26 | 0.399 |

Compute timings include pair/reference metrics, heading sensitivity and four warped overlay PNGs; exclude data preparation and cold JIT compile. `--fresh` recomputes in the engine and then verifies the result through the running HTTP API. Exact HTTP response times and all values are in `benchmark-results.json`.

## Ground and all-three reference

All values are simulation ha. Opaque canopy includes the target cell, so a forest floor covered by canopy is blocked. Bare terrain is a separate scenario, not a measured canopy-free condition.

| Resolution | Preset | AGL m | Bare-ground visible forest | Canopy-ground visible forest | Three-camera smoke reference |
| --- | --- | ---: | ---: | ---: | ---: |
| coarse | Kıyı · Haukilahti | 500 | 764.52 | 0.00 | 3,087.44 |
| coarse | Kıyı · Haukilahti | 600 | 766.44 | 0.00 | 3,083.08 |
| coarse | Kıyı · Haukilahti | 700 | 770.44 | 0.00 | 3,079.72 |
| coarse | İç kesim · Nuuksio | 500 | 10,836.68 | 0.04 | 17,320.60 |
| coarse | İç kesim · Nuuksio | 600 | 11,308.12 | 0.04 | 17,309.76 |
| coarse | İç kesim · Nuuksio | 700 | 11,587.32 | 0.04 | 17,278.56 |
| detailed | Kıyı · Haukilahti | 500 | 731.64 | 0.00 | 3,092.40 |
| detailed | Kıyı · Haukilahti | 600 | 748.44 | 0.00 | 3,088.80 |
| detailed | Kıyı · Haukilahti | 700 | 757.32 | 0.00 | 3,086.80 |
| detailed | İç kesim · Nuuksio | 500 | 8,733.36 | 0.00 | 17,315.64 |
| detailed | İç kesim · Nuuksio | 600 | 9,422.16 | 0.04 | 17,298.84 |
| detailed | İç kesim · Nuuksio | 700 | 9,964.64 | 0.04 | 17,273.28 |

## Pair comparison (detailed 40 m)

Each cell shows **visible forest / overlap forest, simulation ha**. Left+right has zero overlap at these defaults, leaving a central gap. Other FOV/tilt inputs are recomputed geometrically.

| Preset | AGL m | Left + centre | Centre + right | Left + right |
| --- | ---: | ---: | ---: | ---: |
| Kıyı · Haukilahti | 500 | 771.84 / 6.08 | 2,784.40 / 218.08 | 2,852.72 / 0.00 |
| Kıyı · Haukilahti | 600 | 771.12 / 6.24 | 2,784.16 / 222.12 | 2,850.68 / 0.00 |
| Kıyı · Haukilahti | 700 | 771.92 / 6.40 | 2,782.96 / 225.88 | 2,851.00 / 0.00 |
| İç kesim · Nuuksio | 500 | 12,514.04 / 827.24 | 11,437.32 / 950.56 | 12,457.72 / 0.00 |
| İç kesim · Nuuksio | 600 | 12,511.80 / 845.32 | 11,430.32 / 965.28 | 12,466.16 / 0.00 |
| İç kesim · Nuuksio | 700 | 12,502.88 / 859.12 | 11,413.52 / 977.64 | 12,466.92 / 0.00 |

## Heading sensitivity at 600 m (detailed 40 m)

Canopy-obstructed smoke target, current connected left+centre only, simulation ha.

| Preset | −20° | −10° | 0° | +10° | +20° |
| --- | ---: | ---: | ---: | ---: | ---: |
| Kıyı · Haukilahti | 899.16 | 757.24 | 771.12 | 1,039.16 | 1,326.44 |
| İç kesim · Nuuksio | 12,208.24 | 12,223.36 | 12,511.80 | 12,551.56 | 12,504.60 |

## Data and uncertainty

- Real: NLS 10 m DEM (2019 public archive), Syke CORINE 2024 20 m, Luke MS-NFI 2023 numeric height and cover (16 m). No Copernicus fallback needed. All acquired 2026-11-13 under CC BY 4.0. Source URLs/licences are in README and cached metadata.
- Assumed: 20 m opaque canopy on the 5.47% of CORINE forest cells missing valid Luke values. Positive canopy cover is treated as fully opaque; the numeric stand mean is an estimated obstruction, not a measured maximum crown surface.
- Missing: real building heights. Road access, shadow, site constraints and permissions remain field checks.
- Browser actions exercised: initial map/presets, heading 180°→0°, pair switch left+right, a three-corner priority polygon and updated priority hectares. All inspected resource URLs were same-origin localhost; no external requests. A fresh-engine test blocks socket connections.
- Not physically tested: Wi-Fi disconnected, outdoor balloon/camera operation, true smoke detection, newer local NLS import, optional real building-height import, fully assumed-canopy preparation, Python versions other than 3.12, other operating systems.
- Source and prepared raster data are cached under ignored `data/`; the small benchmark JSON and this report are intended for version control. No git state-changing commands were run.
