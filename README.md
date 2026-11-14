<h2 align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/brand/acorn-wordmark-white.svg">
    <img src="assets/brand/acorn-wordmark-black.svg" width="460" alt="ACORN">
  </picture>
  <br>
  Aerial Canopy Observation and Reporting Node
</h2>

ACORN (Aerial Canopy Observation and Reporting Node) is a portable forest observation station built by team Scarabs for the Green European Renaissance challenge at Junction 2026 in Helsinki. It is designed to run wildfire smoke detection on-device on an Arduino UNO Q with cameras; a placement tool estimates forest visibility across the Helsinki capital region.

- [`station/`](station/README.md): Python smoke detection pipeline and local web panel. See its README for setup and operation.
- [`placement/`](placement/README.md): Python line-of-sight analysis and offline map UI. See its README for data preparation and usage.
- [`ground/`](ground/README.md): LoRa-only remote dashboard for compact alert packets over simulated transport, with optional Wi-Fi evidence collection.
- [`tools/`](tools/README.md): upload and restore scripts for large artifacts kept in object storage, with a committed manifest. See its README for usage.
- [`firmware/`](firmware/README.md): MCU sketch designed for the Arduino UNO Q's local KY-026 flame sensor and RGB status LED, with wiring and bring-up instructions.

## What has been verified so far

- **Verified on the UNO Q:** the station has run with two live USB cameras through the kit's hub after a UVC driver bandwidth setting, the microcontroller bridge, the KY-026 flame sensor and the on-board status LED. At model input 192 with 320×240 cameras, measurements were about 278 ms inference, 0.99 analyses per second per camera, 180 MiB RAM, 42% CPU and 47°C peak. See the [board measurements](firmware/BOARD_NOTES.md).
- **Detection trade-off measured on a Mac:** input 192 detects a near plume but misses the same smoke shrunk two to four times in a synthetic proxy; input 640 still detects it, at a much lower analysis rate. The repository now separates a field profile (640 input, confidence 0.25, six-second interval) from a fast demo profile (192 input, confidence 0.35, one-second interval). The board remains on the restored demo settings. The six-second timing curve used confidence 0.35; performance of the exact new field profile remains unmeasured. See [analysis profiles](station/README.md#analysis-profiles) and [detection versus input size](station/DETECTION_VS_INPUT_SIZE.md).
- **Power-cycle recovery verified:** the owner powered the board off and back on; the station started automatically with both cameras and fresh sensor telemetry. An optional SSH tunnel must reconnect separately. Direct authenticated HTTP access on existing Wi-Fi was subsequently validated; the changed bind has not been browser or power-cycle tested. See [direct panel access](station/README.md#direct-panel-access-on-an-existing-wi-fi-network). See the [recovery record](firmware/BOARD_NOTES.md).
- **Not yet verified:** access-point mode, the external RGB LED, any real LoRa radio, and detection quality measured on the board itself.
- **Simulated, not measured:** placement coverage figures are geometric estimates, not a measured detection guarantee.

Supplied logo sources and offline usage are documented in [asset provenance](assets/brand/README.md).

Model weights, downloaded datasets, map tiles, video clips, and generated event evidence are kept out of git.

Use [DEMO.md](DEMO.md) for the demo runbook.
