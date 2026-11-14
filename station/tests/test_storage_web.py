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
            assert 'src="/static/brand/acorn-wordmark-white.svg"' in response.text
            assert 'rel="icon"' not in response.text
            assert "default-src 'self'" in response.headers['content-security-policy']
            for variant in ('wordmark', 'stacked'):
                asset=client.get(f'/static/brand/acorn-{variant}-white.svg')
                assert asset.status_code==200 and asset.headers['content-type']=='image/svg+xml'
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


def test_prune_partial_unlink_is_retryable_and_does_not_leave_dead_media_links(tmp_path, monkeypatch):
    from pathlib import Path
    store = EventStore(tmp_path)
    event_id = store.create('left', D, 0)
    jpg, webm = event_id + '.jpg', event_id + '.webm'
    for filename in (jpg, webm): (store.media / filename).write_bytes(b'evidence')
    store.set_media(event_id, snapshot=jpg, clip=webm)
    unlink = Path.unlink
    def fail_webm(path, *args, **kwargs):
        if path.name == webm: raise PermissionError('injected')
        return unlink(path, *args, **kwargs)
    try:
        with monkeypatch.context() as patch:
            patch.setattr(Path, 'unlink', fail_webm)
            with pytest.raises(PermissionError): store.prune(100000, 1)
        row = store.event(event_id)
        assert row is not None and row['snapshot'] is None and row['clip'] == webm
        assert store.prune(100000, 1) == 1
        assert store.event(event_id) is None and not (store.media / webm).exists()
    finally: store.shutdown()


def test_prune_row_delete_failure_preserves_retry_coherence(tmp_path):
    import sqlite3
    store = EventStore(tmp_path)
    event_id = store.create('left', D, 0)
    jpg = event_id + '.jpg'
    (store.media / jpg).write_bytes(b'evidence')
    store.set_media(event_id, snapshot=jpg)
    store.db.set_authorizer(lambda action, *args: sqlite3.SQLITE_DENY if action == sqlite3.SQLITE_DELETE else sqlite3.SQLITE_OK)
    try:
        with pytest.raises(sqlite3.DatabaseError): store.prune(100000, 1)
        store.db.set_authorizer(None)
        assert store.event(event_id)['snapshot'] is None
        assert store.prune(100000, 1) == 1
        assert store.event(event_id) is None
    finally: store.shutdown()


def test_pending_queue_reaches_old_event_behind_200_decisions_and_is_authenticated(config):
    from fastapi.testclient import TestClient as RawClient
    station = Station(config, detector=EmptyDetector())
    try:
        old = station.store.create('left', D, 1)
        for n in range(200):
            event_id = station.store.create('centre', D, 10 + n)
            station.store.decide(event_id, 'rejected', 300)
        app = create_app(station, manage_lifecycle=False)
        app.state.panel_auth.secret = 'test-only'
        with RawClient(app) as client:
            assert client.get('/api/events/pending').status_code == 401
        with TestClient(app) as client:
            history = client.get('/api/events').json()
            assert len(history) == 200 and old not in {e['id'] for e in history}
            response = client.get('/api/events/pending')
            assert response.status_code == 200
            page = response.json()
            assert page['pending_count'] == 1 and page['next_cursor'] is None
            assert [e['id'] for e in page['events']] == [old]
            assert client.post(f'/api/events/{old}/decision', json={'decision':'confirmed'}).status_code == 200
            assert client.get('/api/events/pending').json()['pending_count'] == 0
    finally: station.stop(); station.store.shutdown()


@pytest.mark.parametrize('order', ['newest', 'oldest'])
def test_pending_cursor_is_bounded_stable_for_ties_and_survives_anchor_decision(config, order):
    station = Station(config, detector=EmptyDetector())
    try:
        ids = [station.store.create('left', D, 100) for _ in range(405)]
        flame = station.store.create_flame(100, {'source':'test'})
        with TestClient(create_app(station, manage_lifecycle=False)) as client:
            page = client.get('/api/events/pending', params={'order':order}).json()
            assert 'events' in page
            assert page['pending_count'] == 405 and len(page['events']) == 200
            seen = [e['id'] for e in page['events']]
            anchor = seen[-1]
            client.post(f'/api/events/{anchor}/decision', json={'decision':'rejected'})
            while page['next_cursor']:
                page = client.get('/api/events/pending', params={'order':order, 'cursor':page['next_cursor']}).json()
                assert len(page['events']) <= 200 and page['pending_count'] == 404
                seen.extend(e['id'] for e in page['events'])
            assert seen == sorted(ids, reverse=order == 'newest')
            assert len(set(seen)) == 405 and flame not in seen
            assert client.get('/api/events/pending', params={'limit':201}).status_code == 422
            assert client.get('/api/events/pending', params={'cursor':'broken'}).status_code == 422
            assert client.get('/api/events/pending', params={'order':'invalid'}).status_code == 422
    finally: station.stop(); station.store.shutdown()


@pytest.mark.parametrize('at', [10**150, -(10**150), True])
def test_pending_cursor_rejects_unsafe_timestamp_values(config, at):
    import base64
    import json
    station = Station(config, detector=EmptyDetector())
    try:
        cursor = base64.urlsafe_b64encode(json.dumps([at, 'a'*32]).encode()).decode().rstrip('=')
        with TestClient(create_app(station, manage_lifecycle=False)) as client:
            assert client.get('/api/events/pending', params={'cursor':cursor}).status_code == 422
    finally: station.stop()


def test_api_decision_timestamp_is_created_under_the_journal_lock(config, monkeypatch):
    from types import SimpleNamespace
    from station import storage, web
    station = Station(config, detector=EmptyDetector())
    try:
        ids = [station.store.create('left', D, 1) for _ in range(2)]
        ticks = iter([1001.0, 1002.0])
        def locked_time():
            assert station.store.lock._is_owned(), 'Timestamp must follow serialized commit order'
            return next(ticks)
        def outside_time():
            raise AssertionError('Decision timestamp was taken before acquiring the store lock')
        monkeypatch.setattr(storage, 'time', SimpleNamespace(time=locked_time), raising=False)
        monkeypatch.setattr(web, 'time', SimpleNamespace(time=outside_time), raising=False)
        with TestClient(create_app(station, manage_lifecycle=False)) as client:
            assert client.post(f'/api/events/{ids[0]}/decision', json={'decision':'confirmed'}).status_code == 200
            first = station.store.decision_changes(1000)[0]
            assert client.post(f'/api/events/{ids[1]}/decision', json={'decision':'rejected'}).status_code == 200
        assert [r['id'] for r in station.store.decision_changes(1000, after=(first['decided_at'],first['id']))] == [ids[1]]
    finally: station.stop()
