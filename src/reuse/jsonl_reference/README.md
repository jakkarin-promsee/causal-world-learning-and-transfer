# Original JSONL reference

This folder preserves the runner and policies from the JSONL-backed baseline. Pair them with `core.storage.WorldDataset` and `core.oracle.OnDemandResponseStore`. They retain the same oracle and hidden-world boundary as the numeric path.

The active implementation is `reuse/numeric_engine/`. Numeric-path changes do not require matching edits here. Use this reference for migration comparisons, and update it only when a deliberate comparison needs a shared conceptual change.
