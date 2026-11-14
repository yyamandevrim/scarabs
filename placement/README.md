# ACORN launch point map

**ACORN — Aerial Canopy Observation and Reporting Node.** An English-only investor website and offline geometric visibility simulator, built by team Scarabs for the Green European Renaissance challenge at Junction 2026, Helsinki. All implementation and generated data live in `placement/`; this app does not depend on `station/`.

The module sits under a tethered balloon above forest. Three cameras on the faces of its triangular housing operate simultaneously, with yaw offsets **0° / 120° / 240°**. By product decision, the horizontal model assigns each camera a **120° azimuth sector**: a full circle with no gaps or overlap. This is a product model, not a measured optical calibration. The previous forward fan, two-input restriction, camera pairs, special reference mode and heading sensitivity have been removed.

Coverage is simulated geometric visibility, not optical smoke-detection range or probability, fire prediction or smoke transport. Tilt, vertical field of view, target heights, terrain/canopy occlusion and the LOS algorithm remain in use. Vertical angles are evaluated in the radial plane so heading rotates sector ownership without changing the union. The former rectilinear horizontal/vertical coupling is superseded by this sector model.

## Public website and artifact handoff

`/` is the Overview; `/map` is the launch map. Identity comes from `brand.json` and local vector artwork. Both pages force English regardless of stored language preference or URL parameters. `i18n.js` no longer loads a translation dictionary; the map control is removed, and the server strips the legacy Overview language button without editing its template.

Compare owns the two site totals, verdict, selected site's balloon height and per-camera visible forest. Breakdown owns area accounting and scenario tables. Data retains concise provenance, the actual assumed-canopy fraction and required CC BY 4.0 attribution. Public limitations copy removed for owner review is recorded verbatim in the external scratchpad `overview/claims-for-owner-map.md`; engineering limitations remain below and in API uncertainty metadata.

See [`DEPLOYMENT.md`](DEPLOYMENT.md) for deployment and [`../tools/README.md`](../tools/README.md) for artifact handling. Neither deployment nor upload is part of this update. Current height/scenario/camera results are in [`blind-audit.json`](blind-audit.json), HTTP benchmarks in [`benchmark-results.json`](benchmark-results.json), and checks in [`VERIFICATION.md`](VERIFICATION.md).

## Cold start

Prerequisites: Python 3.11–3.13, `uv`, and internet access for the initial dependency and raster downloads. Run these commands from this repository. Python 3.12 was used on this Mac; the project supports Python 3.11–3.13. `uv.lock` pins the environment.

```sh
cd placement
uv sync --frozen --python 3.12
uv run python scripts/prepare_data.py
uv run uvicorn forest_placement.api:app --host 127.0.0.1 --port 8787
```

Open **http://127.0.0.1:8787/**. No credentials or API key are needed for the selected public data mirrors.

After environment setup and data preparation, internet access is unnecessary:

```sh
uv run --offline --frozen uvicorn forest_placement.api:app --host 127.0.0.1 --port 8787
```

The preparation script uses a verified certifi CA bundle for urllib and GDAL, including the Syke certificate chain; TLS verification remains enabled. A byte-identical rebuild retains the pinned release timestamps in metadata.json while preparation-run.json records the actual run times.

Preparation downloads approximately 240 MB of regional raw rasters and produces approximately 32 MB in `data/prepared/`. The entire current data/cache directory is approximately 276 MB. To move the demo, copy the source code and `data/prepared/`; install Python dependencies before disconnecting. `data/raw/` is only needed for rebuilding. `data/results/` is recreated automatically. All large data, virtual environments and generated result images are ignored by `placement/.gitignore`.

Local mode leaves rate limiting off. `PLACEMENT_PRODUCTION=1` enables the public 90/client/minute and 360/global/minute limits; `PLACEMENT_RATE_LIMIT=1` or `0` explicitly overrides that choice. The single compute slot applies in both modes.

In ordinary laptop mode, the first visibility request may compile Numba code. Production/Modal mode warms the exact strided-array signature before accepting requests. Later requests use bounded disk cache results keyed by inputs, dataset checksums and algorithm version. Restart the server after preparing a different dataset: raster arrays are held in memory. Use one uvicorn worker for the laptop demo; API calculations are serialized to avoid competing CPU-heavy work.

## Data preparation and provenance

