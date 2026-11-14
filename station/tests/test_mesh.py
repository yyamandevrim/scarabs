"""Meshtastic adapter against a fake interface and bus; no radio, no meshtastic package."""
from dataclasses import replace
import errno
import sys
from threading import Event
from types import SimpleNamespace
import pytest
from conftest import wait_until
from station.lora import mesh
from station.lora.mesh import MeshtasticLink, LinkDown, assess, Refused, djb2, OVERHEAD, PRIVATE_APP
from station.lora.protocol import Packet, Kind, encode, decode
from station.lora.radio import Radio, BANDS, sub_band_for
from station.lora.bridge import LoraConfig

EVENT = '1234567890abcdef1234567890abcdef'
RAW = encode(Packet(Kind.SMOKE, 1, 42, 0, 1700000000, 3600, dict(event_id=EVENT, camera=0, recorded=False, bearing_cd=29000, width=40, height=50, confidence=83)))


def lora(**kw):
    values = dict(region=3, use_preset=True, modem_preset=0, bandwidth=0, spread_factor=0, coding_rate=0, frequency_offset=0.,
                  tx_enabled=True, tx_power=0, channel_num=0, override_duty_cycle=False, override_frequency=0.)
    return SimpleNamespace(**(values | kw))


class Bus:
    def __init__(self):
        self.listeners = {}
    def subscribe(self, fn, topic):
        self.listeners.setdefault(topic, []).append(fn)
    def unsubscribe(self, fn, topic):
        self.listeners[topic].remove(fn)
    def publish(self, topic, **kw):
        # pypubsub delivers subtopics to parent-topic listeners.
        for name, fns in self.listeners.items():
            if topic == name or topic.startswith(name+'.'):
                for fn in list(fns):
                    fn(**kw)


class FakeInterface:
    def __init__(self, config=None, channels=None, fail_send=None):
        self.localNode = SimpleNamespace(localConfig=SimpleNamespace(lora=config or lora()),
                                         getChannelByChannelIndex=lambda i: (channels or {0: SimpleNamespace(role=1, settings=SimpleNamespace(name=''))}).get(i))
        self.myInfo = SimpleNamespace(my_node_num=0x1234abcd)
        self.metadata = SimpleNamespace(firmware_version='2.0.0.test')
        self.isConnected = Event(); self.isConnected.set()
        self.sent, self.closed, self.fail_send = [], False, fail_send
    def getMyNodeInfo(self):
        return {'user': {'id': '!1234abcd', 'hwModel': 'TEST_BOARD'}}
    def sendData(self, data, **kw):
        if self.fail_send:
            raise self.fail_send
        self.sent.append((data, kw))
    def close(self):
        self.closed = True


def link_with(*results, transmit=True, **kw):
    """Each connect attempt consumes one result: an interface or an exception."""
    bus, attempts = Bus(), list(results)
    def connect():
        item = attempts.pop(0) if len(attempts) > 1 else attempts[0]
        if isinstance(item, BaseException):
            raise item
        return item
    return MeshtasticLink(port='/dev/fake-node', connect=connect, bus=bus, retry_seconds=.02, transmit=transmit, **kw), bus


def packet_from(iface, payload, portnum='PRIVATE_APP', **kw):
    return dict(packet=dict(decoded=dict(portnum=portnum, payload=payload), rxRssi=-71, rxSnr=6.25, fromId='!00c0ffee', **kw), interface=iface)


def test_radio_overhead_and_433_band_follow_cited_rules():
    assert BANDS['433.05-434.79'] == (433.05, 434.79, .1)
    plain, wrapped = Radio(11, 250000, 1, preamble=16), Radio(11, 250000, 1, preamble=16, overhead=OVERHEAD)
    assert wrapped.airtime(42) == plain.airtime(42+OVERHEAD) > plain.airtime(42)
    with pytest.raises(ValueError):
        Radio(overhead=250).airtime(48)
    assert sub_band_for(869.4, 869.65) == '869.4-869.65' and sub_band_for(433.0, 433.25) is None


@pytest.mark.parametrize('preset,sf,bw,cr', [(0, 11, 250000, 1), (1, 12, 125000, 4), (4, 9, 250000, 1), (6, 7, 250000, 1), (7, 11, 125000, 4)])
def test_eu868_presets_map_to_the_10_percent_sub_band(preset, sf, bw, cr):
    a = assess(lora(modem_preset=preset))
    assert (a['radio'].sf, a['radio'].bandwidth, a['radio'].coding_rate, a['radio'].preamble) == (sf, bw, cr, 16)
    assert a['sub_band'] == '869.4-869.65' and a['duty_limit'] == .1 and a['region'] == 'EU_868'


