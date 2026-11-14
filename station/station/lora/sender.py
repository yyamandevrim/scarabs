"""Bounded priority queue: first alerts, decisions, repeats, replaceable heartbeat."""
from dataclasses import replace
import heapq
import math
from .protocol import encode, Kind, MAX_PAYLOAD

class Sender:
    def __init__(self, link, radio, budget, repeats=2, repeat_interval=30, max_queue=256, heartbeat_seconds=300):
        if not 0 <= repeats <= 3 or repeat_interval < 1:
            raise ValueError('Invalid repeat policy')
        self.link, self.radio, self.budget = link, radio, budget
        self.repeats, self.repeat_interval, self.max_queue = repeats, repeat_interval, max_queue
        self.queue = []
        self.counter = self.sequence = self.sent = self.refused = self.dropped = 0
        # Spread the allowance across the hour instead of spending an hour in minutes.
        worst = radio.airtime(MAX_PAYLOAD)
        if worst > budget.capacity:
            raise ValueError('Configured duty cycle cannot fit one maximum-size packet per window')
        self.slot_seconds = max(math.ceil(worst/budget.fraction+worst+2),
                                math.ceil((budget.window+worst+2)/math.floor(budget.capacity/worst)))
        if not 2 <= heartbeat_seconds <= 32760 or self.slot_seconds > 32760:
            raise ValueError('Contact interval exceeds the supported wire window')
        self.heartbeat_seconds = heartbeat_seconds
        self.busy_until = max(budget.not_before, budget.last_time+self.slot_seconds if budget.entries else 0)
        self.last_sent_at = None
        self.heartbeat = None

    def enqueue(self, packet, now, priority=None, repeats=None):
        if packet.kind == Kind.STATUS:
            self.heartbeat = packet
            return True
        if packet.kind == Kind.DECISION and priority != 2:
            # Correcting a review supersedes unsent/repeating older decisions.
            self.queue = [x for x in self.queue if not (x[3].kind == Kind.DECISION and x[3].data['event_id'] == packet.data['event_id'])]
            heapq.heapify(self.queue)
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

    def next_tx_at(self, now):
        return max(self.busy_until, self.budget.available_at(self.radio.airtime(MAX_PAYLOAD), now))

    def tick(self, now):
        if now < self.busy_until:
            return None
        ready = [(x, i) for i, x in enumerate(self.queue) if x[1] <= now]
        chosen = min(ready, default=None, key=lambda pair: pair[0][:3])
        if chosen:
            item, index = chosen
            _, _, _, p, repeats = item
        elif self.heartbeat:
            p, repeats, index = self.heartbeat, 0, None
        else:
            return None
        duration = self.radio.airtime(len(encode(p)))
        if not self.budget.reserve(duration, now, not_before=now+self.slot_seconds):
            self.refused += 1
            return None
        next_legal = max(now+self.slot_seconds, self.budget.available_at(self.radio.airtime(MAX_PAYLOAD), now+self.slot_seconds))
        contact = math.ceil(max(next_legal-now, self.heartbeat_seconds)+3)
        wire = replace(p, sequence=self.sequence, remaining_cs=min(65535, int(self.budget.remaining(now)*100)),
                       contact_after=contact,
                       duty_hold=next_legal-now >= self.heartbeat_seconds)
        self.sequence = (self.sequence+1) & 65535
        raw = encode(wire)
        if index is None:
            self.heartbeat = None
        else:
            self.queue.pop(index); heapq.heapify(self.queue)
        self.busy_until = now+self.slot_seconds
        self.last_sent_at = now
        if repeats:
            self.enqueue(p, now+self.repeat_interval, priority=2, repeats=repeats-1)
        self.link.send(raw, duration)  # loss consumes budget and a sequence number
        self.sent += 1
        return raw
