# Reusable episode paths

`numeric_engine/` is the main development path. It stores canonical world rules in numeric `.npy`, computes response columns in NumPy batches, and can persist requested response columns as `.npy` cache files. Its `policies.py` and `runner.py` are the active copies. Top-level `reuse.policies` and `reuse.runner` re-export them for existing imports.

`jsonl_reference/` keeps the earlier runner and policy implementation as a stable comparison reference. Use it with `core.storage.WorldDataset` and `core.oracle.OnDemandResponseStore` over the JSONL dataset. New numeric-path work does not require parallel edits there; update it deliberately only when a reference comparison needs the same conceptual feature.

Both paths use `core.oracle.ExactOracle`, `OracleState`, `Environment`, and stable action IDs. A policy never receives the hidden world or its dataset index.

See [the numeric-path guide](numeric_engine/README.md) for generation, cache use, and validation commands. Run Python commands from `src/`.
