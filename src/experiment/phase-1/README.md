# Phase 1: Understand the base and what can be compared

No learned model is tested in this phase. I first want to understand Stage A/B/C baseline behavior, then learn how much evidence is needed before I can compare results reliably. Candidate sampling and small changes around `d=4,m=4` test how far those comparisons can go. The rough questions are in `../../../ideas/stage-3-actual-experiment-1.md`; experiment designs and controls are still open.

- [Track 0](track-0/README.md): local runtime, memory, and cache benchmark for planning the other tracks; [current results](track-0/LOCAL_RESULTS.md).
- [Track 1](track-1/README.md): Stage A/B/C behavior and meaningful comparisons.
- [Track 2](track-2/README.md): episode count and measurement precision.
- [Track 3](track-3/README.md): candidate-limit impact on quality and computation.
- [Track 4](track-4/README.md): whether the base-world conclusions carry to nearby `d,m` values.
