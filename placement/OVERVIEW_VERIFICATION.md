# Overview verification — improvement round 3

Verified 14–15 November 2026 against the existing server on `http://127.0.0.1:18787`. Implementation is committed in `6330898`. Main advanced to the map agent's `be92393` during this round; the Overview desktop teaser was captured again after that integration. The map runtime/engine, API, shell, tokens and i18n were not edited. The only shared-test adjustment is the Overview branch of the identity test: one shell wordmark plus the station panel's real wordmark.

## Review disposition

All remaining Overview P1s were addressed. Existing CAD surfaces now have finished rear caps, opaque charcoal mounts, stronger baked contact AO, matching shallow optical stacks, curved lens normals and a printed supplied wordmark. Selected parts receive a thin outline rather than a material wash. Callouts use hairlines/dots and ray-tested visibility; all five phone parts remain visible. The module stays level, with rope endpoints at the actual openings. Nine viewpoints at both widths cover every camera front/rear, three-quarter, top and underside.

Every camera choice retains the single real event UUID, timestamp, score and associated media. This follows the owner's choice to keep three bearing options rather than the review's proposed restriction to Camera 3. False station-camera attribution was replaced with neutral visible-pixel descriptions and “Evidence clip”. A smoke press pre-empts status immediately; the travelling packet, compass and receipt form one arrival beat. The compass caption is outside its labels, and its ray was tested against every text bounding box for all three bearings at both widths.

Cheap P2s are addressed: fixed phone geometry, moving video → saved frame → decision, distinct outcomes, station section names/wordmark, visible touch hint, five equal part targets, pointer/keyboard focus handling, bounded zoom, flat 120° observation sectors, no forest/caption collision, aligned closing, proper title and native-sized map/media. The desktop preview is 1312×820 without letterboxing, phone preview is full-width, and evidence video never exceeds 640px. No public disclaimer was added.

The startup P2 is **partly fixed**: studio filtering is offline (14,517 B, 32px cube faces and roughness mips), with asynchronous shader warm-up. The suggested 200ms maximum main-thread task is **not met** under SwiftShader: the acceptance run recorded [790, 857] ms. Separate profiling measured roughly 0.67s in native context creation and substantial shader diagnostics. Settled/off-screen rendering is zero. No claim is made that physical-device startup has the same cost.

## Measurements

Chromium 159.0.8154.6 at 1440×900, normal motion, fresh context, development server without gzip. CDP encoded transfer includes HTTP headers; heap is after full GC and excludes GPU/native allocations.

| Measure | Result |
| --- | ---: |
| Initial transfer | 1,238,314 B |
| Complete interaction journey | 1,485,837 B |
| JS heap after load + GC | 5,705,020 B |
| GLB (quantized, no WASM/meshopt) | 346,008 B |
| 3D JS | 656,156 B raw / 168,539 B gzip (level 6) |
| Offline studio | 14,517 B |
| Click → next animation frame | 13.5–15.6 ms |
| Complete arrival beat | 1951.6–1953.9 ms |
| Settled / off-screen draws | 0/s |
| Initial / entire-journey CLS | 0.01440 / 0.03275 |

The initial transfer and heap were sampled again after the final hover-only refinement; the full journey and long-task trace come from the preceding complete acceptance run. Hover inspection restores the committed selection without turning the model. Click timing uses the input capture handler and the next frame after the transmitting class is applied; it is not a physical RF latency measurement. Timing checks include consecutive camera choices and a status report pre-empted by smoke. Reduced motion has immediate equivalents. DPR is capped at two; no shadow map, post chain or perpetual animation is used.

## Verification

- **85 pytest tests passed**, one upstream Starlette/httpx deprecation warning. Real station codec decodes the 40/42-byte payloads, one UUID and 0°/120°/240° bearings. Gzip/GLB budgets pass.
- Chromium 159.0.8154.6, Firefox 159.0 and WebKit 27.2 render real canvas output at 1440×900 and 393×852 under the served CSP. A stricter self-only CSP also renders. Posters are hidden, renderer calls are positive and actual model pixels were checked in all six canvases.
- The screenshot harness now explicitly waits for a new model draw after toggling FOV: an early WebKit capture had raced its next frame. The targeted six-context render pass was repeated and all actual sector captures inspected.
- All camera/focus/reset/zoom controls, vertical touch and wheel escape, context recovery and no-WebGL fallback pass. No horizontal overflow, console errors, failed HTTP responses or external requests were observed in the final runs.
- First phone view is moving video without event metadata, second is a paused saved frame, third reuses the clip with decisions. Play/pause/seek pass in every engine. Phone position and compass position stay fixed across their states.
- All three report bearings, repeated immediate sends, inspector, evidence modal and local Confirm/Reject/Review again pass. Compass rays intersect no text boxes. Six final evidence-dialog captures verify native media size.
- English passes despite stored Turkish preference and URL parameters. The current map header was captured without editing map code.

The external `overview/round3/` delivery contains 106 final PNGs, nine inspection contact sheets, the per-finding report and raw measurements. All were inspected individually or on named sheets; important optics, zoom, phone and radio states were opened at full size. The owner claim log was updated. No independent re-score was run. Build and verification commands are in `static/vendor/README.md`; the prior round is archived in commit `7e40420`.
