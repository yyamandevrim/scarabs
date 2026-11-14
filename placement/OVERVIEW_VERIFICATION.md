# Overview verification — improvement round 2

Verified 14 November 2026 against the existing server on `http://127.0.0.1:18787`, after integrating main `1ce0131`. Implementation commits: `8d184a9` and `d2ef429`. No map runtime/engine, API, shell, tokens or i18n changes were made during this round. The map agent's Sipoonkorpi/Nuuksio exports were retained; the Overview alt text now names Sipoonkorpi.

## Findings addressed

All three P0s and nine P1s in the Opus review, and the GPT Overview findings, were addressed. The page uses a plain quantized GLB, a full-bleed physical module stage, explicit product explanation, focusable camera selection with automatic facing, 360° graded observation sectors and a complete reset. The report journey is the main radio picture; packet inspection is secondary. Evidence opens in a dialog and the phone's decisions are working local DOM controls around one source case. Native crops remove conflicting legacy annotations without painting over pixels. A still from one second into the same clip makes smoke immediately legible.

Take-apart was removed, as permitted by the design lead: the CAD has no useful internal mechanism to reveal. There is no empty-shell board reveal. Cheap P2 fixes include occluded leaders, larger labels/compass type, visible disabled states, fixed control widths, a single evidence player, a secondary snapshot, responsive map exports and a quiet poster/part-guide fallback.

The detailed per-finding disposition, owner claim log, 79 PNG screenshots, seven named inspection contact sheets and JSON measurements are delivered in the external `overview/round2/` output directory. An independent re-score has not been performed.

## Measurements

Chromium 159.0.8154.6, 1440×900, fresh context, local development server without gzip. CDP transferred bytes include HTTP headers. JS heap is measured after full garbage collection and excludes GPU/native memory.

| Measure | Result |
| --- | ---: |
| Final-layout initial transfer, reduced motion | 1,223,000 B |
| Final-layout JS heap after load + GC | 5,382,256 B |
| Full acceptance initial transfer, normal motion | 1,223,834 B |
| Full acceptance JS heap after load + GC | 5,469,324 B |
| Full interaction journey, including reloads and evidence | 1,494,543 B |
| Quantized GLB, no meshopt/WASM | 355,344 B |
| 3D module bundle | 654,281 B raw / 167,547 B gzip (zlib default level 6) |
| Source event clip, H.264 15fps | 144,586 B |
| Settled and off-screen rendering | 0 draws/s |
| DPR cap | 2 |

The full acceptance run preceded the final fallback-only CSS adjustment; its interaction transfer is retained as measured. A fresh load and both fallback layouts were checked again afterward. SwiftShader's software-rendered load had main-thread long tasks of 704, 817 and 85 ms. These are software-renderer load costs, not hardware-browser frame-rate measurements. Posters remain visible until the first completed render. There is no perpetual animation, shadow map or post-processing chain.

## Browser and interaction evidence

- Chromium 159.0.8154.6, Firefox 159.0 and WebKit 27.2: actual WebGL rendering at 1440×900 and 393×852, ordinary served CSP, no bypass. Poster hidden, renderer calls positive and substantial non-background model pixels verified in every canvas capture.
- Additional stricter `script-src 'self'` load renders without a decoder policy exception.
- All three cameras reachable by focus and turn towards the visitor. Reset clears selection and sectors. Fields of view form the complete observation ring.
- Real touch scrolling inside the stage and ordinary wheel scrolling work. No 393px horizontal overflow. DPR 3 test devices still allocate at most DPR 2 canvases.
- Status begins with zero pending suspicions, schedules on 12-second slots, and smoke reports arrive at both 0° and 240° with the corresponding compass sector and queue entry. Payloads decode with the real station codec: status 40 B, smoke 42 B.
- Evidence dialog focuses in view; all phone steps, Confirm/Reject/Review again, media playback and off-screen pause pass. Local play/pause and keyboard seek pass independently in all three engines. Local controls avoid WebKit's CSP-blocked native media blob icons.
- Context loss/recovery and no-WebGL poster/guide pass. Final fallback caption/list overlap was fixed and re-captured.
- English passes with a stored Turkish preference and URL parameter. The current `/map` header was checked and captured without editing its code.
- Zero console errors, external requests and failed HTTP responses in the complete acceptance run and supplemental media tests.

Firefox on macOS 27 uses a temporary `CFFIXED_USER_HOME` application-data directory to avoid runner TCC restrictions. This does not bypass CSP or alter HOME. Browser packages and build tools live outside the repository. Reproduction commands are in `static/vendor/README.md`.

## Automated checks

`cd placement && uv run --offline --frozen pytest`: **85 passed**, one upstream Starlette/httpx deprecation warning. Both Playwright scripts passed. `scripts/check_language.js` passed as a browser expression. JavaScript syntax and `git diff --check` passed.

Camera choices parameterize one local walkthrough and have distinct case IDs; one archived record supplies the media and real opening score/time. They are not separate physical detections. No live radio deployment, measured optical calibration or physical station integration was newly tested. These engineering details remain in the owner report rather than being added as public caveats.
