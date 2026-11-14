# MicroMesh hardware investigation

Status: **identification blocked; real transport not implemented or verified**.
This record is dated 2026-11-14. The existing laptop demo still uses **LoRa link
(simulated transport)**. End-to-end reception between station and ground is
**unverified**. No RF range or reliability was measured. Alerts remain smoke
suspicion, never automatic confirmed fire; imagery does not belong in radio packets.

## What is documented, and what is not

The [maker's MicroMesh listing](https://www.shopier.com/46120123) describes an
**nRF52840** board with an **RA-01-series 433 MHz** radio, compatible with
Meshtastic and LoRaAPRS. Compatibility is not evidence of the firmware actually
installed or shipped. The [maker's site](https://deeplabstudio.com/) lists
MicroMesh and MiniMesh Lite as separate products.

[Ai-Thinker's radio selection table](https://docs.ai-thinker.com/_media/esp32/docs/ra-08h_v1.1.0_specification.pdf)
distinguishes RA-01 (SX1278, 410–525 MHz), RA-01S (SX1268, 410–525 MHz),
RA-01H (SX1276, 803–930 MHz), and RA-01SH (SX1262, 803–930 MHz).
The full suffix on the actual radio matters. The maker's generic series name
does not establish the exact radio chip. A 433 MHz variant cannot be made into
an 868 MHz radio by changing a software region setting.

The [maker's public design repository](https://github.com/Deeplab-Studio/MiniMeshLite-V1)
contains **MiniMesh Lite**, an ESP32/RA-02 design. It is not a MicroMesh
nRF52840 schematic or pinout. No MicroMesh schematic, pinout, or stock firmware
release was located in the maker sources searched. Do not wire using that other
board's schematic.

The actual module's installed firmware/version, host protocol, enabled USB/UART/
Bluetooth interfaces, binary payload capacity, RF headers, retransmissions,
frequency, spreading factor, bandwidth, coding rate, preamble, transmit power,
configuration API, and duty-cycle enforcement are **not yet established**.
USB-C identifies a connector, not a serial command set. No AT commands or custom
framing have been assumed.

For context only, **if Meshtastic is confirmed**:

- Its [client API](https://meshtastic.org/docs/development/device/client-api/)
  carries protobuf ToRadio/FromRadio messages over serial, TCP or BLE. Serial
  frames have `94 c3`, then a two-byte big-endian length, then protobuf bytes;
  the documented frame limit is 512 bytes. This four-byte host framing is not
  the RF overhead.
- Its [binary send API](https://python.meshtastic.org/mesh_interface.html)
  accepts bytes and supports application ports, acknowledgement/retry choices
  and hop limits. That makes it a candidate for preserving ACORN packet bytes,
  but does not prove this particular module runs it.
- Its [LoRa configuration](https://meshtastic.org/docs/configuration/radio/lora/)
  exposes PHY settings and European hourly duty enforcement, enabled by default
  unless overridden. Do not enable the duty override. These are firmware docs,
  not settings read back from the owner's module.

ACORN's current calculator and rolling ledger describe raw LoRa packets in its
configured EU868 sub-band. They do not account for an unidentified mesh firmware's
RF envelopes, autonomous telemetry, relays or retries. Applying the raw 42-byte
airtime to a mesh transmission would be a **lower bound**, not a complete RF
budget. A real adapter must first reconcile actual PHY settings and overhead
with the existing scheduler and retain its persistent duty budget.

## What was checked on this Mac

At **2026-11-14 07:15:23 UTC** and again at **07:16:16 UTC**:

```sh
ls /dev/cu.* /dev/tty.*
system_profiler SPUSBDataType
system_profiler SPUSBHostDataType
```

Only these serial devices were listed:

```text
/dev/cu.Bluetooth-Incoming-Port
/dev/cu.debug-console
/dev/tty.Bluetooth-Incoming-Port
/dev/tty.debug-console
```

`SPUSBDataType` returned no output. This Mac lists `SPUSBHostDataType` as its
supported USB profiler category; it showed three built-in USB buses with no
attached devices. An additional USB registry inspection also showed no attached
USB peripherals at those checks.

At **07:20:13 UTC**, a new USB device appeared as **USB Type-C Digital AV Adapter**,
vendor/product **343c:0000**, manufacturer `xxxxxxxx`. Read-only USB registry
inspection reported device class `0x11`, subclass/protocol `0/0`, and no serial
interface. The serial device list remained exactly as above. This identity does
not establish that the attached device is a MicroMesh or provide a radio protocol.
**No device identified as MicroMesh or usable radio serial port was found**, so
no radio firmware identity query, configuration read-back, transmit acceptance
or reception was performed.
No radio serial port was opened. No packet was transmitted or received in this
investigation. The borrowed UNO Q was not connected to, changed or flashed.

Documentation-only validation on this Mac: `uv run --offline --frozen pytest -q`
passed **248 station tests** and **21 ground tests**. From `station/`,
`node --test tests/panel.test.mjs ../ground/tests/dashboard.test.mjs` passed
**47 UI tests**. Both Python suites emitted the existing Starlette/httpx
deprecation warning. No real adapter or fake-serial tests were added: the
hardware identification gate remains unresolved, so these passing existing
tests do not establish radio support.

The owner reports **exactly one module**, with a **USB-C connector and its antenna
attached**. These are owner reports, not physical observations. That antenna
confirmation covers this module only. A second transmitting module needs its own
antenna confirmation before testing.

## Owner actions needed to finish identification

1. Connect the module directly to this Mac with a known **data-capable** USB
   cable. It may currently be connected to the UNO Q or another machine, or the
   cable may supply power only. Re-run the inventory commands above.
2. Supply readable photos of both PCB sides and the radio shield/module marking:
   full RA-01 suffix, frequency label and board revision. Include packaging/SKU
   details and the firmware name/version visible on its screen or existing app.
   Do not share channel keys, QR provisioning codes or passwords publicly.
3. Once its actual host protocol is identified, perform a read-only identity and
   configuration query. Do not flash it, guess UART pinouts or issue speculative
   AT commands. Resolve the published 433 MHz versus required 868 MHz mismatch
   before enabling any RF transmission.

No real-radio configuration lines or run commands can be provided accurately
until that identification succeeds. The existing `serial` selection remains an
unimplemented skeleton that refuses startup; it must not be presented as an
absent-radio-safe adapter or a working link. Keep the current demo configuration
on `transport = "simulated"` and follow [DEMO.md](../DEMO.md).

## Where the single module should go

Use the **ground laptop** for the first hardware demonstration: it has a free
USB port and permits host-protocol/read-back testing without disturbing the
borrowed station or either camera. Until a real adapter exists, this is a
separate hardware investigation; the dashboard's working ACORN packet path
remains explicitly simulated. Hearing unrelated mesh traffic would not validate
ACORN packet delivery or create an ACORN smoke alert.

After identification and lawful PHY configuration, a one-radio bench test can
record local identity, configuration read-back and a low-power transmit request
accepted by the firmware. Record actual packet bytes, UTC times, module responses
and any reported RSSI/SNR. Serial acceptance is not proof of RF delivery.
Receiving ambient traffic depends on matching firmware, band, PHY and channel
configuration and on another transmitter actually being present.

## Ways to close end-to-end verification today

| Option | What it needs | What it can establish |
| --- | --- | --- |
| Second matching module | A second radio of the correct band, compatible firmware, antennas on both transmitters, matching PHY/channel settings, and a station USB connection | Preferred path: transmit known ACORN bytes on the station side and compare exact received bytes on ground; exercise status and decision updates too |
| Another team's or venue's node | Owner permission, a compatible band/firmware/PHY/channel, private sharing of any required key, and a host client capable of handling ACORN binary application packets | An actual RF peer; ordinary text chat alone does not validate ACORN binary delivery |
| Phone paired to this module | Installed firmware must support its phone client; Bluetooth/client connection and access to the relevant payloads are needed | Local client functionality only. A phone paired to the **same single radio** is not a second LoRa receiver. For RF end-to-end testing, the phone must be paired to **another** compatible radio |

Meshtastic's [getting-started guide](https://meshtastic.org/docs/getting-started/)
distinguishes the phone/computer client connection from communication between
LoRa radios. A stock phone app may not display arbitrary ACORN binary payloads;
use a compatible binary client/bridge to validate the actual dashboard path.

## Station connection options once the radio is identified

| Connection | Work needed | Tradeoff |
| --- | --- | --- |
| Powered hub with at least three usable downstream ports | Replace the two-port hub; connect both cameras and the radio by data cables; verify power and camera USB bandwidth again | Recommended, least software work; preserves both camera views and stock radio firmware |
| Existing hub with one camera | Owner disconnects one camera and updates its local station configuration | Fast fallback, but loses one active view; requires an explicit demo description |
| Header UART through UNO Q microcontroller | Verified MicroMesh/UNO Q pinouts and logic voltages, wiring, serial framing/flow control and a new MCU-to-Linux bridge alongside the flame sensor/LED sketch | Substantial additional firmware/integration work and eventual board flashing; outside this task's no-board-change constraint |

No header wiring is prescribed until the exact module schematic and voltage
requirements are known. Direct SPI would require bypassing or changing the stock
firmware integration and is not the smallest working path.

For any eventual adapter, preserve simulated defaults, exact ACORN payload bytes,
station-to-ground decision flow, explicit missing/busy/unplugged radio status,
serial resynchronization and partial-frame handling. Test those behaviors using
a fake serial device before claiming hardware support. Keep any channel key in an
ignored local configuration or environment variable selected by that adapter;
never commit a key, provisioning QR code or credential.
