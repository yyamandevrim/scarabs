# ACORN point-to-point packet format, version 1

This is raw LoRa, **not LoRaWAN**. The current implementation is **LoRa link (simulated transport)** over UDP. No radio, range, RSSI, SNR, antenna, positioning or power measurements have been made. The same complete byte string is the radio adapter's payload later. All assets and both applications run offline after initial `uv sync` and model/media preparation.

## Envelope

Network byte order (big endian). Fixed 16-byte header, type-specific body, two-byte application CRC. Maximum accepted payload: **48 bytes**; current packets: **35–40 bytes**. No fragment, image, image URL, coordinates or text field is present. IDs are configured numeric station IDs, displayed directly without an invented station name. Assign unique IDs within a deployment.

| Offset | Bytes | Field |
|---|---:|---|
| 0 | 1 | Magic `AC` hex |
| 1 | 1 | Version in high nibble (`1`), kind in low nibble (`1` smoke, `2` flame, `3` decision, `4` status) |
| 2 | 2 | Configured unsigned station ID, 1–65535 |
| 4 | 4 | Random boot/session ID; not a secret |
| 8 | 2 | Unsigned transmission sequence, wraps at 65536; each physical attempt, including a repeat, gets a new number |
| 10 | 4 | Unix UTC seconds from the station clock: event opening, decision time, or status creation time; no GPS/time synchronisation is claimed |
| 14 | 2 | Sender's **calculated** remaining duty budget after reserving this TX, centiseconds; floored, saturates at 655.35 seconds |
| 16 | variable | Body below |
| final 2 | 2 | CRC-16/CCITT-FALSE over header and body, polynomial `1021`, initial `FFFF`, no reflection, no final XOR |

Unknown versions/types, wrong lengths, out-of-range fields and CRC corruption are rejected. PHY CRC is enabled separately in the airtime calculation. Application CRC detects accidental corruption; it provides **no encryption, sender authentication or replay protection**. The UDP simulator is loopback by default. Do not treat CRC as a security boundary or expose the simulator on an untrusted network. A selected real modem must address field link security before deployment.

### Smoke suspicion: 22-byte body, 40 bytes total

| Offset | Bytes | Field |
|---|---:|---|
| 16 | 16 | Complete original event UUID, binary (the 32 lowercase hex characters in the station store) |
| 32 | 1 | Camera in bits 0–1 (`0` left, `1` centre, `2` right); bit 7 = recorded file source; bits 2–6 reserved zero |
| 33 | 2 | Approximate bearing, unsigned centidegrees clockwise from configured north, 0–35999 |
| 35 | 1 | Normalised bounding-box width × 255, rounded |
| 36 | 1 | Normalised bounding-box height × 255, rounded |
| 37 | 1 | Model confidence × 100, rounded, 0–100 |
| 38 | 2 | CRC |

Bearing uses the horizontal centre `u = (x1+x2)/2` of the normalized original-image box and a pinhole projection:

`bearing = (configured_module_heading + camera_yaw + atan((2*u-1)*tan(hfov/2))) mod 360`.

Angles are converted to radians for trig and back to degrees. A centre box at heading 10°, yaw −70° points approximately 300°; a right-edge point with 80° horizontal FOV is +40° from the optical axis. This assumes a rectilinear lens, correct mounting, heading and FOV; distortion, balloon rotation, tilt and inaccurate calibration add unquantified error. No compass sensor or stabilized heading is claimed. Use `0 < hfov < 180`; configured yaw and heading are not live telemetry. The displayed decimal precision is wire resolution, **not angular accuracy**. The compass radial position is illustrative; it is never a fire location or distance.

Alert content is captured once when the bridge enqueues the event; later detector extensions are not a stream of radio updates. The source marker labels recorded footage even with demo imagery off. Confidence is a model score, not the probability of a fire.

### Local flame sensor: 17-byte body, 35 bytes total

Offsets 16–31: event UUID. Offset 32: source `0` hardware, `1` simulated, `255` unknown. Offsets 33–34: CRC. This is explicitly a **local short-range infrared sensor trigger**, with no camera slot, bearing or model confidence. It does not confirm camera smoke suspicion. The source flag preserves honest simulation labelling independently of transport simulation.

