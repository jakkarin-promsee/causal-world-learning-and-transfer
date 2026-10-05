> This draft is about the actual experiment work: how I control the experiment, save the raw result, read it, interpret it, and use it to decide the next step. I still keep this as a working scratch book. The detail will be frozen one track at a time before I run the expensive experiment.

## Experiment hierarchy definition

1. **Phase** = one scope of research work. A phase should end with some new knowledge or a decision about the next phase.
2. **Track** = one main question inside the phase. Each track can have more than one experiment if the question needs different views.
3. **Experiment** = one reproducible study design. It defines the conditions, controls, sampling, metrics, and decision rule. An experiment is not equal to one Python file.
4. **Condition** = one fixed combination such as stage, policy, budget, and candidate limit.
5. **Replicate / run** = one repeat of a condition under a controlled seed.
6. **Episode** = one hidden world and one complete interaction until the action budget is used.
7. **Step** = one `(action, observation, oracle update)` inside an episode.

One experiment may use several files, but each file should still do only one job. For example:

1. `exp_001_run.py` runs the frozen conditions and saves raw `.jsonl` results.
2. `exp_001_analyze.py` reads the raw result and creates summary tables.
3. `exp_001_plot.py` reads the same result and creates `.png` graphs.

The scientific experiment is `exp_001`. Those Python files are just its runner and analysis tools.

### Experiment rule

1. Every experiment must have one clear question and one forward direction. I should know what decision the result will support before I start the full run.
2. The config is frozen before the final run. Running with the same code, dataset, config, and seed schedule must reproduce the same scientific result. Runtime itself may still change between machines or cache states.
3. One fixed seed is not enough. I will use a recorded seed schedule so the stochastic policy is reproducible while I can still measure its variance.
4. Save the raw result in a format that can be analyzed again without rerunning the expensive oracle. Derived tables and graphs must be rebuildable from the raw result.
5. Do not silently overwrite an old result. Each output must identify its experiment, condition, dataset, config, and code version.
6. A pilot run is allowed to change the design. After the pilot, I freeze the final conditions and do not tune them from the final result.
7. Exact inference, full-candidate greedy policy, and sampled greedy policy are different things. I must not use the word “exact” for all of them as if they are the same guarantee.

## Phase 1: Analyze the base

> I don't train the real model in this phase yet. I want to build the knowledge ground for the random policy, full-candidate greedy information gain policy, and sampled information gain policy first. Then, when the learned model is worse or behaves strangely, I have a baseline that tells me what the problem actually is.

The base world is still `d=4, m=4`, so:

$$|\Omega|=705,600.$$

This phase has three connected questions:

1. **Track 1:** How many independent hidden worlds do I need for a result with enough statistical precision?
2. **Track 2:** How much quality do I lose when I score only a sample of candidate actions instead of every available action?
3. **Track 3:** When `d` or `m` changes, which part of the problem becomes harder: the world space, action space, identifiability, or computation?

The dependency is:

```text
Track 1 pilot
  -> freeze the episode count / precision rule
  -> Track 2 selects a useful candidate-limit setting
  -> Track 3 uses only the selected settings for a small scaling pilot
```

Track 1 does not need to discover one magical episode count for every future experiment. The required count may be different across metrics and conditions. If I want one shared count for convenience, I will select it from the hardest or most variable representative condition.

### Shared contract for all tracks

#### Population and sampling unit

The default population is the raw canonical worlds in $\Omega$, under the uniform prior already used by the exact oracle. A hidden world is the outer sampling unit.

This choice means a large observational equivalence class receives more weight when it contains more raw structural worlds. If I later want every equivalence class to receive equal weight, that is a different experiment and must be named explicitly.

For a stochastic policy, policy seeds are inner repeats of the same hidden world. Several seeds on one world are useful for measuring policy randomness, but they are not several independent worlds.

#### Pairing and controls

