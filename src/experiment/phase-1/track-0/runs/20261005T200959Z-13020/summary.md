# Local Track-0 benchmark

- Status: **completed**
- UTC start: 2026-10-05T20:09:59+00:00
- Profile: `standard`
- Dataset: `dataset\worldgen-4-4`
- Worlds: 705,600; `d=4, m=4`
- CPU: 11th Gen Intel(R) Core(TM) i7-11800H @ 2.30GHz (8 physical / 16 logical cores)
- RAM: 23.6 GiB
- GPU: NVIDIA GeForce RTX 3050 Ti Laptop GPU; **benchmark code uses CPU only**
- Python 3.11.0; NumPy 2.3.5
- Git commit: `edba0258510fe7c04da3e2f55da294f14d41f88d`; dirty working tree: `True`
- Raw event log: [`events.jsonl`](events.jsonl). It includes every response-column access, policy choice, episode, cache size, RSS sample summary, and GPU snapshot.

## Conditions

| Condition | Episodes | Wall time | Cold columns | Median cold column | Peak process RSS | Cache |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `A-random-limitfull-budget2-episodes3` | 3 | 82.3 s | 6 | 13.63 s | 42.2 MiB | 4.0 MiB |
| `B-random-limitfull-budget2-episodes3` | 3 | 76.7 s | 6 | 12.57 s | 42.1 MiB | 4.0 MiB |
| `C-random-limitfull-budget2-episodes3` | 3 | 68.3 s | 6 | 11.30 s | 42.1 MiB | 4.0 MiB |
| `A-greedy_information_gain-limitfull-budget2-episodes2` | 2 | 219.4 s | 16 | 13.67 s | 55.0 MiB | 10.8 MiB |
| `A-sampled_information_gain-limit4-budget2-episodes2` | 2 | 156.9 s | 11 | 14.00 s | 45.7 MiB | 7.4 MiB |
| `B-sampled_information_gain-limit4-budget2-episodes2` | 2 | 171.1 s | 13 | 12.65 s | 47.1 MiB | 8.7 MiB |
| `C-sampled_information_gain-limit4-budget2-episodes2` | 2 | 176.9 s | 16 | 10.82 s | 49.1 MiB | 10.8 MiB |
| `B-sampled_information_gain-limit16-budget1-episodes1` | 1 | 202.9 s | 16 | 12.60 s | 49.7 MiB | 10.8 MiB |
| `C-sampled_information_gain-limit16-budget1-episodes1` | 1 | 179.9 s | 16 | 11.28 s | 49.4 MiB | 10.8 MiB |

Each condition starts with an empty response cache and retains it between episodes. Cold-column time includes streaming and evaluating every world. The first episode and later episodes therefore have different cache states. The GPU numbers in `events.jsonl` are whole-device VRAM usage and cannot be attributed to this CPU-only Python process. These are local planning measurements, not evidence that one policy or stage is scientifically better.

For a future run, estimate the number of **new** response columns it may request, then use the matching cold-column times here as a rough starting point. Do not multiply one episode's warm time by a new workload with an empty cache.
