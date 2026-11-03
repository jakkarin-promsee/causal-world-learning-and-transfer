# Project timeline

This project develops nonlinearly; this file records milestones without relying on commit history.

1. Started from a blank repository.
2. Developed the research direction in `ideas/my-first-ideas.md`, `ideas/stage-1-explore-the-problem.md`, and `ideas/stage-2-model-and-implementation.md`.
3. Built canonical world generation, JSONL.gz storage, reusable policies and runner, and tests; drafted the experiment plan in `ideas/stage-3-actual-experiment-1.md`.
4. Completed the hidden-world environment and exact oracle baseline.
5. Measured local runtime and cache behavior in `src/experiment/phase-1/track-0/` to plan feasible experiments before comparing policies (6 October 2026).
6. Drafted Track 1 in `ideas/experiment-card/track1/exp01.md`: use full-candidate greedy and each Stage's full action budget to see complete uncertainty trajectories, then compare stages at shared steps on the same sampled hidden worlds.
7. Added a specialized runner for Track 1 while keeping the general runner:
   - `run_episode()` still executes the requested budget for any policy. `run_full_candidate_greedy_episode()` requires the full Stage budget and stops when one world survives or every remaining action is unable to split the survivors; its plotted uncertainty stays flat after that point without inventing action records.
   - Why: avoid wasting full-budget computation after a proven plateau, while other tracks retain the original runner behavior. A plateau above zero can mean several observationally equivalent worlds remain, not that the oracle identified one world.
8. Measured cold response-column costs in `src/experiment/phase-1/track-1/exp-other-01/` to locate the slowdown before changing storage. Repeated JSONL reading/decoding/validation was the larger measured component; the test did not isolate disk I/O alone (2 November 2026).
9. Replaced the old flat `src/reuse/` implementation with two explicit paths:
   - `src/reuse/jsonl_reference/` keeps the JSONL-backed runner and policy as a stable reference for parity checks; it is updated only when a deliberate comparison needs it.
   - `src/reuse/numeric_engine/` is the active path: canonical world rules live in `.npy`, responses are computed in vectorized batches and cached as `.npy` only when requested, and top-level `reuse` imports point here.
   - Why: avoid parsing the same JSONL worlds for every action and develop one main path without maintaining two implementations in lockstep. All Stage-C responses are not precomputed because their size grows quickly with `d,m`.
10. Measure the pre-render optimization in `src/experiment/phase-1/track-0/` and record its computation cost before using it to plan later experiments.
11. Split Track 1 Experiment 01 into `src/experiment/phase-1/track-1/exp-01-short/` and `src/experiment/phase-1/track-1/exp-01-long/`. Both use the same base conditions and save reusable raw episode results; the short run completed 10 sampled worlds for early inspection, and the approximately six-hour long run was launched for the larger sample (3 November 2026).
