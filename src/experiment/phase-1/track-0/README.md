# Track 0: Local computation benchmark

This track answers a practical question before the Phase-1 studies: how long do the current oracle and policies take on this computer, and how much process RAM and response-cache memory do they use? It is a planning reference for future agents, not a scientific comparison of stage or policy quality. All benchmark code runs on the CPU. The GPU name and whole-device VRAM usage are recorded because they describe the machine, but they do **not** measure GPU memory used by this Python workload.

The first completed measurements and links to both run logs are in [LOCAL_RESULTS.md](LOCAL_RESULTS.md).

## Run from `src/`

```powershell
python experiment/phase-1/track-0/benchmark_local.py --profile smoke
python experiment/phase-1/track-0/benchmark_local.py --profile standard --max-minutes 90
```

`smoke` checks the logging path with one random episode in each stage and one two-candidate Stage-C sampled-information-gain episode. `standard` uses representative random, full-candidate Stage-A greedy, and sampled-information-gain conditions across stages, budgets, candidate limits, and one to three episodes. It does not exhaustively score all Stage-C actions. The wall-time cap is checked **between** conditions; a single condition can run past it. Use `--help` to choose a dataset, seed, time cap, or new output directory.

Each run creates a new folder under `runs/` and never overwrites an old log. Read `summary.md` first, then `metadata.json` and `events.jsonl` for exact details. The event log is flushed after each event, so completed condition data remains available if a later condition stops. It records the selected hidden-world indices and policy seeds, each policy choice, every cold or warm response-column access, wall and process CPU time, per-episode steps, process RSS, sampled peak RSS, cache size, system available RAM, and whole-device GPU VRAM snapshots. `metadata.json` records the hardware and software environment, dataset manifest hash, and hashes of the benchmark and relevant implementation files.

## How to use the numbers

The dominant cold cost is often creating a new response column, which streams and evaluates every world. Later episodes may reuse cached columns and run much faster. Look at **new response columns** and cache state before estimating another workload; an episode count alone is not enough. Candidate limit is the number of action scores sampled per step, while Stage A/B/C have different total action spaces. Full-candidate greedy here means an exact greedy choice for one step, not a globally optimal action plan.

Times depend on power mode, concurrent work, disk cache, and dataset size. The script reports observations from this local run; estimates for unmeasured conditions should be labeled as estimates. Do not use Track-0 timing as evidence about causal identifiability or policy quality.
