# ACORN — Aerial Canopy Observation and Reporting Node

ACORN (Aerial Canopy Observation and Reporting Node) is a portable forest observation station built by team Scarabs for the Green European Renaissance challenge at Junction 2026 in Helsinki. It is designed to run wildfire smoke detection on-device on an Arduino UNO Q with cameras; a placement tool estimates forest visibility across the Helsinki capital region.

- [`station/`](station/README.md): Python smoke detection pipeline and local web panel. See its README for setup and operation.
- [`placement/`](placement/README.md): Python line-of-sight analysis and offline map UI. See its README for data preparation and usage.
- [`tools/`](tools/README.md): upload and restore scripts for large artifacts kept in object storage, with a committed manifest. See its README for usage.

## What has been verified so far

- **Verified on a Mac:** the detection pipeline and operator panel have been run on an Apple M5 Mac against recorded clips. The only measured inference figure comes from that Mac, not from the board.
- **Pending on hardware:** nothing has been run on the Arduino UNO Q yet. On-board detection, inference timing, live camera capture and field operation are still to be tested.
- **Simulated, not measured:** placement coverage figures are geometric estimates, not a measured detection guarantee.

Model weights, downloaded datasets, map tiles, video clips, and generated event evidence are kept out of git.
