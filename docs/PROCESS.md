# Building ACORN with Codex

ACORN (Aerial Canopy Observation and Reporting Node) is a portable forest smoke-detection station built by team Scarabs at Junction 2026. For the OpenAI “Best Use of Codex” challenge, our evidence is the station, placement simulator, remote dashboard, tests and bring-up records in this repository. Nearly all code and tests were written by parallel Codex child agents using `gpt-6.1-sol`, with written briefs and explicit ownership; Yaman set direction and made decisions, while the orchestrator coordinated without writing product code.

A second model family, Claude, handled most orchestration and independent reviews and rehearsals of Codex’s output. It also implemented some interim work, including the initial firmware/flame-sensor backend, inline event clips and a subsequently replaced redesign; those are not Codex contributions. The detection-size study cited below was also an independent Claude measurement.

## Splitting the work

The initial station and placement builders worked at the same time. They owned separate directories and did not commit; a dedicated commit agent handled git and checked what entered the public repository. Later agents received narrower follow-up tasks and inherited written handovers.

| Codex agent | Ownership or responsibility |
| --- | --- |
| Station builder | `station/`: capture, inference, alarms, evidence, panel and tests |
| Placement builder | `placement/`: terrain/canopy processing, visibility analysis, map and tests |
| Site builder | `placement/` and new `tools/`: deployment preparation and artifact handoff |
| Commit agent | Git, root README and ignore rules; initially scheduled, later on demand |
| Board agent | Mac toolchain, UNO Q bring-up, camera diagnosis and measurement records |
| Communications and UI successors | Radio simulation, `ground/`, ranger access and the accepted interface |

One real site-agent brief, shortened and paraphrased from the orchestration record, was:

> Own `placement/` and new `tools/`. Split blind forest into outside-camera-view and occluded forest. Make the dynamic placement app Modal-deployable, with bounded requests, an English default and Turkish toggle, and configurable name/logo placeholders. Add artifact upload/restore scripts; dry run only. Do not deploy or upload.

The resulting changes include `995171f` (visibility categories), `71d1342` (deployment configuration) and `363b396` (artifact handoff). The assignment and parallel execution come from the contemporaneous orchestration notes; session available on request. Commits show the resulting work, rather than proving which model produced it.

## Concrete pieces Codex carried

**An offline detection pipeline.** Codex built independent capture workers, CPU ONNX inference, spatially consistent smoke-suspicion events, retained evidence and operator decisions. Open `station/` and commits `0466448`, `1a05a46` and `f81781e`. Commit `5bce68e` adds tests against attributed recorded smoke and negative footage. This made the inference path inspectable beyond a panel displaying a prediction.

**Getting software onto the actual board.** The board agent installed the Mac toolchain, brought up the station and MCU bridge, diagnosed startup problems and got two live USB cameras working through the kit hub. The USB bandwidth fix used `uvcvideo quirks=128`; Yaman ran the privileged commands. [BOARD_NOTES.md](../firmware/BOARD_NOTES.md) records measured inference around 278 ms at input 192, with 0.99 analyses per second per camera, and a successful power-cycle recovery. Commits `2bcfe70` and `f73495b` preserve the bring-up and recovery evidence. These measurements do not establish field detection accuracy.

**A constrained remote link.** Codex implemented the packet format, simulated transport, authenticated ranger panel and packet-only ground dashboard (`c2b31a5`, `8d2c630`). A later rehearsal exposed exhausted airtime accounting; fixes `2b08e32` and `a3afd24` paced transmissions and made expected contact windows visible. [DEMO.md](../DEMO.md) documents the current packet sizes, sustainable demo configuration and explicit Wi-Fi imagery switch. Real LoRa hardware remains unverified.

**Turning measurement into configuration.** The independent [detection-size study](../station/DETECTION_VS_INPUT_SIZE.md) found that the fast input setting missed synthetically reduced smoke plumes. Codex implemented separate field and demo profiles in `be56a90`, instead of treating fast board inference as proof of adequate detection. The root [README](../README.md) states the remaining measurement limits.

## Where the loop caught failures

Yaman rejected a light redesign and then an overloaded dark console. The accepted Codex successor kept the dark, map-first direction but reduced repetition and exposed details on demand; `0585dd0` contains the unified consoles. Rejections and acceptance are timeline evidence; session available on request.

Two independent fresh-clone rehearsals exposed setup and operating blockers, including certificate failures, an undemonstrable recorded-source dropout and the radio budget problem. Fix lists went back to implementation agents; `c19de74` adds bounded footage-download retries and `f632491` publishes the runbook.

The later [quality tracker](QUALITY_REVIEW.md) records findings covering stale events, decision ordering, evidence races and incompatible placement comparisons. Codex fixes landed in `87d6bb0` (station), `57c1fb9` (ground) and `a1d1073` (placement), with regression tests. The tracker still marks independent combined acceptance pending; landed fixes are not a claim that every review item is closed.

## Advice to another team

Give each builder a bounded brief, directory ownership and an explicit verification report. Keep a human responsible for product decisions. Rehearse from a fresh clone, return concrete failures to the responsible agent, and keep measured hardware behavior separate from simulation. Parallel implementation helped us assemble the system; written handovers, independent checks and rejected designs made the result reviewable.
