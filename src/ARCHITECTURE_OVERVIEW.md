# Architecture overview

This document is the fast index to the current codebase. Read it before changing the core model or writing a new experiment. The central idea is:

> Enumerate a finite set of deterministic Boolean causal worlds, interact with one hidden world through interventions, and use exact Bayesian elimination to keep only the worlds consistent with the observations.

The current reference dataset uses `d=4` exogenous variables, `m=4` endogenous variables, and contains 705,600 possible worlds.

## 1. System at a glance

```text
                          setup, shared across episodes
WorldSpec -> WorldDataset -> ActionCatalog -> OnDemandResponseStore -> ExactOracle
                 |                                                    |
                 | choose one hidden World                            | predict/update
                 v                                                    v
             Environment -------- observation --------> Runner <-> OracleState
                                                            |
                                                            v
                                                          Policy
```

There are three important ownership boundaries:

1. `Environment` alone owns the episode's `true_world`.
2. A `Policy` sees only the current `OracleState` and the action IDs still available. It must never receive the environment, true-world index, or true world.
3. `OracleState.history` is the evidence/source of truth. Its `survivors` mask is a derived cache that can be reconstructed with `ExactOracle.replay()`.

## 2. Mathematical model and naming

`WorldSpec(d, m)` describes a family with:

- exogenous inputs `x_0, ..., x_(d-1)`;
- endogenous variables `y_0, ..., y_(m-1)`;
- one structural rule for each `y_i`.

Variable IDs share one namespace: `x_j` has ID `j`, while `y_i` has ID `d + i`. The parents of `y_i` may be any `x` or an earlier `y`, so its parent pool has size `d + i`. This restriction gives every world a topological order and prevents cycles.

A node rule is one of:

- `AND(a, b)` or `OR(a, b)`, using two distinct parents. Parent order is canonicalized because these operators are commutative.
- `NOT(a)`, using one parent.

For a parent pool of size `k`, the number of rules is `2*C(k, 2) + k = k^2`. Therefore:

```text
|Omega| = product((d + i)^2 for i in 0..m-1)
```

For `d=4, m=4`, this is `16 * 25 * 36 * 49 = 705,600` worlds.

## 3. Data classes and the values they carry

All current data classes are frozen. Treat them as value objects rather than mutable containers.

| Type | Important fields | Meaning |
| --- | --- | --- |
| `NodeRule` | `op`, `parents` | Structural equation for one `y_i`. `parents` contains global variable IDs. |
| `World` | `nodes` | Tuple of `NodeRule`s for `y_0..y_(m-1)` in topological order. |
| `WorldSpec` | `d`, `m` | Shape of the hypothesis family. `parent_pool_size(i)` returns `d+i`. |
| `Intervention` | `x`, `y` | One action. Every `x` is 0/1; each `y` is 0/1 when forced or `None` when its structural equation should run. |
| `Environment` | `true_world`, `spec` | Hidden deterministic system for one episode. `step()` evaluates an intervention. |
| `ActionEntry` | `action_id`, `intervention`, `minimum_stage` | Stable catalog record for one intervention. |
| `Experiment` | `action_id`, `observation_code` | One piece of evidence: the action taken and encoded `Y` outcome observed. |
| `OracleState` | `history`, `survivors` | Dynamic episode state. `survivors[i]` says whether world `i` is still compatible with all history. |
| `OutcomeDistribution` | `counts`, `probabilities` | Posterior-predictive distribution over all `2^m` encoded observations for one action. |
| `EpisodeConfig` | `stage`, `budget`, `seed` | Controlled episode conditions. The runner records `seed`, but policy construction is responsible for actually using it. |
| `StepRecord` | fields described below | Metrics before and after one oracle update. |
| `EpisodeResult` | `world_index`, `policy_name`, `config`, `steps` | Immutable complete result of one episode. |

The most frequently inspected values are:

- `OracleState.history`: tuple of `Experiment`s, length `t`.
- `OracleState.survivors`: read-only Boolean NumPy array aligned with the stable dataset/world order.
- `OracleState.survivor_count`: `|C_t|`, the number of still-compatible worlds.
- `OracleState.timestep`: number of completed experiments.
- `OutcomeDistribution.counts[o]`: number of surviving worlds that would emit observation code `o` for the queried action.
- `OutcomeDistribution.probabilities[o]`: `counts[o] / survivor_count` under the uniform posterior.

