# Reusable episode tools

`policies.py` chooses actions from the current `OracleState` and available action IDs. `runner.py` runs one episode and records per-step measurements. These modules use the world and oracle contracts in `../core/` without adding experiment-specific conditions.

Keep hidden-world access inside `Environment` and the runner. A policy receives neither `true_world` nor `world_index`. Run Python commands from `src/` and import these tools through `reuse.policies` and `reuse.runner`.