- Compare policies and candidate limits on the same hidden-world set whenever possible.
- Keep stage, action budget, world set, and query definition fixed inside one comparison.
- Do not expose `true_world` or `world_index` to a policy.
- Do not repeat an action inside one episode, following the current runner contract.
- Record the policy seed separately from the hidden-world index.

#### Main measurements

The main uncertainty measurement is:

$$U_t = \log_2 |C_t|.$$

This is easier to compare than the raw survivor count because the world count is large and the distribution may be heavily skewed. When comparing different world sizes, also use:

$$U_t^{norm}=\frac{\log_2 |C_t|}{\log_2 |\Omega|}.$$

Other measurements can include:

- realized information gain at each step;
- predictive entropy of the selected action;
- cumulative information gain after budget $T$;
- final survivor count and probability of exact identification;
- number of response columns computed;
- cold-cache and warm-cache runtime;
- approximate response-cache memory.

The final report should not treat every timestep as an independent sample. The episode or hidden world is still the main unit of analysis.

#### Result artifacts

Every raw result should keep enough metadata to reconstruct its condition:

- experiment and condition ID;
- `d`, `m`, stage, action budget, and action-space size;
- policy name and candidate limit;
- hidden-world index and sampling method;
- policy seed and seed schedule version;
- dataset identity;
- code version;
- one `StepRecord`-like record for every step;
- cache mode and timing method when computation is measured.

---

## Track 1: Number of episodes and result precision

### Question

How many independently sampled hidden worlds are required before the estimate of my primary metric has small enough uncertainty for the decision I want to make?

This replaces the rough question “How many episodes can I trust?” because trust does not come from one universal number. It comes from defining the estimator, its uncertainty, and the error size I can accept.

### What I want to learn

1. Which source is making the result unstable: hidden-world sampling or policy randomness?
2. How fast do the mean and confidence interval stabilize when the number of hidden worlds increases?
3. Can one shared episode count cover all Phase-1 conditions, or do some tracks require a larger count?

### Track 1A: Freeze the estimand

Before the pilot, define:

- primary endpoint: **TODO**, probably final $U_T=\log_2|C_T|$;
- secondary endpoints: **TODO**, such as cumulative information gain and exact identification rate;
- action budget $T$: **TODO**;
- representative stages and policies: **TODO**;
- confidence level: **TODO**, probably 95%;
- acceptable confidence-interval width or Monte Carlo error: **TODO**.

The acceptable width must be stated in the unit of the metric, such as bits of remaining uncertainty. I should not choose it only because one graph looks stable.

### Track 1B: Pilot variance run

1. Select a reproducible pilot set of hidden worlds.
2. Run representative deterministic and stochastic policies.
3. For stochastic policies, run several policy seeds on each world.
4. Separate variation across worlds from variation across policy seeds.
5. Inspect the distribution of $U_T$, not only its mean.
6. Check whether a few hard worlds dominate the variance.

The full-candidate greedy policy is deterministic after the world/history is fixed because its tie-break uses the lowest action ID. Random and sampled policies have an additional RNG source.

### Track 1C: Convergence analysis

For an increasing number of hidden worlds $N$:

1. compute the estimate of the primary endpoint;
2. compute an uncertainty interval by resampling hidden worlds, not individual timesteps;
3. plot the estimate and interval width against $N$;
4. repeat this for the representative conditions;
5. check whether the conclusion between policies changes as $N$ increases.

If several seeds exist for one world, either summarize them within the world first or use a grouped/hierarchical resampling method. Do not pretend they are independent worlds.

### Track 1D: Freeze the final episode count

Select the smallest $N$ that meets the previously defined precision rule. Then:

- round it upward to a convenient number;
- record whether it is a per-condition count or one shared worst-case count;
- freeze the world-sampling seed/list for paired experiments;
- keep pilot results separate from the final Phase-1 comparison.

### Output

- raw pilot episode records;
- convergence table for each candidate $N$;
- estimate-versus-$N$ graph with uncertainty bands;
- variance split between worlds and policy seeds;
- one written decision: the frozen episode count and why it is enough.

