# Deck capture manifest

Source: pitch/deck/acorn-pitch.html opened offline in headless Chromium, no server/port. Commit 0027611; working tree with uncommitted changes. Deck source unchanged. CSS viewport 1440×810, DPR 2; PNG downscales use Lanczos. All nine slides have static embedded images and instant display switching; no slide animation or embedded video exists. MP4s reproduce those exact static holds and cuts at CFR 30; repeated frames are intentional static content, not undersampled motion. Each transition holds each slide for 3 s. Calm flip: 2 s/slide plus 1 s endpoint handles (20 s). Fast flip: 0.6 s/slide plus 1 s endpoint handles (7.4 s), explicitly shorter than generic 6 s minimum per requested montage pace before handles.

H.264 CRF 16, yuv420p, no audio, faststart. All MP4s ffprobed and fully decoded without error. Start/middle/end extracted for visual review in qa/video-start-middle-end.png. Fonts/images passed browser checks; no embedded videos to play. Original rough-cut films only read; hashes preserved in qa/references.json. References include existing editorial content/gaps and are not newly captured product evidence.

| File | Duration | Resolution | FPS | Content / conditions |
|---|---:|---|---:|---|
| video/deck-01-transition-01-to-02-1080.mp4 | 6.00s | 1920×1080 | 30 | Instant slide cut |
| video/deck-01-transition-01-to-02.mp4 | 6.00s | 2880×1620 | 30 | Instant slide cut |
| video/deck-02-transition-02-to-03-1080.mp4 | 6.00s | 1920×1080 | 30 | Instant slide cut |
| video/deck-02-transition-02-to-03.mp4 | 6.00s | 2880×1620 | 30 | Instant slide cut |
| video/deck-03-transition-03-to-04-1080.mp4 | 6.00s | 1920×1080 | 30 | Instant slide cut |
| video/deck-03-transition-03-to-04.mp4 | 6.00s | 2880×1620 | 30 | Instant slide cut |
| video/deck-04-transition-04-to-05-1080.mp4 | 6.00s | 1920×1080 | 30 | Instant slide cut |
| video/deck-04-transition-04-to-05.mp4 | 6.00s | 2880×1620 | 30 | Instant slide cut |
| video/deck-05-transition-05-to-06-1080.mp4 | 6.00s | 1920×1080 | 30 | Instant slide cut |
| video/deck-05-transition-05-to-06.mp4 | 6.00s | 2880×1620 | 30 | Instant slide cut |
| video/deck-06-transition-06-to-07-1080.mp4 | 6.00s | 1920×1080 | 30 | Instant slide cut |
| video/deck-06-transition-06-to-07.mp4 | 6.00s | 2880×1620 | 30 | Instant slide cut |
| video/deck-07-transition-07-to-08-1080.mp4 | 6.00s | 1920×1080 | 30 | Instant slide cut |
| video/deck-07-transition-07-to-08.mp4 | 6.00s | 2880×1620 | 30 | Instant slide cut |
| video/deck-08-transition-08-to-09-1080.mp4 | 6.00s | 1920×1080 | 30 | Instant slide cut |
| video/deck-08-transition-08-to-09.mp4 | 6.00s | 2880×1620 | 30 | Instant slide cut |
| video/deck-09-flip-calm-1080.mp4 | 20.00s | 1920×1080 | 30 | Full deck flip; 1 s extra endpoint holds |
| video/deck-09-flip-calm.mp4 | 20.00s | 2880×1620 | 30 | Full deck flip; 1 s extra endpoint holds |
| video/deck-10-flip-fast-1080.mp4 | 7.40s | 1920×1080 | 30 | Full deck flip; 1 s extra endpoint holds |
| video/deck-10-flip-fast.mp4 | 7.40s | 2880×1620 | 30 | Full deck flip; 1 s extra endpoint holds |
| stills/deck-01-slide-1080.png | — | 1920×1080 | — | Unchanged rendered deck slide |
| stills/deck-01-slide.png | — | 2880×1620 | — | Unchanged rendered deck slide |
| stills/deck-02-slide-1080.png | — | 1920×1080 | — | Unchanged rendered deck slide |
| stills/deck-02-slide.png | — | 2880×1620 | — | Unchanged rendered deck slide |
| stills/deck-03-slide-1080.png | — | 1920×1080 | — | Unchanged rendered deck slide |
| stills/deck-03-slide.png | — | 2880×1620 | — | Unchanged rendered deck slide |
| stills/deck-04-slide-1080.png | — | 1920×1080 | — | Unchanged rendered deck slide |
| stills/deck-04-slide.png | — | 2880×1620 | — | Unchanged rendered deck slide |
| stills/deck-05-slide-1080.png | — | 1920×1080 | — | Unchanged rendered deck slide |
| stills/deck-05-slide.png | — | 2880×1620 | — | Unchanged rendered deck slide |
| stills/deck-06-slide-1080.png | — | 1920×1080 | — | Unchanged rendered deck slide |
| stills/deck-06-slide.png | — | 2880×1620 | — | Unchanged rendered deck slide |
| stills/deck-07-slide-1080.png | — | 1920×1080 | — | Unchanged rendered deck slide |
| stills/deck-07-slide.png | — | 2880×1620 | — | Unchanged rendered deck slide |
| stills/deck-08-slide-1080.png | — | 1920×1080 | — | Unchanged rendered deck slide |
| stills/deck-08-slide.png | — | 2880×1620 | — | Unchanged rendered deck slide |
| stills/deck-09-slide-1080.png | — | 1920×1080 | — | Unchanged rendered deck slide |
| stills/deck-09-slide.png | — | 2880×1620 | — | Unchanged rendered deck slide |
| stills/deck-10-overview.png | — | 1440×900 | — | All slides overview |
| stills/deck-11-reference-acorn-30s-roughcut.png | — | 1920×1200 | — | Reference film contact sheet, every 2 s |
| stills/deck-12-reference-acorn-master-roughcut.png | — | 1920×4500 | — | Reference film contact sheet, every 2 s |
| stills/deck-13-detail-station-detail.png | — | 1866×855 | — | Native DPR 2 detail crop; unchanged slide pixels |
| stills/deck-14-detail-evidence-detail.png | — | 576×1000 | — | Native DPR 2 detail crop; unchanged slide pixels |
| stills/deck-15-detail-placement-detail.png | — | 2070×915 | — | Native DPR 2 detail crop; unchanged slide pixels |
| contact-sheet.png | — | 1920×3300 | — | Labelled review sheet |
| qa/video-start-middle-end.png | — | 1440×6000 | — | Labelled review sheet |

