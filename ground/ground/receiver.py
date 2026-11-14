"""Durable raw packet journal and derived state; no station API access here."""
from dataclasses import asdict
import json
from pathlib import Path
import sqlite3
from threading import RLock, Event, Thread
import time
from station.lora.protocol import decode, Kind, SLOTS

class SequenceTracker:
    """16-bit wrapping high-water mark, bounded late-arrival repair window."""
    def __init__(self):
        self.high = None
        self.received = set()
        self.gaps = set()
        self.expired_missing = 0

    def add(self, sequence):
        if self.high is None:
            absolute = sequence
        else:
            delta = (sequence-(self.high & 65535)+32768) % 65536-32768
            absolute = self.high+delta
        if absolute in self.received or (self.high is not None and absolute < self.high-4096):
            return False
        if self.high is not None and absolute > self.high:
            self.gaps.update(range(self.high+1, absolute))
        self.received.add(absolute)
        self.gaps.discard(absolute)
        self.high = max(absolute, self.high) if self.high is not None else absolute
        old = {x for x in self.gaps if x < self.high-4096}
        self.expired_missing += len(old)
        self.gaps -= old
        self.received = {x for x in self.received if x >= self.high-4096}
        return True

    @property
    def missed(self):
        return self.expired_missing+len(self.gaps)