@pytest.mark.parametrize('config,message', [
    (lora(region=0), 'unset'), (lora(region=1), 'US'), (lora(region='KR'), 'KR'), (lora(override_duty_cycle=True), 'duty'),
    (lora(tx_enabled=False), 'transmit'), (lora(modem_preset=2), 'VERY_LONG_SLOW'), (lora(modem_preset=8), 'fit'),
    (lora(tx_power=30), 'tx_power'), (lora(region=2), 'channel_num'), (lora(override_frequency=868.1), 'sub-band'),
    (lora(use_preset=False, bandwidth=62, spread_factor=12, coding_rate=8), 'Unsupported')])
def test_region_and_phy_refusals(config, message):
    with pytest.raises(Refused, match=message):
        assess(config)


def test_eu433_needs_a_determined_legal_slot():
    # Slot 1 (433.0-433.25 MHz) would cross the g1 lower edge 433.05 MHz.
    with pytest.raises(Refused):
        assess(lora(region=2, channel_num=1))
    a = assess(lora(region=2, channel_num=2))
    assert a['centres_mhz'] == [433.375] and a['sub_band'] == '433.05-434.79' and a['duty_limit'] == .1
    # A named primary channel fixes the firmware's djb2 slot: 'acorn' -> 0, 'acorn-test' -> 1.
    with pytest.raises(Refused):
        assess(lora(region=2), primary_name='acorn')
    assert assess(lora(region=2), primary_name='acorn-test')['centres_mhz'] == [433.375]
    assert djb2('') == 5381 and djb2('a') == 5381*33+97


def test_send_receive_exact_bytes_on_private_port():
    iface = FakeInterface()
    link, bus = link_with(iface)
    try:
        wait_until(lambda: link.ready)
        assert link.status()['region'] == 'EU_868' and link.status()['node']['node_id'] == '!1234abcd'
        assert link.radio == Radio(11, 250000, 1, preamble=16, overhead=OVERHEAD)
        link.send(RAW, .1)
        data, kw = iface.sent[0]
        assert data == RAW and kw['portNum'] == PRIVATE_APP == 256 and kw['wantAck'] is False and kw['hopLimit'] == 0 and kw['destinationId'] == '^all'
        bus.publish('meshtastic.receive.data.PRIVATE_APP', **packet_from(iface, RAW))
        assert link.receive() == RAW and decode(RAW).data['event_id'] == EVENT
        assert link.status()['last_rx'] | dict(at=0) == dict(at=0, size=42, rssi=-71, snr=6.25, from_id='!00c0ffee', hop_start=None, hop_limit=None)
    finally:
        link.close()


def test_garbage_foreign_and_wrong_length_packets_are_counted_never_raised():
    iface, other = FakeInterface(), FakeInterface()
    link, bus = link_with(iface)
    try:
        wait_until(lambda: link.ready)
        for kwargs in (packet_from(iface, b'hello', portnum='TEXT_MESSAGE_APP'), dict(packet='garbage', interface=iface),
                       dict(packet=dict(decoded='x'), interface=iface), dict(packet={}, interface=iface)):
            bus.publish('meshtastic.receive', **kwargs)
        for payload in (b'', b'x'*49, 'text', None):
            bus.publish('meshtastic.receive', **packet_from(iface, payload, portnum=256))
        bus.publish('meshtastic.receive', **packet_from(other, RAW))  # another interface in-process
        bus.publish('meshtastic.receive', **packet_from(iface, b'\x00'*42))  # right size, wrong bytes
        assert link.receive() == b'\x00'*42  # decode/CRC rejection is the receiver's job
        assert link.receive() is None
        s = link.status()
        assert (s['ignored'], s['malformed'], s['ready']) == (4, 4, True)
        with pytest.raises(ValueError):
            link.send(b'x'*49, .1)
    finally:
        link.close()


def test_absent_busy_missing_library_and_refused_states_are_never_ready():
    cases = [(FileNotFoundError(errno.ENOENT, 'Serial port not found', '/dev/fake-node'), 'absent'),
             (OSError(errno.EBUSY, 'Resource busy'), 'busy'),
             (Exception('Could not exclusively lock port /dev/fake-node'), 'busy'),
             (ModuleNotFoundError('Install the optional extra: uv sync --extra meshtastic'), 'unavailable'),
             (SystemExit(1), 'error'),
             (FakeInterface(lora(region=0)), 'refused')]
    for result, state in cases:
        link, _ = link_with(result)
        try:
            wait_until(lambda: link.state == state)
            assert not link.ready and link.radio is None and 'connected' not in link.label.replace('disconnected', '')
            with pytest.raises(LinkDown):
                link.send(RAW, .1)
            if isinstance(result, FakeInterface):
                assert result.closed and 'unset' in link.status()['detail']  # port released for fixing config
        finally:
            link.close()