### Station operator decision: 17-byte body, 35 bytes total

Offsets 16–31: event UUID. Offset 32: `1` operator confirmed the suspicion, `2` operator rejected it. Offsets 33–34: CRC. It is a human review state, not a confirmed-fire message. Decision updates originate at the station's authenticated ranger panel. Ground acknowledgements stay locally on the laptop and create **no radio traffic**. The receiver can apply a decision arriving before its alert.

### Periodic status: 20-byte body, 38 bytes total

| Offset | Bytes | Field |
|---|---:|---|
| 16 | 1 | Active camera mask: left bit 0, centre bit 1, right bit 2 |
| 17 | 1 | Lost camera mask (subset of active) |
| 18 | 2 | Pending smoke + flame events, saturated at 65535 |
| 20 | 4 | Process uptime seconds, saturated |
| 24 | 1 | Battery sentinel `255` = **not measured**; no battery sensor exists |
| 25 | 2 | Configured module heading, unsigned centidegrees |
| 27 | 6 | Three configured yaws: left, centre, right, signed int16 centidegrees |
| 33 | 3 | Three configured horizontal FOVs, rounded unsigned whole degrees |
| 36 | 2 | CRC |

The camera sectors come exclusively from this packet. Before receiving status, the compass says camera configuration is unknown. Camera state and pending/uptime are last-reported values; a stale link does not establish current camera health. Coordinates, camera imagery, machine specifications and battery percentages cannot be inferred from these bytes.

## Airtime

