"""Bounded priority queue: first alerts, decisions, repeats, replaceable heartbeat."""
from dataclasses import replace
import heapq
from .protocol import encode, Kind

class Sender:
    def __init__(self, link, radio, budget, repeats=2, repeat_interval=30, max_queue=256):
        if not 0 <= repeats <= 3 or repeat_interval < 1:
            raise ValueError('Invalid repeat policy')
        self.link, self.radio, self.budget = link, radio, budget
        self.repeats, self.repeat_interval, self.max_queue = repeats, repeat_interval, max_queue
        self.queue = []
        self.counter = self.sequence = self.sent = self.refused = self.dropped = 0
        self.busy_until = 0.
        self.heartbeat = None

    def enqueue(self, packet, now, priority=None, repeats=None):
        if packet.kind == Kind.STATUS:
            self.heartbeat = packet
            return True
        if len(self.queue) >= self.max_queue:
            # Evict a repeat before rejecting a new alert.
            candidates = [i for i, x in enumerate(self.queue) if x[0] == 2]
            if not candidates:
                self.dropped += 1
                return False
            self.queue.pop(candidates[-1]); heapq.heapify(self.queue)
        self.counter += 1
        priority = (1 if packet.kind == Kind.DECISION else 0) if priority is None else priority
        heapq.heappush(self.queue, (priority, now, self.counter, packet, self.repeats if repeats is None else repeats))
        return True

    def tick(self, now):
        if now < self.busy_until:
            return None
        ready = [(x, i) for i, x in enumerate(self.queue) if x[1] <= now]
        chosen = min(ready, default=None, key=lambda pair: pair[0][:3])
        if chosen:
            item, index = chosen
            _, _, _, p, repeats = item
        elif self.heartbeat and not self.queue:
            p, repeats, index = self.heartbeat, 0, None
        else:
            return None
        duration = self.radio.airtime(len(encode(p)))
        # Preserve enough airtime for one maximum-sized new alert when sending a heartbeat.
        remaining = self.budget.remaining(now)
        reserve = self.radio.airtime(48) if p.kind == Kind.STATUS else 0
        if remaining < duration+reserve or not self.budget.reserve(duration, now):
            self.refused += 1
            return None
        wire = replace(p, sequence=self.sequence, remaining_cs=min(65535, int(self.budget.remaining(now)*100)))
        self.sequence = (self.sequence+1) & 65535
        raw = encode(wire)
        if index is None:
            self.heartbeat = None
        else:
            self.queue.pop(index); heapq.heapify(self.queue)
        self.busy_until = now+duration+1  # no back-to-back burst, even with delay disabled
        if repeats:
            self.enqueue(p, now+self.repeat_interval, priority=2, repeats=repeats-1)
        self.link.send(raw, duration)  # loss consumes budget and a sequence number
        self.sent += 1
        return raw
