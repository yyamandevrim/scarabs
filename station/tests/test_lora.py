import binascii
from dataclasses import replace
import math
import struct
import uuid
import pytest
from station.lora.protocol import Packet, Kind, encode, decode, bearing, MAX_PAYLOAD, HEADER
from station.lora.radio import Radio, DutyBudget
from station.lora.sender import Sender
from station.lora.transport import SimulatedLink, SerialModem
from station.lora.bridge import LoraBridge, LoraConfig

EVENT = '1234567890abcdef1234567890abcdef'
DATA = {Kind.SMOKE:dict(event_id=EVENT,camera=0,recorded=False,bearing_cd=29000,width=40,height=50,confidence=83),Kind.FLAME:dict(event_id=EVENT,source='unknown'),Kind.DECISION:dict(event_id=EVENT,decision=1),Kind.STATUS:dict(active=3,lost=2,pending=4,uptime=100,battery=None,heading_cd=0,yaw=[-7000,0,7000],hfov=[80,80,80])}
def packet(kind=Kind.SMOKE, **kw):
    return Packet(kind, 1, 42, 0, 1700000000, 3600, DATA[kind] | kw)

@pytest.mark.parametrize('kind,size', [(Kind.SMOKE,42),(Kind.FLAME,37),(Kind.DECISION,37),(Kind.STATUS,40)])
def test_packet_roundtrip_size(kind,size):
    p=packet(kind);raw=encode(p)
    assert len(raw)==size<=MAX_PAYLOAD
    assert decode(raw)==p

@pytest.mark.parametrize('kind',list(Kind))
def test_corruption_every_byte_and_truncation(kind):
    raw=encode(packet(kind))
    for i in range(len(raw)):
        corrupt=bytearray(raw);corrupt[i]^=1
        with pytest.raises(ValueError):decode(bytes(corrupt))
    for length in range(len(raw)):
        with pytest.raises(ValueError):decode(raw[:length])

def test_unknown_version_and_semantics_even_with_valid_crc():
    raw=bytearray(encode(packet()));raw[1]=0x31
    raw[-2:]=struct.pack('>H',binascii.crc_hqx(raw[:-2],0xffff))
    with pytest.raises(ValueError):decode(bytes(raw))
    for values in (dict(camera=3),dict(confidence=101),dict(bearing_cd=36000)):
        with pytest.raises(ValueError):encode(packet(**values))

@pytest.mark.parametrize('heading,yaw,box,fov,expected',[(0,0,(.4,.1,.6,.9),80,0),(10,-70,(.4,0,.6,1),80,300),(350,20,(0,0,1,1),80,10),(0,0,(1,0,1,1),80,40),(0,0,(0,0,0,1),80,320),(0,0,(.75,0,.75,1),90,math.degrees(math.atan(.5)))])
def test_bearing_projection(heading,yaw,box,fov,expected):
    assert bearing(heading,yaw,box,fov)==pytest.approx(expected)

@pytest.mark.parametrize('fov', [0,180,float('nan')])
def test_invalid_bearing(fov):
    with pytest.raises(ValueError):bearing(0,0,(0,0,1,1),fov)

# Exact formula vector: 10 bytes, SF7, BW125, CR4/5, explicit header,
# CRC enabled, preamble 8 => 41.216 ms.
# Semtech AN1200.86 Fig 6 rounds 11-byte SF7/9/10 to .04/.14/.29 s; SF12 CRC-enabled vector is separate.
@pytest.mark.parametrize('sf,size,expected',[(7,10,.041216),(7,11,.041216),(9,11,.144384),(10,11,.288768),(12,11,1.155072),(12,40,1.974272),(10,40,.534528)])
def test_airtime_reference(sf,size,expected):
    assert Radio(sf).airtime(size)==pytest.approx(expected)

def test_airtime_bandwidth_coding_rate_and_occupied_band():
    assert Radio(10,250000).airtime(40)<Radio().airtime(40)
    assert Radio(coding_rate=4).airtime(40)>Radio().airtime(40)
    assert Radio().band_limit('868.0-868.6',868.3)==.01
    with pytest.raises(ValueError):Radio().band_limit('868.0-868.6',868.01)
    with pytest.raises(ValueError):LoraConfig(duty_fraction=.1)

def test_rolling_duty_persistence_and_clock_reversal(tmp_path):
    path=tmp_path/'duty.json';b=DutyBudget(.01,path=path)
    assert b.reserve(20,1000) and not b.reserve(17,1001)
    assert b.remaining(1002)==16
    b=DutyBudget(.01,path=path)
    assert b.remaining(1002)==16 and not b.reserve(1,999)
    assert b.remaining(4619)==16  # full TX duration accounted until end + hour
    assert b.remaining(4620)==36
    path.write_text('bad json')
    assert DutyBudget(.01,path=path).remaining(1)==0

class FakeLink:
    def __init__(self):self.raw=[]
    def send(self,payload,airtime):self.raw.append(payload)

