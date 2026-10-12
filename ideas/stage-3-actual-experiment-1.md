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

1. [This file](stage-3-actual-experiment-1.md), my personal notebook that use to write an ideas or concept. Write the rough detail or skeleton. Use to map everything part together.
2. `src/experiment/phase-{n}/README.md`, Write the detail for phase N experiment such as what the main experiment do, what is main result that have to read, what is the decision we make, etc. Keep comprehensive, because it's the main document other research will read. (Deeper than this will be artifact for digging, not main thing that have to read).
3. `src/experiment/phase-{n}/track-{n}/README.md`, Write detail what each track discover. Such as having more result graph, experiment detail, More reason for each decision, etc.
4. `src/experiment/phase-{n}/track-{n}/experiment-{n}-control.md`, Full detail of each experiment setting and control, what we think it will be, what we select variable, and how can we read the result, etc.
5. `src/experiment/phase-{n}/track-{n}/experiment-{n}-result.md`, Full detail of each experiment result, the graph read, etc. 

---
## Phase 1: Understand the base and what I can compare

> I don't touch the real model in this phase yet. I want to see what the random policy, full-candidate greedy information gain policy, and sampled information gain policy actually do in each stage. More importantly, I want to know which measurements are reliable enough to compare, and where the comparison would fool me. This phase should give me a trustworthy ground to stand on before I work on the model.

The base world is still fixed at `d=4, m=4`, so:

$$|\Omega|=705,600.$$

Before the four questions, **Track 0** measures what my own computer can actually run. This is a local computation benchmark for planning, not evidence that a stage or a policy is better. I want detailed logs so a future agent can look up the time and memory cost instead of guessing from an action count alone.

This phase has four connected questions:

1. **Track 1:** What does the behavior of Stage A, B, and C look like, and which differences between them can I meaningfully compare?
2. **Track 2:** How many independent hidden worlds do I need before those measurements have enough statistical precision? (number of episode)
3. **Track 3:** How much quality do I lose when I score only a sample of candidate actions instead of every available action? (number of limit-candidate)
4. **Track 4:** When `d` or `m` changes a little, do the baseline behavior and my measurement choices still make sense?

The dependency is:

```text
Track 0: measure local runtime, RAM, response-cache cost, and GPU memory context
  -> Track 1: look at a few episode traces to learn what I should measure
  -> Track 2: find how many independent worlds I need to trust the comparison
  -> return to Track 1: compare stage behavior with enough worlds
  -> Track 3: check the quality / computation tradeoff of sampled information gain
  -> Track 4: make a small check around d=4, m=4
```

One episode is useful for seeing what happens step by step, but it cannot tell me what a whole stage usually does. I will use the first look to shape the question, then use Track 2 before making a stage-level conclusion.

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

## Track 0: My computer's computation cost

### Question

How long does the current baseline actually take on my machine when I change stage, candidate limit, action budget, and number of episodes? Where does the time go, and when does the response cache or RAM become the limit?

### What I want to find

1. Time for a new response column, one policy choice, one episode, and a small set of episodes, with cold and reused cache separated.
2. How process RAM and response-cache memory grow across the practical workloads I may use in Tracks 1–4.
3. What hardware, software, dataset, code version, and power state produced each measurement, so a future agent can judge whether the old timing still applies.
4. What the GPU VRAM looks like on this computer, while being clear that the current oracle and policy implementation uses the CPU and does not benchmark GPU computation.

I don't need to run every possible condition just because my computer is idle. First measure a small workload, then extend to the expensive cases that will actually help me plan. Keep raw logs and a readable summary together. A runtime extrapolation is only an estimate until I run that condition.

### Key insight I found

