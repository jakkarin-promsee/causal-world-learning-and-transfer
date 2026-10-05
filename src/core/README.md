# Core data pipeline

The first exact-oracle implementation has one rule: **history is evidence;
survivors are a derived cache**.

```text
Environment -- observation --> Runner -- Experiment --> ExactOracle
     |                          |                         |
 true_world                current state            static assets
 WorldSpec                 agent/policy             ActionCatalog
                                                     ResponseStore

OracleState
  history:   H_t = ((action_id, observation_code), ...)
  survivors: C_t = boolean mask over Omega
```

## Ownership

- `types.py`, `operators.py`, `worldgen.py`: define the fixed world family.
- `evaluator.py`: evaluates a world and contains `Environment`, the only object
  that owns the episode's `true_world`.
- `oracle_state.py`: contains only per-episode dynamic values (`H_t`, `C_t`).
- `oracle.py`: contains the stable action catalog, lazy response computation,
  prediction, update, and replay logic. `ExactOracle` has no current state.
- the future runner owns `environment`, `oracle`, and the current
  `oracle_state`. It should not copy history or survivor data elsewhere.

## One episode, without an agent yet

This is the complete runner-side flow. A future policy only replaces the line
that chooses `action_id`.

```python
from core.evaluator import Environment, encode_observation
from core.oracle import ActionCatalog, ExactOracle, OnDemandResponseStore, Stage
from core.oracle_state import Experiment
from core.storage import WorldDataset

dataset = WorldDataset("worldgen-4-4")
catalog = ActionCatalog(dataset.spec)
responses = OnDemandResponseStore(dataset, len(dataset), catalog)
oracle = ExactOracle(catalog, responses, stage=Stage.A)

# Only the runner/environment boundary knows the true world.
true_world = next(iter(dataset))
environment = Environment(true_world, dataset.spec)
oracle_state = oracle.initial_state()

for action_id in (0, 1, 2):  # later: policy.choose_action(...)
    action = catalog[action_id].intervention
    observation = environment.step(action)
    experiment = Experiment(
        action_id=action_id,
        observation_code=encode_observation(observation, dataset.spec),
    )
    oracle_state = oracle.update(oracle_state, experiment)

distribution = oracle.predict(oracle_state, action_id=3)
assert oracle.replay(oracle_state.history).survivor_count == \
    oracle_state.survivor_count
```

## Capacity and intentional limits

For `d=4, m=4`:

- `OracleState.survivors` uses 705,600 NumPy booleans, about 0.7 MB.
- one cached response column uses 705,600 `uint8` values, about 0.7 MB.
- all 16 Stage-A response columns therefore use about 11.3 MB.
- response columns are computed only on first use and can be dropped with
  `responses.clear_cache()`.

The current version intentionally does **not** implement a precomputed matrix,
memmap, checkpoints, episode logs, batching, or a generic runner framework.
Those become useful only after the first policy/experiment loop reveals an
actual bottleneck.