Calculated using the standard Semtech LoRa packet equation (AN1200.13 §4). See [Semtech's calculator](https://www.semtech.com/design-support/lora-calculator) and [Semtech AN1200.86, Fig. 6](https://www.semtech.com/uploads/technology/LoRa/lora-and-lorawan.pdf). Unit tests compare the lower-SF 11-byte rounded reference times from that figure (.04/.14/.29 seconds) and exact independently calculated vectors. The figure does not specify all CRC/LDRO assumptions; its SF12 rounded value is not used as a CRC-enabled reference.

`Tsym = 2^SF / BW`

`Npayload = 8 + max(ceil((8*PL - 4*SF + 28 + 16*CRC - 20*IH)/(4*(SF-2*DE))) * (CR+4), 0)`

`ToA = (preamble + 4.25 + Npayload) * Tsym`

`IH=0` (explicit header), `CRC=1`, preamble=8, CR=1 means 4/5; CR=2/3/4 means 4/6, 4/7, 4/8. Low-data-rate optimisation `DE=1` when symbol time ≥16 ms. SF7–12 and BW125/250/500 kHz are configurable; the full occupied bandwidth must fit within the selected sub-band. No LoRaWAN MAC overhead is added because this is raw point-to-point LoRa. A modem that adds an envelope needs its actual PHY payload airtime accounted for before use.

| Packet | Bytes | SF10, BW125, CR4/5 | SF12, BW125, CR4/5 |
|---|---:|---:|---:|
| Suspected smoke | 40 | 534.528 ms | 1974.272 ms |
| Flame-sensor trigger | 35 | 493.568 ms | 1810.432 ms |
| Operator decision | 35 | 493.568 ms | 1810.432 ms |
| Status | 38 | 493.568 ms | 1974.272 ms |

## EU 868 MHz duty cycle and scheduling

Primary regulatory source checked 2026-11-14: [CEPT ERC/REC 70-03, current document](https://docdb.cept.org/document/845), [PDF Annex 1, h1.5–h1.9, page 8](https://docdb.cept.org/download/5013). The current document is amended October 2026; the relevant Annex 1 table retains its October 2025 page edition. These are harmonisation recommendations; national implementation/restrictions and final radio conformity still need checking for the actual deployment. This software chooses the **duty-cycle path**, not the alternative LBT+AFA path.

| Non-specific SRD sub-band | Max e.r.p. | Duty cycle chosen by this implementation | Airtime/hour |
|---|---:|---:|---:|
| 868.0–868.6 MHz (h1.5) | 25 mW | ≤1% | 36 s |
| 868.7–869.2 MHz (h1.6) | 25 mW | ≤0.1% | 3.6 s |
| 869.4–869.65 MHz (h1.7) | 500 mW | ≤10% | 360 s |
| 869.7–870 MHz (h1.9) | 25 mW | ≤1% | 36 s |

Annex 1 also has a 5 mW no-duty-requirement option for 869.7–870 MHz (h1.8); it is not implemented. The separate alarm-only bands in Annex 7 are **not** selected: they have their own application, bandwidth and power requirements. An alert application does not automatically entitle a 125 kHz LoRa modem to use those alarm channels. No output power is set by this simulator; the serial adapter must implement and validate e.r.p. including antenna gain.

`DutyBudget` reserves complete packet airtime against a rolling hour. It conservatively retains that reservation until one hour after TX completion, then frees it. Every attempt, including simulated packet loss and an uncertain serial I/O error, consumes budget. `data/lora-duty.json` persists the ledger; do not delete it to recover budget. Backwards clock movement blocks transmission until the previous time is reached. A corrupt ledger blocks for one hour. Use a correct, stable system clock; do not share the same sub-band among unaccounted transmitters on this device. This is a software budget calculation, not certification.

The queue holds at most 256 messages: new smoke/flame alerts first, operator decisions next, due repeats next, heartbeat last. A new alert evicts a queued repeat if full; if it still cannot fit it remains eligible for the next scan and overflow is counted. There are at most two repeats by default (configurable 0–3), 30 seconds apart, with at least one second quiet time after each packet. A delayed heartbeat is replaced by a fresh one; it never builds a backlog. Heartbeats yield while alert/decision work remains queued and retain airtime for one maximum-size new alert. If the rolling budget is exhausted, even an urgent alert waits: there is no illegal emergency override and delivery is never guaranteed. Outbox errors are logged without stopping camera processing.

At SF10, six smoke suspicions/hour with two repeats each use **9.622 s**. Six decision updates repeated similarly use **8.884 s**. Twelve 5-minute heartbeats use **5.923 s**: total **24.429 s/hour**, below the default 36 s (1%) allowance. This leaves 11.571 s for other alerts; clusters can still queue. At SF12 the same load requires **91.816 s/hour**, so it cannot fit 1%; messages wait and heartbeats yield. Even one repeated smoke + decision/hour plus twelve heartbeats costs **35.045 s**, leaving little margin. Configure longer heartbeat intervals/stale thresholds or a legally available sub-band after selecting and validating the actual hardware; never promise both a fast heartbeat and an arbitrary alert rate at SF12.

## Integration and limitations

`Link.send(payload, airtime)`, `receive()` and `close()` are the adapter boundary. `SimulatedLink` sends precisely the codec output in one UDP datagram, with optional packet loss, payload cap and airtime delay. Sender duty refusal is always enforced, independently of simulated delay/loss. Seeded loss is reproducible; the OS network adds no simulated RSSI. Sender/receiver must use identical PHY settings for calculated airtime; those settings are local configuration, not a fictitious measurement.

`SerialModem` deliberately raises `NotImplementedError`: **unimplemented and untested**. Select a modem and determine raw vs AT framing, serial baud/flow control, radio parameters/frequency/e.r.p., TX-complete and RX framing, packet limits, timeout/error handling and added envelope overhead. Return only original packet bytes to `Receiver.ingest`; the codec and dashboards must not change. Validate integration against golden codec vectors and actual airtime before enabling transmission.

The bridge currently scans up to 10,000 recent events and transmits events opened during the current process session. Historical events are not replayed on restart; pending outbox work is in memory and can be lost on shutdown. The receiver journals packets/acknowledgements in its own SQLite database and de-duplicates alerts by `(station ID, full UUID)` across boots/repeats. Missing sequence numbers are provisional (late arrivals repair gaps within a 4096-number window); sequence loss across more than half the 16-bit range is ambiguous. Lost packets before the first received sequence or after the last cannot be counted. Long-range delivery reliability, persistence of unsent work across station restarts, authenticated radio packets and automated receiver retention remain future field-hardening work, explicitly not demonstrated capabilities.