1. On my computer with `d=4,m=4`, creating one new response column usually took about **11–14 seconds** in the measured conditions. The standard benchmark finished 9 conditions in **22 minutes 32 seconds**. This is a local computation result, not a stage or policy quality result.
2. The response cache changes runtime a lot. Stage-A full-candidate greedy took **219.24 seconds** in its first episode while building all 16 columns, then **0.068 seconds** in the next episode with those columns cached. So I should estimate future runtime from how many *new* columns a run needs, not just its stage, candidate limit, or episode count.
3. These runs used the CPU; the GPU VRAM log is only machine context. Full-candidate Stage C was **not run**. Its roughly **4–5 hour** runtime and **872 MiB** column-cache size are extrapolations, not measurements. The short result and links to raw logs are in [Track-0 local results](../src/experiment/phase-1/track-0/LOCAL_RESULTS.md).

---

## Track 1: Behavior of Stage A, B, and C

### Question

When I give the policies a limited action budget, how does uncertainty change in each stage? Are the differences coming from what actions the stage allows, from which actions the policy chooses, or just from the worlds I happened to sample?

### What I want to find

1. What does the uncertainty trajectory look like for each stage, not only the final number?
2. Is a world still ambiguous because I have not used enough actions, or because that stage cannot distinguish it even with all its available actions?
3. Which stage comparisons look meaningful at the same budget and on the same hidden worlds? Which ones need more care before I read them as a real difference?

At first I can inspect only a few episodes to understand the behavior. That is exploration, not yet evidence that one stage is generally better. I will come back to this question after Track 2 tells me how precise the comparison is.

---

## Track 2: Number of episodes and result precision

### Question

How many independently sampled hidden worlds are required before the estimate of my primary metric has small enough uncertainty for the decision I want to make? (number of episode)

This replaces the rough question “How many episodes can I trust?” because trust does not come from one universal number. It comes from defining the estimator, its uncertainty, and the error size I can accept. This track is here to support the comparisons in the other tracks, not to find a magic episode count by itself.

### What I want to find

1. Which source is making the result unstable: hidden-world sampling or policy randomness?
2. How fast do the mean and confidence interval stabilize when the number of hidden worlds increases?
3. Can one shared episode count cover all Phase-1 conditions, or do some tracks require a larger count?

If I want one shared count for convenience, I will select it from the hardest or most variable representative condition.

(Still working on)

---

## Track 3: Candidate-limit impact on greedy information gain

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

1. What is a small candidate number that is useful for a rough exploration before the full computation?
2. What is a reliable candidate number for a main comparison when scoring every action is too expensive?
3. What is the candidate number behavior when we increase or decrease it? Use for understanding how to interpret the results.

(Still working on)

---

## Track 4: Check beyond the base world size

### Question

When I change `d` or `m` one at a time, do the baseline behavior and the measurement choices from the base world still make sense? Which part changes first: hypothesis-space size, action-space size, identifiability, information per action, or computation?

This replaces the rough question “What world behavior changes?” because world size is not one variable. Increasing `d` and increasing `m` change different parts of the system.

### Scope of this track

The main project still uses `d=4,m=4`. Track 4 is only a small check of how far I can carry the Phase-1 conclusions. It is not yet a full scaling law study.

Do not combine every `(d,m)` value, every stage, and every candidate limit. That would confound the result and make the compute grid explode. Track 4 should use:

- one-factor-at-a-time changes around the base case;
- a small feasible `(d,m)` grid;
- full greedy only where it is computationally possible;
- one or a few sampled settings selected from Track 3;
- the episode-count rule from Track 2.

The exact grid is **TODO after the analytic and memory feasibility table**.

### What I want to find

1. If I increase `d` or `m`, do the stage and policy baselines still have a similar shape, or does the problem change in a way I should notice?
2. Does the episode-count choice from Track 2 still give enough precision outside `d=4,m=4`?
3. Does the candidate-number behavior from Track 3 still look similar, or do I have to check it again for a new world size?

I don't need to fully explain every reason behind a change yet. I just want to know whether my old comparison still works, or whether I have to explore these choices again when I move to another environment.

(Still working on)

---
