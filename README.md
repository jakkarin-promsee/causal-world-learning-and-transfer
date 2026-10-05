# Causal World Learning and Transfer

How can an agent understand a hidden causal world when it can perform only a limited number of interventions? Once it has learned something useful, how can it pass that knowledge to another agent?

This research project starts with finite, deterministic Boolean worlds so those questions can be studied under controlled conditions. The current phase builds exact inference and action-selection baselines. Learning a compact internal representation and transferring it between agents are the longer-term goals.

## Current setup

- Each world is a directed acyclic system of Boolean variables. Its hidden rules use `AND`, `OR`, and `NOT`.
- An agent chooses an intervention, observes the resulting variables, and repeats within an action budget.
- Stages A, B, and C allow progressively more interventions: setting the input variables, forcing one output variable, or forcing any subset of output variables.
- An exact oracle tracks every world consistent with the observations. Random and greedy information-gain policies provide baselines; a finite candidate limit gives **sampled** information gain.

The checked-in `d=4, m=4` dataset contains 705,600 canonical worlds. Current experiment work studies how many episodes are needed for precise comparisons, how candidate limits affect quality and computation, and how the problem changes with world size.

## Try the baseline

The code uses Python and NumPy; plotting also uses Matplotlib. Run commands from `src/` so `core` and `experiments` resolve as packages:

```powershell
cd src
python -m unittest discover -s tests -v
python -m experiments.exp_001_stage_comparison --dataset dataset/worldgen-4-4
```

The smoke run is one Stage-A action, but its first response column still evaluates all 705,600 worlds, so it may take a while. See [experiment instructions](src/experiments/README.md) for more options and plotting, and [architecture overview](src/ARCHITECTURE_OVERVIEW.md) for the implementation contracts.

## Repository map

- `ideas/` — Obsidian research notes with definitions, hypotheses, and experiment plans.
- [`src/core/`](src/core/README.md) — world generation, interventions, storage, and exact inference.
- [`src/experiments/`](src/experiments/README.md) — policies, episode runner, and exploratory studies.
- [`src/dataset/worldgen-4-4/`](src/dataset/worldgen-4-4/manifest.json) — reference Boolean-world dataset.
