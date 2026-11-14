"""Start the three offline laptop services; Ctrl+C stops all children.

From the repository root after DEMO.md preparation:
  uv run --offline --frozen --project station python station/scripts/laptop_demo.py
Add --live for the native macOS camera (smoke-screen positive test unverified).
"""
import argparse
import getpass
from http.cookiejar import CookieJar
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
import tomllib
from urllib.error import HTTPError, URLError
from urllib.request import build_opener, HTTPCookieProcessor, ProxyHandler, Request

ROOT = Path(__file__).resolve().parents[2]
PORTS = {'placement': 38787, 'ground': 28092, 'station': 28091}
STARTUP_TIMEOUT = 30
STOP_TIMEOUT = 10


class LaunchError(RuntimeError):
    def __init__(self, message, code=1):
        super().__init__(message)
        self.code = code


def stop(children):
    def kill_group(child, sig):
        try:
            os.killpg(child.pid, sig)
        except ProcessLookupError:
            pass
    for _, child in children:
        kill_group(child, signal.SIGTERM)
    deadline = time.monotonic() + STOP_TIMEOUT
    for _, child in children:
        try:
            child.wait(timeout=max(0, deadline-time.monotonic()))
        except subprocess.TimeoutExpired:
            pass
    for _, child in children:
        # A uv parent may have exited while a descendant still holds its pipes.
        kill_group(child, signal.SIGKILL)
        child.wait()


def check_ports(udp_port):
    for name, port, kind in [*( (name, port, socket.SOCK_STREAM) for name, port in PORTS.items()),
                             ('ground UDP', udp_port, socket.SOCK_DGRAM)]:
        with socket.socket(type=kind) as sock:
            if kind == socket.SOCK_STREAM:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(('127.0.0.1', port))
                if kind == socket.SOCK_STREAM:
                    sock.listen(1)
            except OSError as exc:
                raise LaunchError(f'{name} port 127.0.0.1:{port} is in use or unavailable; stop its owner or change the matching demo ports.') from exc


def probe(name, opener, secret):
    base = f'http://127.0.0.1:{PORTS[name]}'
    path = {'placement':'/api/config', 'ground':'/api/state', 'station':'/api/status'}[name]
    try:
        try:
            response = opener.open(base+path, timeout=.5)
        except HTTPError as exc:
            if name != 'station' or exc.code != 401:
                raise
            login = Request(base+'/api/auth/login', data=json.dumps({'secret':secret}).encode(),
                            headers={'Content-Type':'application/json'})
            with opener.open(login, timeout=.5):
                pass
            response = opener.open(base+path, timeout=.5)
        with response:
            data = json.load(response)
        if name == 'placement':
            return data.get('ready') is True, 'prepared map data is not ready'
        if name == 'ground':
            return isinstance(data.get('stations'), list) and isinstance(data.get('alerts'), list), 'packet receiver is not ready'
        active = [c for c in data.get('cameras', []) if c.get('active')]
        healthy = (data.get('runtime', {}).get('analysis_running') is True and active
                   and all(c.get('connected') and c.get('analyses', 0) > 0 and not c.get('pipeline_error') for c in active))
        return bool(healthy), 'camera capture or analysis is not ready; check camera permission, source and model'
    except (OSError, URLError, ValueError):
        return False, 'HTTP readiness probe failed; check the service log'


def check_children(children):
    for name, child in children:
        code = child.poll()
        if code is not None:
            raise LaunchError(f'{name} on 127.0.0.1:{PORTS[name]} exited ({code}); stopping the laptop demo.', code if code > 0 else 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true', help='Use the native Mac camera instead of recorded sources')
    args = parser.parse_args()
    if args.live and sys.platform != 'darwin':
        parser.error('The live AVFoundation camera requires macOS')
    secret = os.environ.get('ACORN_PANEL_SECRET')
    if not secret:
        try:
            secret = getpass.getpass('Station panel secret (also used by ground): ')
        except (EOFError, KeyboardInterrupt):
            return 2
    if not secret:
        parser.error('Station panel secret cannot be empty')
    env = os.environ | {'ACORN_PANEL_SECRET': secret, 'ACORN_STATION_SECRET': secret}
    config_name = 'demo-mac-camera.toml' if args.live else 'demo-laptop.toml'
    with (ROOT / 'station' / config_name).open('rb') as stream:
        config = tomllib.load(stream)
    radio = config['lora']
    data = 'data/laptop-live' if args.live else 'data/laptop'
    station_url = f"http://127.0.0.1:{PORTS['station']}"
    uv = ['uv', 'run', '--offline', '--frozen']
    services = [
        ('placement', ['uvicorn', 'forest_placement.api:app', '--host', '127.0.0.1', '--port', str(PORTS['placement'])]),
        ('ground', ['acorn-ground', '--port', str(PORTS['ground']), '--udp-port', str(radio['peer_port']),
                    '--sf', str(radio['sf']), '--data', data, '--station-url', station_url,
                    '--stale-after', '10', '--lost-after', '20']),
        ('station', ['forest-station', '--config', config_name, 'serve', '--port', str(PORTS['station'])]),
    ]
    children, stopping = [], False
    def interrupted(signum, frame):
        nonlocal stopping
        stopping = True
    # Never raise inside Popen: a signal can arrive after spawn but before the
    # returned child is registered, leaving an orphan and inherited pipes open.
    previous = {sig:signal.signal(sig, interrupted) for sig in (signal.SIGINT, signal.SIGTERM)}
    try:
        check_ports(radio['peer_port'])
        print('Launching ' + ('Live Mac camera · smoke-screen positive test unverified.' if args.live else 'Recorded demo · use this jury fallback.'), flush=True)
        for name, command in services:
            if stopping:
                return 0
            started = time.monotonic()
            children.append((name, subprocess.Popen(uv + command, cwd=ROOT/name, env=env, start_new_session=True)))
            opener = build_opener(ProxyHandler({}), HTTPCookieProcessor(CookieJar()))
            while not stopping:
                check_children(children)
                healthy, detail = probe(name, opener, secret)
                if healthy:
                    check_children(children)
                    print(f'{name} ready on 127.0.0.1:{PORTS[name]} ({time.monotonic()-started:.2f}s)', flush=True)
                    break
                if time.monotonic()-started >= STARTUP_TIMEOUT:
                    raise LaunchError(f'{name} on 127.0.0.1:{PORTS[name]} did not become ready within {STARTUP_TIMEOUT:g}s: {detail}.')
                time.sleep(.05)
            if stopping:
                return 0
        print('Laptop demo ready · Station '+station_url+f" · Ground http://127.0.0.1:{PORTS['ground']} · Map http://127.0.0.1:{PORTS['placement']}/map", flush=True)
        print('No board, flame sensor or physical LED. Radio transport is simulated; timings are not measured on the board. Ctrl+C stops all three services.', flush=True)
        while not stopping:
            check_children(children)
            time.sleep(.2)
        return 0
    except LaunchError as exc:
        print(str(exc), file=sys.stderr)
        return exc.code
    except OSError as exc:
        print(f'Cannot launch laptop demo: {exc}', file=sys.stderr)
        return 1
    finally:
        stop(children)
        for sig, handler in previous.items():
            signal.signal(sig, handler)


if __name__ == '__main__':
    raise SystemExit(main())
