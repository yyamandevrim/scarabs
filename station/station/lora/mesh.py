"""Meshtastic node adapter: unchanged ACORN packet bytes as a PRIVATE_APP payload.

IMPLEMENTED AGAINST THE DOCUMENTED `meshtastic` PYTHON API; NEVER RUN ON HARDWARE.
See station/LORA_HARDWARE.md. The `meshtastic` package is optional and imported
only when this transport connects; simulated operation never needs it.

Region and PHY come from the node's own configuration on every connect. The
adapter refuses (reports `refused`, never `ready`) unless the region is EU_433 or
EU_868, the duty-cycle override is off, and every possible channel centre keeps the
whole occupied bandwidth inside one listed sub-band of `radio.BANDS`.
"""
import errno
import logging
import math
import os
from queue import Queue, Empty, Full
from threading import Event, RLock, Thread
import time
from .protocol import MAX_PAYLOAD
from .radio import Radio, BANDS, sub_band_for

PRIVATE_APP = 256  # meshtastic.protobuf.portnums_pb2.PortNum.PRIVATE_APP
# On-air bytes around our payload, per packet. Lower bound: excludes relays,
# routing/ACK frames and the node's own NodeInfo/telemetry/position broadcasts.
HEADER_BYTES = 16  # firmware PacketHeader: to, from, id, flags, channel, next_hop, relay_node
DATA_ENVELOPE_BYTES = 7  # Data protobuf: portnum tag+varint(256)=3, payload tag+len=2, bitfield=2
OVERHEAD = HEADER_BYTES+DATA_ENVELOPE_BYTES
PREAMBLE = 16  # Meshtastic preamble symbols
# Firmware RadioInterface.cpp RDEF: frequency start/end MHz, power limit dBm.
REGIONS = {'EU_433': (433.0, 434.0, 10), 'EU_868': (869.4, 869.65, 27)}
REGION_NAMES = {0: 'UNSET', 1: 'US', 2: 'EU_433', 3: 'EU_868'}
PRESET_NAMES = {0: 'LONG_FAST', 1: 'LONG_SLOW', 2: 'VERY_LONG_SLOW', 3: 'MEDIUM_SLOW', 4: 'MEDIUM_FAST',
                5: 'SHORT_SLOW', 6: 'SHORT_FAST', 7: 'LONG_MODERATE', 8: 'SHORT_TURBO', 9: 'LONG_TURBO'}
# Firmware modemPresetToParams (non-wide LoRa): bandwidth kHz, SF, coding-rate denominator.
PRESETS = {'SHORT_TURBO': (500, 7, 5), 'SHORT_FAST': (250, 7, 5), 'SHORT_SLOW': (250, 8, 5),
           'MEDIUM_FAST': (250, 9, 5), 'MEDIUM_SLOW': (250, 10, 5), 'LONG_FAST': (250, 11, 5),
           'LONG_TURBO': (500, 11, 8), 'LONG_MODERATE': (125, 11, 8), 'LONG_SLOW': (125, 12, 8)}
STATE_TEXT = {'ready': 'radio connected', 'connecting': 'connecting to radio', 'absent': 'radio absent',
              'busy': 'serial port busy', 'disconnected': 'radio disconnected', 'refused': 'radio refused',
              'unavailable': 'Meshtastic software not installed', 'error': 'radio error', 'closed': 'closed'}


class Refused(Exception):
    """Node configuration is not lawful or not supported for ACORN."""


class LinkDown(RuntimeError):
    """No usable radio at this moment; the packet was not handed to a node."""


def djb2(text):
    value = 5381
    for byte in text.encode():
        value = (value*33+byte) & 0xFFFFFFFF
    return value


def enum_name(value, names):
    if isinstance(value, str):
        return value
    return names.get(int(value), f'#{int(value)}')


