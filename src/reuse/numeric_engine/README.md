# Primary numeric-world path

`worlds.npy` is the primary world dataset. Its rows follow `core.worldgen.iter_worlds()` exactly, and each of the `m` rules has three `uint8` fields: operator, first parent, second parent. A `NOT` rule uses 255 as the unused second-parent marker. The `d=4,m=4` file is about 8.08 MiB. The dataset manifest stores the array hash and is written last.

Generate a new dataset from `src/`:

```powershell
python -m reuse.numeric_engine.generate_worlds dataset/worldgen-4-4-npy
```

The output directory must be new or empty. `dataset/worldgen-4-4-npy/` is generated locally and ignored by Git, so run this command once after cloning. The checked-in JSONL source remains under `dataset/worldgen-4-4/` for the `reuse.jsonl_reference` path.

Use numeric worlds with the unchanged oracle and active runner:

```python
from core.evaluator import Environment
from core.oracle import ActionCatalog, ExactOracle, Stage
from reuse import NumericResponseStore, NumericWorldDataset
from reuse.runner import EpisodeConfig, run_full_candidate_greedy_episode

worlds = NumericWorldDataset("dataset/worldgen-4-4-npy")
catalog = ActionCatalog(worlds.spec)
responses = NumericResponseStore(worlds, catalog, cache_dir="dataset/response-cache-4-4-verified")
oracle = ExactOracle(catalog, responses, stage=Stage.A)
result = run_full_candidate_greedy_episode(
    world_index=0,
    environment=Environment(worlds.world_at(0), worlds.spec),
    oracle=oracle,
    config=EpisodeConfig(stage=Stage.A, budget=16, seed=0),
)
```

`NumericResponseStore` computes a column only when requested and keeps it in process memory. If `cache_dir` is given, it saves each column as a separate `.npy` with a SHA-256 checksum and reloads it on later runs. The cache manifest binds the world file hash, action catalog, dtype, and response logic. A mismatch or modified column raises an error instead of using stale responses; after changing response logic, choose a new empty cache directory. If `cache_dir` is omitted, response columns are cached only in memory.

World rules are always prerendered. Response columns are intentionally on demand; precomputing every Stage-C action is not required. For `d=4,m=4`, one response column has 705,600 `uint8` values (about 0.67 MiB), while all 1,296 Stage-C columns would occupy about 872 MiB before file headers.

The world-rule file stays compact as `d,m` increase, but the number of worlds and possible actions grows quickly. For example, `d=4,m=5` would have 45,158,400 worlds, about 646 MiB of numeric rules, and about 163.5 GiB if all 3,888 Stage-C response columns were materialized. Keep response caching on demand when exploring larger world families.

The `jsonl_reference/` path is a reference, not a second development target. The numeric path is checked against it on all actions in a small world family and on representative actions of the full `d=4,m=4` dataset. Run the regression suite from `src/` with `python -m unittest discover -s tests -v`.

In a local migration check on 2 November 2026, the numeric path's four representative columns (action IDs 0, 17, 198, and 215) matched the response hashes from the earlier [JSONL diagnostic](../../experiment/phase-1/track-1/exp-other-01/LOCAL_RESULT.md). Their first numeric computations took 0.053, 0.043, 0.039, and 0.013 seconds respectively on this computer. These are single measurements, not a complete Stage-C benchmark; cache state, chunk size, and machine load can change timing.
