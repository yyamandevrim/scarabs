# Portable forest observation station

Built by team Scarabs for the Green European Renaissance hackathon. The project name is to be decided. An Arduino UNO Q with cameras detects wildfire smoke on-device; a placement tool estimates forest visibility across the Helsinki capital region.

- [`station/`](station/README.md): Python smoke detection pipeline and local web panel. See its README for setup and operation.
- [`placement/`](placement/README.md): Python line-of-sight analysis and offline map UI. See its README for data preparation and usage.

Hardware measurements and simulated coverage numbers are labelled separately. Simulated visibility is an estimate, not a measured detection guarantee.

Model weights, downloaded datasets, map tiles, video clips, and generated event evidence are kept out of git.
