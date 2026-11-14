# Overview runtime assets

The Overview has no frontend build step at runtime. `landing-3d.js` is a tree-shaken ES2020 module built from `../landing-model.js`, including the used Three.js APIs and GLTFLoader. The quantized GLB uses no meshopt decoder or WebAssembly. All runtime assets are local. Three.js and the historical offline meshoptimizer MIT licences are retained beside the bundle; meshoptimizer is no longer a runtime dependency. Leaflet is independent.

## Reproduce

With Node 22+, create an npm directory outside the repository:

```sh
npm init -y
npm install three@0.187.0 esbuild@0.28.2 @gltf-transform/core@4.5.1 @gltf-transform/extensions@4.5.1 @gltf-transform/functions@4.5.1 three-mesh-bvh@0.9.18 playwright@1.65.1
cp REPO/placement/scripts/convert_hardware.mjs .
cp REPO/placement/scripts/build_overview.mjs .
node convert_hardware.mjs REPO
node build_overview.mjs REPO
```

The converter merges the six identified CAD assemblies, welds vertices, uses 36° creased normals and quantizes positions/normals. Sixteen deterministic short-range hemisphere rays per vertex bake AO using a BVH. Existing arm surfaces have a secondary plastic material. See `../../../assets/hardware/README.md` for identification and source geometry.

The viewer uses satin plastic with procedural roughness, darker mounts, concentric optical rings and convex glass within the existing pod faces. A small RoomEnvironment is filtered once into a PMREM for moving softbox reflections. Key/rim lighting and baked AO give depth without shadow maps or post-processing. Procedural bump maps texture the tube ropes. The scene disposes its geometry, materials, textures and environment target.

To render the posters from the same scene:

```sh
cp REPO/placement/scripts/render_overview_posters.mjs .
node render_overview_posters.mjs BASE_URL CHROMIUM_BINARY REPO
```

This captures the full-bleed stage at 1440×900 and 393×852, DPR 2, with overlays hidden. It writes two WebP posters plus a module thumbnail. No image generation service is used.

## Verify

```sh
cp REPO/placement/scripts/check_overview.mjs .
cp REPO/placement/scripts/check_overview_media.mjs .
# Run from the repository root.
node TEMP/check_overview.mjs BASE_URL CHROMIUM_BINARY SCREENSHOT_DIRECTORY
node TEMP/check_overview_media.mjs BASE_URL CHROMIUM_BINARY SCREENSHOT_DIRECTORY
cd placement
uv run --offline --frozen pytest
```

The script uses cached Chromium, Firefox and WebKit with the ordinary served CSP, plus a stricter self-only CSP check. It tests desktop/phone WebGL, all camera selections, reset, 360° sectors, vertical touch/wheel scrolling, radio/evidence/phone interactions, playback/pause, context recovery and no-WebGL fallback. `check_language.js` is a browser expression evaluated in these pages, including a stored Turkish preference and URL language parameter.

On macOS 27, Firefox needs an isolated `CFFIXED_USER_HOME` application-data directory to avoid the runner's TCC-protected app-data location. The test creates/removes that temporary directory; it does not change HOME, page policy or Firefox rendering preferences.

`acornModel.stats.draws` counts renderer calls. There is no idle animation: a short load settle and direct input responses end at zero draws per second. Reduced motion skips the settle. The viewer suspends off-screen/hidden, caps DPR at 2 and preserves vertical page scrolling. Camera selection rotates to the chosen lens; reset clears selection and fields of view. Assembly separation was removed because this CAD has no worthwhile internal mechanism to reveal.

CDP transfer measurements include HTTP headers and uncompressed local development-server assets. Heap is `Runtime.getHeapUsage` after full GC and excludes GPU/native allocations. The gzip figure is compression of the committed bundle, not an assumption about server compression. Current measured results are in [OVERVIEW_VERIFICATION.md](../../OVERVIEW_VERIFICATION.md); the full screenshot manifest is in the delivered round-two report.

## Media and event consistency

See `../demo/README.md` for the native 640×280 crop and H.264 conversion of one archived station event. The real opening time and packet-quantized score drive every report and review. Camera choice parameterizes the local demonstration, uses distinct case IDs and updates the phone and centre together; it does not modify the archived event. Confirm/reject are working local DOM controls, rather than a movie of buttons. Media playback stops off-screen/hidden and loads on interaction.

The smoke footage is “Wildfire Near Monserrate”, Peter Angritt (Mrtony77), CC BY-SA 4.0. Derivatives crop and re-encode; attribution appears on the Overview and in the media README. Media derivatives are reproducible with `scripts/prepare_overview_media.py` (ffmpeg and Pillow). The still comes from one second into the same clip. Local play/seek controls avoid WebKit native-control blob icons under the served CSP. No runtime directory, database or credential is committed.

`map-360-desktop.webp` and `map-360-phone.webp` are the map agent's current real Sipoonkorpi/Nuuksio captures, at 1280×800 and 393×852. The Overview uses their existing filenames/dimensions and describes simulated visible forest. No map runtime behavior was changed in this round.
