# Dynamic public site on Modal

The same `forest_placement.api:app` serves the landing page at `/`, the live map at `/map`, and the calculation API. No static export or station-feed proxy is involved. Local offline use remains available with the original uvicorn command.

## Owner's commands

From the repository root, with prepared data already present (or restored using `../tools/restore_artifacts.py`):

```sh
cd placement
uv sync --frozen --group deploy --python 3.12
uv run --group deploy modal token new
uv run --group deploy modal run modal_app.py::load_data
uv run --group deploy modal deploy modal_app.py
```

`load_data` is a one-time authenticated CLI action that uploads exactly the seven prepared raster/map files into `/prepared/` on the `forest-placement-data` Modal Volume. It is **not** a public HTTP endpoint. Repeat it only when intentionally replacing data, then redeploy/restart so in-memory grids are reloaded. Complete the initial upload before sharing the endpoint. Modal prints the deployed public URL; no domain or credentials are embedded in the repository.

If data is absent and rebuilding is preferred:

```sh
uv run python scripts/prepare_data.py
```

Alternatively restore the pinned artifacts from IronShard as documented in [tools/README.md](../tools/README.md). No Modal credentials are needed for preparation or a local demo.

## Storage and startup choice

Prepared data is about 31 MiB, including the **three derived offline map PNGs** (the existing map uses raster image overlays, not an XYZ tile pyramid). A data Volume keeps those independently restorable and avoids rebuilding an image when data is replaced. The function mounts it **read-only**. The source, UI, locked Python environment and compiled LOS kernel are baked into the image. Raw downloads and station models/media are never copied into the website image.

Numba compiles the exact float32 / bool, **strided-array** signature during image build, using `NUMBA_CPU_NAME=generic`. Code paths and the cache directory stay fixed between build and serve. Startup loads that cached signature and both regional grids. Numeric parameters are normalized before calling the kernel so JSON integers/floats do not trigger extra signatures. A local check confirms that a first coarse and detailed request adds no JIT signatures after warm-up. Cache incompatibility on another runtime can still cause compilation; startup deliberately warms before accepting requests.

`min_containers=0` scales to zero, with a 120-second idle window. `max_containers=1`, one process and one analysis semaphore provide a deployment-wide bound of **one analysis at a time**. Six-candidate comparisons hold that slot across all six calculations. `modal.concurrent(max_inputs=16)` keeps page/assets and quick rejections responsive while the numeric kernel releases the GIL. Raising the container/process limit would require a shared rate/concurrency budget first.

Generated JSON/overlay results live in ephemeral `/tmp`, capped at **256 analyses** (four PNGs plus a JSON each); oldest entries are evicted. They are regenerated after scale-to-zero. Only validated result PNG names are readable over HTTP, never the JSON/cache directory or dataset arrays. A browser returning to an evicted result should rerun it. No visitor chooses a filesystem path or uploads data.

## Public compute protections

- **12 analysis/compare requests per client per 60 seconds**, plus **60 requests globally per 60 seconds**. Invalid requests and cache hits consume the same budget. A comparison contains at most six candidates. HTTP 429 includes `Retry-After: 60`.
- Client identity uses the ASGI peer provided by Modal (`request.client.host`); untrusted `X-Forwarded-For` is ignored. Modal documents this client-IP interface. `PLACEMENT_PROXY_HOPS` is an opt-in for a separately managed trusted reverse proxy and is **unset on Modal**. Do not enable it on a directly accessible local server.
- One nonblocking compute slot; contention returns HTTP 503 with `Retry-After: 2`, without an unbounded application queue.
- 32 KiB request-body limit, including streamed bodies; 1–15 km range; only **120 m or 40 m** grids; **100 polygon vertices / 2,000 km²** maximum positive polygon area; at most six comparison candidates; exactly three camera definitions, with at most two active unless explicitly in reference mode.
- Finite numeric values and angle/height/coordinate limits; invalid/self-intersecting polygons, unknown fields, out-of-region/water launch points are rejected. Heights 10–1,000 m permit low-height diagnostic checks; the intended balloon scenario is 500–700 m.
- Bounded in-memory client tracking; same-origin CSP and no CORS access. Maps and result routes use explicit filename allowlists. No public preparation, upload, configuration-write, arbitrary-file or station-feed endpoint exists.

Budgets are in-process and reset when the container restarts. They bound this hackathon service, not a distributed DDoS defence. Cold starts and static requests still incur platform costs. The single-container cap is intentional; account billing/spend controls remain the owner's Modal settings.

## Verification without an account

```sh
uv run --group deploy python -c 'import modal_app; print("Modal app imported")'
uv run --group deploy modal deploy --help
uv run --group deploy modal run --help
uv run pytest -q tests ../tools/tests
uv run python scripts/production_benchmark.py
PLACEMENT_PRODUCTION=1 NUMBA_CPU_NAME=generic \
  NUMBA_CACHE_DIR=/tmp/placement-numba \
  PLACEMENT_CACHE=/tmp/placement-results \
  uv run uvicorn forest_placement.api:app --host 127.0.0.1 --port 8787 --no-proxy-headers
```

Open `http://127.0.0.1:8787/`, then the map. Production mode requires prepared files at startup. For laptop offline use, leave `PLACEMENT_PRODUCTION` unset and use `uv run --offline --frozen uvicorn forest_placement.api:app --host 127.0.0.1 --port 8787`.

Local measurements on this Mac: **0.6159 s** fresh-process readiness with an empty generic JIT cache; **0.4124 s** with a populated cache and preloaded rasters. Uncached HTTP: **59.8–81.4 ms coarse**, **398.1–450.7 ms detailed**. Repeated identical requests: **1.4–1.9 ms**. These include overlays, pair and heading comparisons. Full samples: [production-timings.json](production-timings.json). They exclude dependency/image installation and data upload, and do not predict Modal image-pull, Volume, network or Linux CPU timings.

SDK **1.6.4** imports the app and validates decorators locally; CLI help commands work without authentication. **Not run:** a Linux image build, authenticated Volume creation/upload, deployment, scale-to-zero/resume, public-IP forwarding verification, cloud latency or live IronShard transfers. No account was accessed or credentials sought.

## Identity and language

Edit only [brand.json](brand.json) to change the name (ACORN), expansion, the two taglines, team/event credit or the logo path; the logo is still a placeholder. The logo asset can live in `static/`; both pages, document title and favicon read the config. Scarabs appears only as the team credit.

English is the default. The Turkish toggle covers both pages and dynamic map labels/results, persists in localStorage, and preserves map/candidate state. The app uses only same-origin local CSS, scripts, fonts and map assets. Without JavaScript the landing's English content remains readable; the live map requires JavaScript and the backend.

References checked 2026-11-13: [Modal ASGI and client IP](https://modal.com/docs/guide/webhooks), [Volumes](https://modal.com/docs/guide/volumes), [input concurrency](https://modal.com/docs/guide/concurrent-inputs), [image builds](https://modal.com/docs/guide/images).
