from dataclasses import replace
import json
from pathlib import Path
import time
import httpx
from fastapi.testclient import TestClient
import pytest
from station.lora.protocol import Packet, Kind, encode
from station.lora.radio import Radio
from ground.receiver import Receiver, SequenceTracker
from ground.web import create_app
from ground.wifi import Wifi

EVENT='1234567890abcdef1234567890abcdef'
def packet(kind=Kind.SMOKE,seq=0,boot=42,**data):
    d={Kind.SMOKE:dict(event_id=EVENT,camera=0,bearing_cd=29000,width=80,height=90,confidence=85),Kind.FLAME:dict(event_id=EVENT),Kind.DECISION:dict(event_id=EVENT,decision=1),Kind.STATUS:dict(active=3,lost=2,pending=1,uptime=60,battery=None,heading_cd=0,yaw=[-7000,0,7000],hfov=[80,80,80])}[kind]
    return Packet(kind,1,boot,seq,1700000000,3500,d|data)

def test_sequences_wrap_reorder_duplicate_and_boot(tmp_path):
    r=Receiver(tmp_path,Radio())
    try:
        assert r.ingest(encode(packet(seq=65534)),100)
        assert r.ingest(encode(packet(seq=0)),101)
        s=r.snapshot(102)['stations'][0];assert s['missed']==1
        assert r.ingest(encode(packet(seq=65535)),102)
        assert not r.ingest(encode(packet(seq=65535)),103)
        assert r.snapshot(103)['stations'][0]['missed']==0
        assert r.ingest(encode(packet(seq=2,boot=43)),104)
        assert r.snapshot(104)['stations'][0]['missed']==0
        assert len(r.snapshot()['alerts'])==1
        assert not r.ingest(b'bad') and r.invalid==1
    finally:r.close()

def test_stale_lost_ack_and_durability(tmp_path):
    r=Receiver(tmp_path,Radio(),stale_after=10,lost_after=20)
    r.ingest(encode(packet()),100)
    assert r.snapshot(109)['stations'][0]['state']=='online'
    assert r.snapshot(110)['stations'][0]['state']=='stale'
    assert r.snapshot(120)['stations'][0]['state']=='lost'
    assert r.acknowledge(1,EVENT,105)
    assert not r.acknowledge(2,EVENT,105)
    r.close();r=Receiver(tmp_path,Radio(),10,20)
    try:
        assert r.snapshot(120)['alerts'][0]['acknowledged_at']==105
        assert r.snapshot(120)['stations'][0]['state']=='lost'
        r.ingest(encode(packet(seq=1)),121)
        assert r.snapshot(121)['stations'][0]['state']=='online'
    finally:r.close()

def test_decision_before_alert_and_flame_separate(tmp_path):
    r=Receiver(tmp_path,Radio())
    try:
        r.ingest(encode(packet(Kind.DECISION,seq=0)),100)
        r.ingest(encode(packet(seq=1)),101)
        r.ingest(encode(packet(Kind.FLAME,seq=2,event_id='a'*32)),102)
        alerts=r.snapshot()['alerts']
        assert next(a for a in alerts if a['kind']=='smoke')['decision']=='confirmed'
        flame=next(a for a in alerts if a['kind']=='flame_sensor')
        assert not any(k in flame for k in ('confidence','bearing_cd','camera'))
    finally:r.close()

def test_status_and_budget_are_only_packet_fields(tmp_path):
    r=Receiver(tmp_path,Radio())
    try:
        r.ingest(encode(packet(Kind.STATUS)),100)
        s=r.snapshot(101)['stations'][0]
        assert s['status']['battery'] is None and s['status']['lost']==2
        assert s['remaining']==35 and s['airtime']==pytest.approx(Radio().airtime(40))
        assert all('snapshot' not in a and 'clip' not in a for a in r.snapshot()['alerts'])
    finally:r.close()

@pytest.fixture
def ground(tmp_path):
    calls=[]
    def handle(req):
        calls.append(req.url.path)
        if req.url.path=='/api/communication':return httpx.Response(200,json={'station_id':1})
        if req.url.path==f'/api/events/{EVENT}':return httpx.Response(200,json=dict(id=EVENT,snapshot=EVENT+'.jpg',clip=EVENT+'.webm'))
        if req.url.path.startswith('/events/'):return httpx.Response(200,content=b'fixture evidence')
        if req.url.path=='/api/status':return httpx.Response(200,json={'cameras':[]})
        return httpx.Response(200,content=b'jpeg')
    client=httpx.Client(base_url='http://station.test',transport=httpx.MockTransport(handle))
    r=Receiver(tmp_path,Radio());w=Wifi('http://station.test','test-only',tmp_path,client=client)
    with TestClient(create_app(r,w)) as c:
        yield c,r,w,calls

