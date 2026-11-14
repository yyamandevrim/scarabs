# Overview runtime assets

The Overview has no frontend build step at runtime. `landing-3d.js` is a minified, tree-shaken ES2020 module built from `../landing-model.js`. It includes only the used Three.js renderer/material/geometry APIs, GLTFLoader and the embedded meshopt decoder. There is no runtime CDN, HDR download, shadow map or post-processing chain. Three.js and meshoptimizer MIT licences are bundled beside it. Existing Leaflet assets are independent.

## Reproduce

Node 22+; create a temporary npm directory **outside the repository**:

```sh
npm init -y
npm install three@0.187.0 esbuild@0.28.2 @gltf-transform/core@4.5.1 @gltf-transform/extensions@4.5.1 @gltf-transform/functions@4.5.1 meshoptimizer@1.3.0 three-mesh-bvh@0.9.18 playwright@1.65.1
cp REPO/placement/scripts/convert_hardware.mjs .
cp REPO/placement/scripts/build_overview.mjs .
node convert_hardware.mjs REPO
node build_overview.mjs REPO
```

The converter welds and quantizes the six identified CAD assemblies and bakes 16 deterministic short-range hemisphere rays per vertex using a BVH. AO is stored as vertex colours. Curved normals are smoothed with a 36° crease threshold; no drawn edge mesh is used in the realistic scene. The only added hardware surface detail is an inset lens disc and centre inside each existing camera face. Tube geometry represents the bridle and tether. A shared 64px procedural grain texture varies plastic roughness; a 256×128 procedural overcast studio is filtered once into a small PMREM. Textures, environment target, geometries and materials are disposed with the viewer.

For posters, run the placement app on an unused local port, then copy and run:

```sh
cp REPO/placement/scripts/render_overview_posters.mjs .
node render_overview_posters.mjs BASE_URL CHROMIUM_BINARY REPO
```

This renders the same scene with reduced motion at 1440×900 and 393×852, DPR 2, and writes the two WebP posters. No image generation service is used.

## Verify

```sh
cp REPO/placement/scripts/check_overview.mjs .
# Run from the repository root so the browser assertion script can be found.
node TEMP/check_overview.mjs BASE_URL CHROMIUM_BINARY SCREENSHOT_DIRECTORY
cd REPO/placement
uv run --offline --frozen pytest
```

Use the installed Chromium from the Playwright cache. The suite uses SwiftShader, checks real WebGL output, English despite a stored Turkish preference and URL language parameters, desktop and phone overflow, wheel/touch scrolling, all three view sectors, part selection, assembly separation, WebGL loss/recovery, no-WebGL fallback, packet delivery/evidence interactions, video playback/pause and idle draw counts. It evaluates `scripts/check_language.js` inside each page; that script is a browser expression, not a Node CLI.

`window.acornModel.stats.draws` counts actual renderer calls. The scene has at most five seconds of very slow idle yaw, ends permanently at first interaction, and draws zero frames once settled. Reduced motion skips both load settle and drift. The scene stops entirely off-screen or when the document is hidden. Ordinary wheel events and vertical touch gestures scroll; Ctrl-wheel/pinch and +/- keys zoom. DPR is capped at 2.

The measurement file uses Chromium CDP `Network.loadingFinished` for actual uncompressed development-server transfer (headers included), and `Runtime.getHeapUsage` after a full GC for JS heap. Heap excludes native GPU allocations. The README's gzip size is compression of the committed bundle; the local FastAPI static server itself does not gzip it.

## Media and claims

`../demo/` contains derivatives of the real app captures documented in `pitch/captures/README.md` and `pitch/captures/apple-screens/README.md`. The phone feed is cropped to existing image pixels; no third feed or old camera label is painted into it. Evidence is the captured event `af27f33e9e244d9db8f18eb4276fd1ad`, re-encoded as H.264 at 640px / 15fps. The phone decision movie is the first seven seconds of `en/B2-phone.mp4`, cropped vertically to remove the lower feed-count heading and resized to 392px / 12fps. Both videos are muted, preload none and pause when off-screen/hidden. Capture pixels retain their original app text.

The smoke footage is “Wildfire Near Monserrate”, Peter Angritt (Mrtony77), CC BY-SA 4.0; derivatives resize/crop/re-encode and retain detection overlays. Attribution is on the Overview and in `demo/README.md`. Sources: `station/footage.json`. No runtime directory, database or credential is committed.

`map-terrain-interim.webp` is the single interim map image. It uses actual terrain/visibility pixels from the existing planner, with no forward wedge as the subject. **Re-capture this file from the separately rebuilt 360° map when that work lands.** No map implementation is changed by this asset.

## Measured acceptance run — 2026-11-14

Chromium 159.0.8154.6 / Playwright 1.65.1, 1440×900, SwiftShader, development FastAPI server, fresh context:

| Measure | Result |
| --- | ---: |
| Initial transferred bytes, including HTTP headers | 1,051,404 B |
| Full scroll + phone walkthrough transfer | 1,184,230 B |
| GLB | 111,784 B |
| 3D bundle | 673,461 B raw / 173,004 B gzip |
| JS heap after load + GC | 5,150,504 B |
| Settled / off-screen / untouched after idle period | 0 draws/s |
| Evidence video, fetched on collection | 143,406 B |
| Phone decision video | 57,741 B |

The full-scroll measurement precedes the explicit LoRa evidence collection, whose media is additional on-demand traffic. JS heap excludes GPU/native allocations. Idle movement is capped at 30 fps and expires after five visible seconds even without interaction. No shadows or outline geometry are allocated. The scene exposes 18 draw calls in its assembled view before observation overlays.

Acceptance: **90 placement tests passed** (one upstream Starlette/httpx deprecation warning). Browser suite passed with 31 screenshots, real WebGL, 0 console errors, 0 external requests, 0 failed responses, no 393px overflow, real touch and wheel scrolling, direct pod selection, keyboard controls, context loss/recovery and no-WebGL fallback. Both phone and evidence videos advanced in view and paused off-screen. The 12-second visible status cadence was checked, and generated smoke/status frames decoded with the actual station codec. `check_language.js` passed on Overview desktop/phone and the current map with a stored Turkish preference and URL language parameters.

The owner-requested claim-removal log and screenshot/measurement files are delivered in the external scratch output directory, not committed as runtime assets. The map preview remains interim. Shared changes were isolated in commit `b79b999`; no map implementation edits followed the ownership split.
