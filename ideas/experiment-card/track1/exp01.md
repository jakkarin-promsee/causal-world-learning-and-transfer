# Track 1 — Experiment 01: Behavior of Stage A/B/C

## Question

With full-candidate greedy information gain, how does uncertainty change as the action budget is used in Stage A, B, and C? What can we learn by comparing the same hidden worlds at the same action step?

## What I want to find

1. The uncertainty trajectory in each stage, not only its final value.
2. Whether remaining ambiguity comes from stopping before the stage is exhausted or from worlds that no action in that stage can distinguish.
3. How much trajectories vary between hidden worlds, and which paired stage differences deserve a closer look.

## Status

**Draft.** The short run uses 10 sampled hidden worlds. The long run has a planned runtime of about 6 hours; its completed world count and artifact format are not frozen yet.

---
## Base experiment

### Fixed conditions

| Item | Setting |
| --- | --- |
| World family | `d=4, m=4`; 705,600 canonical worlds |
| Policy | Full-candidate greedy information gain (`candidate_limit=None`) in every stage |
| Hidden worlds | The same sampled worlds in A, B, and C within each run; one hidden world is the main unit of analysis |
| Action budget | Each stage's maximum: A = 16, B = 144, C = 1,296 distinct actions |
| Sampling | Randomly choose hidden worlds once per run and save the selected indices; no seed repeats or averaging across repeated samples in Exp 01 |


### Changed condition and tracked axis

- **Changed condition:** Stage A, B, or C, which changes the available actions.
- **Tracked axis:** Action step `t`, starting at `t=0` before any action. Compare stages only at steps they share; read each longer tail within its own stage.

### Measurements

- **Primary:** $U_{i,s,t}=\log_2|C_{i,s,t}|$, where $C_{i,s,t}$ is the survivor set for hidden world `i`, stage `s`, after `t` actions.
- **Rescaled view:** $U^{\mathrm{norm}}_{i,s,t}=U_{i,s,t}/\log_2|\Omega|$. Because the world family is fixed here, this has the same shape as $U$.
- **Between-world spread at each stage and step:** Summarize how far individual $U_{i,s,t}$ values lie from their stage-step mean. Choose a readable summary after the pilot; the definition is below.

### Read the result

1. Plot $U$ against action step for each hidden world, grouped by stage. Inspect A/B/C on the **same world at the same step**.
2. Plot the mean trajectory for each stage with a view of between-world spread. Use the normalized scale only when it helps presentation or comparison with a later world family.
3. Check terminal survivor counts and selected action traces for plateaus, striking paired differences, and unusual worlds. Record an explanation only after checking the trace; a curve alone does not identify the cause.

### Two runs of the same base experiment

| Run | Hidden worlds | Main use |
| --- | ---: | --- |
| `exp-01-short` | 10 randomly sampled worlds | Get complete raw episodes quickly; inspect trajectories and traces while the long run is running. Treat interpretations as exploratory. |
| `exp-01-long` | More worlds; completed count determined by an approximately 6-hour run | Run the same stages, policy, budgets, and measurements on a larger sample for aggregate analysis and Track-2 precision analysis. |

Only the number of sampled worlds and the emphasis of the later analysis differ. Both runs save the same kind of full result, so either can be replotted or analyzed again.

## Details for running and interpretation

### Sampling and raw records

For each run, randomly select its hidden worlds once and save the actual world indices. Exp 01 does not require a world-sampling seed or repeated draws to average: the saved indices identify exactly which worlds were measured. Use each run's same indices in A, B, and C, and keep them in result metadata, never in policy input. Full-candidate greedy is deterministic on a given world, so policy seed repeats add no new result. Use Track 2 to evaluate how precise the long-run aggregate estimates are; do not count the 10 short-run worlds as repeated estimates of those aggregates.

For `exp-01-long`, save a randomly selected world order before execution, then complete A, B, and C for one world before moving to the next. Checkpoint the raw result after each completed world. Use about 6 hours as a runtime cap and stop between worlds, so every retained world has a paired A/B/C result. Report the actual runtime and number of completed worlds; the time cap does not define a fixed episode count.

The experiment runner should write a reusable raw artifact, such as `.npz` or another lossless format with a documented schema, rather than only a final plot. For every executed step, save the stage, hidden-world index in metadata, action ID and intervention, observation, survivor counts before and after, predictive entropy, realized information gain, and remaining uncertainty. Record the run name, dataset identity, code version, policy, candidate limit, budget, sampling method, and selected indices with the raw result. Plotting and analysis read that artifact later without rerunning the oracle.

### Reuse in Track 2

Track 2 can read the completed `exp-01-long` worlds in their saved random order and examine how estimates change with the number of worlds, without rerunning the oracle. Use hidden worlds, not action steps, as the independent units. Check precision for a named target such as the mean $U$ at a selected step or a paired A/B/C difference, and decide what interval width would be acceptable before calling an episode count sufficient. Choosing that count from this same result is exploratory; check it on a later independent world sample before treating it as a confirmed rule.

### What a plateau means

- **Exact identification:** $|C_t|=1$, so $U_t=0$.
- **Stage-level observational equivalence:** $|C_t|>1$, but every remaining permitted action gives the same outcome for all survivors. The positive $U_t$ cannot fall further in that stage.

For full-candidate greedy, a zero maximum predictive entropy over **all remaining actions** can certify the second case; checking only the chosen action is insufficient without that maximum guarantee. An early stop at either proven terminal case may extend the constant $U$ value through the stage's maximum step for plotting. Mark those later points as **inferred**, separate from actions actually executed, and record the terminal reason and survivor count. The specialized `run_full_candidate_greedy_episode()` supports this; ordinary `run_episode()` runs its configured budget.

### Between-world spread

At stage `s` and step `t`, compute $\bar U_{s,t}=\frac{1}{N}\sum_i U_{i,s,t}$ and $e_{i,s,t}=U_{i,s,t}-\bar U_{s,t}$. A possible spread summary is $\mathrm{MAE}_{s,t}=\frac{1}{N}\sum_i|e_{i,s,t}|$; another is the sample standard deviation $\sqrt{\frac{1}{N-1}\sum_i e_{i,s,t}^2}$ for `N > 1`. These describe **differences between worlds**, not the uncertainty of the estimated mean. Pick the display after the pilot instead of reporting both by default. Timesteps from one episode are not independent worlds.

### Limits of the comparison

Full-candidate greedy chooses the best expected information gain for **one step** among the available actions; it does not guarantee the best complete action sequence. The stages change the action set while the policy rule and hidden-world sample stay fixed. A stage difference therefore does not, by itself, tell us whether a particular action type, greedy choice, or world property produced it. Track 2 checks sampling precision before a population-level claim; Track 3 later compares sampled information gain with this full-candidate reference on matched worlds and steps where feasible.

The older Track-0 estimate of roughly 4–5 hours for all Stage-C response columns applied to the JSONL path. The [numeric-engine benchmark](../../../src/experiment/phase-1/track-1/exp-other-02/LOCAL_RESULT.md) measured one full-candidate Stage-C episode at 46.01 seconds with an initially empty response cache and a second episode at 9.79 seconds with columns cached. Those timings come from two particular worlds, so use the pilot's actual step counts and cache conditions to plan the main run.
