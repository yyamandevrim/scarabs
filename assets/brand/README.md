# ACORN artwork

ACORN is **Aerial Canopy Observation and Reporting Node**, by team **Scarabs** for **Junction2026 Helsinki**.

These six standalone SVGs are faithful splits of Yaman’s original **Asset 1.svg** (79,462 bytes; SHA-256 `a9c1989cf8c6674ebada3e923d9f2443ff576a7cdf310942189448a06dca24fa`). The supplied file has one flat layer containing 240 vector shapes, visually arranged as six logos. Every shape belongs to exactly one derivative. All original polygon points, rectangle coordinates, path data, fill colors, counters and relative placement are retained, including the outlined caption lettering. No tracing, raster wrapping, font substitution or reconstructed lettering is used.

| Canonical variant | Original layer elements (zero-based, inclusive) | ViewBox | Padding in source units |
| --- | --- | --- | --- |
| `acorn-wordmark-black.svg` | 0–13 | `103.90 1892.57 638.87 207.29` | 8 |
| `acorn-stacked-black.svg` | 14–66 | `-12.00 -12.00 870.67 407.95` | 12 |
| `acorn-wordmark-white.svg` | 67–80 | `103.90 2148.75 638.87 207.29` | 8 |
| `acorn-stacked-white.svg` | 81–133 | `-12.00 564.70 870.67 407.95` | 12 |
| `acorn-horizontal-white.svg` | 134–186 | `99.90 1217.38 1538.83 215.29` | 12 |
| `acorn-horizontal-black.svg` | 187–239 | `99.90 1483.65 1538.83 215.29` | 12 |

Wordmarks contain 14 shapes each; full lockups contain 53 shapes each. Both caption lines are complete in the original vector, even where the earlier PNG sheet clipped them. Tight viewBoxes include deliberate clear space beyond all artwork bounds. The SVGs retain original artwork coordinates; only the document bounds change. The original has no required defs, clip paths, transforms or cross-file IDs. Editor layer IDs and document cruft are omitted. No full sheet, uploaded application screenshot, attachment path or personal metadata is shipped.

## Display sizes

- App headers: white wordmark, 120 px CSS width on desktop, 104 px at viewport widths up to 760 px. Proportional heights are about 38.94 px and 33.74 px. Desktop bars remain 48 px high.
- Landing hero: complete white stacked lockup, up to 460 px wide (215.53 px high).
- Ranger sign-in: complete white stacked lockup, up to 360 px wide (168.67 px high).
- Root README: 460 px wordmark. Station, Ground, Placement and Firmware READMEs: 400 px wordmark. All five center the logo using GitHub-supported `<p align="center">`, `<picture>` and `<img width>` without a fixed height. GitHub’s responsive image rules shrink them on narrow viewers. The full product name appears centered beneath as normal text.

The SVGs are resolution-independent. Landing/sign-in scale to available width without clipping or stretching. Do not alter the custom letterforms, crop lettering, apply color filters, add effects or substitute fonts. The full expansion stays **Aerial Canopy Observation and Reporting Node**, including in Turkish. Accessible labels name each logo once: Station uses its named heading, Ground/sign-in use image alt text, and Placement uses adjacent visually hidden identity text. READMEs select the white SVG for dark themes and black SVG otherwise.

## Offline copies and replacement

This directory is canonical. Independently runnable apps carry byte-identical SVGs:

- `station/station/static/brand/`: white wordmark and stacked lockup.
- `ground/ground/static/brand/`: white wordmark.
- `placement/static/brand/`: white wordmark and stacked lockup.

Station and Ground include their static directories in Python wheels. Placement’s existing deployment image copies its entire static directory. The supplied horizontal variants remain available here for wider contexts; compact headers deliberately use the readable wordmark. No external images or fonts are required. PNG logo derivatives have been retired; PNG map previews are actual UI screenshots.

When replacing artwork, update canonical files, applicable app copies, image URLs/intrinsic dimensions and `placement/brand.json` together. Entry READMEs use relative paths. The unrelated legacy `assets/icon.svg` is not an ACORN logo. No licence changes are made.
