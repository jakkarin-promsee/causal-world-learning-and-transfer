# Track 1 Exp 02 — stage observational equivalence

This experiment partitions all 705,600 canonical `d=4,m=4` worlds by their complete response signature under Stage A, B, and C actions. It measures what each action set can distinguish, independently of the Exp 01 greedy policy and its stopping time. The design is in [the experiment card](../../../../../ideas/experiment-card/track1/exp02.md).

Run from `src/`:

```powershell
python experiment/phase-1/track-1/exp-02/run.py
python experiment/phase-1/track-1/exp-02/summarize_raw.py experiment/phase-1/track-1/exp-02/runs/RUN_ID
```

Use `--stop-stage A` for a short smoke run. Its metadata says `smoke_partial_stages`; it is not a complete A/B/C result. `--output PATH` selects a new output directory. The runner does not overwrite an existing directory.

Each run saves `partitions.npz` and `metadata.json`. For each completed stage `S`, `class_id_S` is one `int32` class ID per canonical world index, and `class_size_S[id]` is that class's world count. IDs are deterministic within the run, derived by exact grouping of the previous class ID and each new action's observation code in ascending action-ID order. They are labels, not stable semantic world properties. The metadata records the dataset hash, source hashes, action counts, stage class counts, and NPZ checksum. The summary script validates the checksum, sizes, and A→B→C refinement, then writes `numeric-summary.json`. The NPZ class maps are enough to recalculate all class-size tables and world-weighted metrics without evaluating response columns again.

The three requested quantities have different denominators:

1. `equivalent_world_count`: $\sum_{c:|c|>1}|c|$, the number of canonical worlds inside non-singleton classes.
2. `avg_class_amount_world_weighted_equivalent_only`: $\sum_{c:|c|>1}|c|^2/\sum_{c:|c|>1}|c|$, the mean class size when sampling a world uniformly **only among those equivalent worlds**.
3. `avg_class_amount_world_weighted_all_worlds`: $\sum_c|c|^2/705600$, the mean class size when sampling uniformly from **all** canonical worlds; a singleton contributes size 1.

The class-count histogram in `numeric-summary.json` uses classes as units. The two averages above use worlds as units, so a class of size 10 has ten times the sampling weight of a class of size 1. No confidence interval is needed for the exhaustive finite-population counts.

## Complete result (3 November 2026)

| Stage | Classes | Worlds in non-singleton classes | Mean amount among those worlds | Mean amount across all worlds |
| --- | ---: | ---: | ---: | ---: |
| A | 394,684 | 424,872 (60.2143%) | 10.0209 | 6.4319 |
| B | 705,416 | 368 (0.0522%) | 2.0000 | 1.0005 |
| C | 705,600 | 0 (0%) | undefined (empty group) | 1.0000 |

All 184 Stage-B non-singleton classes have exactly two worlds. Stage C reached 705,600 singleton classes after action ID 161, the 18th new Stage-C action evaluated in catalog order. Skipping the remaining actions is exact here: once every class is a singleton, no further action can split it. The run evaluated all 16 A actions, all 128 additional B actions, and 18 C actions. It took 21.868 seconds in the recorded local environment. These are exact counts for the stated finite world family and deterministic response semantics, not a claim about other world families.

The [raw NPZ and metadata](runs/20261103T121204Z/metadata.json) and [machine-readable summary](runs/20261103T121204Z/numeric-summary.json) preserve the result. All 30 stage/world terminal survivor counts in the ten-world Exp 01 short run match the corresponding Exp 02 class sizes.
