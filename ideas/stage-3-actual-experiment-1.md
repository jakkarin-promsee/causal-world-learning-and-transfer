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

### Document flow

1. [This file](ideas/stage-3-actual-experiment-1), my personal notebook that use to write an ideas or concept. Write the rough detail or skeleton. Use to map everything part together. 
2. `src/experiment/phase-{n}/README.md`, Write the detail for phase N experiment such as what the main experiment do, what is main result that have to read, what is the decision we make, etc. Keep comprehensive, because it's the main document other research will read. (Deeper than this will be artifact for digging, not main thing that have to read).
3. `src/experiment/phase-{n}/track-{n}/README.md`, Write detail what each track discover. Such as having more result graph, experiment detail, More reason for each decision, etc.
4. `src/experiment/phase-{n}/track-{n}/experiment-{n}-control.md`, Full detail of each experiment setting and control, what we think it will be, what we select variable, and how can we read the result, etc.
5. `src/experiment/phase-{n}/track-{n}/experiment-{n}-result.md`, Full detail of each experiment result, the graph read, etc. 

---
## Phase 1: Analyze the base

> I don't train the real model in this phase yet. I want to build the knowledge ground for the random policy, full-candidate greedy information gain policy, and sampled information gain policy first. Then, when the learned model is worse or behaves strangely, I have a baseline that tells me what the problem actually is.

The base world is still fixed at `d=4, m=4`, so:

$$|\Omega|=705,600.$$

This phase has three connected questions:

1. **Track 1:** How many independent hidden worlds do I need for a result with enough statistical precision? (number of episode)
2. **Track 2:** How much quality do I lose when I score only a sample of candidate actions instead of every available action? (number of limit-candidate)
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

How many independently sampled hidden worlds are required before the estimate of my primary metric has small enough uncertainty for the decision I want to make? (number of episode)

This replaces the rough question “How many episodes can I trust?” because trust does not come from one universal number. It comes from defining the estimator, its uncertainty, and the error size I can accept.

### What I want to find

1. Which source is making the result unstable: hidden-world sampling or policy randomness?
2. How fast do the mean and confidence interval stabilize when the number of hidden worlds increases?
3. Can one shared episode count cover all Phase-1 conditions, or do some tracks require a larger count?

(Still working on)

---

## Track 2: Candidate-limit impact on greedy information gain

### Question

What is the smallest candidate set that keeps sampled information gain close enough to the full-candidate one-step greedy policy, while reducing computation enough to be useful? (limit-candidate)

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

### What I want to find

1. What is the smallest candidate number I can use, while still get accurate result information. (I think about 80% variant trust, cause it just use to make dry experiment, before full computation)
2. What is the reliable candidate number I can use? Use for the main number when the experiment is biggest than I can compute. 
3. What is the candidate number behavior when we increase or decrease it? Use for understanding how to interpret the results.

(Still working on)

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

### What I want to find

1. if we increase d or m, can model still working like the same? Or which part that model need to extend?
2. The variant behavior of different episode number still working as a same at d=4 and m=4 at track 1 experiment? 
3. The candidate number behavior still be the same from track 2 experiment?

We didn't full digging all reason behind it. Just want to know can our old setting still work? Or in the future when we move environment, we have to explore these thing again?

(Still working on)

---