# ACORN point-to-point packets — version 2

Current transport: **LoRa link (simulated transport)** over UDP, not LoRaWAN. A radio adapter later sends the identical payload. No images, image URLs, distance, fire coordinates, battery percentage, RSSI or SNR are carried. Version 2 adds a calculated next-contact window so a receiver can distinguish scheduled duty-cycle silence from a missed contact. The decoder continues to read version-1 packets and existing ground journals; a version-1-only receiver must be upgraded with the sender.

## Binary layout

Network byte order. Maximum application payload **48 bytes**. Version-2 header **18 bytes**, body below, application CRC **2 bytes**. All CRC, length, version and semantic checks apply before journal insertion.

| Offset | Bytes | Header field |
|---|---:|---|
| 0 | 1 | Magic `AC` hex |
| 1 | 1 | Version high nibble `2`, kind low nibble: 1 smoke, 2 flame, 3 decision, 4 status |
| 2 | 2 | Configured unsigned station ID 1–65535 |
| 4 | 4 | Random boot ID; not a secret |
| 8 | 2 | Unsigned physical-attempt sequence; wraps at 65536, each repeat gets a fresh number |
| 10 | 4 | UTC Unix seconds: event opening / decision / status creation from station clock |
| 14 | 2 | Sender-calculated remaining budget **after this TX reservation**, floored centiseconds, saturating at 65535 |
| 16 | 2 | Low 15 bits: calculated next-contact seconds, 0 unannounced. High bit: duty pacing (1), requested heartbeat schedule (0) sets the interval |
| 18 | variable | Body |
| final 2 | 2 | CRC-16/CCITT-FALSE over header + body: polynomial `1021`, initial `FFFF`, no reflection/final XOR |

Version 1 uses the same first 16 header bytes and bodies, omitting the next-contact field. Its total lengths are 40/35/35/38 bytes. The new total lengths are **42/37/37/40 bytes**. A version-1 packet supplies no schedule: its receiver uses configured receipt-age thresholds and can only show a low-budget hint, never invent a current sender state.

CRC detects accidental corruption; it provides **no encryption, authentication or replay protection**. UDP defaults to loopback. Radio security, frequency/power/antenna compliance and actual modem framing remain integration work. A modem-added envelope must be included in the actual PHY airtime before transmission.

### Smoke suspicion — 22-byte body, 42 bytes total

| Offset | Bytes | Field |
|---|---:|---|
| 18 | 16 | Full original event UUID in binary; exact match to station evidence |
| 34 | 1 | Camera 0 left / 1 centre / 2 right in bits 0–1; bit 7 recorded-source marker; other bits zero |
| 35 | 2 | Approximate bearing clockwise from configured north, centidegrees 0–35999 |
| 37 | 1 | Normalised box width ×255, rounded |
| 38 | 1 | Normalised box height ×255, rounded |
| 39 | 1 | Model confidence ×100, rounded 0–100 |
| 40 | 2 | CRC |

The horizontal centre of the original-image normalised box is `u=(x1+x2)/2`:

`bearing = (configured_heading + camera_yaw + degrees(atan((2*u-1)*tan(radians(hfov/2))))) mod 360`.

Assumptions: rectilinear lens, correct mounting and configured heading/FOV, `0 < hfov < 180`. This is neither a live compass reading nor calibrated angular accuracy. Balloon movement, tilt, lens distortion and mounting error add unknown uncertainty. Ground displays **whole approximate degrees**, with the configuration warning adjacent. Compass radius is illustrative, never a distance or fire location. Confidence is a model score, not fire probability. Contents are captured when queued; repeated detector extensions are not streamed.

### Local flame-sensor trigger — 17-byte body, 37 bytes total

Offsets 18–33 UUID, 34 source (`0` hardware, `1` simulated, `255` unknown), 35–36 CRC. No camera, bearing, image or model confidence is invented. This is a local short-range infrared trigger; it never confirms camera smoke suspicion.

### Station operator decision — 17-byte body, 37 bytes total

