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
            assert 'rel="icon"' not in page
            if path=='/':
                assert 'data-brand-stacked src="'+brand['stacked_logo']+'"' in page
                assert client.get(brand['stacked_logo']).headers['content-type']=='image/svg+xml'
                assert '<span data-brand-expansion>'+brand['expansion']+'</span>' in page


def test_asset_revision_prevents_mixed_frontend_versions(tmp_path,monkeypatch):
    import json
    import re
    from fastapi.testclient import TestClient
    from forest_placement import api
    (tmp_path/'static').mkdir()
    (tmp_path/'brand.json').write_text(json.dumps({'name':'Test','team':'Scarabs','logo':'/static/mark.svg','tagline':{'en':'Test','tr':'Test'}}))
    (tmp_path/'static/index.html').write_text('<body><script src="/static/metrics.js"></script></body>')
    script=tmp_path/'static/metrics.js'
    script.write_text('version one')
    monkeypatch.setattr(api,'ROOT',tmp_path)
    with TestClient(api.app) as client:
        first=client.get('/map')
        assert first.headers['Cache-Control']=='no-cache'
        one=re.search(r'metrics.js\?v=([a-f0-9]+)',first.text).group(1)
        script.write_text('version two')
        two=re.search(r'metrics.js\?v=([a-f0-9]+)',client.get('/map').text).group(1)
        assert one!=two
        assert client.get('/static/metrics.js').headers['Cache-Control']=='no-cache'


def test_map_script_never_coerces_missing_metrics_to_zero():
    # The 7,335 ha blind total once showed beside 0/0 parts because the old
    # formatter used `value??0` against a backend that predated the split.
    import re
    script=(ROOT/'static/app.js').read_text()
    assert not re.search(r'\?\?\s*0(?![.\d])|\|\|\s*0(?![.\d])',script)
    assert 'M.blind(' in script and 'M.share(' in script


def test_identity_names_product_team_and_event():
    import json
    from fastapi.testclient import TestClient
    from forest_placement.api import app
    brand=json.loads((ROOT/'brand.json').read_text())
    assert brand['name']=='ACORN' and brand['expansion']=='Aerial Canopy Observation and Reporting Node'
    assert brand['team']=='Scarabs' and brand['event'].startswith('Junction 2026')
    assert brand['challenge']=='Green European Renaissance'
    with TestClient(app) as client:
        for path in ('/','/map'):
            page=client.get(path).text
            assert '<title>ACORN · ' in page
            assert '<span data-brand-team>Scarabs</span>' in page


def test_browser_chart_contract():
    subprocess.run(['node', '--test', str(ROOT / 'tests/ui_charts.cjs')], check=True, cwd=ROOT)


def test_rate_limits_are_public_by_default_and_explicitly_overridable():
    from forest_placement.api import rate_limits_enabled
    assert not rate_limits_enabled({})
    assert rate_limits_enabled({'PLACEMENT_PRODUCTION': '1'})
    for value in ('1', 'true', 'YES', 'on'):
        assert rate_limits_enabled({'PLACEMENT_RATE_LIMIT': value})
    for value in ('0', 'false', 'no', 'off'):
        assert not rate_limits_enabled({'PLACEMENT_PRODUCTION': '1', 'PLACEMENT_RATE_LIMIT': value})


def test_browser_map_display_contract():
    subprocess.run(['node', '--test', str(ROOT / 'tests/ui_map_display.cjs')], check=True, cwd=ROOT)


def test_browser_request_contract():
    subprocess.run(['node', '--test', str(ROOT / 'tests/ui_requests.cjs')], check=True, cwd=ROOT)