def test_demo_off_no_station_http_and_gates_images(ground):
    c,r,w,calls=ground;r.ingest(encode(packet()))
    assert c.get('/api/state').status_code==200 and calls==[]
    assert c.get('/api/demo').json()=={'enabled':False}
    assert c.get('/api/demo/status').status_code==403
    assert c.get('/api/demo/cameras/left.jpg').status_code==403
    assert c.get(f'/api/evidence/1/{EVENT}/{EVENT}.jpg').status_code==403
    assert calls==[]
    assert c.post('/api/demo',json={'enabled':True}).status_code==200
    assert c.get('/api/demo/status').status_code==200
    assert c.get('/api/demo/cameras/left.jpg').status_code==200
    c.post('/api/demo',json={'enabled':False})
    count=len(calls)
    assert c.get('/api/demo/status').status_code==403 and len(calls)==count

def test_exact_event_collection_persists_offline_and_no_unsolicited_alerts(ground):
    c,r,w,calls=ground;r.ingest(encode(packet()))
    assert c.post('/api/evidence/1/'+'b'*32+'/collect').status_code==404
    result=c.post(f'/api/evidence/1/{EVENT}/collect').json()
    assert result['event_id']==EVENT and result['files']==[EVENT+'.jpg',EVENT+'.webm']
    assert f'/api/events/{EVENT}' in calls and '/api/events' not in calls
    assert (w.root/'1'/EVENT/(EVENT+'.jpg')).read_bytes()==b'fixture evidence'
    assert c.get(f'/api/evidence/1/{EVENT}/{EVENT}.jpg').status_code==403
    c.post('/api/demo',json={'enabled':True})
    w.client.close() # cached images still served with no station connection
    assert c.get(f'/api/evidence/1/{EVENT}/{EVENT}.jpg').content==b'fixture evidence'
    assert c.post(f'/api/alerts/1/{EVENT}/ack').status_code==200
    assert r.snapshot()['alerts'][0]['acknowledged_at']
    assert c.post('/api/demo',json={'enabled':True},headers={'Origin':'https://unrelated.invalid'}).status_code==403

def test_wrong_identity_and_uuid_never_saved(tmp_path):
    for response in ({'station_id':2},{'station_id':1}):
        def handle(req):
            if req.url.path=='/api/communication':return httpx.Response(200,json=response)
            return httpx.Response(200,json={'id':'b'*32,'snapshot':EVENT+'.jpg'})
        w=Wifi('http://station.test','test-only',tmp_path,client=httpx.Client(base_url='http://station.test',transport=httpx.MockTransport(handle)))
        with pytest.raises(ValueError):w.collect(1,EVENT)
        assert not (w.root/'1'/EVENT/'manifest.json').exists()
        w.client.close()

def test_wifi_login_cookie_and_secret_not_exposed(tmp_path):
    logged=[False]
    def handle(req):
        if req.url.path=='/api/auth/login':
            assert json.loads(req.content)['secret']=='test-only'
            logged[0]=True;return httpx.Response(200,headers={'Set-Cookie':'acorn_session=test; Path=/'})
        if not logged[0]:return httpx.Response(401)
        assert req.headers['cookie']=='acorn_session=test'
        return httpx.Response(200,json={'station_id':1})
    w=Wifi('http://station.test','test-only',tmp_path,client=httpx.Client(base_url='http://station.test',transport=httpx.MockTransport(handle)))
    w.identity(1);assert logged[0];w.client.close()

def test_no_external_assets_and_demo_label(ground):
    c,_,_,_=ground
    html=c.get('/').text
    assert 'id="demo" hidden' in html and 'Demo only: shown over Wi-Fi, not available over LoRa' in html
    assert 'LoRa link (simulated transport)' in html
    logo=c.get('/static/brand/acorn-wordmark-white.svg')
    assert logo.status_code==200 and logo.headers['content-type']=='image/svg+xml'
    for path in ('/static/app.js','/static/style.css'):
        content=c.get(path).text
        assert 'https://' not in content and 'http://' not in content

def test_late_retired_boot_cannot_replace_current_camera_status(tmp_path):
    r=Receiver(tmp_path,Radio())
    try:
        r.ingest(encode(packet(Kind.STATUS,seq=0,boot=1,lost=2)),100)
        r.ingest(encode(packet(Kind.STATUS,seq=0,boot=2,lost=0)),101)
        r.ingest(encode(packet(Kind.STATUS,seq=1,boot=1,lost=2)),102)
        assert r.snapshot(102)['stations'][0]['boot']==2
        assert r.snapshot(102)['stations'][0]['status']['lost']==0
    finally:r.close()

def test_ground_restarts_with_demo_off_even_after_enabled(tmp_path):
    w=Wifi('http://station.test',None,tmp_path)
    w.enabled=True;w.client.close()
    other=Wifi('http://station.test',None,tmp_path)
    try:assert other.enabled is False
    finally:other.client.close()