`OracleState` and `OutcomeDistribution` defensively copy their arrays and make them read-only. An update returns a new state; it does not mutate an older one.

`StepRecord` stores:

- identity: `timestep`, `action_id`, `observation_code`;
- version-space size: `survivor_count_before`, `survivor_count_after`;
- expected usefulness: `predictive_entropy_bits`;
- outcome-specific quantities: `observed_surprisal_bits` and `realized_information_gain_bits`;
- uncertainty left: `remaining_uncertainty_bits = log2(survivor_count_after)`.

With the current deterministic likelihood and uniform posterior, `observed_surprisal_bits` equals `realized_information_gain_bits` up to floating point error.

## 4. Module map

### `core/types.py` and `core/operators.py`

These define the smallest domain values and Boolean semantics. `Op` is an `IntEnum` (`AND=0`, `OR=1`, `NOT=2`). `arity()`, `apply_operator()`, and `canonicalize_parents()` are the primitive rule operations.

Creating a `World` directly does not fully validate its graph. Call `validate_world()`, or pass it through `Environment`/validated storage.

### `core/worldgen.py`: exact world generation

The name is **worldgen**, not word generation.

- `iter_node_rules(k)` yields all canonical rules for one node in deterministic order: operators first, then lexicographic parent combinations.
- `iter_worlds(spec)` takes the Cartesian product of those per-node rule spaces.
- `world_count(spec)` computes the size without materializing worlds.
- `validate_world(world, spec)` checks node count, arity, parent uniqueness, canonical order, and legal parent range.

Deterministic order matters: every survivor-mask index and every cached response column assumes that repeated iteration yields the same worlds in the same order.

### `core/storage.py`: reusable world datasets

`save_world_dataset()` streams worlds into versioned JSONL shards, optionally gzip-compressed. A record stores each rule as `[operator_integer, parent_1, ...]`. It writes `manifest.json` last; its presence represents a completed dataset.

`WorldDataset` reads the manifest and is re-iterable, which makes it suitable for `OnDemandResponseStore`. Validation is enabled by default. The checked-in `src/worldgen-4-4/` dataset has eight compressed shards and 705,600 worlds.

`src/generate_worlds.py` is the CLI entry point for materializing another dataset.

### `core/evaluator.py`: execution semantics

`evaluate(world, action, spec)` starts a value pool with `action.x`, then walks the world's nodes in topological order. For each `y_i`:

- if `action.y[i] is None`, it evaluates the node's structural rule;
- otherwise, it replaces that rule with the forced value;
- either result is appended to the pool, so downstream nodes see the actual or intervened value.

It returns only `(y_0, ..., y_(m-1))`. `encode_observation()` packs this tuple as an integer with `y_0` as the most-significant bit; `decode_observation()` reverses it. Therefore the oracle has `2^m` possible outcome codes.

`Environment.step()` is the runner's only route to the hidden world's outcome.

### `core/oracle.py`: action space, response cache, and exact inference

#### `ActionCatalog`

The catalog assigns stable contiguous IDs and groups actions by the earliest stage that permits them:

| Stage | Allowed intervention | Total actions | `d=4,m=4` |
| --- | --- | ---: | ---: |
| A | every `do(X)`; no `Y` forced | `2^d` | 16 |
| B | Stage A plus exactly one forced `Y` | `2^d(1+2m)` | 144 |
| C | arbitrary 0/1/`None` pattern over `Y` | `2^d * 3^m` | 1,296 |

Stage-A entries are a prefix of Stage B, and Stage-B entries are a prefix of Stage C. Existing action IDs therefore do not change when a stage expands. Use `action_id_for()`, `entries_for_stage()`, and `validate_for_stage()` rather than rebuilding this mapping elsewhere.

#### `OnDemandResponseStore`

For a requested action, it evaluates that action against every world and creates one response column:

```text
outcomes[action_id][world_index] = encoded observation
```

