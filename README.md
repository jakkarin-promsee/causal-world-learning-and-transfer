# Causal World Learning and Transfer

How can an agent understand a hidden causal world when it can perform only a limited number of interventions? Once it has learned something useful, how can it pass that knowledge to another agent?

This research project starts with finite, deterministic Boolean worlds so those questions can be studied under controlled conditions. The current phase checks how reliably the exact inference and action-selection baselines can be measured and compared. Learning a compact internal representation and transferring it between agents are longer-term goals.

## Current setup

- Each world is a directed acyclic system of Boolean variables. Its hidden rules use `AND`, `OR`, and `NOT`.
- An agent chooses an intervention, observes the resulting variables, and repeats within an action budget.
- Stages A, B, and C allow progressively more interventions: setting the input variables, forcing one output variable, or forcing any subset of output variables.
- An exact oracle tracks every world consistent with the observations. Random and greedy information-gain policies provide baselines; a finite candidate limit gives **sampled** information gain.

The checked-in `d=4, m=4` dataset contains 705,600 canonical worlds. Phase 1 starts by exploring Stage A/B/C behavior, then checks measurement precision, candidate-limit tradeoffs, and whether those comparisons still make sense near the base world size.

## Try the baseline

The code uses Python and NumPy; plotting also uses Matplotlib. Run commands from `src/` so the source packages resolve:

```powershell
cd src
python -m unittest discover -s tests -v
python -m toys.toy_001_stage_comparison
```

The toy smoke run is one Stage-A action, but its first response column still evaluates all 705,600 worlds, so it may take a while. See [toy instructions](src/toys/README.md) for more options and plotting, [source map](src/README.md) for the new layout, and [architecture overview](src/ARCHITECTURE_OVERVIEW.md) for the implementation contracts.

## Repository map

- `ideas/` — research notes (some internal links use Obsidian syntax):
  - [Stage 1: Explore the problem](ideas/stage-1-explore-the-problem.md)
  - [Stage 2: Model and implementation](ideas/stage-2-model-and-implementation.md)
  - [Stage 3: Phase 1 experiment ideas](ideas/stage-3-actual-experiment-1.md)
  - [Early ideas](ideas/my-first-ideas.md)
- [`src/core/`](src/core/README.md) — world generation, interventions, storage, and exact inference.
- [`src/reuse/`](src/reuse/README.md) — reusable policies and one-episode runner.
- [`src/toys/`](src/toys/README.md) — exploratory scripts, separate from the planned studies.
- [`src/experiment/phase-1/track-0/`](src/experiment/phase-1/track-0/README.md) — local computation benchmark and run logs.
- [`src/experiment/phase-1/`](src/experiment/phase-1/README.md) — Phase-1 track plans and future study artifacts.
- [`src/dataset/worldgen-4-4/`](src/dataset/worldgen-4-4/manifest.json) — reference Boolean-world dataset.
