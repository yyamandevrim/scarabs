"""Deploy from placement/: uv run --group deploy modal deploy modal_app.py.

No account is contacted by importing this module. Only the owner's explicit CLI
commands create resources. The Volume is data-only; results remain ephemeral.
"""
from pathlib import Path
import modal

HERE=Path(__file__).resolve().parent
app=modal.App('forest-observation-placement')
volume=modal.Volume.from_name('forest-placement-data',create_if_missing=True,version=2)
image=(modal.Image.debian_slim(python_version='3.12')
       .pip_install('uv==0.12.1')
       .add_local_file(HERE/'pyproject.toml','/opt/placement/pyproject.toml',copy=True)
       .add_local_file(HERE/'uv.lock','/opt/placement/uv.lock',copy=True)
       .run_commands('cd /opt/placement && uv sync --frozen --no-dev')
       .env({'PATH':'/opt/placement/.venv/bin:/usr/local/bin:/usr/bin:/bin',
             'PYTHONPATH':'/opt/placement','NUMBA_CPU_NAME':'generic',
             'NUMBA_CACHE_DIR':'/opt/numba-cache',
             'PLACEMENT_PREPARED':'/data/prepared','PLACEMENT_CACHE':'/tmp/placement-results',
             'PLACEMENT_PRODUCTION':'1'})
       .add_local_dir(HERE/'forest_placement','/opt/placement/forest_placement',copy=True,ignore=['__pycache__','*.pyc','*.nbc','*.nbi'])
       .add_local_dir(HERE/'static','/opt/placement/static',copy=True)
       .add_local_file(HERE/'brand.json','/opt/placement/brand.json',copy=True)
       .run_commands('python -m forest_placement.warmup'))

@app.function(image=image,volumes={'/data':volume.read_only()},cpu=2,memory=2048,
              include_source=False,min_containers=0,max_containers=1,scaledown_window=120,timeout=120)
@modal.concurrent(max_inputs=16)
@modal.asgi_app()
def web():
    from forest_placement.api import app as api
    return api

@app.local_entrypoint()
def load_data():
    """One-time owner-only authenticated CLI upload; no public write endpoint."""
    required=('metadata.json','coarse.npz','detailed.npz','map.json','background.png','forest.png','water.png')
    for filename in required:
        if not (HERE/'data/prepared'/filename).is_file():
            raise FileNotFoundError(f'Missing prepared artifact: {filename}; restore or prepare data first.')
    with volume.batch_upload(force=True) as batch:
        for filename in required:
            batch.put_file(HERE/'data/prepared'/filename,'/prepared/'+filename)