def test_priority_repeats_bounded_heartbeat_yields():
    link=FakeLink();s=Sender(link,Radio(),DutyBudget(.01),repeats=2,repeat_interval=5)
    s.enqueue(packet(Kind.STATUS),0)
    s.enqueue(packet(),0)
    assert decode(s.tick(0)).kind==Kind.SMOKE
    s.enqueue(packet(event_id=uuid.uuid4().hex),s.slot_seconds)
    assert decode(s.tick(s.slot_seconds)).data['event_id']!=EVENT  # new first, before due repeat
    for now in range(2*s.slot_seconds,8*s.slot_seconds,s.slot_seconds):s.tick(now)
    alerts=[decode(x) for x in link.raw if decode(x).kind==Kind.SMOKE]
    assert sum(p.data['event_id']==EVENT for p in alerts)==3
    assert decode(link.raw[-1]).kind==Kind.STATUS
    assert len({p.sequence for p in alerts})==6
    assert s.tick(1000) is None

def test_duty_refusal_keeps_alert_and_heartbeat_yields_after_ledger_recovers():
    link=FakeLink();budget=DutyBudget(.001);s=Sender(link,Radio(),budget)
    budget.reserve(3.2,0)
    s.enqueue(packet(Kind.STATUS),0)
    assert s.tick(0) is None
    s.enqueue(packet(),0)
    assert s.tick(0) is None
    assert s.refused==2
    assert decode(s.tick(3604)).kind==Kind.SMOKE


def test_queue_bounded_and_repeat_evictable():
    s=Sender(FakeLink(),Radio(),DutyBudget(),max_queue=2)
    assert s.enqueue(packet(),0,priority=2)
    assert s.enqueue(packet(),0)
    assert s.enqueue(packet(Kind.FLAME),0)
    assert len(s.queue)==2 and not s.enqueue(packet(),0)

def test_udp_exact_bytes_loss_and_serial_skeleton():
    receiver=SimulatedLink(bind=('127.0.0.1',0))
    sender=SimulatedLink(peer=receiver.socket.getsockname(),loss=0,delay=False)
    try:
        raw=encode(packet());sender.send(raw,.1);assert receiver.receive()==raw
        sender.loss=1;sender.send(raw,.1);assert receiver.receive() is None
        with pytest.raises(ValueError):sender.send(bytes(49),.1)
        with pytest.raises(NotImplementedError):SerialModem('/dev/unselected')
    finally:sender.close();receiver.close()

def test_bridge_uses_event_uuid_and_separate_flame(config):
    from station.runtime import Station
    from station.alarm import Detection
    from test_capture import EmptyDetector
    cfg=replace(config,lora=LoraConfig(enabled=True,airtime_delay=False))
    station=Station(cfg,detector=EmptyDetector());bridge=station.lora
    try:
        now=bridge.started+1
        event=station.store.create('left',Detection((.4,.2,.6,.8),.8),now)
        flame=station.store.create_flame(now,{})
        bridge.poll(now)
        packets=[entry[3] for entry in bridge.sender.queue]
        assert {p.data['event_id'] for p in packets}=={event,flame}
        smoke=next(p for p in packets if p.kind==Kind.SMOKE)
        assert smoke.data['bearing_cd']==29000
        station.store.decide(event,'confirmed',now+1);bridge.poll(now+1)
        assert any(p[3].kind==Kind.DECISION for p in bridge.sender.queue)
        bridge.heartbeat(now)
        assert decode(encode(bridge.sender.heartbeat)).data['battery'] is None
    finally:station.stop();station.store.shutdown()

@pytest.mark.parametrize('sf,published_seconds',[(7,.04),(9,.14),(10,.29)])
def test_published_semtech_11byte_rounded_reference(sf,published_seconds):
    assert round(Radio(sf).airtime(11),2)==published_seconds

def test_corrected_decision_cancels_old_repeats():
    s=Sender(FakeLink(),Radio(),DutyBudget(),repeat_interval=5)
    s.enqueue(packet(Kind.DECISION,decision=1),0)
    s.tick(0)
    assert len(s.queue)==1
    corrected=replace(packet(Kind.DECISION,decision=2),timestamp=1700000001)
    s.enqueue(corrected,2)
    assert len(s.queue)==1
    assert decode(s.tick(s.slot_seconds)).data['decision']==2
    assert all(x[3].data['decision']==2 for x in s.queue)

def test_transport_error_keeps_limited_retry_and_spends_airtime():
    class Broken(FakeLink):
        def send(self,payload,airtime):raise OSError('modem unavailable')
    b=DutyBudget();s=Sender(Broken(),Radio(),b)
    s.enqueue(packet(),0)
    with pytest.raises(OSError):s.tick(0)
    assert len(s.queue)==1 and b.remaining(1)<36

