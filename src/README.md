# Source map

Run Python commands from this directory so `core`, `reuse`, `toys`, and `dataset` resolve as top-level packages. Read [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md) before changing the working implementation.

For the current findings and paths to each phase and track's evidence, see [AGENTS.md](AGENTS.md).

| Location | Role |
| --- | --- |
| [`core/`](core/README.md) | Structural worlds, interventions, storage, exact oracle, and evidence state. |
| [`reuse/`](reuse/README.md) | Action-selection policies and the reusable one-episode runner. |
| [`toys/`](toys/README.md) | Exploratory scripts and plots; toy numbers are not study IDs. |
| [`experiment/phase-1/`](experiment/phase-1/README.md) | Track 0 local benchmark, planned Phase-1 tracks, and future controlled studies. |
| `dataset/` | Checked-in JSONL reference dataset and locally generated numeric `.npy` dataset and response cache. |
| `tests/` | Regression checks for the core contracts and runner. |

## Generate the primary `.npy` world dataset

The numeric world dataset is **not tracked by Git**. From `src/`, generate it once after cloning the repository:

```powershell
python -m reuse.numeric_engine.generate_worlds dataset/worldgen-4-4-npy
```

This creates `dataset/worldgen-4-4-npy/worlds.npy` and its `manifest.json` for `d=4,m=4` in canonical world order. The output directory must be new or empty; the command refuses to overwrite an existing dataset. For another world size, choose a different empty output directory and pass `--d` and `--m`. `NumericWorldDataset` checks the manifest and file hash when loading.

Response columns are separate derived data. `NumericResponseStore` computes a column only when an action requests it; give it a `cache_dir` to keep those columns as `.npy` across runs. They are also ignored by Git. See the [numeric-engine guide](reuse/numeric_engine/README.md) for an episode example and cache path.

## Quick commands

```powershell
python -m unittest discover -s tests -v
python -m reuse.numeric_engine.generate_worlds --help
python experiment/phase-1/track-0/benchmark_local.py --profile smoke
```

The dataset `--help` command shows generation options without writing a dataset. The Track-0 benchmark uses the older JSONL reference path, so its timings do not describe the numeric engine. The older JSONL generator remains available as `python -m dataset.generate_worlds --help`.
