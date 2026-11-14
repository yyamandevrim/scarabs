# Verification report — public dynamic site and blind-forest audit

Verified 2026-11-13 on this Apple M5 Mac, Python 3.12.10. **83 pytest tests pass** (74 placement + 9 artifact tests), zero failed/skipped. The original 36 remain included. One upstream Starlette/httpx deprecation warning remains. The browser assertion script separately checks both rendered languages on landing and map at desktop and phone widths.

## Finding: height insensitivity is real in this geometric scenario

No LOS/height defect was found. The former blind total mixed forest outside the active camera frusta with forest hidden along sightlines inside them. With the default smoke target 50 m above the obstruction surface, 500–700 m observers look down over most intermediate terrain/canopy. Low-height controls produce large occlusion, particularly in inland Nuuksio. At 100 m, coast smoke occlusion is already zero; a claim that both low heights must be strongly occluded everywhere would be incorrect.

The small 500–700 m differences mostly reflect target points crossing the tilted 3D frustum boundaries, plus raster sampling. Raising the observer shifts vertical and horizontal frustum coordinates; it does not guarantee a larger fixed-camera footprint. This result is specific to the elevated smoke-point scenario, not a general claim about forest-floor visibility or optical smoke detection. Bare-ground results show considerably stronger height sensitivity.

Baseline: left + centre active; offsets −70°/0°/+70°, tilt 10° down, HFOV 80°, VFOV 50°, range 12 km, smoke 50 m above canopy. Coast: 60.159 / 24.773, heading 180°. Inland: 60.293 / 24.557, heading 20°. All area values below are **simulated hectares**. No priority polygon; range disks clipped only to the prepared rectangle.

`blind_forest_ha = outside_fov_forest_ha + occluded_forest_ha` (rounding ±0.003 ha). FOV is the union of the active full 3D frusta, before applying LOS. Each forest fraction is counted once. The split is scenario-specific and present for all pairs, reference and heading sensitivities. Unknown-elevation forest is zero in these prepared grids. For other datasets, unknown rays remain unverified rather than proven occlusion and trigger the existing explicit warning.

## Interface finding: blind total beside two zero parts

A design review saw a 7,335 ha blind total next to 0 outside FOV and 0 occluded. The engine always returns the split (`blind = outside + occluded`, checked for every scenario, pair, reference and heading). The screen came from a mixed version: a long-running server predating the split, a newer page, and a formatter that turned missing values into 0 (`value??0`). The coast value itself is real: 7,334.48 ha outside FOV + 0.00 ha occluded. The map now renders any missing or inconsistent part as “—” (not computed), rounds parts before adding so the displayed sum is exact, and versions every static asset so a browser cannot mix old and new files. Regression tests: `tests/ui_metrics.cjs`, `tests/test_ui_metrics.py`.

## Canopy-obstructed smoke: detailed 40 m

| Preset | AGL m | Visible | Outside active FOV | Occluded inside FOV | Blind total |
| --- | ---: | ---: | ---: | ---: | ---: |
| Coast · Haukilahti | 30 | 491.36 | 7,346.68 | 267.56 | 7,614.24 |
| Coast · Haukilahti | 100 | 762.40 | 7,343.20 | 0.00 | 7,343.20 |
| Coast · Haukilahti | 500 | 771.84 | 7,333.76 | 0.00 | 7,333.76 |
| Coast · Haukilahti | 600 | 771.12 | 7,334.48 | 0.00 | 7,334.48 |
| Coast · Haukilahti | 700 | 771.92 | 7,333.68 | 0.00 | 7,333.68 |
| Inland · Nuuksio | 30 | 1,762.88 | 14,491.68 | 10,689.28 | 25,180.96 |
| Inland · Nuuksio | 100 | 12,347.16 | 14,476.24 | 120.44 | 14,596.68 |
| Inland · Nuuksio | 500 | 12,514.04 | 14,429.16 | 0.64 | 14,429.80 |
| Inland · Nuuksio | 600 | 12,511.80 | 14,431.68 | 0.36 | 14,432.04 |
| Inland · Nuuksio | 700 | 12,502.88 | 14,440.64 | 0.32 | 14,440.96 |

## Canopy-obstructed smoke: coarse 120 m

| Preset | AGL m | Visible | Outside active FOV | Occluded inside FOV | Blind total |
| --- | ---: | ---: | ---: | ---: | ---: |
| Coast · Haukilahti | 30 | 455.76 | 7,346.88 | 302.16 | 7,649.04 |
| Coast · Haukilahti | 100 | 760.68 | 7,344.12 | 0.00 | 7,344.12 |
| Coast · Haukilahti | 500 | 770.92 | 7,333.88 | 0.00 | 7,333.88 |
| Coast · Haukilahti | 600 | 769.56 | 7,335.24 | 0.00 | 7,335.24 |
| Coast · Haukilahti | 700 | 770.32 | 7,334.48 | 0.00 | 7,334.48 |
| Inland · Nuuksio | 30 | 1,695.16 | 14,488.68 | 10,750.36 | 25,239.04 |
| Inland · Nuuksio | 100 | 12,408.32 | 14,481.68 | 44.20 | 14,525.88 |
| Inland · Nuuksio | 500 | 12,519.76 | 14,414.44 | 0.00 | 14,414.44 |
| Inland · Nuuksio | 600 | 12,523.56 | 14,410.64 | 0.00 | 14,410.64 |
| Inland · Nuuksio | 700 | 12,518.04 | 14,416.16 | 0.00 | 14,416.16 |

