from dataclasses import replace
from fastapi.testclient import TestClient
import pytest
from station.auth import PanelAuth
from station.runtime import Station
from station.web import create_app
from test_capture import EmptyDetector

@pytest.fixture
def secured(config,monkeypatch):
    monkeypatch.delenv('ACORN_PANEL_SECRET',raising=False)
    station=Station(replace(config,panel_secret='test-only-secret'),detector=EmptyDetector())
    try:
        with TestClient(create_app(station,manage_lifecycle=False)) as client:
            yield client
    finally:station.stop();station.store.shutdown()

@pytest.mark.parametrize('route', ['/api/status','/api/events','/api/mcu','/api/communication','/api/cameras/left/frame.jpg','/events/'+'a'*32+'.jpg'])
def test_all_data_requires_login(secured,route):
    assert secured.get(route).status_code==401

def test_panel_redirect_session_survives_reload_logout(secured):
    assert secured.get('/',follow_redirects=False).status_code==303
    assert secured.get('/login').status_code==200
    response=secured.post('/api/auth/login',json={'secret':'test-only-secret'})
    assert response.status_code==200
    cookie=response.headers['set-cookie'].lower()
    assert 'httponly' in cookie and 'samesite=strict' in cookie
    assert secured.get('/').status_code==200
    assert secured.get('/api/status').status_code==200
    assert secured.get('/').status_code==200
    assert secured.post('/api/auth/logout').status_code==200
    assert secured.get('/api/status').status_code==401

def test_wrong_secret_lockout_and_cross_origin(secured):
    assert secured.post('/api/auth/login',json={'secret':'test-only-secret'},headers={'Origin':'https://unrelated.invalid'}).status_code==403
    for _ in range(5):
        assert secured.post('/api/auth/login',json={'secret':'wrong'}).status_code==401
    assert secured.post('/api/auth/login',json={'secret':'test-only-secret'}).status_code==429

def test_no_secret_configured_fails_closed(config,monkeypatch):
    monkeypatch.delenv('ACORN_PANEL_SECRET',raising=False)
    station=Station(config,detector=EmptyDetector())
    try:
        with TestClient(create_app(station,manage_lifecycle=False)) as c:
            for route in ('/','/api/status','/api/mcu','/events/missing.jpg'):
                assert c.get(route).status_code==503
            assert c.post('/api/auth/login',json={'secret':'anything'}).status_code==503
    finally:station.stop();station.store.shutdown()

def test_expiration_failure_window_and_global_limit():
    now=[1000];auth=PanelAuth('test-secret',clock=lambda:now[0])
    for i in range(5):assert auth.login('wrong',str(i))[0]==401
    assert auth.login('test-secret','new-address')[0]==429
    now[0]+=301
    code,token=auth.login('test-secret','new-address');assert code==200 and auth.valid(token)
    now[0]+=auth.ttl+1;assert not auth.valid(token)

def test_environment_overrides_local_config(monkeypatch):
    monkeypatch.setenv('ACORN_PANEL_SECRET','env-test-secret')
    auth=PanelAuth('local-test-secret')
    assert auth.login('local-test-secret','host')[0]==401
    assert auth.login('env-test-secret','host')[0]==200

def test_login_body_limit_and_malformed_json(secured):
    assert secured.post('/api/auth/login',content=b'{'*2049).status_code==413
    assert secured.post('/api/auth/login',content=b'not json').status_code==401
    response=secured.get('/api/status')
    assert response.headers['cache-control']=='no-store'
    assert "frame-ancestors 'none'" in response.headers['content-security-policy']
