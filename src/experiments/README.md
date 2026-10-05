# Oracle baseline experiments

The code in this directory has three separate responsibilities:

- `runner.py` executes one episode and records measurements.
- `policies.py` chooses actions without seeing the hidden world.
- `exp_001_stage_comparison.py` declares the conditions of the first study.

Run commands from `src` so that the `core` and `experiments` packages are on
Python's import path.

## Smoke run

The safe default runs one single-step Stage-A episode with a random policy.
Even this must stream the 705,600-world dataset to construct an exact response
column, so it may take tens of seconds:

```powershell
python -m experiments.exp_001_stage_comparison
```

## First Stage-A comparison

```powershell
python -m experiments.exp_001_stage_comparison `
  --stages A `
  --policies random information-gain `
  --episodes 10 `
  --budget 8 `
  --output results/exp001-stage-a.jsonl
```

The output file is opened in exclusive-create mode, so an existing result is
never overwritten silently.

## Computational warning

Exact information-gain policy evaluates every unused action.  With `d=4` and
`m=4`, Stage A has 16 actions, Stage B has 144, and Stage C has 1,296.  Each
new action response is evaluated over all 705,600 candidate worlds.  Start
Stage B/C exploration with a sampled candidate set, for example:

```powershell
python -m experiments.exp_001_stage_comparison `
  --stages B C `
  --policies random information-gain `
  --episodes 3 `
  --budget 8 `
  --candidate-limit 32
```

Results produced with `--candidate-limit` must be described as **sampled
information gain**, not exact greedy information gain.

## Plot an Experiment 001 result

`exp_001_synthesis_graph.py` turns one or more Experiment 001 JSONL files into
a four-panel PNG.  It shows the compatible worlds and posterior uncertainty
left after each action, plus realized information gain and its expected
counterpart.  Pale paths are individual hidden worlds; the dark path is the
mean over episodes and the shaded region is an approximate 95% confidence
interval for that mean.  The compatible-world-count panel uses a geometric
mean/interval because it is shown on a logarithmic scale.

```powershell
python -m experiments.exp_001_synthesis_graph results/exp001-stage-a.jsonl
```

By default this writes `results/exp001-stage-a.png`.  To combine result files
or choose a destination:

```powershell
python -m experiments.exp_001_synthesis_graph `
  results/exp001-stage-a.jsonl results/exp001-stage-b.jsonl `
  --output results/exp001-stage-comparison.png
```
