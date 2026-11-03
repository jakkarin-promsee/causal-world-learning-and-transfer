# Experiment findings index

Use this file as the short index of verified results and evidence paths for work under `src/`. Keep stable repository-wide rules in the root `AGENTS.md`, implementation contracts in `ARCHITECTURE_OVERVIEW.md`, and full methods and results in each phase/track folder. When a track produces new results, add a short finding here with its scope, status, and a link to the underlying result; do not turn a pilot observation or runtime estimate into a scientific conclusion.

## Phase 1: Measurement and baseline comparability

The [Phase-1 overview](experiment/phase-1/README.md) maps the tracks. The research questions are still drafted in [the Stage-3 ideas note](../ideas/stage-3-actual-experiment-1.md). No learned model is evaluated in this phase.

| Track | Status and short finding | Read more |
| --- | --- | --- |
| [0: Local computation](experiment/phase-1/track-0/README.md) | **Measured locally, 6 October 2026 (Bangkok).** On the `d=4,m=4` dataset, a new response column took about 11–14 seconds in the tested conditions. Stage-A full-candidate greedy built 16 columns in its first episode (219.24 s); its next episode reused the cache (0.068 s). The CPU ran the workload; GPU VRAM snapshots are machine context. | [Result summary](experiment/phase-1/track-0/LOCAL_RESULTS.md), [standard run summary](experiment/phase-1/track-0/runs/20261005T200959Z-13020/summary.md), [metadata](experiment/phase-1/track-0/runs/20261005T200959Z-13020/metadata.json), [raw events](experiment/phase-1/track-0/runs/20261005T200959Z-13020/events.jsonl). |
| [1: Stage behavior](experiment/phase-1/track-1/README.md) | **Stage comparison planned.** The JSONL diagnostic located repeated dataset preparation costs. A 2 November 2026 numeric benchmark found exact response parity on five sampled actions; cold numeric columns took 0.013–0.060 s versus 11.01–15.59 s for JSONL. Actual first full-candidate numeric episodes took A/B/C 0.93/7.70/46.01 s for hidden world 0, with all stage columns built. These are local computation measurements, not stage-behavior results. | [Track question](experiment/phase-1/track-1/README.md), [old-path diagnostic](experiment/phase-1/track-1/exp-other-01/LOCAL_RESULT.md), [numeric benchmark](experiment/phase-1/track-1/exp-other-02/LOCAL_RESULT.md), [raw numeric measurements](experiment/phase-1/track-1/exp-other-02/runs/20261102T090348Z/results.json). |
| [2: Measurement precision](experiment/phase-1/track-2/README.md) | **Planned.** No episode-count or precision result yet. | [Track question](experiment/phase-1/track-2/README.md). |
| [3: Candidate sampling](experiment/phase-1/track-3/README.md) | **Planned.** Track-0 timings do not establish sampled-information-gain quality. | [Track question](experiment/phase-1/track-3/README.md). |
| [4: Nearby world sizes](experiment/phase-1/track-4/README.md) | **Planned.** No result outside `d=4,m=4` yet. | [Track question](experiment/phase-1/track-4/README.md). |

Track 0's roughly 4–5 hour estimate for all 1,296 Stage-C response columns applies to the older JSONL-backed `OnDemandResponseStore` under its extrapolation assumptions. The numeric benchmark now measured one complete Stage-C full-candidate episode at 46.01 s and a second cache-resident episode at 9.79 s on two specific hidden worlds. The response-column array size remains about 872 MiB at `d=4,m=4`. See the [Track-1 numeric result](experiment/phase-1/track-1/exp-other-02/LOCAL_RESULT.md) for cache conditions, action counts, and limits.

## Later phases

No later phase or track has a recorded result here yet. Add one section per phase when work begins, then link each completed track's result and raw evidence from this index.
