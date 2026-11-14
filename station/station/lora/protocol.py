"""Version 2 (version 1 receive compatibility), network byte order, CRC-16/CCITT-FALSE. See PACKETS.md."""
from dataclasses import dataclass, field
from enum import IntEnum
import binascii
import math
import struct
import uuid

SLOTS = ('left', 'centre', 'right')
MAX_PAYLOAD = 48
HEADER_V1 = struct.Struct('>BBHIHIH')
HEADER = struct.Struct('>BBHIHIHH')
FORMATS = {1: struct.Struct('>16sBHBBB'), 2: struct.Struct('>16sB'),
           3: struct.Struct('>16sB'), 4: struct.Struct('>BBHIBHhhhBBB')}

class Kind(IntEnum):
    SMOKE = 1
    FLAME = 2
    DECISION = 3
    STATUS = 4

@dataclass(frozen=True)
class Packet:
    kind: Kind
    station: int
    boot: int
    sequence: int
    timestamp: int
    remaining_cs: int = 0
    data: dict = field(default_factory=dict)
    contact_after: int = 0  # low 15 bits: calculated seconds, 0 = unannounced
    duty_hold: bool = False  # high bit: pacing, rather than requested heartbeat, sets interval


def bearing(heading, yaw, box, hfov):
    """Pinhole horizontal projection, clockwise from configured north. Not a location."""
    if not all(math.isfinite(v) for v in (heading, yaw, hfov, *box)) or not 0 < hfov < 180:
        raise ValueError('Bearing needs finite heading, box and 0 < horizontal FOV < 180')
    x1, y1, x2, y2 = box
    if not (0 <= x1 <= x2 <= 1 and 0 <= y1 <= y2 <= 1):
        raise ValueError('Expected normalized xyxy box')
    offset = math.degrees(math.atan((x1+x2-1)*math.tan(math.radians(hfov/2))))
    return (heading + yaw + offset) % 360


def encode(p):
    d = p.data
    if not 0 <= p.contact_after <= 32767:
        raise ValueError('Contact window must fit 15 bits')
    try:
        if p.kind == Kind.SMOKE:
            values = (uuid.UUID(d['event_id']).bytes, d['camera'] | (128 if d.get('recorded', False) else 0), d['bearing_cd'], d['width'], d['height'], d['confidence'])
        elif p.kind == Kind.FLAME:
            values = (uuid.UUID(d['event_id']).bytes, {'hardware': 0, 'simulated': 1, 'unknown': 255}[d.get('source', 'unknown')])
        elif p.kind == Kind.DECISION:
            values = (uuid.UUID(d['event_id']).bytes, d['decision'])
        elif p.kind == Kind.STATUS:
            values = (d['active'], d['lost'], d['pending'], d['uptime'], 255, d['heading_cd'], *d['yaw'], *d['hfov'])
        else:
            raise ValueError('Unknown packet kind')
        body = HEADER.pack(0xAC, 0x20 | int(p.kind), p.station, p.boot, p.sequence, p.timestamp, p.remaining_cs, p.contact_after | (0x8000 if p.duty_hold else 0))
        body += FORMATS[int(p.kind)].pack(*values)
        raw = body + struct.pack('>H', binascii.crc_hqx(body, 0xFFFF))
        # Decode also validates semantic ranges, so encoding cannot emit invalid values.
        decode(raw)
        return raw
    except (KeyError, struct.error, TypeError, OverflowError) as exc:
        raise ValueError('Invalid packet fields') from exc


def decode(raw):
    if not isinstance(raw, bytes) or not HEADER_V1.size+2 <= len(raw) <= MAX_PAYLOAD:
        raise ValueError('Invalid packet size')
    if binascii.crc_hqx(raw[:-2], 0xFFFF) != int.from_bytes(raw[-2:], 'big'):
        raise ValueError('CRC mismatch')
    header = HEADER if raw[1] >> 4 == 2 else HEADER_V1
    if len(raw) < header.size+2:
        raise ValueError('Truncated header')
    values = header.unpack(raw[:header.size])
    magic, vt, station, boot, sequence, timestamp, remaining = values[:7]
    window = values[7] if len(values) == 8 else 0
    contact_after, duty_hold = window & 0x7fff, bool(window & 0x8000)
    kind = vt & 15
    if station == 0 or magic != 0xAC or vt >> 4 not in (1, 2) or kind not in FORMATS:
        raise ValueError('Unknown magic, version or kind')
    fmt = FORMATS[kind]
    if len(raw) != header.size+fmt.size+2:
        raise ValueError('Wrong packet length')
    v = fmt.unpack(raw[header.size:-2])
    if kind == Kind.SMOKE:
        d = dict(event_id=v[0].hex(), camera=v[1] & 3, recorded=bool(v[1] & 128), bearing_cd=v[2], width=v[3], height=v[4], confidence=v[5])
        if v[1] & 124 or d['camera'] > 2 or d['bearing_cd'] >= 36000 or d['confidence'] > 100:
            raise ValueError('Invalid smoke fields')
    elif kind == Kind.FLAME:
        d = dict(event_id=v[0].hex(), source={0: 'hardware', 1: 'simulated', 255: 'unknown'}.get(v[1]))
        if d['source'] is None:
            raise ValueError('Invalid sensor source')
    elif kind == Kind.DECISION:
        d = dict(event_id=v[0].hex(), decision=v[1])
        if v[1] not in (1, 2):
            raise ValueError('Invalid decision')
    else:
        d = dict(active=v[0], lost=v[1], pending=v[2], uptime=v[3], battery=None,
                 heading_cd=v[5], yaw=list(v[6:9]), hfov=list(v[9:12]))
        if v[4] != 255 or d['active'] > 7 or d['active'].bit_count() > 2 or any(not -18000 <= y < 18000 for y in d['yaw']) or d['lost'] & ~d['active'] or d['heading_cd'] >= 36000 or any(not 0 < f < 180 for f in d['hfov']):
            raise ValueError('Invalid status fields')
    return Packet(Kind(kind), station, boot, sequence, timestamp, remaining, d, contact_after, duty_hold)
