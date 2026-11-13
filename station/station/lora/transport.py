"""Transport contract: complete raw packets, no imagery or transport envelopes."""
from typing import Protocol
import random
import socket
import time
from .protocol import MAX_PAYLOAD

class Link(Protocol):
    label: str
    def send(self, payload: bytes, airtime: float) -> None: ...
    def receive(self) -> bytes | None: ...
    def close(self) -> None: ...

class SimulatedLink:
    label = 'LoRa link (simulated transport)'

    def __init__(self, peer=None, bind=None, loss=0., delay=False, payload_limit=MAX_PAYLOAD, seed=None):
        if not 0 <= loss <= 1 or not 1 <= payload_limit <= MAX_PAYLOAD:
            raise ValueError('Invalid simulated constraints')
        self.peer, self.loss, self.delay, self.limit = peer, loss, delay, payload_limit
        self.rng = random.Random(seed)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if bind:
            self.socket.bind(bind)
        self.socket.settimeout(.2)

    def send(self, payload, airtime):
        if len(payload) > self.limit:
            raise ValueError('Simulated payload limit exceeded')
        if self.delay:
            time.sleep(airtime)
        if self.rng.random() >= self.loss:
            self.socket.sendto(payload, self.peer)

    def receive(self):
        try:
            return self.socket.recvfrom(65535)[0]
        except socket.timeout:
            return None

    def close(self):
        self.socket.close()

class SerialModem:
    """UNIMPLEMENTED / UNTESTED. No modem command set or wiring is assumed.

    Implement TX completion, RX framing, modem errors and PHY configuration here.
    Preserve packet bytes. Radio/duty scheduling remains upstream of this adapter.
    """
    label = 'LoRa link (serial adapter unimplemented / untested)'
    def __init__(self, port, **settings):
        raise NotImplementedError('Choose and validate a modem before implementing its serial adapter')
    def send(self, payload, airtime):
        raise NotImplementedError
    def receive(self):
        raise NotImplementedError
    def close(self):
        pass
