"""Public API boundaries, split accounting, bilingual assets and identity contract."""
import json
from pathlib import Path
import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError
from forest_placement.core import summarize
from forest_placement.models import Candidate, PRESETS
from forest_placement.security import PublicLimits
from forest_placement.engine import analyze, PREP
from forest_placement import api

@pytest.mark.parametrize('indices',[[],[0],[0,1],[0,2],[0,1,2]])
def test_blind_split_counts_unique_frustum_union(indices):
    forest=np.array([[1.,.5,1.,1.,1.]])
    water=np.zeros_like(forest);eligible=np.array([[True,True,True,True,False]])
    fov=np.array([[[True,True,False,False,True]],[[False,True,True,False,True]],[[False,False,False,True,False]]])
    seen=fov & np.array([[True,False,True,False,True]])
    m,_=summarize(seen[indices],forest,water,eligible,10000,fov_masks=fov[indices])
    assert m['outside_fov_forest_ha']+m['occluded_forest_ha']==pytest.approx(m['blind_forest_ha'])
    assert m['visible_forest_ha']+m['blind_forest_ha']==m['total_forest_ha']
    if indices==[0,1]:assert m['outside_fov_forest_ha']==1 and m['occluded_forest_ha']==.5

@pytest.mark.skipif(not(PREP/'metadata.json').exists(),reason='Requires real prepared data')
def test_real_height_sensitivity_and_split():
    for preset in PRESETS:
        high=analyze(preset.model_copy(update={'resolution':'detailed'}))
        low=analyze(preset.model_copy(update={'height':30.,'resolution':'detailed'}))
        hm=high['metrics']['canopy_smoke'];lm=low['metrics']['canopy_smoke']
        assert hm['occluded_forest_ha']<1
        assert lm['occluded_forest_ha']>250
        for r in (high,low):
            metrics=list(r['metrics'].values())+list(r['reference']['metrics'].values())+r['heading_sensitivity']
            for p in r['pair_comparison']:metrics.extend(p[s] for s in r['metrics'])
            for m in metrics:assert m['outside_fov_forest_ha']+m['occluded_forest_ha']==pytest.approx(m['blind_forest_ha'],abs=.003)

@pytest.mark.parametrize('update',[
 {'max_range':15001},{'max_range':999},{'resolution':'native'},{'height':float('inf')},
 {'lat':float('nan')},{'cell_size':1},{'cameras':[{}]*4},
 {'priority':[[24,60],[26,60],[26,61],[24,61]]},
 {'priority':[[24,60]]*101},{'priority':[[24,60],[25,61],[24,61],[25,60]]},
 {'priority':[[24,float('nan')],[25,60],[24,61]]}
])
def test_hard_caps(update):
    with pytest.raises(ValidationError):Candidate(**{**PRESETS[0].model_dump(),**update})

def limited_app(**kwargs):
    app=FastAPI()
    @app.post('/api/analyze')
    async def compute():return {'ok':True}
    app.add_middleware(PublicLimits,**kwargs)
    return app

def test_per_client_rate_limit_cannot_be_spoofed():
    with TestClient(limited_app(per_client=2,global_limit=10)) as client:
        for i in range(2):assert client.post('/api/analyze',headers={'X-Forwarded-For':f'1.1.1.{i}'}).status_code==200
        r=client.post('/api/analyze',headers={'X-Forwarded-For':'9.9.9.9'})
        assert r.status_code==429 and r.headers['Retry-After']=='60'

def test_independent_clients_and_global_budget():
    app=limited_app(per_client=2,global_limit=3)
    with TestClient(app,client=('1.1.1.1',100)) as a, TestClient(app,client=('2.2.2.2',100)) as b:
        assert a.post('/api/analyze').status_code==200
        assert a.post('/api/analyze').status_code==200
        assert b.post('/api/analyze').status_code==200
        assert b.post('/api/analyze').status_code==429

def test_body_limit_before_json_parse():
    with TestClient(limited_app()) as client:
        assert client.post('/api/analyze',content=b'x'*32769).status_code==413
        assert client.post('/api/analyze',content=b'{}',headers={'Content-Length':'garbage'}).status_code==400

def test_concurrent_analysis_rejected_without_queue():
    api.lock.acquire()
    try:
        with TestClient(api.app) as client:
            r=client.post('/api/analyze',json=PRESETS[0].model_dump())
            assert r.status_code==503 and r.headers['Retry-After']=='2'
    finally:api.lock.release()

def test_file_routes_are_allowlisted():
    with TestClient(api.app) as client:
        for path in ('/maps/metadata.json','/maps/detailed.npz','/results/secret.json','/maps/%2e%2e/brand.json','/api/upload'):
            assert client.get(path).status_code in (404,405)

def test_identity_is_single_source(tmp_path,monkeypatch):
    brand={'name':'Changed name','tagline':{'en':'New tagline','tr':'Yeni slogan'},'logo':'/static/new.svg','team':'Scarabs'}
    (tmp_path/'brand.json').write_text(json.dumps(brand));monkeypatch.setattr(api,'ROOT',tmp_path)
    with TestClient(api.app) as client:assert client.get('/api/brand').json()==brand
    root=Path(__file__).resolve().parents[1]
    original=json.loads((root/'brand.json').read_text())
    assert original['placeholder'] and original['team']=='Scarabs'
    for page in ('landing.html','index.html'):
        html=(root/'static'/page).read_text()
        assert 'data-brand-name' in html and 'data-brand-logo' in html and 'data-brand-tagline' in html
        assert original['name'] not in html and original['logo'] not in html
    js=(root/'static/i18n.js').read_text()
    assert "fetch('/api/brand')" in js and 'brand.logo' in js and 'brand.tagline[lang]' in js

def test_language_assets_cover_landing_and_map():
    with TestClient(api.app) as client:
        for page in ('/','/map'):
            html=client.get(page).text
            assert 'lang="en"' in html and 'class="language"' in html and '/static/i18n.js' in html
        translations=client.get('/static/translations.json').json()
        assert translations['Open the launch point map']=='Kalkış noktası haritasını aç'
        assert translations['Outside FOV']=='Görüş dışında'
        assert translations['Occluded in FOV']=='Görüş içinde perdelenmiş'
        js=client.get('/static/i18n.js').text
        assert "lang==='en'?'tr':'en'" in js and "localStorage.setItem('language',lang)" in js

def test_warmup_compiles_production_array_layout():
    from forest_placement.warmup import warmup
    from forest_placement.core import sightlines
    warmup()
    assert any(str(signature[0].layout)=='A' for signature in sightlines.signatures)

@pytest.mark.skipif(not(PREP/'metadata.json').exists(),reason='Requires real prepared data')
def test_result_cache_evicts_old_analysis_assets(tmp_path,monkeypatch):
    from forest_placement import engine
    monkeypatch.setattr(engine,'CACHE',tmp_path)
    for i in range(257):
        name=f'{i:024x}'
        (tmp_path/(name+'.json')).write_text('{}')
        (tmp_path/(name+'_canopy_smoke.png')).write_bytes(b'old')
    analyze(PRESETS[0],use_cache=False)
    assert len(list(tmp_path.glob('*.json')))<=256
    assert not (tmp_path/('0'*24+'_canopy_smoke.png')).exists()
