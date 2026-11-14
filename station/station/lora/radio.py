"""Semtech LoRa airtime and conservative per-sub-band rolling-hour accounting."""
from dataclasses import dataclass
import json
import math
from pathlib import Path

# ERC/REC 70-03 Annex 1 h1.5, h1.6, h1.7, h1.9 (duty-cycle path, not LBT).
BANDS = {'868.0-868.6': (868.0, 868.6, .01), '868.7-869.2': (868.7, 869.2, .001),
         '869.4-869.65': (869.4, 869.65, .1), '869.7-870.0': (869.7, 870., .01)}

@dataclass(frozen=True)
class Radio:
    sf: int = 10
    bandwidth: int = 125000
    coding_rate: int = 1  # 1..4 means 4/5..4/8
    preamble: int = 8

    def __post_init__(self):
        if self.sf not in range(7, 13) or self.bandwidth not in (125000, 250000, 500000) or self.coding_rate not in range(1, 5) or self.preamble < 6:
            raise ValueError('Unsupported radio parameters')

    def airtime(self, size):
        if not 0 <= size <= 255:
            raise ValueError('Invalid payload length')
        symbol = 2**self.sf/self.bandwidth
        de = int(symbol >= .016)  # automatic low-data-rate optimisation
        # Explicit header (IH=0), PHY CRC enabled (CRC=1).
        payload = 8 + max(math.ceil((8*size-4*self.sf+28+16)/(4*(self.sf-2*de)))*(self.coding_rate+4), 0)
        return (self.preamble+4.25+payload)*symbol

    def band_limit(self, band, frequency):
        low, high, limit = BANDS[band]
        half_width = self.bandwidth/2e6
        if frequency-half_width < low or frequency+half_width > high:
            raise ValueError('Occupied bandwidth crosses the selected sub-band')
        return limit

class DutyBudget:
    """Reserves the entire TX at its start; only frees it one hour after its end.

    Persist with wall-clock seconds in production. A backwards clock blocks TX.
    Files are private runtime state, never credentials. Do not delete to gain airtime.
    """
    def __init__(self, fraction=.01, window=3600, path=None):
        if not 0 < fraction <= .1 or window <= 0:
            raise ValueError('Invalid duty budget')
        self.fraction = fraction
        self.capacity = fraction*window
        self.window = window
        self.path = Path(path) if path else None
        self.entries = []
        self.last_time = 0
        self.not_before = 0
        self.blocked_until = 0
        if self.path and self.path.exists():
            try:
                state = json.loads(self.path.read_text())
                self.entries = [tuple(x) for x in state['entries']]
                self.last_time = state['last_time']
                self.not_before = state.get('not_before', 0)
            except (ValueError, KeyError, TypeError):
                # Corrupt accounting fails closed; one full quiet hour required.
                import time
                self.blocked_until = time.time()+window

    def remaining(self, now):
        if now < max(self.last_time, self.blocked_until):
            return 0.
        self.entries = [(end, duration) for end, duration in self.entries if end > now-self.window]
        return max(0., self.capacity-sum(duration for _, duration in self.entries))

    def available_at(self, duration, now):
        """Earliest legal reservation, also for pre-pacing ledgers already exhausted."""
        if duration > self.capacity:
            raise ValueError('One packet exceeds the entire duty-cycle allowance')
        now = max(now, self.last_time, self.blocked_until)
        # Forecast without pruning the live ledger at a future time.
        entries = [(end,used) for end,used in self.entries if end > now-self.window]
        remaining = max(0., self.capacity-sum(used for _,used in entries))
        if remaining+1e-9 >= duration:
            return now
        for end, used in sorted(entries):
            remaining += used
            if remaining+1e-9 >= duration:
                return max(now, end+self.window)
        return now+self.window

    def reserve(self, duration, now, not_before=None):
        if duration <= 0 or duration > self.remaining(now)+1e-9:
            return False
        self.entries.append((now+duration, duration))
        self.last_time = now
        if not_before is not None:
            self.not_before = not_before
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix('.tmp')
            temporary.write_text(json.dumps(dict(entries=self.entries, last_time=now, not_before=self.not_before)))
            temporary.replace(self.path)
        return True
