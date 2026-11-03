# Exp 01 long: raw run

Run from `src/` with `python experiment/phase-1/track-1/exp-01-long/run.py`. The script saves a random permutation of all 705,600 world indices before execution, then finishes A, B, and C for each world and syncs one raw JSONL record after every completed world. It stops between worlds after the cumulative six-hour runtime cap, so every retained world has a paired result. `--resume PATH_TO_RUN` continues an interrupted run from the saved order and checkpoint. `--hours N` changes the cap for a separate run.

The raw artifact is a timestamped directory under `runs/`. `selected_world_indices.npy` records the planned order; `metadata.json` records the completed prefix and actual elapsed time; `episodes.jsonl` holds one complete paired world per line. The shared schema is described in the [Track 1 Exp 01 README](../EXP01_RAW_SCHEMA.md).
