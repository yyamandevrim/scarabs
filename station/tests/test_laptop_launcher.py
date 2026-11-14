"""Real child processes and HTTP probes, isolated on ephemeral ports."""
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time

import pytest
from conftest import ROOT, wait_until

SCRIPT = ROOT / 'scripts/laptop_demo.py'
NAMES = ('placement', 'ground', 'station')
STARTUP_SECONDS = 30


def free_port(kind=socket.SOCK_STREAM):
    with socket.socket(type=kind) as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def launcher(root, *, live=False, failure='', boot_delay=0, hang='', timeout=STARTUP_SECONDS, delayed_spawn=False, ports=None, ignore_term=False, udp_port=None):
    ports = ports or {name: free_port() for name in NAMES}
    for name in NAMES:
        (root/name).mkdir()
    config = f'[lora]\npeer_port = {udp_port or free_port(socket.SOCK_DGRAM)}\nsf = 7\n'
    for name in ('demo-laptop.toml', 'demo-mac-camera.toml'):
        (root/'station'/name).write_text(config)
    binary = root/'uv'
    binary.write_text(f'''#!{sys.executable}
import json,os,signal,sys,time
from pathlib import Path
from http.server import BaseHTTPRequestHandler,HTTPServer
name=Path.cwd().name
root=Path(os.environ['LAUNCH_TRACE'])
time.sleep(float(os.environ.get('BOOT_DELAY','0')) if name=='placement' else 0)
def stop(*args):
 (root/(name+'.stopped')).write_text('stopped')
 sys.exit(0)
signal.signal(signal.SIGTERM,signal.SIG_IGN if os.environ.get('IGNORE_TERM')=='1' else stop)
(root/(name+'.json')).write_text(json.dumps({{'pid':os.getpid(),'argv':sys.argv[1:],'started':time.monotonic(),'same_secret':os.environ.get('ACORN_PANEL_SECRET')==os.environ.get('ACORN_STATION_SECRET')}}))
if name==os.environ.get('FAIL_PROJECT'):
 time.sleep(.1)
 sys.exit(7)
if name==os.environ.get('HANG_PROJECT'):
 while True:time.sleep(.05)
port=int(sys.argv[sys.argv.index('--port')+1])
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_POST(self):
  self.send_response(200);self.end_headers();self.wfile.write(b'{{"ok":true}}')
 def do_GET(self):
  body={{'placement':{{'ready':True}},'ground':{{'stations':[],'alerts':[]}},'station':{{'runtime':{{'analysis_running':True}},'cameras':[{{'active':True,'connected':True,'analyses':1,'pipeline_error':None}}]}}}}[name]
  (root/(name+'.probed')).write_text(str(time.monotonic()))
  self.send_response(200);self.end_headers();self.wfile.write(json.dumps(body).encode())
HTTPServer(('127.0.0.1',port),Handler).serve_forever()
''')
    binary.chmod(0o755)
    wrapper = root/'launch.py'
    race = f'''
original=subprocess.Popen
def delayed(*args,**kwargs):
 child=original(*args,**kwargs)
 if Path(kwargs.get('cwd','')).name=='station':
  Path({str(root/'spawned.pid')!r}).write_text(str(child.pid))
  time.sleep(1)
 return child
subprocess.Popen=delayed
''' if delayed_spawn else ''
    wrapper.write_text(f'''import runpy,subprocess,time
from pathlib import Path
ns=runpy.run_path({str(SCRIPT)!r})
g=ns['main'].__globals__
g['ROOT']=Path({str(root)!r})
g['PORTS']={ports!r}
g['STARTUP_TIMEOUT']={timeout!r}
g['STOP_TIMEOUT']=.5
{race}
raise SystemExit(ns['main']())
''')
    env = os.environ | {'PATH':str(root)+os.pathsep+os.environ['PATH'], 'ACORN_PANEL_SECRET':'test-launcher-only',
                        'LAUNCH_TRACE':str(root),'FAIL_PROJECT':failure,'BOOT_DELAY':str(boot_delay),
                        'HANG_PROJECT':hang,'IGNORE_TERM':str(int(ignore_term))}
    with (root/'stdout').open('w') as stdout, (root/'stderr').open('w') as stderr:
        process = subprocess.Popen([sys.executable,str(wrapper),*(['--live'] if live else [])],cwd=root,env=env,stdout=stdout,stderr=stderr)
    return process, ports


def output(root):
    return (root/'stdout').read_text(), (root/'stderr').read_text()


def ready(process, root, timeout=STARTUP_SECONDS*len(NAMES)+5):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        if 'Laptop demo ready' in output(root)[0]:return
        assert process.poll() is None, output(root)
        time.sleep(.02)
    pytest.fail(f'No readiness result: {output(root)}')


def assert_reaped(root):
    for name in NAMES:
        path=root/(name+'.json')
        if path.exists():
            with pytest.raises(ProcessLookupError):os.kill(json.loads(path.read_text())['pid'],0)


