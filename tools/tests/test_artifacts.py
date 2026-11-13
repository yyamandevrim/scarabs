import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import pytest

TOOLS=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('artifacts',TOOLS/'artifacts.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)

def test_pinned_manifest_and_exclusions():
    m=a.load_manifest(a.MANIFEST)
    assert len(m['artifacts'])==13
    assert all(e.get('licence') and e.get('source') and e['size']>0 for e in m['artifacts'])
    assert 'station/media/fog.webm' not in {e['path'] for e in m['artifacts']}
    assert any('fog.webm' in e['path'] for e in m['excluded'])

def test_upload_and_restore_dry_run_without_credentials_or_sdk():
    # python -S removes site-packages: dry-run must not need boto3 or network.
    for script,verb in [('upload_artifacts.py','WOULD UPLOAD'),('restore_artifacts.py','WOULD RESTORE')]:
        r=subprocess.run([sys.executable,'-S',str(TOOLS/script),'--dry-run'],capture_output=True,text=True,env={},check=True)
        assert verb in r.stdout and 'sha256:' in r.stdout and '13 artifacts' in r.stdout
        assert 'EXCLUDED\tstation/media/fog.webm' in r.stdout

def test_manifest_regeneration_matches_pinned_bytes():
    assert a.inventory()==json.loads(a.MANIFEST.read_text())

@pytest.mark.parametrize('path',['../../secret','station/config.toml','placement/data/raw/private','/etc/passwd'])
def test_paths_are_restricted(path):
    with pytest.raises(ValueError):a.local_path(a.ROOT,path)

def test_rejects_tampered_manifest_and_symlinks(tmp_path):
    m=json.loads(a.MANIFEST.read_text());m['artifacts'][0]['sha256']='not a hash'
    path=tmp_path/'manifest.json';path.write_text(json.dumps(m))
    with pytest.raises(ValueError):a.load_manifest(path)
    root=tmp_path/'repo';(root/'station').mkdir(parents=True);(root/'station/models').symlink_to(tmp_path)
    with pytest.raises(ValueError):a.local_path(root,'station/models/smoke.onnx')

def test_upload_refuses_changed_artifact(tmp_path):
    m={'schema':1,'artifacts':[{'path':'station/models/smoke.onnx','size':3,'sha256':'0'*64,'source':'source','licence':'AGPL-3.0-only'}]}
    (tmp_path/'tools').mkdir();manifest=tmp_path/'tools/artifacts-manifest.json';manifest.write_text(json.dumps(m))
    (tmp_path/'station/models').mkdir(parents=True);(tmp_path/'station/models/smoke.onnx').write_bytes(b'bad')
    with pytest.raises(ValueError,match='differs from manifest'):a.main('upload',['--dry-run'],root=tmp_path)