class Receiver:
    def __init__(self, root, radio, stale_after=660, lost_after=1200, transport_label='LoRa link (simulated transport)'):
        if not 0 < stale_after < lost_after:
            raise ValueError('Require 0 < stale < lost thresholds')
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.radio, self.stale_after, self.lost_after = radio, stale_after, lost_after
        self.transport_label = transport_label
        self.lock = RLock()
        self.stations = {}
        self.alerts = {}
        self.trackers = {}
        self.decisions = {}
        self.retired = {}
        self.invalid = 0
        self.db = sqlite3.connect(self.root/'ground.sqlite3', check_same_thread=False)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('CREATE TABLE IF NOT EXISTS packets (id INTEGER PRIMARY KEY, received REAL, raw BLOB)')
        self.db.execute('CREATE TABLE IF NOT EXISTS acknowledgements (station INTEGER, event TEXT, at REAL, PRIMARY KEY(station,event))')
        self.acks = {(s, e): at for s, e, at in self.db.execute('SELECT * FROM acknowledgements')}
        for received, raw in self.db.execute('SELECT received,raw FROM packets ORDER BY id'):
            self._apply(decode(raw), received, len(raw))

    def ingest(self, raw, now=None):
        now = time.time() if now is None else now
        with self.lock:
            try:
                p = decode(raw)
            except ValueError:
                self.invalid += 1
                return False
            # Keep repeated datagrams as received-link statistics, dedup semantic state.
            with self.db:
                self.db.execute('INSERT INTO packets(received,raw) VALUES(?,?)', (now, raw))
            return self._apply(p, now, len(raw))

    def _apply(self, p, now, size):
        s = self.stations.setdefault(p.station, dict(id=p.station, packets=0, duplicates=0, last_heard=now, status=None, boot=p.boot, last_size=size))
        s.update(packets=s['packets']+1, last_heard=now, last_size=size, airtime=self.radio.airtime(size))
        retired = self.retired.setdefault(p.station, set())
        if p.boot != s['boot'] and p.boot not in retired:
            retired.add(s['boot'])
            s.update(boot=p.boot, status=None)
        tracker = self.trackers.setdefault((p.station, p.boot), SequenceTracker())
        fresh = tracker.add(p.sequence)
        if not fresh:
            s['duplicates'] += 1
            return False
        # Late packets may fill gaps but cannot roll the current budget/status backwards.
        newest = p.boot == s['boot'] and p.sequence == (tracker.high & 65535)
        if newest:
            s.update(boot=p.boot, remaining=p.remaining_cs/100, budget_at=now, contact_after=p.contact_after, duty_hold=p.duty_hold)
        d = p.data
        if p.kind == Kind.STATUS and newest:
            s['status'] = dict(d, timestamp=p.timestamp)
        elif p.kind in (Kind.SMOKE, Kind.FLAME):
            key = (p.station, d['event_id'])
            self.alerts.setdefault(key, dict(station=p.station, event_id=d['event_id'], kind='smoke' if p.kind == Kind.SMOKE else 'flame_sensor',
                                            timestamp=p.timestamp, **{k: v for k, v in d.items() if k != 'event_id'}))
            self.alerts[key]['decision'] = self.decisions.get(key, {}).get('decision', 'pending')
        elif p.kind == Kind.DECISION:
            key = (p.station, d['event_id'])
            previous = self.decisions.get(key)
            # Timestamp remains the semantic clock. Break same-second ties only
            # within the current boot, using the tracker's unwrapped order.
            # Sender cancels queued old decision repeats when a correction is
            # enqueued; a physical sequence is not a general revision number.
            absolute = tracker.high + (p.sequence-(tracker.high & 65535)+32768) % 65536-32768
            tied_newer = previous is not None and p.timestamp == previous['timestamp'] and p.boot == s['boot'] and (
                p.boot != previous['boot'] or absolute > previous['sequence'])
            if previous is None or p.timestamp > previous['timestamp'] or tied_newer:
                self.decisions[key] = dict(timestamp=p.timestamp, boot=p.boot, sequence=absolute,
                                           decision='confirmed' if d['decision'] == 1 else 'rejected')
                if key in self.alerts:
                    self.alerts[key]['decision'] = self.decisions[key]['decision']
        return True

    def snapshot(self, now=None):
        now = time.time() if now is None else now
        with self.lock:
            stations = []
            for s in self.stations.values():
                age = max(0, now-s['last_heard'])
                contact = s.get('contact_after', 0)
                stale = max(self.stale_after, contact+5 if contact else 0)
                lost = max(self.lost_after, stale+self.lost_after-self.stale_after)
                due_in = max(0, s.get('budget_at', s['last_heard'])+contact-now) if contact else None
                state = 'lost' if age >= lost else 'stale' if age >= stale else ('holding' if s.get('duty_hold') else 'scheduled') if contact and age >= min(self.stale_after, contact/4) else 'online'
                item = dict(s, age=age, state=state, next_contact_in=due_in, effective_stale_after=stale,
                            duty_hint=s.get('remaining', 65535) < self.radio.airtime(48),
                            missed=sum(t.missed for (sid, _), t in self.trackers.items() if sid == s['id']))
                stations.append(item)
            alerts = [dict(a, acknowledged_at=self.acks.get(key)) for key, a in self.alerts.items()]
            return dict(stations=stations, alerts=sorted(alerts, key=lambda a: a['timestamp'], reverse=True), invalid_packets=self.invalid,
                        radio=asdict(self.radio), transport=self.transport_label)

    def acknowledge(self, station, event, now=None):
        key = (station, event)
        with self.lock:
            if key not in self.alerts:
                return False
            at = time.time() if now is None else now
            with self.db:
                self.db.execute('INSERT OR REPLACE INTO acknowledgements VALUES(?,?,?)', (*key, at))
            self.acks[key] = at
            return True

    def close(self):
        self.db.close()

class Listener:
    def __init__(self, receiver, link):
        self.receiver, self.link = receiver, link
        self.receiver.transport_label = link.label
        self.stop_event = Event()
        self.thread = Thread(target=self.run, name='lora-receiver', daemon=True)
        self.error = None

    def run(self):
        while not self.stop_event.is_set():
            try:
                raw = self.link.receive()
                if raw is not None:
                    self.receiver.ingest(raw)
            except Exception as exc:
                self.error = str(exc)
                self.stop_event.wait(.5)

    def start(self):
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        self.thread.join(timeout=2)
        self.link.close()