def test_announced_duty_wait_has_bounded_stale_and_lost_deadline(tmp_path):
    r=Receiver(tmp_path,Radio(),10,20)
    try:
        r.ingest(encode(replace(packet(),contact_after=64,duty_hold=True)),100)
        s=r.snapshot(130)['stations'][0]
        assert s['state']=='holding' and s['next_contact_in']==34
        assert s['effective_stale_after']==69
        assert r.snapshot(166)['stations'][0]['state']=='holding'
        assert r.snapshot(170)['stations'][0]['state']=='stale'
        assert r.snapshot(180)['stations'][0]['state']=='lost'
        r.ingest(encode(replace(packet(seq=1),contact_after=64)),161)
        assert r.snapshot(162)['stations'][0]['state']=='online'
    finally:r.close()


def test_collected_evidence_availability_is_visible_without_wifi_or_demo(ground):
    c,r,w,calls=ground;r.ingest(encode(packet()))
    c.post(f'/api/evidence/1/{EVENT}/collect')
    calls.clear()
    state=c.get('/api/state').json()
    assert state['local_evidence'][0]['event_id']==EVENT
    assert EVENT+'.webm' in state['local_evidence'][0]['files']
    assert calls==[] and not c.get('/api/demo').json()['enabled']

@pytest.mark.parametrize('sf',[7,12])
def test_two_hours_of_paced_packets_do_not_falsely_lose_a_healthy_station(tmp_path,sf):
    from station.lora.sender import Sender
    from station.lora.radio import DutyBudget
    r=Receiver(tmp_path,Radio(sf),10,20)
    clock=[0]
    class Link:
        def send(self,raw,airtime):r.ingest(raw,clock[0])
    sender=Sender(Link(),Radio(sf),DutyBudget(.01),repeat_interval=5,heartbeat_seconds=4)
    try:
        for now in range(7201):
            clock[0]=now
            if now%4==0:sender.enqueue(packet(Kind.STATUS),now)
            if now%55==3:sender.enqueue(packet(event_id=f'{now:032x}'),now)
            sender.tick(now)
            assert r.snapshot(now)['stations'][0]['state'] in ('online','holding','scheduled')
    finally:r.close()

def test_announced_slow_heartbeat_is_not_mislabelled_as_duty_refusal(tmp_path):
    r=Receiver(tmp_path,Radio(),10,20)
    try:
        r.ingest(encode(replace(packet(),contact_after=300)),100)
        assert r.snapshot(130)['stations'][0]['state']=='scheduled'
    finally:r.close()

@pytest.mark.parametrize('start_sequence', [0, 65535])
def test_equal_second_decision_correction_survives_reorder_wrap_and_reload(tmp_path, start_sequence):
    from station.lora.sender import Sender
    from station.lora.radio import DutyBudget
    from station.lora.protocol import decode
    class Link:
        def __init__(self): self.raw = []
        def send(self, raw, airtime): self.raw.append(raw)
    link = Link()
    sender = Sender(link, Radio(7), DutyBudget(.01), repeats=2, repeat_interval=1)
    sender.sequence = start_sequence
    original = replace(packet(Kind.DECISION), timestamp=1000)
    corrected = replace(original, data=original.data | {'decision': 2})
    sender.enqueue(original, 1000.1)
    sender.tick(1000.1)
    sender.enqueue(corrected, 1000.9)
    sender.tick(1000.1 + sender.slot_seconds)
    # Real Sender cancels queued old repeats; every later emitted repeat must
    # carry the correction, even though physical sequence numbers keep advancing.
    for i in (2, 3): sender.tick(1000.1 + i * sender.slot_seconds)
    assert [decode(raw).data['decision'] for raw in link.raw] == [1, 2, 2, 2]
    assert [decode(raw).sequence for raw in link.raw[:2]] == [start_sequence, (start_sequence + 1) & 65535]
    r = Receiver(tmp_path, Radio(7))
    try:
        r.ingest(encode(replace(packet(Kind.FLAME, seq=(start_sequence-1) & 65535), timestamp=990)), 990)
        r.ingest(link.raw[1], 1013)
        r.ingest(link.raw[0], 1014)
        assert r.snapshot()['alerts'][0]['decision'] == 'rejected'
    finally: r.close()
    r = Receiver(tmp_path, Radio(7))
    try: assert r.snapshot()['alerts'][0]['decision'] == 'rejected'
    finally: r.close()


