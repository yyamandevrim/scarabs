"""Regenerate current 360° engineering verification tables and local height chart."""
import json
from pathlib import Path
from html import escape

root=Path(__file__).resolve().parents[1]
rows=json.loads((root/'blind-audit.json').read_text())
algorithm=rows[0]['algorithm']
lines=['# Verification report — 360° launch map and Overview','',
'Verified 2026-11-14 on macOS, Python 3.12.10. **85 placement pytest tests pass**, zero failed/skipped. One upstream Starlette/httpx deprecation warning remains. The suite includes Node presentation and DOM request-sequencing checks. Playwright uses the locally cached Chromium 1255; its npm packages were installed in a temporary directory outside the repo.','',
'## Current model','',
'Three simultaneously active cameras on the faces of a triangular housing, yaw **0° / 120° / 240°**. Each camera is modelled as a **120° horizontal sector by product decision**, not a measured lens calibration. Half-open seams give every eligible azimuth exactly one camera. Common tilt and VFOV are evaluated in the radial vertical plane: heading rotates ownership without changing the union. The old rectilinear horizontal/vertical coupling, forward fan, pair/reference modes and heading sensitivity are superseded. Terrain/canopy LOS, target heights, curvature and raster weighting are unchanged.','',
f'Cache algorithm: `{algorithm}`. Tests reject old v7 cache entries and retired public camera modes. Default geometry is 600 m AGL, 10° down, 50° VFOV, 12 km maximum range and smoke 50 m above the local canopy/surface. Default A is Sipoonkorpi at 60.320 / 25.190; B is Nuuksio at 60.293 / 24.557. Both use heading 0°. No priority polygon.','',
'The annular guides solve the vertical boundaries, including curvature, on a level target plane through the launch cell. The inner blind disc is not filled by a camera wedge. Actual visibility masks use the local terrain/canopy target at every cell. Steeper settings can also reduce the outer guide radius below maximum range.','',
'## Historical sanity check against the retired three-camera reference','',
'All values below are **simulated hectares** at 600 m. Historical values were read from the pre-change committed blind-audit.json before regeneration. The old reference used yaw −70°/0°/+70° and 80° rectilinear HFOV (nominal ~220° horizontal union; the task calls it the ~210° fan).','',
'| Site | Grid | Old all-camera fan | New full circle |','| --- | ---: | ---: | ---: |',
'| Haukilahti | 120 m | 3,083.08 | 8,072.24 |',
'| Nuuksio | 120 m | 17,309.76 | 26,849.84 |',
'| Haukilahti | 40 m | 3,088.80 | 8,072.92 |',
'| Nuuksio | 40 m | 17,298.84 | 26,856.96 |','',
'Both historical sites increase. The round-two defaults are Sipoonkorpi (≈19,460 simulated ha; 6% water) and Nuuksio (≈26,850 simulated ha; 8% water). The 360° model still has a vertical blind disc, terrain/canopy occlusion and raster sampling effects. A larger height can reduce visible forest because the inner blind region grows; no monotonic-height claim is made.','',
'## Height audit','',
'`blind_forest_ha = outside_fov_forest_ha + occluded_forest_ha` within rounding ±0.003 ha. Each forest fraction is counted once; camera forest areas sum to the union within rounding. Overlap is zero. Outside FOV is vertical exclusion; low-height occlusion remains substantial. Unknown-elevation rays remain blind and the candid API uncertainty metadata is retained.','']
for resolution in ('coarse','detailed'):
    lines += [f'### {resolution.title()} canopy-smoke scenario','',
    '| Site | AGL m | Visible | Outside vertical FOV | Occluded | Blind total |',
    '| --- | ---: | ---: | ---: | ---: | ---: |']
    for row in rows:
        if row['resolution']!=resolution:continue
        m=row['metrics']['canopy_smoke']
        lines.append(f"| {row['preset']} | {row['height']} | {m['visible_forest_ha']:,.2f} | {m['outside_fov_forest_ha']:,.2f} | {m['occluded_forest_ha']:,.2f} | {m['blind_forest_ha']:,.2f} |")
    lines.append('')
