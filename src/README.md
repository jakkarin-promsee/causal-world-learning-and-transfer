# Source map

Run Python commands from this directory so `core`, `reuse`, `toys`, and `dataset` resolve as top-level packages. Read [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md) before changing the working implementation.

For the current findings and paths to each phase and track's evidence, see [AGENTS.md](AGENTS.md).

| Location | Role |
| --- | --- |
| [`core/`](core/README.md) | Structural worlds, interventions, storage, exact oracle, and evidence state. |
| [`reuse/`](reuse/README.md) | Action-selection policies and the reusable one-episode runner. |
| [`toys/`](toys/README.md) | Exploratory scripts and plots; toy numbers are not study IDs. |
| [`experiment/phase-1/`](experiment/phase-1/README.md) | Track 0 local benchmark, planned Phase-1 tracks, and future controlled studies. |
| [`dataset/`](dataset/worldgen-4-4/manifest.json) | Dataset generator and the checked-in `d=4,m=4` world dataset. |
| `tests/` | Regression checks for the core contracts and runner. |

## Quick commands

```powershell
python -m unittest discover -s tests -v
python -m toys.toy_001_stage_comparison
python -m dataset.generate_worlds --help
python experiment/phase-1/track-0/benchmark_local.py --profile smoke
```

The toy command runs one Stage-A action, but constructing its first response column still evaluates all 705,600 worlds. The dataset command shows generation options without writing a dataset.
