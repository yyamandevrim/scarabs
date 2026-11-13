"""Write the updated split/height report and standalone chart from blind-audit.json."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
rows=json.loads((root/'blind-audit.json').read_text())
lines=['# Verification report — public dynamic site and blind-forest audit','',
'Verified 2026-11-13 on this Apple M5 Mac, Python 3.12.10. **71 pytest tests pass** (62 placement + 9 artifact tests), zero failed/skipped. The original 36 remain included. One upstream Starlette/httpx deprecation warning remains. The browser assertion script separately checks both rendered languages on landing and map at desktop and phone widths.','',
'## Finding: height insensitivity is real in this geometric scenario','',
'No LOS/height defect was found. The former blind total mixed forest outside the active camera frusta with forest hidden along sightlines inside them. With the default smoke target 50 m above the obstruction surface, 500–700 m observers look down over most intermediate terrain/canopy. Low-height controls produce large occlusion, particularly in inland Nuuksio. At 100 m, coast smoke occlusion is already zero; a claim that both low heights must be strongly occluded everywhere would be incorrect.','',
'The small 500–700 m differences mostly reflect target points crossing the tilted 3D frustum boundaries, plus raster sampling. Raising the observer shifts vertical and horizontal frustum coordinates; it does not guarantee a larger fixed-camera footprint. This result is specific to the elevated smoke-point scenario, not a general claim about forest-floor visibility or optical smoke detection. Bare-ground results show considerably stronger height sensitivity.','',
'Baseline: left + centre active; offsets −70°/0°/+70°, tilt 10° down, HFOV 80°, VFOV 50°, range 12 km, smoke 50 m above canopy. Coast: 60.159 / 24.773, heading 180°. Inland: 60.293 / 24.557, heading 20°. All area values below are **simulated hectares**. No priority polygon; range disks clipped only to the prepared rectangle.','',
'`blind_forest_ha = outside_fov_forest_ha + occluded_forest_ha` (rounding ±0.003 ha). FOV is the union of the active full 3D frusta, before applying LOS. Each forest fraction is counted once. The split is scenario-specific and present for all pairs, reference and heading sensitivities. Unknown-elevation forest is zero in these prepared grids. For other datasets, unknown rays remain unverified rather than proven occlusion and trigger the existing explicit warning.','',
'## Canopy-obstructed smoke: detailed 40 m','',
'| Preset | AGL m | Visible | Outside active FOV | Occluded inside FOV | Blind total |','| --- | ---: | ---: | ---: | ---: | ---: |']
for r in rows:
 if r['resolution']!='detailed':continue
 m=r['metrics']['canopy_smoke'];lines.append(f"| {r['preset']} | {r['height']} | {m['visible_forest_ha']:,.2f} | {m['outside_fov_forest_ha']:,.2f} | {m['occluded_forest_ha']:,.2f} | {m['blind_forest_ha']:,.2f} |")
lines+=['','## Canopy-obstructed smoke: coarse 120 m','',
'| Preset | AGL m | Visible | Outside active FOV | Occluded inside FOV | Blind total |','| --- | ---: | ---: | ---: | ---: | ---: |']
for r in rows:
 if r['resolution']!='coarse':continue
 m=r['metrics']['canopy_smoke'];lines.append(f"| {r['preset']} | {r['height']} | {m['visible_forest_ha']:,.2f} | {m['outside_fov_forest_ha']:,.2f} | {m['occluded_forest_ha']:,.2f} | {m['blind_forest_ha']:,.2f} |")
lines+=['','## Ground-height control (detailed 40 m, simulation ha)','',
'| Preset | AGL m | Bare-ground visible | Canopy-ground visible |','| --- | ---: | ---: | ---: |']
for r in rows:
 if r['resolution']=='detailed':lines.append(f"| {r['preset']} | {r['height']} | {r['metrics']['bare_ground']['visible_forest_ha']:,.2f} | {r['metrics']['canopy_ground']['visible_forest_ha']:,.2f} |")
lines+=['','## All pairs at 600 m (detailed 40 m, simulation ha)','',
'| Preset | Pair | Visible | Outside FOV | Occluded inside FOV | Overlap |','| --- | --- | ---: | ---: | ---: | ---: |']
for r in rows:
 if r['resolution']!='detailed' or r['height']!=600:continue
 for pair,label in zip(r['pairs'],('Left + centre','Centre + right','Left + right')):
  m=pair['canopy_smoke'];lines.append(f"| {r['preset']} | {label} | {m['visible_forest_ha']:,.2f} | {m['outside_fov_forest_ha']:,.2f} | {m['occluded_forest_ha']:,.2f} | {m['overlap_forest_ha']:,.2f} |")
lines+=['','## Implementation and checks','',
'- Landing at `/`, live bilingual map at `/map`; config-driven project name/tagline/logo/favicon and team credit. English default, Turkish toggle with persistent choice. No station-feed proxy or fabricated panel screenshot.',
'- Blind split and distinct grey/rust overlays; all existing scenario, pair, reference, priority and heading functionality retained. The numeric algorithm did not need a height fix. Numba releases the GIL; warm-up compiles the strided production signature, with numeric normalization to avoid request-time specialization.',
'- API caps, 12/client/min and 60/global/min budgets, single concurrent analysis, bounded result cache, request body limits, finite inputs, polygon validation and explicit file routes. Tests cover rejection paths and original real-data outputs.',
'- Modal SDK 1.6.4 app import and CLI help pass offline. The same ASGI app was started in production mode locally. Volume read-only mount, scale-to-zero and image build steps are declared but not cloud-executed.',
'- Browser: 1280×800 and 390×844 CSS viewports; landing→map, live click at land locations, pair selection including zero-overlap left+right, both languages and persistence across navigation. No horizontal page overflow, inspected console errors or external resource requests. Layer controls collapse on phones to avoid legend overlap.',
'- Artifact scripts: only dry-run executed; 13 artifacts, 112,267,118 bytes plus manifest. SHA-256/size/provenance recorded. Fog excluded for unresolved licence review; smoke+cloud alternative config supplied in tools/ without changing station/.','',
'## Local production timings','',
'Fresh process with empty generic JIT cache: **0.6159 s** to HTTP readiness. With populated cache: **0.4124 s**. Startup includes module import, warm-up and loading both prepared grids. Fresh HTTP analysis: **59.8–81.4 ms coarse**, **398.1–450.7 ms detailed**. Repeated identical requests: **1.4–1.9 ms**. No new Numba signature appeared after warm-up on first coarse/detailed analysis. These are Mac measurements, exclude image installation/data upload, and are not Modal/Linux/cold-network timings. Samples in [production-timings.json](production-timings.json).','',
'## Reproduce','',
'```sh','uv run pytest -q tests ../tools/tests','uv run python scripts/blind_audit.py','uv run python scripts/production_benchmark.py','uv run python scripts/write_report.py','```','',
'Full scenario/pair/reference/sensitivity values: [blind-audit.json](blind-audit.json). Earlier live-verified 500–700 m benchmark remains in [benchmark-results.json](benchmark-results.json) as a historical baseline. Updated split chart: [comparison-chart.html](comparison-chart.html).','',
'## Not verified, omitted or intentionally provisional','',
'- No Modal account access, Linux image build, deployment, Volume upload, public IP forwarding test, scale-to-zero/resume or cloud latency measurement. Owner commands are in [DEPLOYMENT.md](DEPLOYMENT.md).',
'- No IronShard upload/download, endpoint compatibility or judge bucket-read policy tested. AGPL model licence and upstream editable-weight/training-source links provided; a complete corresponding-source archive was not independently audited. Fog is deliberately excluded pending provenance review.',
'- `[Project name]` and the logo remain explicit replaceable identity placeholders. Roadmap mission modes are proposed, not implemented.',
'- Existing physical limits remain: no UNO Q/USB/tether/field validation; no optical detection range, weather, calibration or smoke dynamics. No building heights; 5.47% of forest canopy values assumed; real NLS 2019 / CORINE 2024 / Luke 2023 vintages differ. No ecological impact quantities are claimed.',
'- Station code, root README and root .gitignore were not edited. No git state-changing commands were run. No physical Wi-Fi-disconnection test. Station screenshots were optional and were not added.','']
(root/'VERIFICATION.md').write_text('\n'.join(lines))
# Standalone, theme-aware comparison. Individual hover labels preserve tiny high-altitude occlusion values.
selected=[r for r in rows if r['resolution']=='detailed']
chart='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Simulated forest visibility by height</title><style>
*{box-sizing:border-box}body{margin:0;color:var(--foreground,#173e49);font:13px/1.5 var(--font-sans,system-ui)}p{color:var(--muted-foreground,#526d78)}.key{display:flex;gap:16px;flex-wrap:wrap;font-size:11px;margin:12px 0 24px}.key i{display:inline-block;width:10px;height:10px;margin-right:5px}.visible{background:var(--chart-2,#438b83)}.outside{background:var(--chart-4,#9aa9b1)}.occluded{background:var(--chart-5,#bc634b)}h3{margin:20px 0 10px;font-size:15px}.row{display:grid;grid-template-columns:48px 1fr 78px;align-items:center;gap:8px;margin:8px 0}.bar{display:flex;height:20px;overflow:hidden;border-radius:3px}.bar i{height:20px;display:block}.ha{text-align:right;font:11px var(--font-mono,monospace)}.label{font-size:11px}table{border-collapse:collapse;width:100%;font-size:11px;margin-top:20px}th,td{padding:7px 4px;border-bottom:1px solid var(--border,#c9dbe2);text-align:right}th:first-child,td:first-child{text-align:left}small{color:var(--muted-foreground,#526d78)}</style></head><body><p>Default two cameras · 40 m grid · 12 km radius · 50 m smoke target above canopy. All areas are simulated hectares, not detection range.</p><div class="key"><span><i class="visible"></i>Visible forest</span><span><i class="outside"></i>Outside active FOV</span><span><i class="occluded"></i>Occluded inside FOV</span></div>'''
for preset in dict.fromkeys(r['preset'] for r in selected):
 chart+=f'<h3>{preset}</h3><small>Height AGL → forest fraction in range disk; right label = visible ha</small>'
 for r in selected:
  if r['preset']!=preset:continue
  m=r['metrics']['canopy_smoke'];total=m['total_forest_ha'];chart+=f'<div class="row"><span class="label">{r["height"]} m</span><div class="bar">'
  for cls,key in [('visible','visible_forest_ha'),('outside','outside_fov_forest_ha'),('occluded','occluded_forest_ha')]:chart+=f'<i class="{cls}" style="width:{100*m[key]/total:.6f}%" title="{key}: {m[key]:,.2f} simulated ha"></i>'
  chart+=f'</div><span class="ha">{m["visible_forest_ha"]:,.2f}</span></div>'
chart+='<table><thead><tr><th>At 600 m AGL</th><th>Outside FOV</th><th>Occluded in FOV</th></tr></thead><tbody>'
for r in selected:
 if r['height']==600:
  m=r['metrics']['canopy_smoke'];chart+=f'<tr><td>{r["preset"]}</td><td>{m["outside_fov_forest_ha"]:,.2f} ha</td><td>{m["occluded_forest_ha"]:,.2f} ha</td></tr>'
chart+='</tbody></table><p><small>Occlusion is large at 30 m, then becomes tiny or zero at balloon heights. Tiny nonzero values may be thinner than a screen pixel. Hover bars for exact values. No terrain-height defect was found.</small></p></body></html>'
(root/'comparison-chart.html').write_text(chart)
print('Wrote VERIFICATION.md and comparison-chart.html')