@pytest.mark.parametrize('sf', [7, 10, 12])
def test_three_hours_of_demo_traffic_stays_legal_and_keeps_contact(sf):
    """4s requested heartbeats + a new recorded suspicion each 55s, not a 4min burst."""
    link=FakeLink();radio=Radio(sf);budget=DutyBudget(.01)
    sender=Sender(link,radio,budget,repeat_interval=5)
    sender.heartbeat_seconds=4
    transmissions=[]
    for now in range(3*3600+1):
        if now%4==0:sender.enqueue(packet(Kind.STATUS),now)
        if now%55==3:sender.enqueue(packet(event_id=uuid.UUID(int=now).hex),now)
        raw=sender.tick(now)
        if raw:
            transmissions.append((now,radio.airtime(len(raw)),decode(raw)))
    safe_interval=sender.slot_seconds
    assert safe_interval=={7:12,10:61,12:241}[sf]
    assert transmissions[-1][0]>10800-safe_interval, 'traffic continues through the final contact window'
    assert max(b[0]-a[0] for a,b in zip(transmissions,transmissions[1:]))<=safe_interval+1
    assert all(b[0]-a[0]<=a[2].contact_after for a,b in zip(transmissions,transmissions[1:]))
    for start,duration,_ in transmissions:
        at=start+duration
        used=sum(max(0,min(t+d,at)-max(t,at-3600)) for t,d,_ in transmissions)
        assert used<=36+1e-8
    assert any(p.kind==Kind.SMOKE for at,_,p in transmissions if at>7200)


def test_restart_preserves_pacing_not_just_hourly_usage(tmp_path):
    path=tmp_path/'duty.json';link=FakeLink()
    first=Sender(link,Radio(),DutyBudget(.01,path=path))
    first.enqueue(packet(),1000);assert first.tick(1000)
    restarted=Sender(link,Radio(),DutyBudget(.01,path=path))
    restarted.enqueue(packet(Kind.FLAME),1001)
    assert restarted.tick(1001) is None

def test_version_one_journals_remain_readable_and_new_contact_is_crc_protected():
    from station.lora.protocol import HEADER_V1, FORMATS
    p=packet()
    body=HEADER_V1.pack(0xac,0x11,p.station,p.boot,p.sequence,p.timestamp,p.remaining_cs)
    body+=FORMATS[1].pack(bytes.fromhex(EVENT),0,29000,40,50,83)
    old=body+struct.pack('>H',binascii.crc_hqx(body,0xffff))
    assert decode(old)==p and decode(old).contact_after==0
    new=encode(replace(p,contact_after=64))
    assert decode(new).contact_after==64
    corrupt=bytearray(new);corrupt[16]^=1
    with pytest.raises(ValueError):decode(bytes(corrupt))

def test_legacy_exhausted_ledger_recovers_when_legal_without_reset(tmp_path):
    path=tmp_path/'duty.json';old=DutyBudget(.01,path=path)
    assert old.reserve(36,1000)
    s=Sender(FakeLink(),Radio(),DutyBudget(.01,path=path))
    s.enqueue(packet(),1001)
    assert s.tick(1001) is None
    assert s.next_tx_at(1100)==4636
    assert s.tick(4636)

def test_bridge_respects_slow_requested_heartbeat_and_refreshes_queued_status(config):
    from station.runtime import Station
    from test_capture import EmptyDetector
    station=Station(replace(config,lora=LoraConfig(enabled=True,heartbeat_seconds=300,airtime_delay=False)),detector=EmptyDetector())
    try:
        bridge=station.lora;bridge.started=1000;link=FakeLink();bridge.sender.link=link
        times=[]
        for second in range(601):
            if bridge.step(1000+second):times.append(second)
        assert times==[0,300,600]
        assert decode(link.raw[-1]).data['uptime']==600
    finally:station.stop();station.store.shutdown()

def test_long_range_burst_then_quiet_heartbeats_keep_the_announced_window():
    sender=Sender(FakeLink(),Radio(12),DutyBudget(.01),repeat_interval=5,heartbeat_seconds=4)
    transmissions=[]
    for now in range(10801):
        if now%4==0:sender.enqueue(packet(Kind.STATUS),now)
        if 1<=now<=5:sender.enqueue(packet(event_id=f'{now:032x}'),now)
        raw=sender.tick(now)
        if raw:transmissions.append((now,decode(raw)))
    assert all(b[0]-a[0]<=a[1].contact_after for a,b in zip(transmissions,transmissions[1:])), 'heartbeat-only traffic must not hit a reserve-induced silence'

def test_partial_legacy_budget_announces_the_real_recovery_window_without_early_refill():
    b=DutyBudget(.01);assert b.reserve(35.7,0)
    s=Sender(FakeLink(),Radio(7),b,repeats=0,heartbeat_seconds=4)
    packets=[]
    for now in (100,112,124):
        s.enqueue(packet(event_id=f'{now:032x}'),now)
        packets.append(decode(s.tick(now)))
    assert packets[-1].contact_after>3400 and packets[-1].duty_hold
    remaining=b.remaining(124)
    assert b.available_at(.1,4000)==4000
    assert b.remaining(124)==pytest.approx(remaining), 'forecasting must never refill the live ledger early'
