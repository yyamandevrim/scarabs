"""Start the three offline laptop services; Ctrl+C stops all children.

From the repository root after DEMO.md preparation:
  uv run --offline --frozen --project station python station/scripts/laptop_demo.py
Add --live for the native macOS camera (smoke-screen positive test unverified).
"""
import argparse
import getpass
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import tomllib

ROOT = Path(__file__).resolve().parents[2]


def stop(children):
    for _, child in children:
        try:
            os.killpg(child.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    for _, child in children:
        try:
            child.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait()


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
    uv = ['uv', 'run', '--offline', '--frozen']
    services = [
        ('placement', ['uvicorn', 'forest_placement.api:app', '--host', '127.0.0.1', '--port', '38787']),
        ('ground', ['acorn-ground', '--port', '28092', '--udp-port', str(radio['peer_port']),
                    '--sf', str(radio['sf']), '--data', data, '--station-url', 'http://127.0.0.1:28091',
                    '--stale-after', '10', '--lost-after', '20']),
        ('station', ['forest-station', '--config', config_name, 'serve', '--port', '28091']),
    ]
    children = []
    def interrupted(signum, frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, interrupted)
    try:
        for name, command in services:
            children.append((name, subprocess.Popen(uv + command, cwd=ROOT/name, env=env, start_new_session=True)))
        print('Launching ' + ('Live Mac camera · smoke-screen positive test unverified.' if args.live else 'Recorded demo · use this jury fallback.'), flush=True)
        print('Station http://127.0.0.1:28091 · Ground http://127.0.0.1:28092 · Map http://127.0.0.1:38787/map', flush=True)
        print('No board, flame sensor or physical LED. Radio transport is simulated; timings are not measured on the board. Ctrl+C stops all three services.', flush=True)
        while True:
            for name, child in children:
                code = child.poll()
                if code is not None:
                    print(f'{name} exited ({code}); stopping the laptop demo. Check preparation and port availability in DEMO.md.', file=sys.stderr)
                    return code if code > 0 else 1
            time.sleep(.2)
    except KeyboardInterrupt:
        return 0
    except OSError as exc:
        print(f'Cannot launch laptop demo: {exc}', file=sys.stderr)
        return 1
    finally:
        stop(children)


if __name__ == '__main__':
    raise SystemExit(main())
