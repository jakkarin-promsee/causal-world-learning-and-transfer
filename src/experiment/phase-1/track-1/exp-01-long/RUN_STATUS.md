# Exp 01 long run (started 3 November 2026, Bangkok)

The six-hour capped run started at 2026-11-03 06:22:44 UTC (13:22:44 Bangkok) as background process PID 37852. It saved a random permutation of all 705,600 canonical world indices before execution. The first completed checkpoints were verified to contain paired A/B/C results in the saved order. The final number of worlds and runtime are determined only when the run stops between worlds at the time cap.

- [Current metadata and completed count](runs/20261103T062244Z/metadata.json)
- [Saved random world order](runs/20261103T062244Z/selected_world_indices.npy)
- [Raw paired episodes](runs/20261103T062244Z/episodes.jsonl)
- [Shared schema](../EXP01_RAW_SCHEMA.md)

The live stdout and stderr logs are `launch.stdout.log` and `launch.stderr.log` in this folder. If interrupted, run `python experiment/phase-1/track-1/exp-01-long/run.py --resume experiment/phase-1/track-1/exp-01-long/runs/20261103T062244Z` from `src/`.
