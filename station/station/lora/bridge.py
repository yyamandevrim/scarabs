"""Opt-in station outbox; detector and evidence never wait for radio airtime."""
from dataclasses import dataclass, field
import logging
import math
import secrets
from threading import Event, Thread
import time
from .protocol import Packet, Kind, SLOTS, bearing
from .radio import Radio, DutyBudget
from .sender import Sender
from .transport import SimulatedLink, SerialModem

@dataclass
class LoraConfig:
    enabled: bool = False
    transport: str = 'simulated'
    station_id: int = 1
    heading: float = 0.
    peer_host: str = '127.0.0.1'
    peer_port: int = 9901
    sf: int = 10
    bandwidth: int = 125000
    coding_rate: int = 1
    sub_band: str = '868.0-868.6'
    frequency: float = 868.3
    duty_fraction: float = .01
    heartbeat_seconds: float = 300
    repeats: int = 2
    repeat_seconds: float = 30
    loss: float = 0.
    airtime_delay: bool = True
    payload_limit: int = 48
    seed: int | None = None
    serial_port: str = ''
    # transport = "meshtastic": PHY, region and sub-band are read from the node.
    mesh_port: str = ''  # USB serial device of the node (local config only)
    mesh_ble: str = ''  # alternatively a BLE address
    mesh_channel_index: int = 0
    mesh_hop_limit: int = 0
    mesh_destination: str = '^all'
    mesh_retry_seconds: float = 5.

    def __post_init__(self):
        radio = Radio(self.sf, self.bandwidth, self.coding_rate)
        limit = radio.band_limit(self.sub_band, self.frequency)
        if not 0 < self.duty_fraction <= limit:
            raise ValueError('Duty fraction exceeds selected sub-band limit')
        if not 1 <= self.station_id <= 65535 or not math.isfinite(self.heading) or not 0 <= self.heading < 360:
            raise ValueError('Invalid station ID or configured heading')
        if self.heartbeat_seconds < 2 or not 0 <= self.loss <= 1 or not 0 <= self.repeats <= 3 or self.repeat_seconds < 1 or not 42 <= self.payload_limit <= 48:
            raise ValueError('Invalid LoRa queue/link configuration')
        if self.transport not in ('simulated', 'serial', 'meshtastic'):
            raise ValueError('Unknown LoRa transport')
        if self.transport == 'meshtastic' and bool(self.mesh_port) == bool(self.mesh_ble):
            raise ValueError('Meshtastic transport needs exactly one of mesh_port or mesh_ble')