---

## Track 2: Candidate-limit impact on greedy information gain

### Question

What is the smallest candidate set that keeps sampled information gain close enough to the full-candidate one-step greedy policy, while reducing computation enough to be useful?

The reference policy searches all available actions at the current step. It is an exact greedy choice for that step, but it is **not** a globally optimal plan over the whole action budget.

### Why this track exists

For a response column that is not cached yet, the main computation is closer to:

$$\text{new candidate actions}\times|\Omega|\times \text{world evaluation cost},$$

not only:

$$\text{action budget}\times|\Omega|.$$

For `d=4,m=4`, the total action counts are:

| Stage | Available actions |
| --- | ---: |
| A | 16 |
| B | 144 |
| C | 1,296 |

Full Stage C may compute about 914 million world-action outcomes and keep about 0.91 GB of `uint8` response columns. So Stage C must pass a feasibility check before I promise a full reference sweep.

### Candidate-limit design

Candidate limits should include:

- very small absolute limits;
- several fractions of the current available action set;
- the full available action set as the reference where feasible.

The exact grid is **TODO after a small timing pilot**. The same absolute limit does not mean the same approximation level across stages. For example, 16 is the full Stage-A space but only a small part of Stage C.

Record the actual number of candidates scored at every step because the number of unused actions decreases throughout the episode.

### Track 2A: One-step approximation quality

Give sampled and full-candidate evaluation the same `OracleState`. Then measure:

1. whether sampled greedy selects the same action as full greedy;
2. predictive entropy of the selected action;
3. one-step entropy regret:

$$R_t=\max_{a\in A_t}H(O\mid H_t,a) -H(O\mid H_t,a_t^{sampled});$$

4. how regret changes with stage, timestep, survivor count, and candidate limit;
5. variation across candidate-sampling seeds.

The shared states should come from more than one trajectory type, such as full greedy, sampled greedy, and random trajectories. Otherwise I may only learn how the approximation behaves on states created by one policy.

### Track 2B: Whole-episode consequence

Run complete rollouts for every candidate-limit condition on the same hidden worlds and budgets. Compare:

- final $U_T$ and normalized $U_T^{norm}$;
- cumulative/realized information gain;
- uncertainty curve across steps;
- exact-identification rate when it is possible;
- paired difference from full greedy on each hidden world.

A sampled rollout changes the next state, so it can no longer be compared to full greedy action-by-action as if both histories were the same. That is why the one-step study and whole-episode study are separate.

Random policy is a sanity-floor baseline, not the definition of candidate approximation quality. In Stage C, random policy may sample many actions that force several or all `Y` values and contain little information. Record the number of intervened `Y` variables so this action-space dilution is visible.

### Track 2C: Computational consequence

Measure quality and computation separately. At least record:

- total runtime and per-step runtime;
- number of unique response columns computed;
- number of candidate predictions;
- approximate cache memory;
- cold-cache versus warm-cache condition.

For a cold-cache comparison, each condition needs a fresh response cache or an explicit `clear_cache()`. For a warm-cache comparison, precomputation and cache reuse must be declared. Running conditions in different orders must not make one policy look faster only because a previous policy prepared its columns.

### Track 2D: Select the working candidate limit

Before the final run, define **TODO** thresholds such as:

- maximum acceptable paired loss in final uncertainty;
- maximum acceptable one-step entropy regret;
- minimum compute or memory reduction.

Select the smallest candidate limit that satisfies the quality threshold with its uncertainty interval, not only the one with the best point estimate.

The selected limit can be different by stage. If full Stage C is not feasible, first validate the method on smaller worlds and clearly label the Stage-C result as comparison against the largest feasible reference, not against full greedy.

### Output

- one-step action-match and entropy-regret tables;
- whole-episode paired performance curves;
- quality-versus-candidate-limit graph;
- runtime/cache-versus-candidate-limit graph;
- one selected candidate-limit rule for each stage;
- written limitations when a full reference is computationally unavailable.