def test_equal_second_decisions_respect_current_boot_and_newer_timestamps(tmp_path):
    r = Receiver(tmp_path, Radio())
    def ingest(boot, seq, decision, timestamp=1000):
        r.ingest(encode(replace(packet(Kind.DECISION, boot=boot, seq=seq, decision=decision), timestamp=timestamp)))
    try:
        r.ingest(encode(packet(Kind.FLAME, boot=1, seq=100)))
        ingest(1, 101, 1)
        ingest(2, 0, 2)  # current boot wins a tie over the retired boot
        ingest(1, 102, 1)  # late, previously unseen old-boot datagram
        assert r.snapshot()['alerts'][0]['decision'] == 'rejected'
        r.close()
        r = Receiver(tmp_path, Radio())
        assert r.snapshot()['alerts'][0]['decision'] == 'rejected'
        ingest(2, 1, 1, 1001)  # strictly newer timestamps still win
        ingest(2, 2, 2, 999)  # higher physical sequence cannot override time
        assert r.snapshot()['alerts'][0]['decision'] == 'confirmed'
    finally: r.close()
    r = Receiver(tmp_path, Radio())
    try: assert r.snapshot()['alerts'][0]['decision'] == 'confirmed'
    finally: r.close()


def test_concurrent_same_event_collection_publishes_readable_offline_evidence(tmp_path, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier, Event, Lock
    start = Barrier(2)
    both_writing = Event()
    count_lock = Lock()
    writes = 0
    real_replace = Path.replace
    def replace_together(path, target):
        nonlocal writes
        if path.name == EVENT+'.jpg.part':
            with count_lock:
                writes += 1
                if writes == 2: both_writing.set()
            # Allows the original shared-temp implementation to collide, while
            # a serialized collector can finish and release its lock normally.
            both_writing.wait(.2)
        return real_replace(path, target)
    monkeypatch.setattr(Path, 'replace', replace_together)
    def handle(req):
        if req.url.path == '/api/communication': return httpx.Response(200, json={'station_id': 1})
        if req.url.path == f'/api/events/{EVENT}': return httpx.Response(200, json={'id': EVENT, 'snapshot': EVENT+'.jpg', 'clip': EVENT+'.webm'})
        return httpx.Response(200, content=b'offline fixture')
    with httpx.Client(base_url='http://station.test', transport=httpx.MockTransport(handle)) as client:
        w = Wifi('http://station.test', None, tmp_path, client)
        def collect():
            start.wait(timeout=2)
            try: return w.collect(1, EVENT)
            except Exception as exc: return exc
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(collect) for _ in range(2)]
            results = [f.result(timeout=3) for f in futures]
        assert all(isinstance(result, dict) for result in results), results
    # No station access remains available; both files and the committed manifest
    # must be complete and readable after the concurrent requests finish.
    assert w.saved(1, EVENT)['files'] == [EVENT+'.jpg', EVENT+'.webm']
    for name in w.saved(1, EVENT)['files']:
        assert (w.root/'1'/EVENT/name).read_bytes() == b'offline fixture'
    assert sorted(p.name for p in (w.root/'1'/EVENT).iterdir()) == [EVENT+'.jpg', EVENT+'.webm', 'manifest.json']


def test_collection_failure_cleans_temps_preserves_good_evidence_and_retries(tmp_path):
    mode = ['initial']
    def handle(req):
        if req.url.path == '/api/communication': return httpx.Response(200, json={'station_id': 1})
        if req.url.path == f'/api/events/{EVENT}':
            data = {'id': EVENT}
            if mode[0] != 'empty': data['snapshot'] = EVENT+'.jpg'
            if mode[0] in ('failure', 'retry'): data['clip'] = EVENT+'.webm'
            return httpx.Response(200, json=data)
        if req.url.path.endswith('.webm') and mode[0] == 'failure': return httpx.Response(503)
        return httpx.Response(200, content=b'original' if mode[0] == 'initial' else b'later')
    with httpx.Client(base_url='http://station.test', transport=httpx.MockTransport(handle)) as client:
        w = Wifi('http://station.test', None, tmp_path, client)
        assert w.collect(1, EVENT)['files'] == [EVENT+'.jpg']
        mode[0] = 'failure'
        with pytest.raises(httpx.HTTPStatusError): w.collect(1, EVENT)
        assert w.saved(1, EVENT)['files'] == [EVENT+'.jpg']
        assert (w.root/'1'/EVENT/(EVENT+'.jpg')).read_bytes() == b'original'
        assert sorted(p.name for p in (w.root/'1'/EVENT).iterdir()) == [EVENT+'.jpg', 'manifest.json']
        mode[0] = 'retry'
        assert w.collect(1, EVENT)['files'] == [EVENT+'.jpg', EVENT+'.webm']
        mode[0] = 'empty'
        assert w.collect(1, EVENT)['files'] == [EVENT+'.jpg', EVENT+'.webm']
        assert (w.root/'1'/EVENT/(EVENT+'.jpg')).read_bytes() == b'original'
        assert (w.root/'1'/EVENT/(EVENT+'.webm')).read_bytes() == b'later'
