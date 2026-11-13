"""Minimal MessagePack codec for the UNO Q router socket (no extension types).

The arduino-router speaks MessagePack-RPC over a Unix socket. Only the core
types are needed (nil, bool, int, float, str, bin, array, map), so this avoids
adding a dependency to the locked environment.
"""
import struct


class Incomplete(Exception):
    """The buffer ends inside a value; wait for more bytes."""


def pack(obj) -> bytes:
    out = bytearray()
    _pack(obj, out)
    return bytes(out)


def _pack(obj, out):
    if obj is None:
        out.append(0xC0)
    elif obj is True:
        out.append(0xC3)
    elif obj is False:
        out.append(0xC2)
    elif isinstance(obj, int):
        if 0 <= obj < 0x80:
            out.append(obj)
        elif -32 <= obj < 0:
            out.append(obj & 0xFF)
        elif 0 <= obj <= 0xFF:
            out += b"\xcc" + struct.pack(">B", obj)
        elif 0 <= obj <= 0xFFFF:
            out += b"\xcd" + struct.pack(">H", obj)
        elif 0 <= obj <= 0xFFFFFFFF:
            out += b"\xce" + struct.pack(">I", obj)
        elif 0 <= obj <= 0xFFFFFFFFFFFFFFFF:
            out += b"\xcf" + struct.pack(">Q", obj)
        elif -0x80 <= obj:
            out += b"\xd0" + struct.pack(">b", obj)
        elif -0x8000 <= obj:
            out += b"\xd1" + struct.pack(">h", obj)
        elif -0x80000000 <= obj:
            out += b"\xd2" + struct.pack(">i", obj)
        elif -0x8000000000000000 <= obj:
            out += b"\xd3" + struct.pack(">q", obj)
        else:
            raise ValueError("integer out of MessagePack range")
    elif isinstance(obj, float):
        out += b"\xcb" + struct.pack(">d", obj)
    elif isinstance(obj, str):
        data = obj.encode("utf-8")
        n = len(data)
        if n < 32:
            out.append(0xA0 | n)
        elif n <= 0xFF:
            out += b"\xd9" + struct.pack(">B", n)
        elif n <= 0xFFFF:
            out += b"\xda" + struct.pack(">H", n)
        else:
            out += b"\xdb" + struct.pack(">I", n)
        out += data
    elif isinstance(obj, (bytes, bytearray)):
        n = len(obj)
        if n <= 0xFF:
            out += b"\xc4" + struct.pack(">B", n)
        elif n <= 0xFFFF:
            out += b"\xc5" + struct.pack(">H", n)
        else:
            out += b"\xc6" + struct.pack(">I", n)
        out += obj
    elif isinstance(obj, (list, tuple)):
        n = len(obj)
        if n < 16:
            out.append(0x90 | n)
        elif n <= 0xFFFF:
            out += b"\xdc" + struct.pack(">H", n)
        else:
            out += b"\xdd" + struct.pack(">I", n)
        for item in obj:
            _pack(item, out)
    elif isinstance(obj, dict):
        n = len(obj)
        if n < 16:
            out.append(0x80 | n)
        elif n <= 0xFFFF:
            out += b"\xde" + struct.pack(">H", n)
        else:
            out += b"\xdf" + struct.pack(">I", n)
        for key, value in obj.items():
            _pack(key, out)
            _pack(value, out)
    else:
        raise TypeError(f"cannot MessagePack-encode {type(obj).__name__}")


_FIXED = {0xCC: ">B", 0xCD: ">H", 0xCE: ">I", 0xCF: ">Q", 0xD0: ">b", 0xD1: ">h", 0xD2: ">i", 0xD3: ">q", 0xCA: ">f", 0xCB: ">d"}


def _take(buf, pos, n):
    if pos + n > len(buf):
        raise Incomplete
    return buf[pos:pos + n], pos + n


def _decode(buf, pos):
    if pos >= len(buf):
        raise Incomplete
    b = buf[pos]
    pos += 1
    if b <= 0x7F:
        return b, pos
    if b >= 0xE0:
        return b - 0x100, pos
    if 0xA0 <= b <= 0xBF:
        data, pos = _take(buf, pos, b & 0x1F)
        return data.decode("utf-8"), pos
    if 0x90 <= b <= 0x9F:
        return _array(buf, pos, b & 0x0F)
    if 0x80 <= b <= 0x8F:
        return _map(buf, pos, b & 0x0F)
    if b == 0xC0:
        return None, pos
    if b == 0xC2:
        return False, pos
    if b == 0xC3:
        return True, pos
    if b in _FIXED:
        fmt = _FIXED[b]
        data, pos = _take(buf, pos, struct.calcsize(fmt))
        return struct.unpack(fmt, data)[0], pos
    if b in (0xD9, 0xDA, 0xDB, 0xC4, 0xC5, 0xC6):
        fmt = {0xD9: ">B", 0xDA: ">H", 0xDB: ">I", 0xC4: ">B", 0xC5: ">H", 0xC6: ">I"}[b]
        data, pos = _take(buf, pos, struct.calcsize(fmt))
        data, pos = _take(buf, pos, struct.unpack(fmt, data)[0])
        return (data.decode("utf-8") if b >= 0xD9 else bytes(data)), pos
    if b in (0xDC, 0xDD, 0xDE, 0xDF):
        fmt = ">H" if b in (0xDC, 0xDE) else ">I"
        data, pos = _take(buf, pos, struct.calcsize(fmt))
        n = struct.unpack(fmt, data)[0]
        return (_array if b in (0xDC, 0xDD) else _map)(buf, pos, n)
    raise ValueError(f"unsupported MessagePack type 0x{b:02x}")


def _array(buf, pos, n):
    items = []
    for _ in range(n):
        item, pos = _decode(buf, pos)
        items.append(item)
    return items, pos


def _map(buf, pos, n):
    result = {}
    for _ in range(n):
        key, pos = _decode(buf, pos)
        value, pos = _decode(buf, pos)
        result[key] = value
    return result, pos


def unpack(data: bytes):
    value, pos = _decode(bytes(data), 0)
    if pos != len(data):
        raise ValueError("trailing bytes after MessagePack value")
    return value


class Unpacker:
    """Stream decoder: feed() socket bytes, then iterate complete values."""

    def __init__(self, limit=1 << 20):
        self.buffer = bytearray()
        self.limit = limit

    def feed(self, data: bytes):
        self.buffer += data
        if len(self.buffer) > self.limit:
            raise ValueError("MessagePack stream buffer limit exceeded")

    def __iter__(self):
        while self.buffer:
            try:
                value, pos = _decode(bytes(self.buffer), 0)
            except Incomplete:
                return
            del self.buffer[:pos]
            yield value
