"""Explicit in-range HTTP evidence path. Never used by the LoRa state receiver."""
import json
from pathlib import Path
import re
from urllib.parse import urlsplit
import httpx

class Wifi:
    def __init__(self, url, secret, root, client=None):
        parsed = urlsplit(url)
        if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ('', '/'):
            raise ValueError('Station URL must be a fixed HTTP(S) origin without credentials')
        self.client = client or httpx.Client(base_url=url.rstrip('/'), timeout=12, follow_redirects=False, trust_env=False)
        self.secret = secret
        self.root = Path(root)/'evidence'
        self.root.mkdir(parents=True, exist_ok=True)
        self.enabled = False

    def get(self, path):
        r = self.client.get(path)
        if r.status_code == 401:
            if not self.secret:
                raise ValueError('Set ACORN_STATION_SECRET on the ground receiver for Wi-Fi access')
            login = self.client.post('/api/auth/login', json={'secret': self.secret})
            login.raise_for_status()
            r = self.client.get(path)
        r.raise_for_status()
        return r

    def identity(self, station):
        if self.get('/api/communication').json()['station_id'] != station:
            raise ValueError('Wi-Fi station identity does not match the received alert')

    def status(self):
        if not self.enabled:
            raise ValueError('Demo mode is off')
        return dict(self.get('/api/status').json(), wifi_station_id=self.get('/api/communication').json()['station_id'])

    def frame(self, camera):
        if not self.enabled or camera not in ('left', 'centre', 'right'):
            raise ValueError('Demo mode is off or camera is invalid')
        return self.get(f'/api/cameras/{camera}/frame.jpg').content

    def collect(self, station, event):
        if not re.fullmatch('[0-9a-f]{32}', event):
            raise ValueError('Invalid event identifier')
        self.identity(station)
        metadata = self.get(f'/api/events/{event}').json()
        if metadata['id'] != event:
            raise ValueError('Wi-Fi evidence UUID does not match alert')
        target = self.root/str(station)/event
        target.mkdir(parents=True, exist_ok=True)
        saved = []
        for field, suffixes in (('snapshot', ('jpg',)), ('clip', ('webm', 'avi'))):
            filename = metadata.get(field)
            if not filename:
                continue  # clip may still be encoding; retry the explicit collection later
            if filename not in [event+'.'+ext for ext in suffixes]:
                raise ValueError('Unexpected evidence filename')
            response = self.get('/events/'+filename)
            if len(response.content) > 64*1024*1024:
                raise ValueError('Evidence exceeds 64 MiB limit')
            temporary = target/(filename+'.part')
            temporary.write_bytes(response.content)
            temporary.replace(target/filename)
            saved.append(filename)
        manifest = dict(station=station, event_id=event, files=saved, via='Wi-Fi; not delivered over LoRa')
        temporary = target/'manifest.tmp'
        temporary.write_text(json.dumps(manifest))
        temporary.replace(target/'manifest.json')
        return manifest

    def saved(self, station, event):
        path = self.root/str(station)/event/'manifest.json'
        return json.loads(path.read_text()) if path.is_file() else None
