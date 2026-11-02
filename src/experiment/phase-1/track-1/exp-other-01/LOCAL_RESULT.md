# Local result: Cold response-column breakdown (2 November 2026, Bangkok)

On the checked-in `d=4, m=4` dataset of 705,600 worlds, the instrumented CPU run spent **10.78–12.23 seconds per column reading, decoding, and validating the dataset**, versus **2.35–7.08 seconds evaluating, encoding, and storing outcomes** for the four tested actions. Dataset preparation was the larger measured component in every tested condition. This does **not** show that disk I/O alone is the bottleneck: gzip decompression, JSON parsing, world construction, validation, and batch-list creation are included in the first number.

| Representative action | Stage | Action ID | Read/decode/validate | Evaluate/encode/store | Total instrumented wall time | Read share |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| No `Y` forced | A | 0 | 12.23 s | 7.08 s | 19.31 s | 63% |
| One `Y` forced | B | 17 | 10.88 s | 5.57 s | 16.45 s | 66% |
| Two `Y` forced | C | 198 | 10.91 s | 4.45 s | 15.36 s | 71% |
| All four `Y` forced | C | 215 | 10.78 s | 2.35 s | 13.13 s | 82% |

The normal `OnDemandResponseStore` built the Stage-A action-0 column in **16.28 s**. The instrumented version took **19.31 s** and produced an exactly matching column. The 3.02 s difference shows that batching and instrumentation affect absolute timing; use the table to locate work within this measured path, not to replace Track-0 production timing estimates. Whole-pass process CPU time was close to wall time (13.05–18.91 s versus 13.13–19.31 s), consistent with substantial CPU work, but this run does not isolate the individual costs of decompression, JSON parsing, and validation.

## What this means for optimization

Moving only `evaluate()` to PyTorch/CUDA cannot remove the measured dataset-preparation time. A faster response builder would need to avoid repeatedly decoding and validating the same 705,600 worlds for each action, for example by preparing a compact numeric world representation once, then evaluating actions in batches. That is a proposed direction, **not a measured speedup**. A persistent response cache would avoid rebuilding a column altogether on later runs.

The all-forced Stage-C action is included to show the lower evaluation cost when structural rules are bypassed. It is not a useful greedy candidate. No full Stage-C sweep, GPU implementation, or policy episode was run here.

## Evidence and limits

- [Raw measurements](runs/20261102T074705Z/results.json) include each action's intervention, component times, process CPU time, column size, and response hash.
- [Metadata](runs/20261102T074705Z/metadata.json) records Python 3.11.0, NumPy 2.3.5, the CPU compute device, batch size 4,096, Git revision, and SHA-256 hashes for the dataset and relevant code.
- [Benchmark code](benchmark_response_column.py) creates a new run folder and does not change core inference or response-cache behavior.
- This was one local pass per action on one machine. Timing can change with filesystem cache, power mode, concurrent processes, and the chosen action. The measured fraction should not be projected onto every Stage-C action without more sampling.
