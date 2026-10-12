# Local Track-0 benchmark

- Status: **completed**
- UTC start: 2026-10-05T20:08:38+00:00
- Profile: `smoke`
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
| `A-random-limitfull-budget1-episodes1` | 1 | 14.3 s | 1 | 13.73 s | 38.9 MiB | 0.7 MiB |
| `B-random-limitfull-budget1-episodes1` | 1 | 14.0 s | 1 | 13.91 s | 39.0 MiB | 0.7 MiB |
| `C-random-limitfull-budget1-episodes1` | 1 | 11.4 s | 1 | 11.37 s | 38.9 MiB | 0.7 MiB |
| `C-sampled_information_gain-limit2-budget1-episodes1` | 1 | 23.5 s | 2 | 11.71 s | 39.6 MiB | 1.3 MiB |

Each condition starts with an empty response cache and retains it between episodes. Cold-column time includes streaming and evaluating every world. The first episode and later episodes therefore have different cache states. The GPU numbers in `events.jsonl` are whole-device VRAM usage and cannot be attributed to this CPU-only Python process. These are local planning measurements, not evidence that one policy or stage is scientifically better.

For a future run, estimate the number of **new** response columns it may request, then use the matching cold-column times here as a rough starting point. Do not multiply one episode's warm time by a new workload with an empty cache.
