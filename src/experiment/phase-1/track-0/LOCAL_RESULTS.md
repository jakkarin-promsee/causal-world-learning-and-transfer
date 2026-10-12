# Local benchmark results (6 October 2026, Bangkok)

These measurements are for this computer and the current `d=4,m=4` dataset of 705,600 worlds. The [standard run](runs/20261005T200959Z-13020/summary.md) completed all 9 conditions in **22 minutes 32 seconds**. Its [raw event log](runs/20261005T200959Z-13020/events.jsonl) contains 19 episodes, 36 policy choices, 106 newly computed response columns, and 108 accesses to already cached columns. A separate [smoke run](runs/20261005T200838Z-23964/summary.md) checked the logging path before the standard run. Each run has its own `metadata.json` with dataset and code hashes, hardware details, seed, and condition list.

The machine reported an Intel Core i7-11800H (8 physical / 16 logical cores), 23.6 GiB RAM, and an NVIDIA RTX 3050 Ti Laptop GPU with 4 GiB VRAM. Python 3.11.0 and NumPy 2.3.5 ran the benchmark while plugged into power. **The current oracle uses the CPU; the GPU was not a compute device for these runs.** GPU VRAM snapshots in the raw log show whole-device usage, not memory owned by this process.

## Useful numbers for planning

| Measured workload | Wall time | New columns | Peak process RSS |
| --- | ---: | ---: | ---: |
| Stage A random, 3 episodes × 2 actions | 82.3 s | 6 | 42.2 MiB |
| Stage B random, 3 episodes × 2 actions | 76.7 s | 6 | 42.1 MiB |
| Stage C random, 3 episodes × 2 actions | 68.3 s | 6 | 42.1 MiB |
| Stage A full-candidate greedy, 2 episodes × 2 actions | 219.4 s | 16 | 55.0 MiB |
| Stage A/B/C sampled IG, candidate limit 4, 2 episodes × 2 actions | 156.9 / 171.1 / 176.9 s | 11 / 13 / 16 | 45.7 / 47.1 / 49.1 MiB |
| Stage B/C sampled IG, candidate limit 16, 1 episode × 1 action | 202.9 / 179.9 s | 16 / 16 | 49.7 / 49.4 MiB |

Across these conditions, the median time to create one cold response column was about **10.8–14.0 seconds**. It includes streaming and evaluating all 705,600 worlds. A cached column access is much cheaper. In the Stage-A full-greedy condition, episode 1 took **219.24 seconds** and built all 16 Stage-A columns; episode 2 took **0.068 seconds** and built none. The cache for those 16 `uint8` columns was about **10.8 MiB**. The sampled peak RSS is a process measurement at 0.2-second intervals, so a brief spike could be missed.

**Unmeasured estimate:** Full-candidate Stage C would have up to 1,296 distinct response columns, occupying about **872 MiB** of column arrays. If each new column continued to take roughly 11–14 seconds, computing all of them would take roughly **4–5 hours** before other overhead. This is an extrapolation, not a Stage-C full-greedy benchmark. Stage-C interventions differ in evaluation cost, the disk cache can change, and a real run may request fewer columns if they are already cached.

For future run estimates, first ask how many **new** action columns that workload will request under its cache plan. Episode count, stage name, and candidate limit alone do not determine runtime. These figures describe computation cost only; they say nothing about which policy or stage makes a better scientific decision.
