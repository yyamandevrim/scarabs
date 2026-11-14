"""Regenerate current 360° engineering verification tables and local height chart."""
import json
from pathlib import Path
from html import escape

root=Path(__file__).resolve().parents[1]
rows=json.loads((root/'blind-audit.json').read_text())
algorithm=rows[0]['algorithm']
lines=['# Verification report — 360° launch map','',
'Verified 2026-11-14 on macOS, Python 3.12.10. **83 placement pytest tests pass**, zero failed/skipped. One upstream Starlette/httpx deprecation warning remains. The suite includes Node presentation and DOM request-sequencing checks. Playwright uses the locally cached Chromium 1255; its npm packages were installed in a temporary directory outside the repo.','',
'## Current model','',
'Three simultaneously active cameras on the faces of a triangular housing, yaw **0° / 120° / 240°**. Each camera is modelled as a **120° horizontal sector by product decision**, not a measured lens calibration. Half-open seams give every eligible azimuth exactly one camera. Common tilt and VFOV are evaluated in the radial vertical plane: heading rotates ownership without changing the union. The old rectilinear horizontal/vertical coupling, forward fan, pair/reference modes and heading sensitivity are superseded. Terrain/canopy LOS, target heights, curvature and raster weighting are unchanged.','',
f'Cache algorithm: `{algorithm}`. Tests reject old v7 cache entries and retired public camera modes. Default geometry is 600 m AGL, 10° down, 50° VFOV, 12 km maximum range and smoke 50 m above the local canopy/surface. Coast: 60.159 / 24.773, seam heading 180°; inland: 60.293 / 24.557, seam heading 20°. No priority polygon.','',
'The annular guides solve the vertical boundaries, including curvature, on a level target plane through the launch cell. The inner blind disc is not filled by a camera wedge. Actual visibility masks use the local terrain/canopy target at every cell. Steeper settings can also reduce the outer guide radius below maximum range.','',
'## Default sanity check against the retired three-camera reference','',
'All values below are **simulated hectares** at 600 m. Historical values were read from the pre-change committed blind-audit.json before regeneration. The old reference used yaw −70°/0°/+70° and 80° rectilinear HFOV (nominal ~220° horizontal union; the task calls it the ~210° fan).','',
'| Site | Grid | Old all-camera fan | New full circle |','| --- | ---: | ---: | ---: |',
'| Haukilahti | 120 m | 3,083.08 | 8,072.24 |',
'| Nuuksio | 120 m | 17,309.76 | 26,849.84 |',
'| Haukilahti | 40 m | 3,088.80 | 8,072.92 |',
'| Nuuksio | 40 m | 17,298.84 | 26,856.96 |','',
'Both sites increase. Default quick headlines round to ≈8,070 and ≈26,850 simulated ha; water share is 43% and 8%. The 360° model still has a vertical blind disc, terrain/canopy occlusion and raster sampling effects. A larger height can reduce visible forest because the inner blind region grows; no monotonic-height claim is made.','',
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
'- Compare: site A/B totals and verdict; selected-site height and detail; three per-camera forest bars. Shared tilt/VFOV, position, range and smoke height are in a disclosure. Breakdown includes scenario accounting and camera rows. Data keeps real data provenance, assumed-canopy percentage and CC BY 4.0 attribution.','- English is forced in the shared loader, saved preference is reset to en, dictionary loading is removed, and language controls are removed. URL language parameters do not affect rendering. The server strips the legacy Overview toggle without modifying its template.','- Playwright checks 1440×900 default, Breakdown, Data, site B, 100 m height, and 393×852 top/scrolled and each tab. All captures were visually inspected; the full ring, inner blind boundary, sector labels, balanced dock and mobile overflow were checked. Secondary place labels yield to camera/site labels. Zero console errors and external requests.','- `scripts/check_language.js` passes at every captured state after seeding localStorage language=tr and requesting ?lang=tr&language=tr. Tests include no obsolete pair/disconnected copy.','- Evidence: `browser-verification.json`; screenshots under `/private/tmp/claude-501/-Users-yamandevrim--t3-projects-junction/2d00c443-8aa2-4c2c-af46-792d4247fcf0/scratchpad/overview/map/`. Clean Overview capture: `map-preview-1440.png`. The owner copy review is one level up at `claims-for-owner-map.md`.','- Historical public browser evidence is explicitly marked superseded in `public-browser-verification.json`. No deployment was performed. The other agent owns the rebuilt Overview template/scripts/styles; its integration must supply the updated landing copy and preview.','',
'## Reproduce','',
'```sh','uv run --offline --frozen pytest','uv run --offline --frozen python scripts/blind_audit.py','uv run --offline --frozen python scripts/benchmark.py --url http://127.0.0.1:56232 --fresh','uv run --offline --frozen python scripts/production_benchmark.py','uv run --offline --frozen python scripts/write_report.py','```','',
'`blind-audit.json` has 20 current analyses (2 sites × 5 heights × 2 grids), including every scenario and per-camera breakdown. `benchmark-results.json` contains the fresh-engine/live-HTTP verification at 500/600/700 m. `production-timings.json` was regenerated against this model, in isolated temporary caches. Timing measurements are local Mac observations, not cloud/cold-network measurements. `comparison-chart.html` is regenerated from the current audit.','',
'## Engineering limitations and ownership','',
'No measured lens calibration, field detection accuracy, smoke transport, weather, refraction or balloon/tether motion model. No building-height dataset; positive canopy cover is opaque, Luke mean height is not maximum treetop height, 5.47% of forest cells use assumed 20 m canopy, and raster years differ (NLS 2019 / CORINE 2024 / Luke 2023). Land launch validation is approximate; permission/access/tether suitability remain field checks. No physical Wi-Fi-off test or cloud deployment was performed. Investor-facing limitations text removed from the map is recorded verbatim for the owner; no replacement accuracy/range claims were added.','',
'Only this worktree uses the prepared-data symlink; writes go to its own results cache. The main server on 18787 and main checkout data were left alone. Overview-owned landing.html, landing.js and site.css were not changed. Shared integration points changed here: i18n.js and forest_placement/api.py. tokens.css and shell.js were not changed.','']
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
