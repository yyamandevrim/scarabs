# ACORN artwork

ACORN is **Aerial Canopy Observation and Reporting Node**, by team **Scarabs** for **Junction2026 Helsinki**.

These are crops of Yaman’s supplied artwork, not recreated lettering. Source labels below are generic descriptions of the original uploads; the full uploaded sheets and application chrome are intentionally excluded.

| Asset | Source and extraction | Use |
| --- | --- | --- |
| `acorn-wordmark-white.png` (562 × 195) | `acorn-logo-sheet.png`, 1386 × 2000 transparent PNG. Complete top wordmark cropped at `(80, 475, 642, 670)`; original pixels, spacing and alpha retained. | Dark app headers, 80 px CSS width on desktop and phone. |
| `acorn-stacked-white.png` (255 × 120) | `illustrator-logo-reference.png`, 2000 × 1299 screenshot. Complete white stacked variant cropped at `(740, 480, 995, 600)`. Flat gray pasteboard (RGB 56) removed using its white-to-background coverage as alpha; no tracing, redrawing or retyping. | Landing hero and ranger sign-in, at native width or smaller. |
| `acorn-wordmark-black.png`, `acorn-stacked-black.png` | Black monochrome counterparts using exactly the corresponding white asset’s alpha silhouette. | Light README surfaces; `<picture>` selects white artwork for dark themes. |

The larger sheet’s stacked caption touches/clips the left canvas edge, its horizontal caption clips the right edge, and the bottom wordmark clips the bottom edge. Those variants are not shipped. The complete screenshot-sourced stacked caption has limited raster resolution: never enlarge it beyond 255 px. No horizontal variant or favicon is supplied here.

Keep the intrinsic width/height ratio, surrounding transparent padding and layout clear space. Headers have at least 12 px surrounding layout space; hero/sign-in logos have at least 24 px. Do not stretch, crop, recolor with CSS filters, add effects or substitute a font. The accessible brand name appears once per logo: station uses its named heading, Ground uses image alt text, and placement uses adjacent visually hidden identity text. The English expansion stays unchanged in Turkish.

This directory is canonical. Independently runnable applications carry byte-identical offline copies:

- `station/station/static/brand/`: white wordmark and stacked logo.
- `ground/ground/static/brand/`: white wordmark.
- `placement/static/brand/`: white wordmark and stacked logo.

Station and Ground include their static directories in their Python wheels. Placement’s existing deployment image copies its entire static directory. No external image service or font is required. When replacing artwork, update canonical files, the applicable app copies, intrinsic dimensions and `placement/brand.json` together. Entry READMEs use relative paths to this directory.
