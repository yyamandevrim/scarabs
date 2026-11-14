"""Ground receive path over a fake Meshtastic interface; no radio or meshtastic package."""
import errno
from threading import Event
import time
from types import SimpleNamespace
import httpx
from fastapi.testclient import TestClient
from station.lora.mesh import MeshtasticLink, OVERHEAD
from station.lora.protocol import Packet, Kind, encode
from station.lora.radio import Radio
from ground.receiver import Receiver, Listener
from ground.web import create_app
from ground.wifi import Wifi

EVENT = '1234567890abcdef1234567890abcdef'
RAW = encode(Packet(Kind.SMOKE, 1, 42, 0, 1700000000, 3500, dict(event_id=EVENT, camera=0, bearing_cd=29000, width=80, height=90, confidence=85)))


class Bus:
    def __init__(self):
        self.listeners = {}
    def subscribe(self, fn, topic):
        self.listeners.setdefault(topic, []).append(fn)
    def unsubscribe(self, fn, topic):
        self.listeners[topic].remove(fn)
    def publish(self, topic, **kw):
        for name, fns in self.listeners.items():
            if topic == name or topic.startswith(name+'.'):
                for fn in list(fns):
                    fn(**kw)


def interface(region=3):
    lora = SimpleNamespace(region=region, use_preset=True, modem_preset=0, tx_enabled=False, tx_power=0, channel_num=0,
                           override_duty_cycle=False, override_frequency=0., frequency_offset=0.)
    iface = SimpleNamespace(localNode=SimpleNamespace(localConfig=SimpleNamespace(lora=lora), getChannelByChannelIndex=lambda i: None),
                            isConnected=Event(), closed=False, sent=[])
    iface.isConnected.set()
    iface.close = lambda: setattr(iface, 'closed', True)
    iface.sendData = lambda *a, **k: iface.sent.append(a)
    return iface


def wait(predicate, timeout=3):
    deadline = time.monotonic()+timeout
    while time.monotonic() < deadline and not predicate():
        time.sleep(.02)
    assert predicate()


def ground(tmp_path, results):
    bus, attempts = Bus(), list(results)
    def connect():
        item = attempts.pop(0) if len(attempts) > 1 else attempts[0]
        if isinstance(item, BaseException):
            raise item
        return item
    link = MeshtasticLink(port='/dev/fake-node', connect=connect, bus=bus, retry_seconds=.02, transmit=False)
    receiver = Receiver(tmp_path, Radio())
    client = httpx.Client(base_url='http://station.test', transport=httpx.MockTransport(lambda r: httpx.Response(503)))
    app = create_app(receiver, Wifi('http://station.test', 'test-only', tmp_path, client=client), Listener(receiver, link))
    return app, receiver, link, bus


def test_mesh_packets_feed_the_same_decode_path_and_use_node_phy(tmp_path):
    iface = interface()
    app, receiver, link, bus = ground(tmp_path, [iface])
    with TestClient(app) as c:
        wait(lambda: link.ready)
        bus.publish('meshtastic.receive.data.PRIVATE_APP', packet=dict(decoded=dict(portnum='PRIVATE_APP', payload=b'\x01'*42)), interface=iface)
        bus.publish('meshtastic.receive.data.PRIVATE_APP', packet=dict(decoded=dict(portnum='PRIVATE_APP', payload=RAW), rxRssi=-90, rxSnr=-3.5), interface=iface)
        wait(lambda: c.get('/api/state').json()['alerts'])
        state = c.get('/api/state').json()
        assert state['alerts'][0]['event_id'] == EVENT and state['invalid_packets'] == 1
        assert state['link']['ready'] and state['link']['region'] == 'EU_868' and state['link']['last_rx']['rssi'] == -90
        assert state['radio']['sf'] == 11 and state['radio']['overhead'] == OVERHEAD
        assert state['transport'] == 'LoRa link (Meshtastic radio · radio connected)'
        assert iface.sent == []  # ground never transmits
    assert iface.closed


def test_absent_or_unset_region_radio_is_shown_and_never_healthy(tmp_path):
    for result, state, text in ((FileNotFoundError(errno.ENOENT, 'Serial port not found'), 'absent', 'radio absent'),
                                (interface(region=0), 'refused', 'radio refused')):
        app, receiver, link, bus = ground(tmp_path/state, [result])
        with TestClient(app) as c:
            wait(lambda: link.state == state)
            body = c.get('/api/state').json()
            assert body['link']['ready'] is False and body['transport'] == f'LoRa link (Meshtastic radio · {text})'
            assert text in c.get('/').text and body['stations'] == []


def test_simulated_ground_state_has_no_real_link():
    import tempfile
    with tempfile.TemporaryDirectory() as root:
        r = Receiver(root, Radio())
        try:
            s = r.snapshot()
            assert s['link'] is None and s['transport'] == 'LoRa link (simulated transport)'
        finally:
            r.close()