def assess(lora, primary_name='', transmit=True):
    """Derive Radio, sub-band and duty limit from a node LoRaConfig, or raise Refused."""
    region = enum_name(getattr(lora, 'region', 0), REGION_NAMES)
    if region == 'UNSET':
        raise Refused('Node region is unset; set EU_433 or EU_868 to match the radio hardware')
    if region not in REGIONS:
        raise Refused(f'Node region {region} is not an EU band supported by ACORN')
    if getattr(lora, 'override_duty_cycle', False):
        raise Refused('Node overrides its duty cycle; turn override_duty_cycle off')
    if transmit and not getattr(lora, 'tx_enabled', True):
        raise Refused('Node transmit is disabled (lora.tx_enabled is false)')
    if getattr(lora, 'use_preset', True):
        preset = enum_name(getattr(lora, 'modem_preset', 0), PRESET_NAMES)
        if preset not in PRESETS:
            raise Refused(f'Modem preset {preset} is not supported by ACORN airtime accounting')
        bw, sf, cr = PRESETS[preset]
    else:
        preset = 'custom'
        bw, sf, cr = getattr(lora, 'bandwidth', 0), getattr(lora, 'spread_factor', 0), getattr(lora, 'coding_rate', 0)
    if bw not in (125, 250, 500) or cr not in range(5, 9) or sf not in range(7, 13):
        raise Refused(f'Unsupported PHY: {bw} kHz, SF{sf}, CR4/{cr}')
    radio = Radio(sf, bw*1000, cr-4, preamble=PREAMBLE, overhead=OVERHEAD)
    start, end, power_limit = REGIONS[region]
    power = getattr(lora, 'tx_power', 0) or 0
    if power > power_limit:
        raise Refused(f'Node tx_power {power} dBm exceeds the {region} limit of {power_limit} dBm')
    width = bw/1000
    offset = float(getattr(lora, 'frequency_offset', 0) or 0)
    if getattr(lora, 'override_frequency', 0):
        centres = [float(lora.override_frequency)]
    else:
        slots = math.floor((end-start)/width+1e-6)
        if slots < 1:
            raise Refused(f'{bw} kHz does not fit region {region}')
        channel = getattr(lora, 'channel_num', 0) or 0
        if channel:
            indices = [(channel-1) % slots]
        elif primary_name:
            indices = [djb2(primary_name) % slots]
        else:
            # Slot follows a hash of a firmware display name: check every candidate.
            indices = range(slots)
        centres = [start+width/2+i*width for i in indices]
    centres = [round(c+offset, 6) for c in centres]
    bands = {sub_band_for(c-width/2, c+width/2) for c in centres}
    if None in bands or len(bands) != 1:
        raise Refused('Possible channel frequencies leave one legal sub-band; set lora.channel_num on the node')
    sub_band = bands.pop()
    return dict(region=region, preset=preset, radio=radio, sub_band=sub_band, duty_limit=BANDS[sub_band][2],
                centres_mhz=centres, sf=sf, bandwidth_khz=bw, coding_rate=f'4/{cr}', tx_power_dbm=power or None)


def classify(exc):
    """Map a connect failure to a displayed state without exposing a traceback."""
    text = str(exc) or type(exc).__name__
    number = getattr(exc, 'errno', None)
    lowered = text.lower()
    if number in (errno.EBUSY, errno.EACCES) or 'busy' in lowered or 'lock' in lowered or 'in use' in lowered:
        return 'busy', text
    if number == errno.ENOENT or 'no such file' in lowered or 'not found' in lowered:
        return 'absent', text
    return 'error', text