Visual review complete: all nine slides and start/middle/end frames of every native and 1080p clip inspected. No capture failures found. Existing editorial gap: both rough cuts end with MISSING SHOT 20 / REAL (assembly photograph); deck slide 3 also states assembly photograph still required. No source fixes made. No server started; headless browser closed.

## Supporting files

| File | Duration | Resolution | FPS | Content / conditions |
|---|---:|---|---:|---|
| capture.cjs | — | — | — | Capture/encoding script, navigation checks, reference hashes or exact timing list |
| produce.py | — | — | — | Capture/encoding script, navigation checks, reference hashes or exact timing list |
| qa/browser.json | — | — | — | Capture/encoding script, navigation checks, reference hashes or exact timing list |
| qa/deck-01-transition-01-to-02-0.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-01-transition-01-to-02-1.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-01-transition-01-to-02-1080-0.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-01-transition-01-to-02-1080-1.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-01-transition-01-to-02-1080-2.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-01-transition-01-to-02-2.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-01-transition-01-to-02.txt | — | — | — | Capture/encoding script, navigation checks, reference hashes or exact timing list |
| qa/deck-02-transition-02-to-03-0.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-02-transition-02-to-03-1.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-02-transition-02-to-03-1080-0.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-02-transition-02-to-03-1080-1.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-02-transition-02-to-03-1080-2.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-02-transition-02-to-03-2.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-02-transition-02-to-03.txt | — | — | — | Capture/encoding script, navigation checks, reference hashes or exact timing list |
| qa/deck-03-transition-03-to-04-0.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-03-transition-03-to-04-1.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-03-transition-03-to-04-1080-0.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-03-transition-03-to-04-1080-1.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-03-transition-03-to-04-1080-2.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-03-transition-03-to-04-2.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-03-transition-03-to-04.txt | — | — | — | Capture/encoding script, navigation checks, reference hashes or exact timing list |
| qa/deck-04-transition-04-to-05-0.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-04-transition-04-to-05-1.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-04-transition-04-to-05-1080-0.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-04-transition-04-to-05-1080-1.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-04-transition-04-to-05-1080-2.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-04-transition-04-to-05-2.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-04-transition-04-to-05.txt | — | — | — | Capture/encoding script, navigation checks, reference hashes or exact timing list |
| qa/deck-05-transition-05-to-06-0.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-05-transition-05-to-06-1.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-05-transition-05-to-06-1080-0.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-05-transition-05-to-06-1080-1.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-05-transition-05-to-06-1080-2.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-05-transition-05-to-06-2.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-05-transition-05-to-06.txt | — | — | — | Capture/encoding script, navigation checks, reference hashes or exact timing list |
| qa/deck-06-transition-06-to-07-0.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-06-transition-06-to-07-1.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-06-transition-06-to-07-1080-0.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-06-transition-06-to-07-1080-1.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-06-transition-06-to-07-1080-2.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-06-transition-06-to-07-2.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-06-transition-06-to-07.txt | — | — | — | Capture/encoding script, navigation checks, reference hashes or exact timing list |
| qa/deck-07-transition-07-to-08-0.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-07-transition-07-to-08-1.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-07-transition-07-to-08-1080-0.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-07-transition-07-to-08-1080-1.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-07-transition-07-to-08-1080-2.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-07-transition-07-to-08-2.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-07-transition-07-to-08.txt | — | — | — | Capture/encoding script, navigation checks, reference hashes or exact timing list |
| qa/deck-08-transition-08-to-09-0.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-08-transition-08-to-09-1.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-08-transition-08-to-09-1080-0.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-08-transition-08-to-09-1080-1.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-08-transition-08-to-09-1080-2.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-08-transition-08-to-09-2.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-08-transition-08-to-09.txt | — | — | — | Capture/encoding script, navigation checks, reference hashes or exact timing list |
| qa/deck-09-flip-calm-0.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-09-flip-calm-1.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-09-flip-calm-1080-0.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-09-flip-calm-1080-1.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-09-flip-calm-1080-2.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-09-flip-calm-2.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-09-flip-calm.txt | — | — | — | Capture/encoding script, navigation checks, reference hashes or exact timing list |
| qa/deck-10-flip-fast-0.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-10-flip-fast-1.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-10-flip-fast-1080-0.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-10-flip-fast-1080-1.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-10-flip-fast-1080-2.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-10-flip-fast-2.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/deck-10-flip-fast.txt | — | — | — | Capture/encoding script, navigation checks, reference hashes or exact timing list |
| qa/ref-11-000.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-11-001.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-11-002.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-11-003.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-11-004.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-11-005.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-11-006.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-11-007.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-11-008.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-11-009.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-11-010.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-11-011.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-11-012.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-11-013.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-11-014.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-000.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-001.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-002.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-003.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-004.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-005.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-006.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-007.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-008.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-009.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-010.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-011.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-012.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-013.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-014.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-015.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-016.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-017.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-018.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-019.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-020.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-021.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-022.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-023.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-024.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-025.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-026.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-027.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-028.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-029.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-030.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-031.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-032.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-033.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-034.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-035.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-036.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-037.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-038.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-039.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-040.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-041.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-042.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-043.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-044.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-045.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-046.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-047.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-048.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-049.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-050.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-051.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-052.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-053.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-054.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-055.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/ref-12-056.png | — | 480×270 | — | QA/reference extracted frame or review sheet |
| qa/review-1.png | — | 1440×1500 | — | QA/reference extracted frame or review sheet |
| qa/review-2.png | — | 1440×1500 | — | QA/reference extracted frame or review sheet |
| qa/review-3.png | — | 1440×1500 | — | QA/reference extracted frame or review sheet |
| qa/review-4.png | — | 1440×1500 | — | QA/reference extracted frame or review sheet |
