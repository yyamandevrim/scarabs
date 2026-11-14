"""Overview assets and packet-demo contracts."""
from fastapi.testclient import TestClient
from forest_placement import api

def test_overview_local_assets_and_plain_gltf_budget():
    import gzip
    with TestClient(api.app) as client:
        model=client.get('/static/hardware/acorn.glb')
        assert model.status_code==200 and model.content[:4]==b'glTF'
        assert len(model.content)<400_000
        bundle=client.get('/static/vendor/landing-3d.js')
        assert bundle.status_code==200 and len(gzip.compress(bundle.content))<200_000
        for asset in ('/static/hardware/acorn-poster.webp','/static/hardware/acorn-poster-phone.webp',
                      '/static/demo/event-frame.webp','/static/demo/event-clip.mp4','/static/demo/map-360-desktop.webp','/static/demo/map-360-phone.webp'):
            assert client.get(asset).status_code==200
        import json,struct
        size=struct.unpack_from('<I',model.content,12)[0]
        document=json.loads(model.content[20:20+size])
        assert 'EXT_meshopt_compression' not in document.get('extensionsUsed',[])


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
    assert status.contact_after==12 and status.duty_hold
    assert status.data['pending']==0
    assert len({decode(bytes(raw)).data['event_id'] for raw in result['smoke']})==3