def test_disconnect_mid_run_then_reconnect():
    first, second = FakeInterface(), FakeInterface()
    link, bus = link_with(first, OSError(errno.ENOENT, 'No such file'), second)
    try:
        wait_until(lambda: link.ready)
        bus.publish('meshtastic.connection.lost', interface=first)
        assert not link.ready
        with pytest.raises(LinkDown):
            link.send(RAW, .1)
        wait_until(lambda: link.ready and link.iface is second)
        assert first.closed
        second.isConnected.clear()  # silent drop without a lost event
        wait_until(lambda: second.closed)
    finally:
        link.close()


def test_send_failure_marks_link_down_without_crashing():
    iface = FakeInterface(fail_send=OSError(errno.EIO, 'Input/output error'))
    link, _ = link_with(iface)
    try:
        wait_until(lambda: link.ready)
        with pytest.raises(LinkDown):
            link.send(RAW, .1)
        assert link.state == 'disconnected' and 'Input/output' in link.status()['detail']
    finally:
        link.close()


def test_receive_only_link_never_transmits_and_accepts_tx_disabled_node():
    iface = FakeInterface(lora(tx_enabled=False))
    link, _ = link_with(iface, transmit=False)
    try:
        wait_until(lambda: link.ready)
        with pytest.raises(LinkDown):
            link.send(RAW, .1)
        assert iface.sent == []
    finally:
        link.close()


def test_secondary_channel_must_exist():
    iface = FakeInterface(channels={0: SimpleNamespace(role=1, settings=SimpleNamespace(name=''))})
    link, _ = link_with(iface, channel_index=1)
    try:
        wait_until(lambda: link.state == 'refused')
        assert 'index 1' in link.status()['detail']
    finally:
        link.close()


def test_library_absent_reports_unavailable(monkeypatch):
    monkeypatch.setitem(sys.modules, 'meshtastic', None)
    monkeypatch.setitem(sys.modules, 'pubsub', None)
    link = MeshtasticLink(port='/dev/fake-node', retry_seconds=.02)
    try:
        wait_until(lambda: link.state == 'unavailable')
        assert 'extra meshtastic' in link.status()['detail']
    finally:
        link.close()


def test_config_selects_meshtastic_but_simulated_stays_default():
    assert LoraConfig().transport == 'simulated'
    assert LoraConfig(transport='meshtastic', mesh_port='/dev/x').mesh_hop_limit == 0
    with pytest.raises(ValueError):
        LoraConfig(transport='meshtastic')
    with pytest.raises(ValueError):
        LoraConfig(transport='meshtastic', mesh_port='/dev/x', mesh_ble='AA:BB')


def test_station_bridge_waits_for_read_back_band_and_shows_absent(config, monkeypatch):
    from station.runtime import Station
    from test_capture import EmptyDetector
    iface, bus = FakeInterface(), Bus()
    attempts = [FileNotFoundError(errno.ENOENT, 'Serial port not found'), iface]
    gate = Event()
    def connect(self):
        item = attempts.pop(0) if len(attempts) > 1 else attempts[0]
        if isinstance(item, BaseException):
            raise item
        gate.wait(5)
        return item
    hold = Event()
    monkeypatch.setattr(mesh.MeshtasticLink, '_library_connect', lambda self: (hold.wait(5), connect(self))[1])
    original = mesh.MeshtasticLink._ensure_bus
    def ensure(self):
        self._bus = self._bus or bus
        original(self)
    monkeypatch.setattr(mesh.MeshtasticLink, '_ensure_bus', ensure)
    station = Station(replace(config, lora=LoraConfig(enabled=True, transport='meshtastic', mesh_port='/dev/fake-node', mesh_retry_seconds=.02, repeats=0)), detector=EmptyDetector())
    try:
        bridge = station.lora; bridge.started = 1000
        assert bridge.sender is None and bridge.step(1000) is None and iface.sent == []
        hold.set()
        wait_until(lambda: bridge.link.state == 'absent')
        status = bridge.radio_status()
        assert status['state'] == 'absent' and not status['ready'] and bridge.step(1001) is None
        gate.set()
        wait_until(lambda: bridge.link.ready)
        raw = bridge.step(2000)
        assert raw and iface.sent[-1][0] == raw and decode(raw).kind == Kind.STATUS
        assert bridge.sender.radio.overhead == OVERHEAD
        assert bridge.sender.budget.path.name == 'lora-duty-meshtastic-869.4-869.65.json'
        assert bridge.radio_status()['sub_band'] == '869.4-869.65'
        attempts[:] = [FileNotFoundError(errno.ENOENT, 'Serial port not found')]  # unplugged
        bus.publish('meshtastic.connection.lost', interface=iface)
        assert bridge.step(5000) is None and bridge.radio_status()['state'] in ('disconnected', 'connecting', 'absent')
        wait_until(lambda: bridge.link.state == 'absent')
        assert iface.closed and bridge.step(6000) is None
    finally:
        station.stop(); station.store.shutdown()