Offsets 18–33 UUID, 34 decision (`1` operator confirmed suspicion, `2` operator rejected suspicion), 35–36 CRC. It is a human annotation, not confirmed fire. Corrections supersede queued old decisions/repeats. Ground acknowledgements remain local and create no radio traffic.

### Status — 20-byte body, 40 bytes total

| Offset | Bytes | Field |
|---|---:|---|
| 18 | 1 | Active camera mask, left/centre/right bits 0/1/2 |
| 19 | 1 | Lost mask, subset of active |
| 20 | 2 | Pending smoke + flame count, saturated |
| 22 | 4 | Process uptime seconds, saturated |
| 26 | 1 | Battery `255` = **not measured** |
| 27 | 2 | Configured module heading, unsigned centidegrees |
| 29 | 6 | Three signed int16 camera yaws, centidegrees |
| 35 | 3 | Three configured horizontal FOVs, rounded whole degrees |
| 38 | 2 | CRC |

These sectors and camera states are last-reported configuration/status, not proof of present camera health. Before status arrives, ground marks configuration unknown. No live calibration or geographic position is implied.

## Airtime

Standard Semtech LoRa equation ([Semtech calculator](https://www.semtech.com/design-support/lora-calculator), [AN1200.86 Fig. 6](https://www.semtech.com/uploads/technology/LoRa/lora-and-lorawan.pdf)):

`Tsym=2^SF/BW`

`Npayload=8+max(ceil((8*PL-4*SF+28+16*CRC-20*IH)/(4*(SF-2*DE)))*(CR+4),0)`

`ToA=(preamble+4.25+Npayload)*Tsym`

Explicit header `IH=0`, PHY `CRC=1`, preamble 8, CR1 = 4/5 (2/3/4 mean 4/6, 4/7, 4/8), DE enabled for symbol time ≥16 ms. SF7–12 and BW125/250/500 kHz are configurable. Tests compare published lower-SF rounded 11-byte figures and independent exact vectors; no measured hardware airtime is claimed.

| Version-2 packet | Bytes | SF7/BW125/CR4/5 demo | SF10/BW125/CR4/5 | SF12/BW125/CR4/5 |
|---|---:|---:|---:|---:|
| Smoke suspicion | 42 | 87.296 ms | 534.528 ms | 2138.112 ms |
| Flame / decision | 37 | 82.176 ms | 493.568 ms | 1974.272 ms |
| Status | 40 | 82.176 ms | 534.528 ms | 1974.272 ms |

## EU 868 MHz budget

Primary source: [CEPT ERC/REC 70-03](https://docdb.cept.org/document/845), [current PDF Annex 1 h1.5–h1.9, page 8](https://docdb.cept.org/download/5013), checked 2026-11-14. The document is amended October 2026; the relevant table page retains its October 2025 edition. These harmonisation recommendations still require national implementation/conformity checks for actual deployment. This code uses the **duty-cycle path**, not LBT+AFA.

| Non-specific SRD sub-band | Max e.r.p. | Selected duty limit | Airtime/hour |
|---|---:|---:|---:|
| 868.0–868.6 MHz | 25 mW | 1% | 36 s |
| 868.7–869.2 MHz | 25 mW | 0.1% | 3.6 s |
| 869.4–869.65 MHz | 500 mW | 10% | 360 s |
| 869.7–870 MHz | 25 mW | 1% | 36 s |

The separate Annex 7 alarm-only bands and the 5 mW no-duty option are not implemented. The entire occupied bandwidth must fit the selected sub-band. No simulator output power is set or measured.

`DutyBudget` reserves complete airtime at TX start and conservatively frees it one hour after TX end. Loss and uncertain modem I/O consume the allowance. The JSON ledger persists usage **and pacing**; backwards clock movement blocks transmission, corrupt accounting blocks for an hour. Do not erase the ledger, or change the transmitter/sub-band behind its back, to gain airtime.

### Sustained scheduling, not an hourly burst

The pre-rehearsal sender legally spent 36 seconds in about 4.5 minutes with a requested four-second heartbeat; it then had to wait for the rolling hour. Accounting did refill, and restart/archive correctly retained it. The fix spreads use over time, rather than clearing the ledger or bypassing duty limits in simulation.

Each legal slot is the larger of `ceil(ToA(48)/duty_fraction + ToA(48) + 2)` and `ceil((window + ToA(48) + 2)/floor(capacity/ToA(48)))` seconds. The integer packet-count bound prevents an extra packet near the rolling-hour boundary. Using the maximum frame plus a completion/polling margin bounds every rolling hour, even as packet sizes vary. At 1% this is **12 s SF7, 61 s SF10, 241 s SF12**. The next slot survives restart. The rolling ledger remains a second independent enforcement check. An already-exhausted old ledger recovers automatically at its earliest legal release, exposed in authenticated `/api/communication`; a software upgrade cannot legally reclaim already-used airtime.

Queue order remains new alerts, decisions, due repeats, replaceable heartbeat. Alerts always beat a queued heartbeat at the next legal slot. Repeats are limited (default two, configurable 0–3), never an unbounded retransmission loop; new alerts can evict queued repeats under pressure. A future repeat no longer blocks an otherwise eligible heartbeat. New alerts take priority at the next legal slot. No emergency override circumvents legality. Inference/evidence do not wait for a radio slot.

Every transmitted packet announces `ceil(max(next_legal_TX-now, requested_heartbeat_seconds)+3)` seconds to the next expected contact. Normally next legal TX is one paced slot away; a partially exhausted legacy ledger can require a longer window, calculated without pruning or refilling live accounting early. The receiver derives its effective stale threshold as the larger of its configured minimum and that advertised window +5 s; lost follows after its configured stale-to-lost grace. Silence within the advertised window is labelled **calculated duty-cycle wait** when its reason bit says duty pacing; a deliberately slower heartbeat is labelled **scheduled contact wait** instead. Neither is proof the station is lost. Missed deadlines still become stale/lost, including after station shutdown. Packet loss, hardware failure, clock error and overload cannot guarantee delivery; no inferred battery or RF value is substituted. The receiver cannot establish a holdoff reason from missing legacy packets alone.

A continuously looping clip can generate more distinct alerts than a long-range link can carry promptly. Those original alerts queue; repeats and heartbeats yield. SF12/1% cannot carry a two-second message every ten seconds. Use the clearly labelled SF7 recorded-footage demo config for sustainable stage responsiveness, or accept the calculated long-range contact window and backlog. Three-hour tests at SF7/SF10/SF12 simulate four-second heartbeat requests and a new suspicion every 55 seconds, check **every rolling hour**, ongoing contacts, priorities, legacy-ledger recovery and pacing across restart. `ground/traffic-verification.json` records the computed run figures.

## Transport and prototype limits

`Link.send(payload, airtime)`, `receive()` and `close()` are the boundary. `SimulatedLink` carries exactly one encoded packet per UDP datagram, with optional payload cap, airtime delay and seeded loss. All senders, including simulation, obey the same duty/pacing policy. Ground PHY settings must match for its calculated airtime; they are configuration, not radio measurement.

`SerialModem` raises `NotImplementedError` deliberately: **unimplemented / untested**. Choose a modem, specify serial baud/flow control/AT or raw framing, frequency, power including antenna gain, TX-complete and RX framing, overhead, limits and errors; validate against codec vectors and actual airtime. Preserve bytes and the receiver interface, with no dashboard format workaround.

The bridge scans up to 10,000 recent events opened in its current session; historical events are not replayed at startup. Unsent queue entries remain in memory and can be lost at shutdown. Queue size is bounded at 256. Receiver journals persist independently; alert deduplication uses `(station ID, full UUID)`. Sequence gaps are provisional and late arrivals repair within a 4096-number window; half-range wrap ambiguity and loss before first/after last receipt remain unknowable. Automatic ground retention and authenticated radio framing remain field-hardening work.
