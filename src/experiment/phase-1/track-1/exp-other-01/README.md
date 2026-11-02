# Exp other 01: Cold response-column cost breakdown

This local diagnostic asks where the current CPU implementation spends time when it creates a new response column for the checked-in `d=4, m=4` dataset. It supports planning Track 1 computation and possible cache or evaluator work. It does not run episodes, compare policies, or test GPU speed.

The [local result](LOCAL_RESULT.md) summarizes the first measured run. Its [raw measurements](runs/20261102T074705Z/results.json) and [metadata](runs/20261102T074705Z/metadata.json) identify the action patterns, dataset and code hashes, timing method, and machine software context.

## Method

For each representative action, [the script](benchmark_response_column.py) streams all 705,600 worlds in batches of 4,096. It times dataset iteration separately from `evaluate()` plus `encode_observation()` and writing a `uint8` output column. The read portion includes gzip decompression, JSON parsing, object creation, validation, and batch-list construction. The evaluation portion includes Python loop overhead as well as the Boolean operations, encoding, and array writes. It also times the normal `OnDemandResponseStore` for the Stage-A action and checks that its column exactly matches the instrumented result.

The actions are Stage A with no forced `Y`, Stage B with one forced `Y`, Stage C with two forced `Y`, and Stage C with all four `Y` values forced. The last action is a low-evaluation-cost control; its result is not evidence of useful information gain.

## Run from `src/`

```powershell
python experiment/phase-1/track-1/exp-other-01/benchmark_response_column.py
```

The script creates a new timestamped folder under `runs/` and writes `metadata.json` and `results.json`. Use `--dataset`, `--chunk-size`, or `--output` to change the inputs. The output directory must not already exist.

## Interpretation

These timings partition one instrumented CPU execution path. They do not separate disk latency from gzip/JSON/validation CPU work, and batching changes the timing compared with the normal store. The four actions are representative examples, not a random sample of all 1,296 Stage-C actions. A GPU speedup requires a separate implementation and end-to-end benchmark.