class LoraBridge:
    def __init__(self, station):
        self.station = station
        self.config = c = station.config.lora
        if c.enabled and any(not 1 <= round(camera.hfov) < 180 for camera in station.config.cameras):
            raise ValueError('LoRa bearing projection requires horizontal FOV rounding to 1..179 degrees')
        self.boot = secrets.randbits(32)
        self.started = time.time()
        self.stop_event = Event()
        self.thread = None
        self.seen = set()
        self.decision_cursor = None
        self.error = None
        self.next_heartbeat = 0
        self.sender = None
        self.link = None
        if not c.enabled:
            return
        if c.transport == 'meshtastic':
            # Sender waits for the node's real region/PHY; see attach_radio().
            from .mesh import MeshtasticLink
            self.link = MeshtasticLink(port=c.mesh_port, ble=c.mesh_ble, channel_index=c.mesh_channel_index,
                                       hop_limit=c.mesh_hop_limit, destination=c.mesh_destination,
                                       retry_seconds=c.mesh_retry_seconds)
            return
        self.link = SimulatedLink(peer=(c.peer_host, c.peer_port), loss=c.loss, delay=c.airtime_delay, payload_limit=c.payload_limit, seed=c.seed) if c.transport == 'simulated' else SerialModem(c.serial_port, sf=c.sf, bandwidth=c.bandwidth, coding_rate=c.coding_rate, frequency=c.frequency)
        self.sender = Sender(self.link, Radio(c.sf, c.bandwidth, c.coding_rate),
                             DutyBudget(c.duty_fraction, path=station.config.data_dir/'lora-duty.json'),
                             c.repeats, c.repeat_seconds, heartbeat_seconds=c.heartbeat_seconds)

    def attach_radio(self):
        """Build the sender from the node's read-back band once; refuse a changed PHY."""
        link, c = self.link, self.config
        status = link.status()
        if not status['ready']:
            return False
        if self.sender is not None:
            if self.sender.radio != link.radio:
                raise RuntimeError('Meshtastic PHY changed since start; restart the station to re-account airtime')
            return True
        if c.duty_fraction > status['duty_limit']:
            raise RuntimeError(f"duty_fraction exceeds the {status['sub_band']} MHz sub-band limit")
        # One ledger per real sub-band, separate from the simulated ledger.
        path = self.station.config.data_dir/f"lora-duty-meshtastic-{status['sub_band']}.json"
        self.sender = Sender(link, link.radio, DutyBudget(c.duty_fraction, path=path),
                             c.repeats, c.repeat_seconds, heartbeat_seconds=c.heartbeat_seconds)
        return True

    def radio_status(self):
        """Displayed link state; never reports a healthy real radio it has not read back."""
        if self.link is None:
            return None
        status = self.link.status() if hasattr(self.link, 'status') else dict(transport=self.config.transport, state='simulated', ready=True, label=self.link.label)
        return dict(status, error=self.error)

    def packet(self, kind, now, data):
        return Packet(kind, self.config.station_id, self.boot, 0, int(now), data=data)

    def poll(self, now):
        # This is a bounded catch-up scan. Historical rows do not flood a newly started link.
        for e in reversed(self.station.store.events(limit=10000, kind='all')):
            if e['opened_at'] < self.started:
                continue
            if e['id'] not in self.seen:
                d = {'event_id': e['id']}
                if e['kind'] == 'smoke':
                    camera = next(c for c in self.station.config.cameras if c.name == e['camera'])
                    b = e['box']
                    d.update(recorded=camera.kind == 'file', camera=SLOTS.index(e['camera']), bearing_cd=round(bearing(self.config.heading, camera.yaw, b, camera.hfov)*100) % 36000,
                             width=round((b[2]-b[0])*255), height=round((b[3]-b[1])*255),
                             confidence=round((e['alarm_confidence'] if e['alarm_confidence'] is not None else e['confidence'])*100))
                else:
                    d['source'] = (e.get('details') or {}).get('source', 'unknown')
                kind = Kind.SMOKE if e['kind'] == 'smoke' else Kind.FLAME
                if self.sender.enqueue(self.packet(kind, e['opened_at'], d), now):
                    self.seen.add(e['id'])
        # Alert startup filtering must not hide new reviews of persisted events.
        # Advance only accepted changes: a full bounded outbox retries next poll.
        for e in self.station.store.decision_changes(self.started, self.decision_cursor):
            if not self.sender.enqueue(self.packet(Kind.DECISION, e['decided_at'], dict(event_id=e['id'], decision=1 if e['decision'] == 'confirmed' else 2)), now):
                break
            self.decision_cursor = (e['decided_at'], e['id'])

    def heartbeat(self, now):
        cameras = {c['name']: c for c in self.station.status()['cameras']}
        ordered = [cameras[name] for name in SLOTS]
        d = dict(active=sum(1 << i for i, c in enumerate(ordered) if c['active']),
                 lost=sum(1 << i for i, c in enumerate(ordered) if c['active'] and not c['connected']),
                 pending=min(65535, sum(self.station.store.pending_count(kind) for kind in ('smoke', 'flame_sensor'))),
                 uptime=min(2**32-1, int(now-self.started)), heading_cd=round(self.config.heading*100) % 36000,
                 yaw=[round(((c['yaw']+180) % 360-180)*100) for c in ordered], hfov=[min(179, round(c['hfov'])) for c in ordered])
        self.sender.enqueue(self.packet(Kind.STATUS, now, d), now)

    def start(self):
        if self.link is None:
            return
        self.thread = Thread(target=self.run, name='lora-outbox', daemon=True)
        self.thread.start()

    def step(self, now):
        if hasattr(self.link, 'status') and not self.attach_radio():
            return None  # radio absent/refused: events stay unseen and are scanned once ready
        self.poll(now)
        if now >= self.next_heartbeat:
            self.heartbeat(now)
            self.next_heartbeat = now+self.config.heartbeat_seconds
        elif self.sender.heartbeat is not None and now >= self.sender.next_tx_at(now):
            # Refresh an already due but deferred heartbeat, without shortening a
            # deliberately slow requested interval.
            self.heartbeat(now)
        return self.sender.tick(now)

    def run(self):
        while not self.stop_event.is_set():
            try:
                self.step(time.time())
                self.error = None
            except Exception as exc:
                self.error = str(exc)
                logging.exception('LoRa outbox error (capture continues)')
            self.stop_event.wait(.2)

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=15)
        if self.link is not None:
            self.link.close()
