# Exp 01 short: raw run

Run from `src/` with `python experiment/phase-1/track-1/exp-01-short/run.py`. Each invocation randomly selects 10 distinct hidden-world indices and runs full-candidate greedy information gain in Stages A, B, and C for each world. The same world is used in all three stages.

The raw artifact is a timestamped directory under `runs/`. `selected_world_indices.npy` records sample order; `metadata.json` records its hash, sampling seed, dataset and source identities, policy, budgets, and completion status; `episodes.jsonl` contains one complete A/B/C record per line. The shared schema is described in the [Track 1 Exp 01 README](../EXP01_RAW_SCHEMA.md).