Only the per-action column is materialized. It is cached and read-only after the first request. The backing world source must be re-iterable with stable ordering. `clear_cache()` drops derived columns without changing inference.

The dtype is the smallest unsigned integer that holds `m` observation bits (`uint8` through `uint64`). With 705,600 worlds and `m=4`, one column is about 0.7 MB and all 16 Stage-A columns are about 11.3 MB.

#### `ExactOracle`

The oracle owns fixed assets (`catalog`, `responses`, `stage`) but no current episode state.

- `initial_state()` returns empty history and an all-true survivor mask.
- `predict(state, action_id)` selects outcomes for surviving worlds, uses `bincount`, and returns their uniform posterior-predictive distribution.
- `update(state, experiment)` intersects the current mask with worlds whose cached outcome matches the observation. It rejects stage-invalid actions, invalid codes, and observations explained by no survivor.
- `replay(history)` rebuilds the state from evidence and is the consistency check for the “history is source of truth” rule.

The inference is exact only for the current assumptions: finite enumerated worlds, uniform prior, and deterministic observations.

### `experiments/policies.py`: action selection

The `Policy` protocol is deliberately small:

```python
choose_action(*, state: OracleState, available_action_ids: Sequence[int]) -> int
```

`RandomPolicy` samples uniformly using its own seeded NumPy generator and ignores posterior evidence.

`GreedyInformationGainPolicy` asks the oracle to predict every candidate's outcome distribution and chooses the action with maximum entropy. In this deterministic, uniform setting, predictive entropy equals expected information gain about the exact world. Ties go to the lowest action ID.

When `candidate_limit=None`, greedy search scores every available action and is exact. A finite limit first samples candidate actions without replacement; its name becomes `sampled_information_gain_N`, and results must be described as sampled/approximate rather than exact greedy information gain.

### `experiments/runner.py`: one episode

`run_episode()` coordinates the objects without leaking the hidden world:

```text
initial OracleState
  -> remove previously used actions
  -> policy.choose_action(state, available IDs)
  -> oracle.predict(state, action)
  -> environment.step(intervention)
  -> encode observation
  -> oracle.update(state, Experiment(...))
  -> record metrics
  -> repeat until budget is exhausted
```

The runner rejects repeated/unavailable policy actions, a budget larger than the stage's distinct action set, mismatched environment/oracle specs, and mismatched config/oracle stages. `world_index` is result metadata; it is never passed to the policy.

## 5. Practical extension guide

- **Add a policy:** implement `name` and `choose_action()`. Keep all evidence in `OracleState`; do not add access to `Environment`.
- **Add an episode metric:** derive it in `run_episode()` from the pre-update prediction and the old/new states, then add it to `StepRecord`.
- **Change the causal language:** start with `Op`, rule generation/counting, evaluation, and validation together. Their contracts must remain consistent.
- **Change the prior or add observation noise:** the Boolean survivor mask is no longer a sufficient posterior representation. This is an inference-model change, not just a new policy.
- **Optimize response computation:** preserve the contract `outcomes_for_action(action_id) -> one outcome per world in stable order` so `ExactOracle` does not need to change.

## 6. Tests as executable contracts

- `tests/test_worldgen.py`: operator behavior, counts, canonical enumeration, and storage round trips.
- `tests/test_evaluator.py`: Stage A/B/C intervention semantics and shape/value validation.
- `tests/test_oracle.py`: action-ID prefixes, encoding, monotone immutable updates, replay, predictive distributions, stage checks, and lazy caching.
- `tests/test_experiment_runner.py`: runner invariants, metrics, reproducible random choice, and greedy policy behavior.

Run commands from `src/` because imports use `core` and `experiments` as top-level packages:

```powershell
python -m unittest discover -s tests -v
```

## 7. Invariants worth protecting

1. World order is stable everywhere: dataset iteration, response columns, and survivor masks must stay aligned.
2. The hidden world never crosses the environment/runner boundary into a policy.
3. History is canonical evidence; survivors and response columns are caches.
4. Oracle updates are monotone: a world can be eliminated but never restored.
5. Action IDs are stable prefixes across stages.
6. “Exact information gain” and “sampled information gain” are not reported as the same method.

