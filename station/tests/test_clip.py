"""Event clip format, fallback and legacy AVI handling."""
import time
import cv2
import numpy as np
from fastapi.testclient import TestClient
import pytest
from station import clip
from station.alarm import Detection
from station.runtime import Station
from station.web import create_app
from test_capture import EmptyDetector

D = Detection((.25, .25, .75, .75), .88)


def ring(count=20, fps=5, width=320, height=180):
    # Synthetic mechanics frames only; never presented as smoke footage.
    frames = []
    for i in range(count):
        image = np.full((height, width, 3), 60+i*4, np.uint8)
        frames.append((1000+i/fps, cv2.imencode('.jpg', image)[1].tobytes()))
    return frames


def read_all(path):
    cap = cv2.VideoCapture(str(path))
    frames = []
    while True:
        ok, image = cap.read()
        if not ok:
            break
        frames.append(image)
    cap.release()
    return frames


def test_clip_is_vp8_webm_with_detection_box(tmp_path):
    result = clip.encode(ring(), 5, tmp_path, 'a'*32, D)
    assert result.filename == 'a'*32+'.webm' and result.format == 'WebM/VP8'
    path = tmp_path/result.filename
    assert path.read_bytes()[:4] == b'\x1a\x45\xdf\xa3'  # EBML/Matroska header
    cap = cv2.VideoCapture(str(path))
    assert int(cap.get(cv2.CAP_PROP_FOURCC)).to_bytes(4, 'little').decode().upper().startswith('VP8')
    cap.release()
    frames = read_all(path)
    assert len(frames) == result.frames == 20
    # The amber box edge is drawn on the clip like on the snapshot (BGR ~ 31,124,188).
    edge = frames[0][90, 80].astype(int)
    assert edge[2] > edge[0]+60, edge
    assert result.encode_ms > 0
    assert not list(tmp_path.glob('*.tmp.*'))


def test_fallback_to_avi_when_webm_encoder_missing(tmp_path, monkeypatch):
    broken = clip.ClipFormat('.webm', 'VP80', cv2.CAP_FFMPEG, 'WebM/VP8')
    original = clip._write
    monkeypatch.setattr(clip, '_write', lambda path, fmt, *args: 0 if fmt is broken else original(path, fmt, *args))
    result = clip.encode(ring(), 5, tmp_path, 'b'*32, D, formats=(broken, clip.FORMATS[1]))
    assert result.filename.endswith('.avi') and result.format == 'MJPEG AVI'
    assert len(read_all(tmp_path/result.filename)) == 20
    assert sorted(p.name for p in tmp_path.iterdir()) == ['b'*32+'.avi']


def test_no_encoder_raises_and_leaves_no_files(tmp_path, monkeypatch):
    monkeypatch.setattr(clip, '_write', lambda *args: 0)
    with pytest.raises(OSError, match='WebM/VP8 encoder unavailable; MJPEG AVI encoder unavailable'):
        clip.encode(ring(), 5, tmp_path, 'c'*32, D)
    assert not list(tmp_path.iterdir())


def test_station_records_fallback_clip_and_failure(config, monkeypatch):
    station = Station(config, detector=EmptyDetector())
    try:
        ok_id = station.store.create('left', D, time.time())
        monkeypatch.setattr(clip, 'FORMATS', (clip.FORMATS[1],))
        station._write_clip({'id': ok_id, 'frames': ring(), 'detection': D})
        event = station.store.events()[0]
        assert event['clip'] == ok_id+'.avi' and event['media_error'] is None
        bad_id = station.store.create('left', D, time.time()+1)
        station._write_clip({'id': bad_id, 'frames': [], 'detection': D})
        bad = next(e for e in station.store.events() if e['id'] == bad_id)
        assert bad['clip'] is None and 'No captured evidence frames' in bad['media_error']
    finally:
        station.stop(); station.store.shutdown()


def test_webm_served_inline_with_ranges_and_legacy_avi_still_listed(config):
    station = Station(config, detector=EmptyDetector())
    try:
        new_id = station.store.create('left', D, time.time())
        result = clip.encode(ring(), 5, station.store.media, new_id, D)
        station.store.set_media(new_id, clip=result.filename)
        # A legacy event recorded before WebM existed: AVI clip on disk and in the row.
        legacy_id = station.store.create('centre', D, time.time()-60)
        (station.store.media/(legacy_id+'.avi')).write_bytes(b'RIFF legacy')
        station.store.set_media(legacy_id, clip=legacy_id+'.avi')
        with TestClient(create_app(station, manage_lifecycle=False)) as client:
            events = {e['id']: e for e in client.get('/api/events').json()}
            assert events[legacy_id]['clip'].endswith('.avi') and events[new_id]['clip'].endswith('.webm')
            full = client.get('/events/'+result.filename)
            assert full.status_code == 200 and full.headers['content-type'] == 'video/webm'
            assert 'attachment' not in full.headers.get('content-disposition', '')
            assert "media-src 'self'" in full.headers['content-security-policy']
            part = client.get('/events/'+result.filename, headers={'Range': 'bytes=0-99'})
            assert part.status_code == 206 and len(part.content) == 100
            legacy = client.get(f'/events/{legacy_id}.avi')
            assert legacy.status_code == 200 and 'attachment' in legacy.headers['content-disposition']
            assert client.get(f'/events/{new_id}.mp4').status_code == 404
    finally:
        station.stop(); station.store.shutdown()


def test_retention_prunes_webm(config):
    station = Station(config, detector=EmptyDetector())
    try:
        old = station.store.create('left', D, 0)
        for suffix in ('.webm', '.tmp.webm', '.avi'):
            (station.store.media/(old+suffix)).write_bytes(b'x')
        station.store.prune(10*86400, 1)
        assert not list(station.store.media.iterdir())
    finally:
        station.stop(); station.store.shutdown()
