"""Real prepared regional rasters, API contracts, active-pair and cache checks."""
import json
import numpy as np
import pytest
from fastapi.testclient import TestClient
from forest_placement.api import app
from forest_placement.engine import PREP,analyze,metadata,priority_mask,TO_METRIC
from forest_placement.models import PRESETS,Candidate

pytestmark=[pytest.mark.integration,pytest.mark.skipif(not(PREP/'metadata.json').exists(),reason='Run scripts/prepare_data.py to prepare real data')]

@pytest.fixture(scope='module')
def preset_results():return [analyze(c) for c in PRESETS]

def test_real_sources_and_complete_grid():
    m=metadata();assert m['invalid_cells']==0
    names=' '.join(s['name'] for s in m['sources'])
    assert '2024' in names and '10m' in names and '2023' in names
    for resolution in ['coarse','detailed']:
        with np.load(PREP/(resolution+'.npz')) as g:
            assert g['forest'].max()==1 and g['water'].max()==1
            assert g['valid'].all()
            assert ((g['forest']+g['water'])<=1.00001).all()

def test_presets_water_and_accounting(preset_results):
    coast,inland=preset_results
    assert coast['active_cameras']==[0,1] and inland['active_cameras']==[0,1]
    assert coast['metrics']['canopy_smoke']['water_share_pct']>70
    assert inland['metrics']['canopy_smoke']['water_share_pct']<20
    for r in preset_results:
        assert not r['range_clipped'] and r['unknown_forest_ha']==0
        for name,m in r['metrics'].items():
            assert m['visible_forest_ha']+m['blind_forest_ha']==pytest.approx(m['total_forest_ha'],abs=.01)
            assert 0<=m['overlap_forest_ha']<=m['visible_forest_ha']
            assert r['reference']['metrics'][name]['visible_forest_ha']>=m['visible_forest_ha']
        assert r['metrics']['canopy_smoke']['visible_forest_ha']>0
        assert r['sectors'][2]['label'].endswith('bağlı değil')

def test_pair_comparison_counts(preset_results):
    for r in preset_results:
        pairs=r['pair_comparison'];assert len(pairs)==3
        assert pairs[0]['canopy_smoke']==r['metrics']['canopy_smoke']
        for name in r['metrics']:
            assert pairs[2][name]['overlap_forest_ha']==0
        assert pairs[0]['canopy_smoke']['overlap_forest_ha']>0

def test_switch_pair_controls_all_results(preset_results):
    c=PRESETS[0].model_dump();c['cameras'][1]['active']=False;c['cameras'][2]['active']=True
    r=analyze(Candidate(**c));assert r['active_cameras']==[0,2]
    assert r['metrics']['canopy_smoke']==preset_results[0]['pair_comparison'][2]['canopy_smoke']
    assert r['heading_sensitivity'][2]['visible_forest_ha']==r['metrics']['canopy_smoke']['visible_forest_ha']
    assert r['metrics']['canopy_smoke']['overlap_forest_ha']==0

def test_heading_changes_and_reference():
    c=PRESETS[0].model_dump();c['heading']=0
    north=analyze(Candidate(**c));south=analyze(PRESETS[0])
    assert north['metrics']['canopy_smoke']['visible_forest_ha']>south['metrics']['canopy_smoke']['visible_forest_ha']
    c['reference']=True
    for cam in c['cameras']:cam['active']=True
    ref=analyze(Candidate(**c))
    assert ref['mode']=='üç kamera, referans'
    assert ref['metrics']==ref['reference']['metrics']

def test_real_priority_and_cache(preset_results):
    c=PRESETS[1].model_dump();c['priority']=[[24.3,60.2],[24.8,60.2],[24.8,60.5],[24.3,60.5]]
    result=analyze(Candidate(**c))
    assert result['metrics']['canopy_smoke']['priority_visible_ha']>0
    assert result['metrics']['canopy_smoke']['priority_visible_ha']<=result['metrics']['canopy_smoke']['visible_forest_ha']
    assert result['id']!=preset_results[1]['id']
    cached=analyze(Candidate(**c));assert cached['cached'] and result['metrics']==cached['metrics']

def test_priority_transform():
    x,y=TO_METRIC.transform(24.6,60.3)
    mask=priority_mask([[24.5,60.2],[24.7,60.2],[24.7,60.4],[24.5,60.4]],np.array([[x,x+100000]]),np.array([[y,y]]))
    assert mask.tolist()==[[True,False]]

@pytest.mark.parametrize('resolution',['coarse','detailed'])
def test_api_presets_and_offline_assets(resolution):
    with TestClient(app) as client:
        conf=client.get('/api/config');assert conf.status_code==200 and conf.json()['ready']
        assert client.get('/').status_code==200
        assert "connect-src 'self'" in client.get('/').headers['Content-Security-Policy']
        for path in ['/static/vendor/leaflet.js','/static/vendor/leaflet.css','/static/app.js','/maps/background.png','/maps/forest.png','/maps/water.png']:
            assert client.get(path).status_code==200
        for preset in PRESETS:
            c=preset.model_dump();c['resolution']=resolution
            response=client.post('/api/analyze',json=c);assert response.status_code==200,response.text
            r=response.json();assert r['resolution_m']==(120 if resolution=='coarse' else 40)
            assert client.get(r['images']['canopy_smoke']['url']).status_code==200
        c=PRESETS[0].model_dump();c['cameras'][2]['active']=True
        assert client.post('/api/analyze',json=c).status_code==422
        c=PRESETS[0].model_dump();c['lat']=60.7;c['lon']=26
        assert client.post('/api/analyze',json=c).status_code==422

def test_api_comparison_ranks_priority_first():
    with TestClient(app) as client:
        response=client.post('/api/compare',json={'candidates':[c.model_dump() for c in PRESETS]})
        assert response.status_code==200
        data=response.json();assert data['ranking']==[1,0]
        assert len(data['results'])==2

def test_analysis_with_external_network_blocked(monkeypatch):
    import socket
    blocked=[]
    def deny(*args,**kwargs):
        blocked.append(args)
        raise AssertionError('Runtime attempted network access')
    monkeypatch.setattr(socket,'create_connection',deny)
    monkeypatch.setattr(socket.socket,'connect',deny)
    # Force fresh LOS and PNGs instead of merely reading cached JSON.
    for preset in PRESETS:
        r=analyze(preset,use_cache=False)
        assert r['metrics']['canopy_smoke']['visible_forest_ha']>0
    assert blocked==[]
