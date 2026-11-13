"""Reproduce height sensitivity with fresh real-data analyses, no HTTP cache."""
import json
import sys
sys.path.insert(0,str(__import__('pathlib').Path(__file__).resolve().parents[1]))
from pathlib import Path
from forest_placement.models import PRESETS
from forest_placement.engine import analyze
rows=[]
for resolution in ('coarse','detailed'):
    for preset in PRESETS:
        for height in (30,100,500,600,700):
            candidate=preset.model_copy(update=dict(height=height,resolution=resolution))
            r=analyze(candidate,use_cache=False)
            row=dict(preset=preset.name,resolution=resolution,height=height,seconds=r['computed_seconds'],metrics=r['metrics'],pairs=r['pair_comparison'],reference=r['reference']['metrics'],heading_sensitivity=r['heading_sensitivity'])
            rows.append(row)
            m=r['metrics']['canopy_smoke']
            print(resolution,preset.name,height,{k:m[k] for k in ('visible_forest_ha','outside_fov_forest_ha','occluded_forest_ha')},flush=True)
Path('blind-audit.json').write_text(json.dumps(rows,indent=2))
