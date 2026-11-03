# Exp other 02: JSONL versus numeric runtime

This CPU diagnostic measures the current `d=4, m=4` architecture. It builds the same five action columns through the older `WorldDataset` + `OnDemandResponseStore` path and the primary `NumericWorldDataset` + `NumericResponseStore` path. The actions force 0, 1, 2, 3, and 4 `Y` nodes. Every paired response column must match exactly before its timing is accepted.

Run from `src/` after generating `dataset/worldgen-4-4-npy/`:

```powershell
python experiment/phase-1/track-1/exp-other-02/benchmark_numeric_engine.py
```

The script times first column construction, in-process cache hits, verified `.npy` disk reloads, and one-candidate greedy scoring on the initial survivor set. It also runs two complete full-budget numeric greedy episodes per stage: the first starts with an empty response cache; the second reuses that stage's columns. Each stage gets its own temporary cache. The measured runs use hidden-world indices 0 and 1, seed 0, `candidate_limit=None`, and budgets A=16, B=144, C=1,296. The cache directories are removed after the run; only `metadata.json` and `results.json` remain.

`results.json` estimates the cost of building all permitted columns by multiplying each forced-`Y` sample time by the count of that action type in a stage. It separately estimates one initial greedy scoring pass and disk reload of all columns. These are **planning extrapolations** from one action per type, not a measured full sweep of the JSONL path. An actual episode may spend more time scoring candidates over multiple steps, and later episodes depend on the number of executed steps and cache state. Use the measured stage episodes as local examples, not as an average over hidden worlds.

The benchmark is for runtime planning only. It does not compare uncertainty trajectories or support a stage-behavior conclusion.