## Ground-height control (detailed 40 m, simulation ha)

| Preset | AGL m | Bare-ground visible | Canopy-ground visible |
| --- | ---: | ---: | ---: |
| Coast · Haukilahti | 30 | 263.52 | 0.00 |
| Coast · Haukilahti | 100 | 436.28 | 0.00 |
| Coast · Haukilahti | 500 | 731.64 | 0.00 |
| Coast · Haukilahti | 600 | 748.44 | 0.00 |
| Coast · Haukilahti | 700 | 757.32 | 0.00 |
| Inland · Nuuksio | 30 | 173.76 | 0.00 |
| Inland · Nuuksio | 100 | 2,543.96 | 0.00 |
| Inland · Nuuksio | 500 | 8,733.36 | 0.00 |
| Inland · Nuuksio | 600 | 9,422.16 | 0.04 |
| Inland · Nuuksio | 700 | 9,964.64 | 0.04 |

## All pairs at 600 m (detailed 40 m, simulation ha)

| Preset | Pair | Visible | Outside FOV | Occluded inside FOV | Overlap |
| --- | --- | ---: | ---: | ---: | ---: |
| Coast · Haukilahti | Left + centre | 771.12 | 7,334.48 | 0.00 | 6.24 |
| Coast · Haukilahti | Centre + right | 2,784.16 | 5,321.44 | 0.00 | 222.12 |
| Coast · Haukilahti | Left + right | 2,850.68 | 5,254.92 | 0.00 | 0.00 |
| Inland · Nuuksio | Left + centre | 12,511.80 | 14,431.68 | 0.36 | 845.32 |
| Inland · Nuuksio | Centre + right | 11,430.32 | 15,513.16 | 0.36 | 965.28 |
| Inland · Nuuksio | Left + right | 12,466.16 | 14,477.68 | 0.00 | 0.00 |

## Implementation and checks

- Landing at `/`, live bilingual map at `/map`; config-driven project name/tagline/logos and team credit. English default, Turkish toggle with persistent choice. No station-feed proxy or fabricated panel screenshot.
- Blind split and distinct grey/rust overlays; all existing scenario, pair, reference, priority and heading functionality retained. The numeric algorithm did not need a height fix. Numba releases the GIL; warm-up compiles the strided production signature, with numeric normalization to avoid request-time specialization.
- API caps, 12/client/min and 60/global/min budgets, single concurrent analysis, bounded result cache, request body limits, finite inputs, polygon validation and explicit file routes. Tests cover rejection paths and original real-data outputs.
- Modal SDK 1.6.4 app import and CLI help pass offline. The same ASGI app was started in production mode locally. Volume read-only mount, scale-to-zero and image build steps are declared but not cloud-executed.
- Browser: 1280×800 and 390×844 CSS viewports; landing→map, live click at land locations, pair selection including zero-overlap left+right, both languages and persistence across navigation. No horizontal page overflow, inspected console errors or external resource requests. Layer controls collapse on phones to avoid legend overlap.
- Artifact scripts: only dry-run executed; 13 artifacts, 112,267,118 bytes plus manifest. SHA-256/size/provenance recorded. Fog excluded for unresolved licence review; smoke+cloud alternative config supplied in tools/ without changing station/.

## Local production timings

Fresh process with empty generic JIT cache: **0.6159 s** to HTTP readiness. With populated cache: **0.4124 s**. Startup includes module import, warm-up and loading both prepared grids. Fresh HTTP analysis: **59.8–81.4 ms coarse**, **398.1–450.7 ms detailed**. Repeated identical requests: **1.4–1.9 ms**. No new Numba signature appeared after warm-up on first coarse/detailed analysis. These are Mac measurements, exclude image installation/data upload, and are not Modal/Linux/cold-network timings. Samples in [production-timings.json](production-timings.json).

## Reproduce

```sh
uv run pytest -q tests ../tools/tests
uv run python scripts/blind_audit.py
uv run python scripts/production_benchmark.py
uv run python scripts/write_report.py
```

Full scenario/pair/reference/sensitivity values: [blind-audit.json](blind-audit.json). Earlier live-verified 500–700 m benchmark remains in [benchmark-results.json](benchmark-results.json) as a historical baseline. Updated split chart: [comparison-chart.html](comparison-chart.html).

## Not verified, omitted or intentionally provisional

- No Modal account access, Linux image build, deployment, Volume upload, public IP forwarding test, scale-to-zero/resume or cloud latency measurement. Owner commands are in [DEPLOYMENT.md](DEPLOYMENT.md).
- No IronShard upload/download, endpoint compatibility or judge bucket-read policy tested. AGPL model licence and upstream editable-weight/training-source links provided; a complete corresponding-source archive was not independently audited. Fog is deliberately excluded pending provenance review.
- The name is ACORN; supplied wordmark and stacked artwork are configured in `brand.json` and bundled locally in `static/brand/`. Roadmap mission modes are proposed, not implemented.
- Existing physical limits remain: no USB/tether/field validation of this placement model (the station’s recorded-clip/MCU/KY-026/on-board LED run on a real UNO Q is separate); no optical detection range, weather, calibration or smoke dynamics. No building heights; 5.47% of forest canopy values assumed; real NLS 2019 / CORINE 2024 / Luke 2023 vintages differ. No ecological impact quantities are claimed.
- Station code, root README and root .gitignore were not edited. No git state-changing commands were run. No physical Wi-Fi-disconnection test. Station screenshots were optional and were not added.