class MeshtasticLink:
    """Link contract over a Meshtastic node via USB serial (or BLE).

    `connect` and `bus` are injection points for tests; by default the
    meshtastic library's SerialInterface/BLEInterface and pypubsub are used.
    """

    def __init__(self, port='', ble='', channel_index=0, hop_limit=0, destination='^all', transmit=True,
                 connect=None, bus=None, retry_seconds=5., timeout=30):
        if bool(port) == bool(ble):
            raise ValueError('Meshtastic transport needs exactly one of a serial port or BLE address')
        if not 0 <= channel_index <= 7 or not 0 <= hop_limit <= 7 or retry_seconds <= 0:
            raise ValueError('Invalid Meshtastic channel index, hop limit or retry interval')
        self.port, self.ble = port, ble
        self.channel_index, self.hop_limit, self.destination, self.transmit = channel_index, hop_limit, destination, transmit
        self.retry_seconds, self.timeout = retry_seconds, timeout
        self._connect = connect or self._library_connect
        self._bus = bus
        self.lock = RLock()
        self.iface = None
        self.state, self.detail = 'connecting', ''
        self.assessment = None
        self.node = {}
        self.inbox = Queue(maxsize=256)
        self.ignored = self.malformed = self.overflow = self.sent = 0
        self.last_rx = None
        self._lost = Event()
        self._stop = Event()
        self._subscribed = False
        self.thread = Thread(target=self._supervise, name='meshtastic-link', daemon=True)
        self.thread.start()

    # -- Link contract ---------------------------------------------------
    @property
    def label(self):
        return f'LoRa link (Meshtastic radio · {STATE_TEXT.get(self.state, self.state)})'

    @property
    def ready(self):
        return self.state == 'ready'

    @property
    def radio(self):
        a = self.assessment
        return a['radio'] if a and self.ready else None

    def send(self, payload, airtime):
        if not isinstance(payload, bytes) or not 1 <= len(payload) <= MAX_PAYLOAD:
            raise ValueError('ACORN payload must be 1..48 bytes')
        if not self.transmit:
            raise LinkDown('This Meshtastic link is receive-only')
        with self.lock:
            iface = self.iface if self.ready else None
            detail = self.detail
        if iface is None:
            raise LinkDown(f'LoRa radio not ready: {detail or self.state}')
        try:
            iface.sendData(payload, destinationId=self.destination, portNum=PRIVATE_APP, wantAck=False,
                           channelIndex=self.channel_index, hopLimit=self.hop_limit)
        except (Exception, SystemExit) as exc:  # the library may call sys.exit on odd states
            self._mark_lost(f'Send failed: {exc or type(exc).__name__}')
            raise LinkDown('LoRa radio send failed; packet treated as lost') from exc
        self.sent += 1

    def receive(self):
        try:
            return self.inbox.get(timeout=.2)
        except Empty:
            return None

    def close(self):
        self._stop.set()
        self.thread.join(timeout=5)
        self._drop_interface()
        if self._subscribed:
            try:
                self._bus.unsubscribe(self._on_receive, 'meshtastic.receive')
                self._bus.unsubscribe(self._on_lost, 'meshtastic.connection.lost')
            except Exception:
                pass
            self._subscribed = False
        with self.lock:
            self.state, self.detail = 'closed', ''

    def status(self):
        with self.lock:
            a = self.assessment if self.ready else None
            return dict(transport='meshtastic', state=self.state, ready=self.ready, label=self.label, detail=self.detail,
                        port=self.port or None, ble=self.ble or None, node=dict(self.node),
                        region=a and a['region'], preset=a and a['preset'], sub_band=a and a['sub_band'],
                        centres_mhz=a and a['centres_mhz'], duty_limit=a and a['duty_limit'],
                        sf=a and a['sf'], bandwidth_khz=a and a['bandwidth_khz'], coding_rate=a and a['coding_rate'],
                        sent=self.sent, ignored=self.ignored, malformed=self.malformed, overflow=self.overflow,
                        last_rx=dict(self.last_rx) if self.last_rx else None,
                        accounting='lower bound: Meshtastic relays, routing and node broadcasts are not counted')

    # -- Connection supervision -----------------------------------------
    def _library_connect(self):
        try:
            if self.port:
                from meshtastic.serial_interface import SerialInterface
            else:
                from meshtastic.ble_interface import BLEInterface
        except ImportError as exc:
            raise ModuleNotFoundError('Install the optional extra: uv sync --extra meshtastic') from exc
        if self.port:
            if not os.path.exists(self.port):
                raise FileNotFoundError(errno.ENOENT, 'Serial port not found', self.port)
            return SerialInterface(devPath=self.port, timeout=self.timeout)
        return BLEInterface(self.ble, timeout=self.timeout)

    def _ensure_bus(self):
        if self._subscribed:
            return
        if self._bus is None:
            try:
                from pubsub import pub  # installed with meshtastic
            except ImportError as exc:
                raise ModuleNotFoundError('Install the optional extra: uv sync --extra meshtastic') from exc
            self._bus = pub
        self._bus.subscribe(self._on_receive, 'meshtastic.receive')
        self._bus.subscribe(self._on_lost, 'meshtastic.connection.lost')
        self._subscribed = True

    def _set(self, state, detail=''):
        with self.lock:
            if (state, detail) != (self.state, self.detail):
                logging.info('Meshtastic link %s %s', state, detail)
            self.state, self.detail = state, detail

    def _supervise(self):
        while not self._stop.is_set():
            try:
                self._check()
            except Exception as exc:  # supervision must never die
                self._set('error', str(exc))
                self._drop_interface()
            self._stop.wait(self.retry_seconds if not self.ready else .5)

    def _check(self):
        if self.iface is not None:
            connected = getattr(self.iface, 'isConnected', None)
            if self._lost.is_set() or (connected is not None and not connected.is_set()):
                self._drop_interface()
                self._set('disconnected', self.detail if self.state == 'disconnected' else 'Node connection lost; retrying')
            return
        # Retries keep the last failure visible instead of flickering to 'connecting'.
        try:
            self._ensure_bus()
            iface = self._connect()
        except ModuleNotFoundError as exc:
            self._set('unavailable', str(exc))
            return
        except (Exception, SystemExit) as exc:
            self._set(*classify(exc))
            return
        self._lost.clear()
        try:
            local = iface.localNode
            lora = local.localConfig.lora
            primary = local.getChannelByChannelIndex(0) if hasattr(local, 'getChannelByChannelIndex') else None
            name = getattr(getattr(primary, 'settings', None), 'name', '') or ''
            channel = local.getChannelByChannelIndex(self.channel_index) if hasattr(local, 'getChannelByChannelIndex') else None
            if self.channel_index and (channel is None or not getattr(channel, 'role', 0)):
                raise Refused(f'Node has no enabled channel at index {self.channel_index}')
            assessment = assess(lora, name, self.transmit)
        except (Refused, ValueError) as exc:
            self._close_quietly(iface)
            with self.lock:
                self.assessment = None
            self._set('refused', str(exc))
            return
        except (Exception, SystemExit) as exc:
            self._close_quietly(iface)
            self._set('error', f'Could not read node configuration: {exc}')
            return
        info = {}
        try:
            info['node_num'] = getattr(getattr(iface, 'myInfo', None), 'my_node_num', None)
            info['firmware'] = getattr(getattr(iface, 'metadata', None), 'firmware_version', None)
            user = ((iface.getMyNodeInfo() or {}).get('user') or {}) if hasattr(iface, 'getMyNodeInfo') else {}
            info['node_id'], info['hw_model'] = user.get('id'), user.get('hwModel')
        except Exception:
            pass
        with self.lock:
            self.iface, self.assessment, self.node = iface, assessment, info
        self._set('ready', f"{assessment['region']} · {assessment['sub_band']} MHz · {assessment['preset']}")

    def _mark_lost(self, detail):
        self._lost.set()
        self._set('disconnected', detail)

    def _drop_interface(self):
        with self.lock:
            iface, self.iface = self.iface, None
        if iface is not None:
            self._close_quietly(iface)

    @staticmethod
    def _close_quietly(iface):
        try:
            iface.close()
        except (Exception, SystemExit):
            pass

    # -- Library callbacks (publishing thread) ---------------------------
    def _on_lost(self, interface=None, **_):
        if interface is not None and interface is self.iface:
            self._mark_lost('Node connection lost; retrying')

    def _on_receive(self, packet=None, interface=None, **_):
        if interface is None or interface is not self.iface:
            return  # another interface in this process, or a stale one
        try:
            decoded = packet.get('decoded') if isinstance(packet, dict) else None
            if not isinstance(decoded, dict) or decoded.get('portnum') not in ('PRIVATE_APP', PRIVATE_APP):
                self.ignored += 1
                return
            payload = decoded.get('payload')
            if not isinstance(payload, (bytes, bytearray)) or not 1 <= len(payload) <= MAX_PAYLOAD:
                self.malformed += 1
                return
            self.last_rx = dict(at=time.time(), size=len(payload), rssi=packet.get('rxRssi'), snr=packet.get('rxSnr'),
                                from_id=packet.get('fromId'), hop_start=packet.get('hopStart'), hop_limit=packet.get('hopLimit'))
            self.inbox.put_nowait(bytes(payload))
        except Full:
            self.overflow += 1
        except Exception:
            self.malformed += 1
