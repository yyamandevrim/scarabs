# MicroMesh hardware and the Meshtastic transport

Status, **2026-11-14**: a Meshtastic transport is **implemented and tested only
against a fake Meshtastic interface**. **None of it has been run on hardware.**
The module has not yet enumerated on this Mac: it was not with the owner during
this pass. Its firmware, region, frequency, modem settings and node ID are
**unknown**. No packet has been transmitted or received. No range, RSSI, SNR or
reliability has been measured. The default stays **LoRa link (simulated
transport)**, and every existing demo and test behaves as before. Alerts remain
smoke suspicions, never confirmed fires. Radio packets never carry imagery.

## What the module is documented to be

The [maker's MicroMesh listing](https://www.shopier.com/46120123) describes an
**nRF52840** board with an **RA-01-series** radio that is compatible with
Meshtastic and LoRaAPRS. A compatibility claim does not tell us which firmware is
actually installed. [Ai-Thinker's selection table](https://docs.ai-thinker.com/_media/esp32/docs/ra-08h_v1.1.0_specification.pdf)
lists four variants. Read the full suffix on the radio can to know which one it is:

| Marking | Chip | Band |
| --- | --- | --- |
| RA-01 | SX1278 | 410–525 MHz |
| RA-01S | SX1268 | 410–525 MHz |
| RA-01H | SX1276 | 803–930 MHz |
| RA-01SH | SX1262 | 803–930 MHz |

A 433 MHz part cannot become an 868 MHz radio through a software region setting,
and the reverse is also true. The maker's public repository holds the different
MiniMesh Lite (ESP32/RA-02) design. It is not a MicroMesh schematic.

## Mac checks so far

| UTC time (2026-11-14) | Result |
| --- | --- |
| 07:15, 07:16 | `ls /dev/cu.* /dev/tty.*` lists only Bluetooth-Incoming-Port and debug-console. USB profilers show no attached device. |
| 07:20 | A "USB Type-C Digital AV Adapter" (343c:0000, class 0x11, no serial interface) appears. It is not the module: it is gone again later. |
| Later pass | There is still no serial device and the USB device tree is empty. The owner confirms the module is **not at hand**. `meshtastic --ble-scan` (listen only) found no node. That is not conclusive: the module may be off or out of reach, or the terminal may lack Bluetooth permission. |

## What is implemented (none of it run on hardware)

- `station/station/lora/mesh.py`, `MeshtasticLink`:
  - It uses the `meshtastic` Python library's documented `SerialInterface` (or
    `BLEInterface`), `sendData` and pypubsub `meshtastic.receive` /
    `meshtastic.connection.lost` topics.
  - The unchanged ACORN packet bytes (37–42 B; the protocol allows up to 48)
    travel as a binary payload on **`PRIVATE_APP` (port 256)**. The send uses
    `wantAck=False`, a configurable channel index, hop limit 0 by default, and
    broadcast `^all` by default.
  - On receive, it ignores other ports and other interfaces. It counts and drops
    non-dict garbage and payloads outside 1–48 bytes. A right-sized payload goes
    to the same `decode()` path as UDP, and the ground receiver counts a CRC or
    format failure as an invalid packet. It records RSSI, SNR and the sender ID
    of the last packet as reported.
  - Serial framing, resynchronisation and partial frames are handled inside the
    `meshtastic` library's stream reader. Our tests cannot exercise that layer
    without a device.
- **States.** The link reports one of `connecting`, `absent` (no port), `busy`
  (port locked by another program), `unavailable` (optional package missing),
  `refused` (region or PHY not acceptable), `error`, `disconnected` (lost
  mid-run) or `ready`. A supervisor retries every `mesh_retry_seconds` and keeps
  the last failure visible. On a refusal it closes the port, so the CLI can fix
  the node's configuration. The library's own `sys.exit` calls are caught.
- **What the UIs show.** Only `ready` is shown as connected. The station panel
  header shows a LoRa line, red unless the radio is ready. A ready radio reads
  "delivery not confirmed". The ground dashboard label reads, for example,
  "LoRa link (Meshtastic radio · radio absent)" in red. The station API exposes
  the same state as `lora` in `/api/status` and as `radio` in
  `/api/communication`; ground exposes it as `link` in `/api/state`.
- **Station sending.** The station builds its sender only after reading back the
  node's band. Events that open while the radio is absent stay unsent and are
  scanned in once it is ready. Heartbeats are not queued while the radio is
  absent. A send that fails mid-run counts as a lost packet: its airtime is
  already charged. If the PHY changes on reconnect, the station refuses to send
  until it is restarted. The ledger is separate per real sub-band:
  `data/lora-duty-meshtastic-<sub-band>.json`.
- **Ground receiving.** The ground side is receive-only (`transmit=False`). It
  replaces the configured airtime PHY with the node's read-back PHY.
- **Optional dependency.** `meshtastic` is an optional extra (`--extra
  meshtastic`). Without it, station and ground import and run simulated as
  before, and a Meshtastic link shows `unavailable`.

Fake-interface tests: `station/tests/test_mesh.py` and
`ground/tests/test_mesh_ground.py`. They cover send, receive, region and PHY
refusal, absent, busy and missing-library states, disconnect and reconnect, send
failure, garbage, wrong lengths, foreign ports and interfaces, and the
station-bridge and ground-API states. The UI tests cover the panel and dashboard
states. A separate check against the real `meshtastic` 2.7.11 library, with real
pypubsub and real protobuf `LoRaConfig` enums but no device, confirmed three
things: a missing port shows as `absent`, an EU_868 LONG_FAST configuration reads
as ready, and receive and connection-lost dispatch work.

## Region and band: read from the node, never assumed

On every connect the adapter reads `localNode.localConfig.lora` and refuses to
operate unless **all** of these hold:

- The region is **EU_433** or **EU_868**. UNSET or any other region is refused.
- `override_duty_cycle` is off.
- `tx_enabled` is on (station only).
- `tx_power` is at or below the region limit, where 0 means the firmware default.
- The preset is one of SHORT_TURBO, SHORT_FAST, SHORT_SLOW, MEDIUM_FAST,
  MEDIUM_SLOW, LONG_FAST, LONG_TURBO, LONG_MODERATE or LONG_SLOW, or a custom PHY
  is used with 125/250/500 kHz, SF7–12 and CR 4/5–4/8.
- Every possible channel centre keeps the whole occupied bandwidth inside **one**
  sub-band listed in `radio.BANDS`.

The channel centre uses the firmware formula from `RadioInterface.cpp`:
`freqStart + bw/2 + slot·bw`, where `slot` is `channel_num-1` or
djb2(primary channel name) mod the number of slots, then `+ frequency_offset`, or
`override_frequency` when set. If the slot depends on a firmware display name
that we do not reproduce, every slot is checked.

| Node region | Firmware span | Legal sub-band used | ERC/REC 70-03 Annex 1 | Duty limit | Firmware power limit |
| --- | --- | --- | --- | --- | --- |
| EU_868 | 869.4–869.65 MHz | 869.4–869.65 MHz | h1.7: 500 mW e.r.p., ≤ 10% or LBT+AFA | 10% | 27 dBm |
| EU_433 | 433.0–434.0 MHz | 433.05–434.79 MHz | g1: 10 mW e.r.p., ≤ 10% duty cycle | 10% | 10 dBm |

Source: [CEPT ERC/REC 70-03](https://docdb.cept.org/download/5013), page 8
(edition of October 2025), checked 2026-11-14. National implementation, here
Traficom for Finland, still applies.

- **EU_433 caveat.** Meshtastic's slot 1 (433.0–433.25 MHz at 250 kHz) crosses
  the g1 lower edge of 433.05 MHz. With an empty channel name the default slot
  is therefore refused. Set `lora.channel_num` to 2, 3 or 4 (centres 433.375,
  433.625 and 433.875 MHz), or use a named primary channel whose hash lands
  inside the band.
- **Antenna gain.** These limits are e.r.p. A conducted power limit plus a gain
  antenna can exceed them. The antenna's gain is unknown, so lower `tx_power` if
  the gain is above about 2 dBi.

## Airtime accounting is a lower bound

The airtime calculation uses:

- the node's read-back SF, bandwidth and coding rate;
- a 16-symbol preamble;
- an estimated **23 bytes** of Meshtastic on-air overhead: a 16-byte header plus
  about 7 bytes of `Data` protobuf (portnum 256, payload length, bitfield).

A 42-byte alert is therefore charged as about 65 bytes. The station keeps its
existing rolling-hour ledger and pacing at `duty_fraction` (default 1%, below
the 10% sub-band limit).

The calculation does **not** count:

- relays by other nodes;
- routing and ACK frames;
- the node's own NodeInfo, telemetry and position broadcasts;
- anything the node rebroadcasts for others.

The firmware also applies its own transmit-utilisation check in duty-limited
regions unless `override_duty_cycle` is set (ACORN refuses that), and it may
hold or drop packets on its own. For these reasons ACORN's ledger is a **lower
bound** on real channel use, not a complete RF budget.

## Connect and identify the module (do this first)

1. Bring the module. Connect it **directly** to the Mac, with no hub or AV
   adapter, using a USB-C cable known to carry data. Switch it on and check that
   an LED or screen lights.
2. Find it:

   ```sh
   ls /dev/cu.*        # expect a new /dev/cu.usbmodem… entry
   system_profiler SPUSBHostDataType
   ```

   If nothing appears, try another known data cable and the other USB-C port.
   Do not guess further, and do not reflash.
3. Identify it **read-only**, in a throwaway environment, with no setting
   changes:

   ```sh
   export ACORN_MESH_PORT=/dev/cu.usbmodemXXXX   # local shell only, never committed
   uvx --from 'meshtastic==2.7.11' meshtastic --port "$ACORN_MESH_PORT" --info
   uvx --from 'meshtastic==2.7.11' meshtastic --port "$ACORN_MESH_PORT" --get lora
   ```

   Record the firmware version, hardware model, node ID, `lora.region`,
   `modem_preset`/`use_preset`, `channel_num`, `tx_power`, `override_duty_cycle`
   and `tx_enabled`. Also read the radio can marking (RA-01 versus RA-01H/SH).
   These commands exchange data with the node over USB only. However, if a
   region is already set, the node may transmit its own broadcasts on its own
   schedule. Do not run `--set`, `--sendtext`, `--reboot`, `--factory-reset` or
   any flashing command at this step.
4. Region decision, made only once the chip band is known:
   - A 433 MHz part (RA-01/RA-01S) gets EU_433 plus a legal `channel_num`.
   - An 868 MHz part (RA-01H/RA-01SH) gets EU_868.

   **Setting a region turns the radio on and the node starts its own
   transmissions.** Confirm that the antenna is attached first. These are
   configuration writes, not flashing:

   ```sh
   meshtastic --port "$ACORN_MESH_PORT" --set lora.region EU_868   # 868 MHz hardware only
   # or, 433 MHz hardware only:
   meshtastic --port "$ACORN_MESH_PORT" --set lora.region EU_433 --set lora.channel_num 2
   ```

5. Private channel, so that ACORN payloads do not ride the public default key.
   The key lives only on the nodes and in an ignored `.env`. ACORN code never
   reads it.

   ```sh
   # In an ignored .env:  ACORN_MESH_PSK="base64:$(openssl rand -base64 32)"
   meshtastic --port "$ACORN_MESH_PORT" --ch-add acorn
   meshtastic --port "$ACORN_MESH_PORT" --ch-index 1 --ch-set psk "$ACORN_MESH_PSK"
   ```

   Use the same channel name and PSK, and the same region and preset, on the
   second node.

## Run the real transport

The station side goes in an ignored `communication.local.toml`, under `[lora]`:

```toml
enabled = true
transport = "meshtastic"
mesh_port = "/dev/cu.usbmodemXXXX"   # or mesh_ble = "<address>"
mesh_channel_index = 1
mesh_hop_limit = 0
duty_fraction = 0.01
```

```sh
cd station && uv sync --extra meshtastic
uv run --extra meshtastic forest-station --config communication.local.toml serve --port 8091
```

The ground side is receive-only and needs the second node on its own USB port:

```sh
cd ground && uv sync --extra meshtastic
uv run --extra meshtastic acorn-ground --transport meshtastic --mesh-port "$ACORN_MESH_PORT" --mesh-channel-index 1
```

`--mesh-port` defaults to the `ACORN_MESH_PORT` environment variable. The
station's `sf`, `bandwidth`, `sub_band` and `frequency` lines are not used for
Meshtastic: the node's values are. Do not delete the duty ledger files.

## One module: what can and cannot be demonstrated

**Correction to an earlier plan:** a phone paired over Bluetooth to our **only**
module is **not** a second LoRa endpoint. That path is phone↔node over
Bluetooth, not over the air, so it proves nothing about RF delivery. Also, a
node may serve only one client API connection at a time, so do not use USB and
BLE together (untested).

An over-the-air demonstration therefore needs a **second compatible radio**: the
same band hardware, region, preset and channel/PSK, with its antenna attached.
Options:

- **Second node on the ground laptop (preferred).** Run `acorn-ground
  --transport meshtastic` on it. Compare exact bytes, the alert and the
  RSSI/SNR it reports.
- **Phone paired to the second node.** The stock app will at best show our node
  in its node list with signal values. It does not display binary `PRIVATE_APP`
  payloads as messages, so this shows RF between two radios but not ACORN packet
  delivery.

With one module, the only possible bench test is identification, configuration
read-back, and the firmware accepting a single transmission from the station.
Acceptance by the node is not proof of reception.

## Bench test to run when hardware is present (ordered)

1. Identification (above). Record the outputs with UTC times. Do not commit the
   port path.
2. Region and channel set-up, with the owner re-confirming the antenna before the
   first transmission.
3. Start the station with the local config. The panel must show `radio
   connected`, the region and the sub-band.
4. Unplug the cable. The panel must turn red ("radio disconnected", then "radio
   absent"). Replug it and check that it recovers without a restart.
5. With a second radio: start ground, trigger a recorded smoke suspicion, and
   compare the received bytes and alert. Record RSSI/SNR from
   `/api/state` → `link.last_rx`.
6. Busy port: open the port with `meshtastic --port … --listen` while the
   station runs. The station must show "serial port busy".

## Verified versus not

| Item | Status |
| --- | --- |
| Packet format, duty ledger, pacing, simulated UDP link | Tested (existing suites) |
| Meshtastic adapter logic, refusals, states, UI display | Tested with a fake interface only |
| Adapter with real `meshtastic` library objects (no device) | Checked once in a throwaway venv |
| Enumeration, firmware, region, frequency of the actual module | **Not done**: module not at hand |
| Any RF transmission or reception, RSSI/SNR, range | **Not done** |
| Firmware's own duty enforcement and overhead | Documented from firmware source, not measured |

## Demo-flow notes

- Keep the jury demo on the simulated transport unless the bench test above has
  passed on the day.
- If two radios pass the bench test, show the ground label switching from
  "radio absent" to "radio connected" when the node is plugged in. Then show one
  smoke suspicion arriving, and say that delivery and range were not measured
  beyond that bench test.

## Station connection options

The station-side options are unchanged. A powered hub with three or more data
ports keeps both cameras and the radio. Using one camera fewer is the fast
fallback. Header UART through the UNO Q needs verified pinouts and new MCU
firmware, which is out of scope here. Never reflash the module unless there is
no other way, and only after asking the owner.