lines += ['## UI and browser verification','',
'- Compare: site A/B totals and verdict; selected-site height and detail; three per-camera forest bars. Shared tilt/VFOV, position, range and smoke height are in a disclosure. Breakdown includes scenario accounting and camera rows. Data keeps real data provenance, assumed-canopy percentage and CC BY 4.0 attribution.','- English is forced in the shared loader, saved preference is reset to en, dictionary loading is removed, and language controls are removed. URL language parameters do not affect rendering. Overview and map templates have no language control; the server also strips any legacy toggle.','- Playwright checks 1440×900 default, Breakdown, Data, site B, 100 m height, and 393×852 top/scrolled and each tab. All captures were visually inspected; the full ring, inner blind boundary, sector labels, balanced dock and mobile overflow were checked. Secondary place labels yield to camera/site labels. Zero console errors and external requests.','- `scripts/check_language.js` passes at every captured state after seeding localStorage language=tr and requesting ?lang=tr&language=tr. Tests include no obsolete pair/disconnected copy.','- Evidence: `browser-verification.json`; screenshots under `local-scratch/overview/map/`. Clean Overview capture: `map-preview-1440.png`. The owner copy review is one level up at `claims-for-owner-map.md`.','- Historical public browser evidence is explicitly marked superseded in `public-browser-verification.json`. No cloud deployment was performed. Overview and map are now integrated, and the Overview map section uses responsive captures of the 360° default view.','',
'## Reproduce','',
'```sh','uv run --offline --frozen pytest','uv run --offline --frozen python scripts/blind_audit.py','uv run --offline --frozen python scripts/benchmark.py --url http://127.0.0.1:56232 --fresh','uv run --offline --frozen python scripts/production_benchmark.py','uv run --offline --frozen python scripts/write_report.py','```','',
'`blind-audit.json` has 20 current analyses (2 sites × 5 heights × 2 grids), including every scenario and per-camera breakdown. `benchmark-results.json` contains the fresh-engine/live-HTTP verification at 500/600/700 m. `production-timings.json` was regenerated against this model, in isolated temporary caches. Timing measurements are local Mac observations, not cloud/cold-network measurements. `comparison-chart.html` is regenerated from the current audit.','',
'## Engineering limitations and ownership','',
'No measured lens calibration, field detection accuracy, smoke transport, weather, refraction or balloon/tether motion model. No building-height dataset; positive canopy cover is opaque, Luke mean height is not maximum treetop height, 5.47% of forest cells use assumed 20 m canopy, and raster years differ (NLS 2019 / CORINE 2024 / Luke 2023). Land launch validation is approximate; permission/access/tether suitability remain field checks. No physical Wi-Fi-off test or cloud deployment was performed. Investor-facing limitations text removed from the map is recorded verbatim for the owner; no replacement accuracy/range claims were added.','',
'Integration combines the Overview renderer, link/Wi-Fi demos, English-only brand hydration and root-only WebAssembly CSP with the 360° map. The landing map section has a real responsive WebP preview and height-based copy. Its layout and all other Overview sections are retained. Prepared rasters are read-only in this worktree; analyses write only its own results cache. The approved claims list remains in the owner scratch directory. tokens.css and shell.js are unchanged.','']
evidence=root/'merged-browser-verification.json'
if evidence.exists():
    checks=json.loads(evidence.read_text())
    overview=checks['overview']
    lines += ['## Merged Overview acceptance','',
        'The complete `scripts/check_overview.mjs` interaction suite was rerun after integration. It retains the Overview agent’s WebGL, CAD selection, all-camera view, assembly, packet codec, LoRa/evidence, video, touch/scroll, fallback/context recovery and idle-render checks. The page-specific language/title assertions and map obsolete-copy assertions are combined in `scripts/check_language.js`.', '',
        f"Measured initial transfer: **{overview['initialTransferredBytes']:,} B**; full scroll + phone walkthrough: **{overview['fullPageTransferredBytes']:,} B**. The previous full-scroll baseline was 1,184,230 B. The increase is **{overview['fullPageTransferredBytes']-1184230:,} B**, within the requested ~150 KB budget. These CDP development-server measurements include HTTP headers and exclude later explicit evidence collection.", '',
        'Initial integration preview assets (superseded by the round-two refresh): desktop 1280×800 / 119,632 B; phone 393×852 / 41,208 B; WebP quality 78, method 6. Only the matching responsive source loads, lazily, with declared dimensions. The retired source was 61,062 B. The map-section layout and style are retained.', '',
        'Fresh `/` and `/map` desktop/393px checks pass with zero console errors, external requests, failed responses or horizontal overflow, and English despite Turkish storage/URL preferences. Screenshots and measurements: `local-scratch/overview/merged/`. Overview implementation/build methods remain documented in `static/vendor/README.md`.', '',
        'Reproduce the full Overview suite from the repository root by copying `placement/scripts/check_overview.mjs` into the temporary npm directory and running `node TEMP/check_overview.mjs BASE_URL CHROMIUM_BINARY SCREENSHOT_DIRECTORY`. It evaluates `check_language.js` in the browser; that file is not a standalone Node CLI.', '']
