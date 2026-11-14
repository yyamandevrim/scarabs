"""Overview assets and packet-demo contracts."""
from fastapi.testclient import TestClient
from forest_placement import api

def test_overview_local_assets_and_scoped_wasm_policy():
    import gzip
    with TestClient(api.app) as client:
        model=client.get('/static/hardware/acorn.glb')
        assert model.status_code==200 and model.content[:4]==b'glTF'
        assert len(model.content)<300_000
        bundle=client.get('/static/vendor/landing-3d.js')
        assert bundle.status_code==200 and len(gzip.compress(bundle.content))<200_000
        for asset in ('/static/hardware/acorn-poster.webp','/static/hardware/acorn-poster-phone.webp',
                      '/static/demo/iphone-station-cameras.webp','/static/demo/iphone-station-evidence.webp',
                      '/static/demo/evidence.webp','/static/demo/map-terrain-interim.webp'):
            assert client.get(asset).status_code==200
        assert "'wasm-unsafe-eval'" in client.get('/').headers['Content-Security-Policy']
        assert "'wasm-unsafe-eval'" not in client.get('/map').headers['Content-Security-Policy']


def test_demo_packets_decode_with_the_real_station_codec(monkeypatch):
    import json
    import subprocess
    import base64
    from pathlib import Path
    root=Path(__file__).resolve().parents[2]
    monkeypatch.syspath_prepend(str(root/'station'))
    from station.lora.protocol import decode,Kind
    source=(root/'placement/static/radio-packet.js').read_bytes()
    module='data:text/javascript;base64,'+base64.b64encode(source).decode()
    code=f"import {{encodeSmoke,encodeStatus}} from '{module}'; console.log(JSON.stringify({{smoke:['centre','right','left'].map(c=>[...encodeSmoke(c)]),status:[...encodeStatus()]}}));"
    result=json.loads(subprocess.check_output(['node','--input-type=module','-e',code],text=True))
    for raw,bearing in zip(result['smoke'],[0,12000,24000]):
        packet=decode(bytes(raw))
        assert len(raw)==42 and packet.kind==Kind.SMOKE
        assert packet.data['bearing_cd']==bearing and packet.data['confidence']==59
    status=decode(bytes(result['status']))
    assert len(result['status'])==40 and status.kind==Kind.STATUS
    assert status.contact_after==15 and status.duty_hold
