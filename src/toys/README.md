# Toys

This folder is for exploratory scripts. A toy can help me inspect behavior or make a graph, but its number is not an experiment ID and its output is not a frozen Phase-1 result. The reusable policies and one-episode runner live in `../reuse/`; the planned studies live in `../experiment/phase-1/`.

Run commands from `src/`. The first toy uses `dataset/worldgen-4-4` by default.

## Smoke run

The default runs one Stage-A action with a random policy. Its first response column still evaluates all 705,600 worlds, so it may take a while.

```powershell
python -m toys.toy_001_stage_comparison
```

## Explore Stage A

```powershell
python -m toys.toy_001_stage_comparison `
  --stages A `
  --policies random information-gain `
  --episodes 10 `
  --budget 8 `
  --output results/toy001-stage-a.jsonl
```

The output file is opened in exclusive-create mode, so an old result is not silently overwritten. Exact greedy information gain scores every unused action. Stage B has 144 actions and Stage C has 1,296, so start those stages with a small sampled candidate set if you want a quick look:

```powershell
python -m toys.toy_001_stage_comparison `
  --stages B C `
  --policies random information-gain `
  --episodes 3 `
  --budget 8 `
  --candidate-limit 32
```

Results made with `--candidate-limit` use **sampled information gain**, not full-candidate greedy information gain.

## Plot toy output

```powershell
python -m toys.toy_001_synthesis_graph results/toy001-stage-a.jsonl
```

By default this writes `results/toy001-stage-a.png`. Pass `--output` to choose a different PNG destination. The plot shows compatible worlds, uncertainty, realized information gain, and predictive entropy across actions. Its bands are exploratory summaries; the formal unit of analysis and uncertainty method belong to a future study design.