polish=root/'map-polish-verification.json'
if polish.exists():
    lines += ['## Round-two map polish', '',
        'All compatible map findings from the GPT and Opus reviews were addressed. See `MAP-POLISH.md` for the per-finding decisions and `map-polish-verification.json` for desktop/393px checks and current preset metrics. This is presentation and preset selection only: camera-sector physics, LOS, numeric rasters and algorithm version remain unchanged.', '',
        'The desktop view shows both complete ring perimeters; the selected raster is mint over a quieter basemap. Mobile keeps navigation and uses A/B labels on a larger canvas. The active site has an accent rule and explicit Editing label. One simulation label covers the comparison group. Breakdown has three columns, 44 px rows, More metrics and no shared measured-zero rows. Vertical exclusion is called Vertical blind area.', '',
        'The height audit, live benchmark and production timings were regenerated for Sipoonkorpi and Nuuksio. The 600 m default is retained; the zero high-altitude smoke occlusion is expected from the unchanged model, and low-height controls still show strong occlusion. No numbers were invented and no new public caveats were added.', '',
        'The Overview preview sources were re-exported at the same 1280×800 / 393×852 dimensions and filenames. Overview templates, scripts and styles were not edited during this polish round. Evidence screenshots are under `local-scratch/overview/round2-map/`.', '']
(root/'VERIFICATION.md').write_text('\n'.join(lines))

chart='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>360° simulated forest visibility by height</title><style>
*{box-sizing:border-box}body{margin:0;padding:24px;background:#090e13;color:#e3e9ee;font:14px/1.5 system-ui}h1{font-size:22px}h2{font-size:17px;margin-top:28px}.row{display:grid;grid-template-columns:65px minmax(0,1fr) 100px;gap:10px;align-items:center;margin:12px 0}.bar{display:flex;height:18px;background:#151e27}.bar i{height:100%}.visible{background:#5aefb0}.outside{background:#8f969c}.occluded{background:#b87850}.key{display:flex;gap:20px;flex-wrap:wrap;color:#a7b4bf}.key i{display:inline-block;width:12px;height:12px;margin-right:6px}.ha{text-align:right;font-variant-numeric:tabular-nums}.note{color:#a7b4bf}</style></head><body><h1>Full-circle forest visibility</h1><p class="note">Three active 120° sectors · 40 m grid · 12 km maximum range · all figures simulated ha</p><div class="key"><span><i class="visible"></i>Visible</span><span><i class="outside"></i>Outside vertical FOV</span><span><i class="occluded"></i>Occluded</span></div>'''
selected=[r for r in rows if r['resolution']=='detailed']
for preset in dict.fromkeys(r['preset'] for r in selected):
    chart+=f'<h2>{escape(preset)}</h2>'
    for row in selected:
        if row['preset']!=preset:continue
        m=row['metrics']['canopy_smoke'];total=m['total_forest_ha']
        chart+=f'<div class="row"><span>{row["height"]} m</span><div class="bar">'
        for cls,key in [('visible','visible_forest_ha'),('outside','outside_fov_forest_ha'),('occluded','occluded_forest_ha')]:
            chart+=f'<i class="{cls}" style="width:{100*m[key]/total:.6f}%" title="{key}: {m[key]:,.2f} simulated ha"></i>'
        chart+=f'</div><span class="ha">{m["visible_forest_ha"]:,.2f}</span></div>'
chart+='<p class="note">Height above ground at left; visible forest at right. Hover segments for exact areas.</p></body></html>'
(root/'comparison-chart.html').write_text(chart)
print('Wrote current VERIFICATION.md and comparison-chart.html')
