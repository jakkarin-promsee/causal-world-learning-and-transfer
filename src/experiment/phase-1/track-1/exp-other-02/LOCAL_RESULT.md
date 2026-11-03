# Local result: JSONL versus numeric runtime (2 November 2026, Bangkok)

On this CPU and the `d=4, m=4` dataset of 705,600 worlds, the five paired response columns matched **exactly**. A cold JSONL column took 11.01–15.59 seconds; a cold numeric column, including writing its verified `.npy` cache, took 0.013–0.060 seconds. The observed per-action speedup was 252–845×. A verified disk reload of each sampled numeric column took 0.0011–0.0016 seconds. These are single samples per intervention type, not confidence intervals.

| Forced `Y` count | Action ID | JSONL cold | Numeric cold | Numeric disk reload | Cold speedup |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 0 | 15.003 s | 0.060 s | 0.0016 s | 252× |
| 1 | 17 | 15.590 s | 0.039 s | 0.0012 s | 400× |
| 2 | 207 | 13.442 s | 0.046 s | 0.0012 s | 292× |
| 3 | 213 | 12.051 s | 0.023 s | 0.0011 s | 516× |
| 4 | 215 | 11.006 s | 0.013 s | 0.0011 s | 845× |

## Full-candidate numeric episodes actually run

Each stage used its maximum action budget and its own initially empty response cache. Hidden worlds 0 and 1 were run in sequence; the second episode reused all columns built by the first. The specialized greedy runner stopped on a singleton or a proven equivalence plateau.

| Stage | Budget | World 0: cold episode | World 1: cached episode | Columns after world 0 |
| --- | ---: | --- | --- | ---: |
| A | 16 | 0.931 s, 4 steps, equivalent class of 273 | 0.104 s, 4 steps, equivalent class of 21 | 16 |
| B | 144 | 7.702 s, 12 steps, singleton | 1.152 s, 9 steps, singleton | 144 |
| C | 1,296 | 46.013 s, 11 steps, singleton | 9.785 s, 8 steps, singleton | 1,296 |

The later episode is faster partly because all response columns are already in process memory; its hidden world also led to fewer steps in B and C. These two effects are not separately identified by the episode times.

## Numbers for planning a later run

The table below is a **stratified extrapolation**, not a full column sweep. For each stage, it multiplies the one measured cold time at forced-`Y` count `k` by the exact number of stage actions with that `k`. “Initial scoring” multiplies the measured one-candidate greedy score on the initial survivor set by those same counts. It does not include later greedy passes, updates, output processing, or changes in time as the survivor set shrinks.

| Stage | Actions | Estimated old JSONL all cold columns | Estimated numeric all cold columns | Estimated numeric all disk reloads | Estimated one initial numeric greedy score |
| --- | ---: | ---: | ---: | ---: | ---: |
| A | 16 | 240 s (4.0 min) | 0.95 s | 0.026 s | 0.051 s |
| B | 144 | 2,236 s (37.3 min) | 5.94 s | 0.17 s | 0.43 s |
| C | 1,296 | 16,385 s (4.55 h) | 38.92 s | 1.50 s | 3.74 s |

For a future full-candidate run, use **time ≈ new-column construction + every greedy scoring pass + episode updates + any cache reload**. The number of newly built columns is paid once per cache lifetime, not once per hidden world. The first actual C episode took 46.0 seconds, versus 38.9 seconds estimated for building all C columns; the difference includes multiple scoring passes and updates. With the cache already resident, the measured second C episode still took 9.8 seconds. A conditional planning example for **10 episodes per stage** is `cold world 0 + 9 × cached world 1`: A ≈ 1.9 seconds, B ≈ 18.1 seconds, C ≈ 134.1 seconds (2.2 minutes). These are workload scenarios using two specific worlds, not a population-runtime prediction; the step count and equivalence structure can change substantially across sampled worlds. Track 1 should record actual step counts and cache state per episode before using these numbers for a larger sweep.

## Evidence and limits

- [Raw result](runs/20261102T090348Z/results.json) records paired hashes, exact timings, cache modes, stage action counts, extrapolations, and both episodes per stage.
- [Metadata](runs/20261102T090348Z/metadata.json) records dataset identity, source hashes, runtime, seed, policy, and chunk size. The `.npy` world file was hash-verified on load; its load took 0.013 seconds in this run.
- [Benchmark code](benchmark_numeric_engine.py) uses fresh temporary cache directories, asserts response parity, and does not modify the core implementation.
- All times are wall-clock CPU timings from one local run. Disk/OS cache, power mode, background load, and response-cache placement can change them. Cold here means an empty application response cache; it does not mean a cold operating-system page cache. The results say nothing about stage quality or uncertainty trajectories.