def cleanup(process, root):
    if process.poll() is None:
        process.send_signal(signal.SIGINT)
        try:process.wait(timeout=3)
        except subprocess.TimeoutExpired:process.kill();process.wait()
    for path in [*(root.glob('*.json')),root/'spawned.pid']:
        if not path.exists():continue
        pid=int(path.read_text()) if path.suffix=='.pid' else json.loads(path.read_text())['pid']
        try:os.killpg(pid,signal.SIGKILL)
        except ProcessLookupError:pass


def test_launcher_waits_for_readiness_before_starting_the_next_service(tmp_path):
    # Reproduce a cold child taking longer than the old test's 3 s trace deadline.
    process, ports=launcher(tmp_path,boot_delay=3.2)
    try:
        ready(process,tmp_path)
        for previous,following in zip(NAMES,NAMES[1:]):
            assert json.loads((tmp_path/(following+'.json')).read_text())['started'] >= float((tmp_path/(previous+'.probed')).read_text())
        args=json.loads((tmp_path/'station.json').read_text())
        assert 'demo-laptop.toml' in args['argv'] and args['same_secret']
        stdout,stderr=output(tmp_path)
        assert 'Recorded demo' in stdout and 'not measured on the board' in stdout
        assert 'test-launcher-only' not in stdout+stderr
        process.send_signal(signal.SIGINT);assert process.wait(timeout=3)==0
        assert_reaped(tmp_path)
    finally:cleanup(process,tmp_path)


def test_launcher_failure_names_service_and_port_and_stops_started_services(tmp_path):
    process,ports=launcher(tmp_path,failure='ground')
    try:
        assert process.wait(timeout=5)==7
        stderr=output(tmp_path)[1]
        assert 'ground' in stderr and str(ports['ground']) in stderr and 'exited' in stderr
        assert not (tmp_path/'station.json').exists()
        assert_reaped(tmp_path)
    finally:cleanup(process,tmp_path)


def test_live_launcher_selects_native_config_or_rejects_non_mac(tmp_path):
    process,_=launcher(tmp_path,live=True)
    try:
        if sys.platform!='darwin':
            assert process.wait(timeout=5)!=0 and 'macOS' in output(tmp_path)[1]
            assert not (tmp_path/'station.json').exists();return
        ready(process,tmp_path)
        assert 'demo-mac-camera.toml' in json.loads((tmp_path/'station.json').read_text())['argv']
        assert 'unverified' in output(tmp_path)[0]
        process.send_signal(signal.SIGINT);assert process.wait(timeout=3)==0
        assert_reaped(tmp_path)
    finally:cleanup(process,tmp_path)


@pytest.mark.parametrize('sig',[signal.SIGINT,signal.SIGTERM])
def test_interrupt_during_spawn_reaps_the_new_child(tmp_path,sig):
    process,_=launcher(tmp_path,delayed_spawn=True)
    try:
        wait_until(lambda:(tmp_path/'station.json').exists())
        process.send_signal(sig);assert process.wait(timeout=3)==0
        assert_reaped(tmp_path)
    finally:cleanup(process,tmp_path)


def test_unready_service_times_out_by_name_and_port_and_is_killed_and_reaped(tmp_path):
    process,ports=launcher(tmp_path,hang='ground',timeout=.4,ignore_term=True)
    try:
        assert process.wait(timeout=4)!=0
        stderr=output(tmp_path)[1]
        assert 'ground' in stderr and str(ports['ground']) in stderr and 'ready' in stderr
        assert not (tmp_path/'station.json').exists()
        assert_reaped(tmp_path)
    finally:cleanup(process,tmp_path)


def test_occupied_port_is_rejected_without_starting_any_child(tmp_path):
    with socket.socket() as blocker:
        blocker.bind(('127.0.0.1',0));blocker.listen()
        ports={name:free_port() for name in NAMES};ports['ground']=blocker.getsockname()[1]
        process,_=launcher(tmp_path,ports=ports)
        try:
            assert process.wait(timeout=3)!=0
            stderr=output(tmp_path)[1]
            assert 'ground' in stderr and str(ports['ground']) in stderr and 'in use' in stderr
            assert not any((tmp_path/(name+'.json')).exists() for name in NAMES)
        finally:cleanup(process,tmp_path)


def test_occupied_udp_port_is_rejected_without_starting_any_child(tmp_path):
    with socket.socket(type=socket.SOCK_DGRAM) as blocker:
        blocker.bind(('127.0.0.1',0))
        port=blocker.getsockname()[1]
        process,_=launcher(tmp_path,udp_port=port)
        try:
            assert process.wait(timeout=3)!=0
            stderr=output(tmp_path)[1]
            assert 'ground UDP' in stderr and str(port) in stderr and 'in use' in stderr
            assert not any((tmp_path/(name+'.json')).exists() for name in NAMES)
        finally:cleanup(process,tmp_path)
