"""Run the actual browser presentation rules, including legacy API responses."""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_browser_metric_contract():
    subprocess.run(['node', '--test', str(ROOT / 'tests/ui_metrics.cjs')], check=True, cwd=ROOT)

def test_map_legend_and_render_share_palette():
    from forest_placement.palette import map_color
    assert map_color('visible',195)==[0,158,115,195]
    assert map_color('occluded',190)==[184,120,80,190]
    assert map_color('outside',125)==[143,150,156,125]

def test_server_renders_config_identity_before_javascript():
    import json
    from fastapi.testclient import TestClient
    from forest_placement.api import app
    brand=json.loads((ROOT/'brand.json').read_text())
    with TestClient(app) as client:
        for path in ('/', '/map'):
            page=client.get(path).text
            assert 'data-brand-logo src="'+brand['logo']+'"' in page
            assert brand['name'] in page
            assert client.get(brand['logo']).status_code==200
