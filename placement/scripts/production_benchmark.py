"""Local production-mode startup and HTTP timings; does not access Modal."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import httpx
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from forest_placement.models import PRESETS

root=Path(__file__).resolve().parents[1]
records=[]
with tempfile.TemporaryDirectory(prefix='placement-production-') as temp:
    for phase in ('empty-jit-cache','image-like-jit-cache'):
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
        env={**os.environ,'PLACEMENT_PRODUCTION':'1','NUMBA_CPU_NAME':'generic','NUMBA_CACHE_DIR':temp+'/numba','PLACEMENT_CACHE':temp+'/'+phase,'PLACEMENT_PREPARED':str(root/'data/prepared')}
        log=open(Path(temp)/(phase+'.log'),'w')
        start=time.perf_counter()
        process=subprocess.Popen([sys.executable,'-m','uvicorn','forest_placement.api:app','--host','127.0.0.1','--port',str(port),'--no-proxy-headers'],cwd=root,env=env,stdout=log,stderr=log)
        try:
            with httpx.Client(base_url=f'http://127.0.0.1:{port}',timeout=30) as client:
                while True:
                    if process.poll() is not None:raise RuntimeError('ASGI server failed to start')
                    try:
                        if client.get('/api/config').status_code==200:break
                    except httpx.ConnectError:pass
                    if time.perf_counter()-start>30:raise TimeoutError('ASGI startup exceeded 30s')
                    time.sleep(.025)
                record=dict(phase=phase,startup_seconds=round(time.perf_counter()-start,4),requests=[])
                for resolution in ('coarse','detailed'):
                    for preset in PRESETS:
                        candidate=preset.model_dump();candidate['resolution']=resolution
                        for cached in (False,True):
                            before=time.perf_counter();r=client.post('/api/analyze',json=candidate);seconds=time.perf_counter()-before
                            r.raise_for_status();result=r.json();assert result['cached']==cached
                            record['requests'].append(dict(preset=preset.name,resolution=resolution,cached=cached,http_seconds=round(seconds,4),compute_seconds=result['computed_seconds']))
                records.append(record);print(json.dumps(record),flush=True)
        finally:
            process.terminate();process.wait(timeout=10);log.close()
Path('production-timings.json').write_text(json.dumps(records,indent=2)+'\n')
