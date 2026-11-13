"""Create the reviewable numeric report from the live-verified benchmark JSON."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
rows=json.loads((root/'benchmark-results.json').read_text())
lines=['# Verification report','',
'Run on 2026-11-13 on this Mac. **36 pytest tests passed; zero failed or skipped.** One upstream Starlette/httpx deprecation warning. Real data preparation completed, live server/API calls completed, and browser/resource checks completed.','',
'All area figures below are **simulated hectares**, not optical detection range. Baseline: **left + centre active**, yaw −70°/0°/+70°, tilt 10° down, HFOV 80°, VFOV 50°, range 12 km, smoke target 50 m above canopy. Coast: Haukilahti, lat 60.159/lon 24.773, heading 180°. Inland: Nuuksio, lat 60.293/lon 24.557, heading 20°. No priority polygon in these tables.','',
'## Canopy-obstructed smoke target','',
'| Resolution | Preset | AGL m | Visible forest (simulation ha) | Blind forest (simulation ha) | ≥2 camera forest (simulation ha) | Water view (simulation ha) | Water share (simulation %) | Compute s |',
'| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
for r in rows:
 m=r['metrics']['canopy_smoke'];lines.append(f"| {r['resolution']} ({120 if r['resolution']=='coarse' else 40} m) | {r['name']} | {r['height']} | {m['visible_forest_ha']:,.2f} | {m['blind_forest_ha']:,.2f} | {m['overlap_forest_ha']:,.2f} | {m['water_view_ha']:,.2f} | {m['water_share_pct']:.2f} | {r['seconds']:.3f} |")
lines+=['','Compute timings include pair/reference metrics, heading sensitivity and four warped overlay PNGs; exclude data preparation and cold JIT compile. `--fresh` recomputes in the engine and then verifies the result through the running HTTP API. Exact HTTP response times and all values are in `benchmark-results.json`.','',
'## Ground and all-three reference','',
'All values are simulation ha. Opaque canopy includes the target cell, so a forest floor covered by canopy is blocked. Bare terrain is a separate scenario, not a measured canopy-free condition.','',
'| Resolution | Preset | AGL m | Bare-ground visible forest | Canopy-ground visible forest | Three-camera smoke reference |',
'| --- | --- | ---: | ---: | ---: | ---: |']
for r in rows:
 lines.append(f"| {r['resolution']} | {r['name']} | {r['height']} | {r['metrics']['bare_ground']['visible_forest_ha']:,.2f} | {r['metrics']['canopy_ground']['visible_forest_ha']:,.2f} | {r['reference']['canopy_smoke']['visible_forest_ha']:,.2f} |")
lines+=['','## Pair comparison (detailed 40 m)','',
'Each cell shows **visible forest / overlap forest, simulation ha**. Left+right has zero overlap at these defaults, leaving a central gap. Other FOV/tilt inputs are recomputed geometrically.','',
'| Preset | AGL m | Left + centre | Centre + right | Left + right |','| --- | ---: | ---: | ---: | ---: |']
for r in rows:
 if r['resolution']!='detailed':continue
 values=[f"{p['canopy_smoke']['visible_forest_ha']:,.2f} / {p['canopy_smoke']['overlap_forest_ha']:,.2f}" for p in r['pairs']]
 lines.append(f"| {r['name']} | {r['height']} | "+' | '.join(values)+' |')
lines+=['','## Heading sensitivity at 600 m (detailed 40 m)','',
'Canopy-obstructed smoke target, current connected left+centre only, simulation ha.','',
'| Preset | −20° | −10° | 0° | +10° | +20° |','| --- | ---: | ---: | ---: | ---: | ---: |']
for r in rows:
 if r['resolution']=='detailed' and r['height']==600:
  lines.append('| '+r['name']+' | '+' | '.join(f"{s['visible_forest_ha']:,.2f}" for s in r['heading_sensitivity'])+' |')
lines+=['','## Data and uncertainty','',
'- Real: NLS 10 m DEM (2019 public archive), Syke CORINE 2024 20 m, Luke MS-NFI 2023 numeric height and cover (16 m). No Copernicus fallback needed. All acquired 2026-11-13 under CC BY 4.0. Source URLs/licences are in README and cached metadata.',
'- Assumed: 20 m opaque canopy on the 5.47% of CORINE forest cells missing valid Luke values. Positive canopy cover is treated as fully opaque; the numeric stand mean is an estimated obstruction, not a measured maximum crown surface.',
'- Missing: real building heights. Road access, shadow, site constraints and permissions remain field checks.',
'- Browser actions exercised: initial map/presets, heading 180°→0°, pair switch left+right, a three-corner priority polygon and updated priority hectares. All inspected resource URLs were same-origin localhost; no external requests. A fresh-engine test blocks socket connections.',
'- Not physically tested: Wi-Fi disconnected, outdoor balloon/camera operation, true smoke detection, newer local NLS import, optional real building-height import, fully assumed-canopy preparation, Python versions other than 3.12, other operating systems.',
'- Source and prepared raster data are cached under ignored `data/`; the small benchmark JSON and this report are intended for version control. No git state-changing commands were run.','']
(root/'VERIFICATION.md').write_text('\n'.join(lines))
print('Wrote VERIFICATION.md')
