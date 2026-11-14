"""No network calls: retry the real fetch path against deterministic HTTP responses."""
import importlib.util
import io
from pathlib import Path
from urllib.error import HTTPError
import pytest

spec=importlib.util.spec_from_file_location('footage_fetch',Path(__file__).parents[1]/'scripts/fetch_footage.py')
f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)

def test_429_honours_retry_after_and_cleans_partial(tmp_path,monkeypatch):
    attempts=[];sleeps=[]
    def open_url(req,timeout):
        attempts.append(req)
        if len(attempts)==1:raise HTTPError(req.full_url,429,'Slow down',{'Retry-After':'45'},None)
        if len(attempts)==2:raise HTTPError(req.full_url,429,'Slow down',{},None)
        return io.BytesIO(b'verified-video-bytes')
    monkeypatch.setattr(f.urllib.request,'urlopen',open_url)
    monkeypatch.setattr(f.time,'sleep',sleeps.append)
    target=tmp_path/'clip.part';f.download('https://media.example/clip',target)
    assert target.read_bytes()==b'verified-video-bytes'
    assert sleeps==[45,60] and len(attempts)==3

def test_permanent_errors_are_not_retried(tmp_path,monkeypatch):
    def unavailable(*args,**kwargs):raise HTTPError('https://media.example',404,'Missing',{},None)
    monkeypatch.setattr(f.urllib.request,'urlopen',unavailable)
    with pytest.raises(HTTPError):f.download('https://media.example/clip',tmp_path/'clip.part')
    assert not (tmp_path/'clip.part').exists()
