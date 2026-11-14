# ACORN — Aerial Canopy Observation and Reporting Node

ACORN (Aerial Canopy Observation and Reporting Node) is a portable forest observation station built by team Scarabs for the Green European Renaissance challenge at Junction 2026 in Helsinki. It is designed to run wildfire smoke detection on-device on an Arduino UNO Q with cameras; a placement tool estimates forest visibility across the Helsinki capital region.

- [`station/`](station/README.md): Python smoke detection pipeline and local web panel. See its README for setup and operation.
- [`placement/`](placement/README.md): Python line-of-sight analysis and offline map UI. See its README for data preparation and usage.
- [`ground/`](ground/README.md): LoRa-only remote dashboard for compact alert packets over simulated transport, with optional Wi-Fi evidence collection.
- [`tools/`](tools/README.md): upload and restore scripts for large artifacts kept in object storage, with a committed manifest. See its README for usage.
- [`firmware/`](firmware/README.md): MCU sketch designed for the Arduino UNO Q's local KY-026 flame sensor and RGB status LED, with wiring and bring-up instructions.

## What has been verified so far

- **Verified on the UNO Q:** the station has run with two live USB cameras through the kit's hub after a UVC driver bandwidth setting, the microcontroller bridge, the KY-026 flame sensor and the on-board status LED. At model input 192 with 320×240 cameras, measurements were about 278 ms inference, 0.99 analyses per second per camera, 180 MiB RAM, 42% CPU and 47°C peak. See the [board measurements](firmware/BOARD_NOTES.md).
- **Detection trade-off measured on a Mac:** input 192 detects a near plume but misses the same smoke shrunk two to four times in a synthetic proxy; input 640 still detects it, at a much lower analysis rate. The field setting is still being decided. See [detection versus input size](station/DETECTION_VS_INPUT_SIZE.md).
- **Not yet verified:** unattended restart after a power cycle, access-point mode, the external RGB LED, any real LoRa radio, and detection quality measured on the board itself.
- **Simulated, not measured:** placement coverage figures are geometric estimates, not a measured detection guarantee.

Model weights, downloaded datasets, map tiles, video clips, and generated event evidence are kept out of git.

Use [DEMO.md](DEMO.md) for the demo runbook.
