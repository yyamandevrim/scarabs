from dataclasses import replace
import re
import time
from auth_client import TestClient
import pytest
from station.alarm import Detection
from station.led import LedHook
from station.runtime import Station
from station.storage import EventStore
from station.web import create_app
from station import identity
from test_capture import EmptyDetector

D=Detection((.1,.2,.3,.4),.88)


@pytest.mark.parametrize("decision", ["confirmed", "rejected"])
def test_persistence_operator_decision_and_extension(tmp_path, decision):
    store=EventStore(tmp_path)
    event_id=store.create('left',D,100)
    store.decide(event_id,decision,101)
    store.extend(event_id,Detection(D.box,.95),105)
    store.shutdown()
    store=EventStore(tmp_path)
    try:
        event=store.events()[0]
        assert event['id']==event_id
        assert event['camera']=='left' and event['opened_at']==100 and event['last_seen']==105
        assert event['decision']==decision and event['decided_at']==101
        assert event['confidence']==.95 and event['box']==list(D.box)
    finally:store.shutdown()


def test_retention_prunes_media_and_rows(tmp_path):
    store=EventStore(tmp_path)
    old=store.create('left',D,0);new=store.create('centre',D,100000)
    for event_id in (old,new):
        for suffix in ('.jpg','.avi'):(store.media/(event_id+suffix)).write_bytes(b'evidence')
    assert store.prune(100000,1)==1
    assert [e['id'] for e in store.events()]==[new]
    assert not (store.media/(old+'.jpg')).exists()
    assert not (store.media/(old+'.avi')).exists()
    assert (store.media/(new+'.jpg')).exists()
    store.shutdown()


def test_invalid_decision(tmp_path):
    store=EventStore(tmp_path)
    try:
        with pytest.raises(ValueError):store.decide('missing','anything',0)
        assert not store.decide('missing','rejected',0)
    finally:store.shutdown()


def test_api_and_locally_served_assets(config):
    station=Station(config,detector=EmptyDetector())
    event_id=station.store.create('left',D,time.time())
    app=create_app(station,manage_lifecycle=False)
    try:
        with TestClient(app) as client:
            response=client.get('/')
            assert response.status_code==200
            assert 'lang="tr"' in response.text
            assert f'<title>{identity.NAME}</title>' in response.text
            assert f'aria-label="{identity.NAME}"' in response.text
            assert 'src="/static/brand/acorn-wordmark-white.png"' in response.text
            assert 'rel="icon"' not in response.text
            assert "default-src 'self'" in response.headers['content-security-policy']
            for variant in ('wordmark', 'stacked'):
                asset=client.get(f'/static/brand/acorn-{variant}-white.png')
                assert asset.status_code==200 and asset.headers['content-type']=='image/png'
            for asset in ('/static/app.js','/static/style.css'):
                r=client.get(asset);assert r.status_code==200
                assert not re.search(r'https?://|@import|fonts.googleapis|cdn\.',r.text)
            assert len(client.get('/api/status').json()['cameras'])==3
            assert client.get('/api/events').json()[0]['title']=='Duman şüphesi'
            for decision in ('confirmed','rejected'):
                assert client.post(f'/api/events/{event_id}/decision',json={'decision':decision}).status_code==200
                assert station.store.events()[0]['decision']==decision
            assert client.post(f'/api/events/{event_id}/decision',json={'decision':'invalid'}).status_code==422
            assert client.post('/api/events/missing/decision',json={'decision':'confirmed'}).status_code==404
            assert client.get('/api/cameras/right/frame.jpg').status_code==404
            assert client.get('/api/cameras/left/frame.jpg').status_code==503
            assert client.get('/events/events.sqlite3').status_code==404
    finally:station.stop();station.store.shutdown()


def test_identity_is_rendered_from_one_definition(config, monkeypatch):
    monkeypatch.setattr(identity, 'NAME', 'Test node — Field <observation>')
    station=Station(config,detector=EmptyDetector())
    try:
        app=create_app(station,manage_lifecycle=False)
        with TestClient(app) as client:
            markup=client.get('/').text
            assert '<title>Test node — Field &lt;observation&gt;</title>' in markup
            assert 'aria-label="Test node — Field &lt;observation&gt;"' in markup
            assert '{{station_' not in markup
            assert app.title==identity.NAME
    finally:station.stop();station.store.shutdown()


def test_led_noop_and_unavailable(tmp_path):
    LedHook().set_alarm(True)
    missing=LedHook(tmp_path/'missing'/'brightness');missing.set_alarm(True)
    assert missing.failed
    path=tmp_path/'brightness';path.write_text('0')
    led=LedHook(path);led.set_alarm(True);assert path.read_text()=='1'
    led.set_alarm(False);assert path.read_text()=='0'