`scripts/prepare_data.py` downloads, clips, resamples/reprojects numeric data into **EPSG:3067 (ETRS-TM35FIN)**, records source URLs, access dates and prepared-file SHA-256 digests in `data/prepared/metadata.json`, and renders a local raster background in Web Mercator for Leaflet. All geometric analysis remains in EPSG:3067. Data obtained on **2026-11-13**:

| Dataset | Actual data used | Source and licence |
| --- | --- | --- |
| Elevation | **Real NLS Finland 10 m ground DEM**, public Paituli **2019 archive**, 28 GeoTIFF sheets. This is the intended national DEM, not Copernicus or synthetic terrain. | [Files and index VRT](https://www.nic.funet.fi/index/geodata/mml/dem10m/), [NLS product](https://www.maanmittauslaitos.fi/en/maps-and-spatial-data/datasets-and-interfaces/product-descriptions/elevation-model-10-m), [CC BY 4.0 terms](https://www.maanmittauslaitos.fi/en/opendata-licence-cc40). Attribution: contains National Land Survey of Finland Elevation model 10 m, 2019 snapshot, accessed 2026-11-13 through CSC/Paituli. |
| Land cover | **Real Syke CORINE Land Cover 2024 national 20 m raster**, published 2026-09-29, obtained through numeric WCS GetCoverage. Latest published release checked on preparation date. | [Syke catalogue](https://www.syke.fi/en/environmental-data/downloadable-spatial-datasets), [WCS](https://paikkatiedot.ymparisto.fi/geoserver/inspire_lc/wcs?service=WCS&request=GetCapabilities&version=1.1.0), [full 20 m download](https://wwwd3.ymparisto.fi/d3/Static_rs/spesific/Clc2024_FI20m.zip), [CC BY 4.0](https://www.syke.fi/en/environmental-data/use-license-and-responsibilities). Attribution: Syke, CORINE Land Cover 2024; includes contributing Finnish national data sources. |
| Tree height | **Real Luke MS-NFI 2023 numeric stand mean height**, native 16 m, decimetres converted to metres. Published 2025-10-22. Regional blocks downloaded using HTTP range reads. This is an estimated stand mean, not a LiDAR maximum canopy top. | [Numeric GeoTIFF](https://www.nic.funet.fi/index/geodata/luke/vmi/2023/keskipituus_vmi1x_1923.tif), [Luke product documentation](https://kartta.luke.fi/index-en.html), [2023 README](https://kartta.luke.fi/mvmi-inspire-metsavara-aineistot/README-2023.txt). **CC BY 4.0**, Natural Resources Institute Finland (Luke). |
| Canopy cover | **Real Luke MS-NFI 2023 numeric canopy-cover percentage**, native 16 m. Values 32766/32767 are missing/non-forestry codes, not valid heights or percentages. | [Numeric GeoTIFF](https://www.nic.funet.fi/index/geodata/luke/vmi/2023/latvuspeitto_vmi1x_1923.tif), [Luke Atom feed](https://kartta.luke.fi/inspireatom/MVMI-2023.xml). **CC BY 4.0**, Luke. |
| Buildings | **Not acquired.** CORINE built-up areas are on the background map but do not provide building heights. | Building obstruction is an explicit uncertainty. An optional numeric GeoTIFF loader is provided below. |
| Background map | Derived locally from the above real land-cover classes and elevation shading. Town/forest names are manually positioned orientation labels. No online basemap, road network or administrative boundary service is used. | Same underlying CC BY 4.0 attribution. |
| Browser map library | Leaflet **1.9.4**, JS/CSS/images/source map vendored in `static/vendor/`. | [Leaflet](https://leafletjs.com/), BSD-2-Clause, full notice in `static/vendor/LEAFLET-LICENSE`. |

The public CSC/Paituli mirror made the intended NLS data accessible without an NLS API key. **No Copernicus elevation fallback was necessary.** A newer local NLS DEM can replace the archived snapshot:

```sh
uv run python scripts/prepare_data.py --dem /absolute/path/to/nls_10m.tif
```

The supplied DEM must be a numeric georeferenced ground-elevation raster in metres with a valid CRS and nodata declaration. The loader reprojects it to EPSG:3067. Preserve its source and licence information when substituting data.

If Luke cannot be reached on another machine, the script fails plainly; it never silently invents a real-data layer. An explicit alternate scenario is available:

```sh
uv run python scripts/prepare_data.py --assumed-canopy
```

This assigns a **20 m opaque canopy to all CORINE forest**, labels it as an assumption in metadata/API/UI, and retains the bare-ground comparison. With the actual downloaded Luke data, **5.47% of CORINE forest cells** lack a valid height or cover value. Only those missing forest cells receive the explicitly labelled 20 m, 100% cover assumption. The other cells use numeric Luke estimates. This percentage describes the entire prepared region, not a candidate-specific uncertainty interval.

Optional measured building heights above ground, in metres:

```sh
uv run python scripts/prepare_data.py --building-heights /absolute/path/to/building_heights.tif
```

This takes the maximum of canopy and building height at each cell. No building dataset is bundled, and this optional import has not been exercised against a real building-height dataset. Supply/document the data licence and original URL when using it. Do not substitute a WMS image for numeric terrain, canopy or buildings.

## Model and outputs

The prepared **75.12 km × 75.12 km** rectangle is `(345000, 6650000, 420120, 6725120)` in EPSG:3067. Metrics use the candidate's range disk intersected with this rectangle, not municipal borders. `range_clipped` and missing-elevation flags remain in the API.

1. CORINE forest is national codes **3111–3133**. Transitional woodland/clearcut `324*` is excluded; water is `51**/52**`. Forest and water fractions retain native 20 m area weights. Fast comparison uses **120 m**, detailed analysis **40 m**. Terrain and obstruction surfaces use conservative maximum-height aggregation.
2. Defaults: **600 m AGL**, **10° down tilt**, **50° VFOV**, **12 km maximum range**, smoke targets **50 m above the local obstruction surface**. All cameras share vertical geometry. Bearings are clockwise from EPSG:3067 grid north. Horizontal sectors are half-open at seams: every ray belongs to exactly one of Camera 1/2/3. Public validation rejects inactive cameras, different yaw/HFOV and old reference inputs.
3. The vertical test preserves the radial-plane tilt and VFOV angle limits. Curvature subtracts `distance²/(2 × radius)` from targets, terrain and obstruction heights; default radius is 6,371,000 m. Rays are sampled at intervals no greater than half an analysis cell by the unchanged Numba LOS function. Observer and target cells are excluded as intermediate blockers; unknown intermediate cells invalidate the ray. The target's own opaque canopy blocks ground targets.
4. Four scenarios remain: bare ground, bare elevated smoke, canopy ground, canopy elevated smoke. The bare smoke comparison uses the same physical canopy/surface+smoke target height. Positive measured canopy cover is opaque, not a visibility probability. Water adds no forest hectares; rays can cross water.
5. The union counts forest fractions once. Three nonoverlapping sector masks sum to the union; `overlap_forest_ha` remains a compatibility accounting field and is zero in this model. `camera_breakdown` returns all four scenario metrics for each camera. Heading remains an API seam orientation; it is absent from public controls because it does not change totals.
6. `blind_forest_ha = outside_fov_forest_ha + occluded_forest_ha`. Outside FOV now means vertical exclusion (including the inner blind region), not a missing horizontal camera. Missing target elevations and unverified intermediate rays remain blind and are disclosed in API uncertainty metadata.
7. Sector guides form an annulus, including its inner boundary. The guide radii solve the selected scenario's vertical limits on a level target plane through the launch cell, with curvature. For smoke this uses local canopy+smoke height; ground uses local terrain. The actual raster uses each cell's terrain/canopy target height. Positive lower downward angle can also make the outer vertical limit smaller than maximum range. Guides are not a claim that all cells inside are visible.
8. Priority polygons are transformed to EPSG:3067; cell centres determine membership and only visible forest fractions contribute. Ranking uses canopy-smoke visible priority forest first, then total visible forest. All compared candidates must share an equivalent priority polygon (or all omit it).
9. Cache algorithm **`opaque-ray-half-cell-v8-360-sectors-en`** supersedes v7. Keys still include all candidate inputs and dataset checksums. The worktree reads prepared rasters through a symlink and writes only its own `data/results` cache.

## API

- `GET /`, `GET /map`: English-only Overview and map.
- `GET /api/brand`, `GET /api/config`: identity, fixed three-camera presets and data metadata.
- `POST /api/analyze`: four scenario unions, per-camera breakdown, annular sector guides, PNG overlays and candid uncertainty metadata. No pair/reference/sensitivity outputs.
- `POST /api/compare`: 2–6 candidates with shared priority geometry, priority-first ranking. Height, position, range and vertical geometry may differ. Heading changes camera assignment only.
- `GET /maps/{filename}`, `/results/{filename}`, `/static/*`: allowlisted local maps/results and UI assets. Numeric datasets and cached JSON are not exposed as files.
- `GET /openapi.json`: local schema; Swagger/ReDoc CDN pages are disabled.

```sh
curl -s http://127.0.0.1:8787/api/analyze \
  -H 'Content-Type: application/json' \
  -d '{"name":"Haukilahti","lon":24.773,"lat":60.159,"height":600,"resolution":"detailed"}'
```

Explicit `cameras` must have yaw 0/120/240, HFOV 120 and `active:true`, with identical tilt/VFOV across all three. Invalid/self-crossing priorities, out-of-region locations and mostly-water launch cells return 422.

## Demo sequence

1. Open `/map`: **Haukilahti** `(60.159, 24.773)` and **Nuuksio** `(60.293, 24.557)`, both 600 m. Three cameras watch the full circle.
2. The quick default canopy-smoke view shows approximately **8,070** and **26,850 simulated ha**, with **43%** and **8%** water share. Select either site to show its own raster and per-camera breakdown.
3. Change the selected site's height, then use Detailed · 40 m if needed. Shared tilt/VFOV, position, range and smoke elevation are in Position and geometry. Ground/bare scenarios remain available.
4. Draw a priority forest polygon to compare visible priority forest; Clear area restores the total-forest comparison. Clicking the map moves the selected site.
5. Access, tether/ground suitability and flight permission require field assessment. These are not computed launch authorizations.

## Verification on this Mac

Use Python 3.12 for the cached offline dependencies (`uv sync --offline --frozen --python 3.12`). The DOM request tests also require happy-dom, normally supplied by `npm ci` in `station/`; browser verification used Playwright and happy-dom installed outside the repo in a temporary directory.

```sh
uv run --offline --frozen pytest
uv run --offline --frozen python scripts/blind_audit.py
uv run --offline --frozen python scripts/benchmark.py --url http://127.0.0.1:8787 --fresh
uv run --offline --frozen python scripts/production_benchmark.py
uv run --offline --frozen python scripts/write_report.py
```

Checks cover full-circle tiling, exact seam ownership, unchanged totals under heading rotation, inner/outer vertical limits, unique forest accounting, priority ranking, low-height occlusion, real data at both resolutions, old-cache rejection, offline operation and UI request sequencing. `scripts/check_language.js` asserts English-only rendering and no obsolete camera copy, overflow or external resources. Current browser evidence is local, not a deployment check; the historical public-browser JSON is marked superseded.

## Known limits / not verified

- No real building-height dataset acquired; building obstruction is omitted. The optional import is implemented but not validated against real buildings.
- Road access, shadow, ground/tether suitability, airspace permission and site constraints are explicitly **field checks**, not computed.
- No optical detection, smoke dynamics, camera calibration, refraction, visibility/weather or actual field validation. These are outside the geometric prototype.
- The 2019 DEM is real but older than current NLS updates. A current local NLS file can be loaded; that alternative was not exercised.
- Luke missing forest data (5.47%) uses a clearly disclosed 20 m opaque-canopy assumption. Opaque mean-height cells may overstate or understate real canopy blocking. No uncertainty confidence interval is claimed.
- The fully assumed `--assumed-canopy` option and real building-height import were not used in the delivered benchmark. No Copernicus fallback was exercised or needed.
- No municipal administrative clipping or offline road labels. Counts are regional rectangle/range-disk counts. Priority boundaries and range circles use analysis-cell centres.
- No physical internet-disconnection test; runtime socket blocking and same-origin browser inspection were performed instead.
- Browser state is in memory; refresh resets candidates and drawn priority polygons. Server results are capped at 256 analyses; Modal results are ephemeral and disappear on container recycle.
- Python 3.11/3.13 and other operating systems were not run; verified runtime is this Mac on Python 3.12.

Board status: the station has run on a real UNO Q using recorded clips, the MCU bridge, KY-026 and on-board status LED. This does not validate placement visibility or field detection range. Board inference performance for the demo, USB cameras, AP mode, external RGB LED and real LoRa radio remain unverified; see [BOARD_NOTES.md](../firmware/BOARD_NOTES.md) for ongoing bring-up work.
