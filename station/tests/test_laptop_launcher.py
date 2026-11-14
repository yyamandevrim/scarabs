"""Exercise the one-command launcher's real child lifetime with a fake uv binary."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from conftest import ROOT, wait_until


SCRIPT = ROOT / 'scripts/laptop_demo.py'


def launcher(tmp_path, live=False, failure=None):
    binary = tmp_path / 'uv'
    binary.write_text(f'''#!{sys.executable}
import json,os,signal,sys,time
from pathlib import Path
project=Path.cwd().name
root=Path(os.environ['LAUNCH_TRACE'])
(root/(project+'.json')).write_text(json.dumps({{'argv':sys.argv[1:],'same_secret':os.environ.get('ACORN_PANEL_SECRET')==os.environ.get('ACORN_STATION_SECRET')}}))
def stop(*args):
 (root/(project+'.stopped')).write_text('stopped')
 sys.exit(0)
signal.signal(signal.SIGTERM,stop)
if project==os.environ.get('FAIL_PROJECT'):
 time.sleep(.1)
 sys.exit(7)
while True:time.sleep(.05)
''')
    binary.chmod(0o755)
    env = os.environ | {'PATH': str(tmp_path) + os.pathsep + os.environ['PATH'],
                       'ACORN_PANEL_SECRET': 'test-launcher-only', 'LAUNCH_TRACE': str(tmp_path)}
    if failure:
        env['FAIL_PROJECT'] = failure
    process = subprocess.Popen([sys.executable, str(SCRIPT), *(['--live'] if live else [])],
                               cwd=tmp_path, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return process


def test_recorded_launcher_starts_all_services_and_ctrl_c_stops_every_child(tmp_path):
    process = launcher(tmp_path)
    try:
        wait_until(lambda: all((tmp_path / (name+'.json')).exists() for name in ['placement', 'ground', 'station']))
        station = json.loads((tmp_path/'station.json').read_text())
        ground = json.loads((tmp_path/'ground.json').read_text())
        assert 'demo-laptop.toml' in station['argv']
        assert 'demo-mac-camera.toml' not in station['argv']
        assert station['same_secret'] and ground['same_secret']
        assert ground['argv'][ground['argv'].index('--udp-port') + 1] == '49173'
        assert ground['argv'][ground['argv'].index('--station-url') + 1] == 'http://127.0.0.1:28091'
        process.send_signal(signal.SIGINT)
        stdout, stderr = process.communicate(timeout=5)
        assert process.returncode == 0, stderr
        assert 'Recorded demo' in stdout and 'not measured on the board' in stdout
        assert 'test-launcher-only' not in stdout + stderr
        assert all((tmp_path/(name+'.stopped')).exists() for name in ['placement', 'ground', 'station'])
    finally:
        if process.poll() is None:
            process.send_signal(signal.SIGINT)
            process.communicate(timeout=5)


def test_launcher_failure_returns_nonzero_and_stops_other_services(tmp_path):
    process = launcher(tmp_path, failure='ground')
    try:
        stdout, stderr = process.communicate(timeout=5)
        assert process.returncode == 7
        assert 'ground exited' in stderr
        assert (tmp_path/'placement.stopped').exists()
        assert (tmp_path/'station.stopped').exists()
    finally:
        if process.poll() is None:
            process.send_signal(signal.SIGINT)
            process.communicate(timeout=5)


def test_live_launcher_selects_native_config_or_rejects_non_mac(tmp_path):
    process = launcher(tmp_path, live=True)
    try:
        if sys.platform != 'darwin':
            _, stderr = process.communicate(timeout=5)
            assert process.returncode != 0 and 'macOS' in stderr
            assert not (tmp_path/'station.json').exists()
            return
        wait_until(lambda: (tmp_path/'station.json').exists())
        args = json.loads((tmp_path/'station.json').read_text())['argv']
        assert 'demo-mac-camera.toml' in args and 'demo-laptop.toml' not in args
        process.send_signal(signal.SIGINT)
        stdout, stderr = process.communicate(timeout=5)
        assert process.returncode == 0, stderr
        assert 'unverified' in stdout
    finally:
        if process.poll() is None:
            process.send_signal(signal.SIGINT)
            process.communicate(timeout=5)
