"""Real recorded video + real ONNX model. No network is used or permitted."""
from dataclasses import replace
import hashlib
import socket
import time
import cv2
from auth_client import TestClient
import pytest
from station.config import load_config
from station.runtime import Station
from station.web import create_app
from conftest import ROOT,wait_until

@pytest.mark.integration
@pytest.mark.parametrize("negative", ["fog.webm", "cloud.webm", "glare.webm"])
def test_real_smoke_negative_pipeline_offline(tmp_path,monkeypatch,negative):
    required=[ROOT/'models/smoke.onnx',ROOT/'media/smoke.ogv',ROOT/'media'/negative]
    if not all(path.is_file() for path in required):
        pytest.skip('Run fetch_model.py and fetch_footage.py before real-video integration tests')
    assert hashlib.sha256(required[0].read_bytes()).hexdigest()=='5c17b5f917b3cd61bafd15b808cbe3c3b03e054e2e9f09ca72f6309d53d8e76b'
    def forbidden(*args,**kwargs):
        raise AssertionError('Network access forbidden during real pipeline test')
    monkeypatch.setattr(socket.socket,'connect',forbidden)
    monkeypatch.setattr(socket,'create_connection',forbidden)
    config=replace(load_config(ROOT/'config.toml'),data_dir=tmp_path/'real-data',analysis_hz=1,confidence=.35,event_timeout=12,pre_seconds=2,post_seconds=2)
    config=replace(config,cameras=[replace(c,source=str(ROOT/'media'/negative)) if c.name=='centre' else c for c in config.cameras])
    station=Station(config)
    with TestClient(create_app(station)) as client:
        wait_until(lambda:station.metrics['left']['analyses']>=8 and station.metrics['centre']['analyses']>=8,timeout=16)
        events=client.get('/api/events').json()
        smoke=[e for e in events if e['camera']=='left']
        assert smoke, 'Actual smoke clip must create a spatially consistent three-of-five event'
        assert not [e for e in events if e['camera']=='centre'], f'{negative} produced a false alarm'
        event=smoke[0]
        wait_until(lambda:any(e['id']==event['id'] and e['clip'] for e in station.store.events()))
        event=next(e for e in station.store.events() if e['id']==event['id'])
        snapshot=client.get('/events/'+event['snapshot']);assert snapshot.status_code==200
        clip=client.get('/events/'+event['clip']);assert clip.status_code==200
        assert event['clip'].endswith('.webm') and clip.headers['content-type']=='video/webm'
        cap=cv2.VideoCapture(str(station.store.media/event['clip']))
        decoded=0
        while cap.read()[0]:decoded+=1
        cap.release()
        assert decoded>=10
        assert client.get('/api/cameras/left/frame.jpg').status_code==200
        assert client.get('/api/cameras/centre/frame.jpg').status_code==200
        assert client.get('/api/cameras/right/frame.jpg').status_code==404
        assert client.post(f"/api/events/{event['id']}/decision",json={'decision':'confirmed'}).status_code==200
        assert next(e for e in client.get('/api/events').json() if e['id']==event['id'])['decision']=='confirmed'
        # Simulate removing one active input; the second still processes the real negative video.
        before=station.metrics['centre']['analyses']
        station.workers['left'].stop()
        wait_until(lambda:station.metrics['centre']['analyses']>=before+2)
        status={c['name']:c for c in client.get('/api/status').json()['cameras']}
        assert status['left']['status_text']=='connection lost'
        assert status['centre']['connected']
        assert status['right']['status_text']=='mounted, inactive'