---

## Track 3: Impact of world size

### Question

When I change `d` or `m` one at a time, how do hypothesis-space size, action-space size, identifiability, information per action, and computation change?

This replaces the rough question “What world behavior changes?” because world size is not one variable. Increasing `d` and increasing `m` change different parts of the system.

### Scope of this track

The main project still uses `d=4,m=4`. Track 3 is only a small scaling pilot to check whether this base case behaves like a useful middle point. It is not yet a full scaling law study.

Do not combine every `(d,m)` value, every stage, and every candidate limit. That would confound the result and make the compute grid explode. Track 3 should use:

- one-factor-at-a-time changes around the base case;
- a small feasible `(d,m)` grid;
- full greedy only where it is computationally possible;
- one or a few sampled settings selected from Track 2;
- the episode-count rule from Track 1.

The exact grid is **TODO after the analytic and memory feasibility table**.

### Track 3A: Analytic feasibility map

For every proposed `(d,m)` condition, compute without running episodes:

1. world count:

$$|\Omega_{d,m}|=\prod_{i=0}^{m-1}(d+i)^2;$$

2. action counts:

$$|A_A|=2^d,$$

$$|A_B|=2^d(1+2m),$$

$$|A_C|=2^d3^m;$$

3. initial uncertainty $\log_2|\Omega|$;
4. maximum observation-code size $2^m$;
5. estimated response-column memory;
6. estimated full-policy computation.

Use this table as a go/no-go gate. For example, the world space already grows from 705,600 at `d=4,m=4` to 45,158,400 at `d=4,m=5`, so “only one more node” is not a small experiment.

### Track 3B: Static world/action characterization

Before sequential policy comparison, measure what can be understood without a rollout:

- distribution of prior predictive entropy across actions;
- proportion of zero-information or low-information actions;
- distribution of observational equivalence-class sizes where feasible;
- irreducible survivor floor after the full permitted action set where feasible;
- difference between stages and between numbers of intervened `Y` variables.

This part helps separate “the policy failed” from “the action set cannot identify the world anyway.”

### Track 3C: Sequential scaling pilot

For each feasible world condition:

1. sample hidden worlds with a recorded rule;
2. run the frozen budget and policy conditions;
3. compare both raw and normalized uncertainty;
4. record information gain per action;
5. record runtime, new response columns, and cache memory;
6. compare the curve when changing `d` while keeping `m` fixed;
7. compare the curve when changing `m` while keeping `d` fixed.

Keep the action budget fixed if the question is “What can be learned with the same interaction budget?” If I later scale the budget with action-space or world-space size, that is a second named comparison, not something mixed into the first one.

### Track 3D: Interpret the source of scaling difficulty

For every observed degradation, ask which mechanism explains it:

- larger initial hypothesis uncertainty;
- more available actions to search;
- more observation bits per step;
- larger equivalence classes;
- candidate sampling becoming a smaller fraction of the action set;
- response generation and memory becoming the bottleneck.

The output should not only say that a bigger world is slower or harder. It should identify which dimension causes the change and whether that matters for the future learned model.

### Output

- analytic feasibility table for the proposed `(d,m)` grid;
- static action/equivalence characterization where feasible;
- normalized uncertainty and information-gain curves;
- runtime and memory scaling curves;
- one decision about whether `d=4,m=4` stays as the main base case;
- a short list of conditions that are safe and meaningful for Phase 2.

---

## Phase 1 completion condition

I can close Phase 1 when I have:

1. a justified episode-count rule, not only a guessed number;
2. a measured relation between candidate limit, information quality, and computation;
3. a small scaling map that separates world-space, action-space, identifiability, and compute effects;
4. reproducible raw results that can be analyzed again without rerunning the oracle;
5. a written decision about which baseline conditions the first learned model must beat.

The goal of this phase is not to claim that one policy solves the whole problem. It is to know the ground well enough that the next model experiment has a fair baseline, a realistic compute budget, and a result I can actually interpret.
