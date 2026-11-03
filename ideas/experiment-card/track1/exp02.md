# Track 1 — Experiment 02: Observational equivalence in Stages A/B/C

## Question

For the complete `d=4, m=4` world family, how many structural worlds are indistinguishable under **all** actions available in each stage? How much do the additional actions in B and C refine the equivalence classes from the preceding stage?

## Why this follows Exp 01

[Exp 01](exp01.md) follows full-candidate greedy information gain on sampled hidden worlds. In its [10-world short run](../../../src/experiment/phase-1/track-1/exp-01-short/README.md), Stage A stopped with more than one survivor in 7/10 worlds, while B and C reached a singleton in all 10. One Stage-A plateau contained 28 worlds. Those observations motivate this question but are not estimates of the frequency or size of equivalence classes across all 705,600 worlds. Exp 02 measures the limit imposed by each stage's **action set**, independently of which actions a policy selects or how quickly it selects them.

## Status

**Draft; method and output format to freeze before the exhaustive run.** No Exp 02 counts have been measured yet.

---

## Definitions and fixed conditions

| Item | Setting |
| --- | --- |
| Population | All 705,600 canonical structural worlds in the `d=4, m=4` numeric dataset; each world has equal weight |
| Observation | Encoded tuple `(y0, y1, y2, y3)` produced by the deterministic evaluator after an intervention |
| Stage A | All 16 `do(X)` actions |
| Stage B | Stage A plus exactly one forced `Y`: 144 actions total |
| Stage C | Every allowed pattern of forced/unforced `Y`: 1,296 actions total |
| Action order | Stable `ActionCatalog` IDs; A's IDs are a prefix of B's, and B's are a prefix of C's |

Let $\mathcal A_s$ be the **entire** permitted action set in stage $s$. Define the stage signature of world $w$ as $\sigma_s(w)=(\mathcal E(w,a))_{a\in\mathcal A_s}$ in action-ID order. Worlds $w$ and $w'$ are observationally equivalent in stage $s$ exactly when $\sigma_s(w)=\sigma_s(w')$. An equivalence class $[w]_s$ is the set of all worlds with that signature, and $n_s(w)=|[w]_s|$. A class ID is only a deterministic label for a signature; it is not an action ID or an intrinsic property of a world.

These definitions use potential responses to every available action. They do not require running an episode, choosing a policy, drawing hidden worlds, or setting an action budget. Because $\mathcal A_A\subset\mathcal A_B\subset\mathcal A_C$, each later partition can only split earlier classes; it cannot merge them. Stage equivalence is relative to this world family and observation model, not a claim that two causal systems are identical in every possible setting.

## Measurements

For each stage, calculate:

1. **Number of classes** $K_s$ and a class-size table: the number of classes of each size $k$, plus the number of raw worlds in those classes ($k$ times the class count). Include singleton classes, the largest class, and readable size quantiles.
2. **World-weighted ambiguity:** $P_s(n>1)=|\{w:n_s(w)>1\}|/|\Omega|$ and $\bar U_s=|\Omega|^{-1}\sum_w\log_2 n_s(w)$. The first is the fraction of uniformly sampled hidden worlds that cannot be identified exactly in that stage; the second is the mean irreducible uncertainty in bits. Report the class-weighted histogram separately so large classes are not accidentally treated as one world.
3. **Refinement from A to B and B to C:** for every parent class, count its child classes and their sizes. Report how many parent classes split, how many worlds belong to split parents, and the paired changes $n_A(w)\to n_B(w)\to n_C(w)$ (or $\log_2 n_s(w)$) across all worlds. Include the direct A-to-C change if it helps read the result.

The stage-specific class size $n_s(w)$ is the **best possible terminal survivor count** for hidden world $w$ if enough permitted actions are observed. It says nothing about how many steps greedy needs, and a fixed small action budget can leave more than $n_s(w)$ survivors.

## Analysis and interpretation

1. Build a table for A/B/C with $K_s$, singleton-world fraction, ambiguous-world fraction, $\bar U_s$, and class-size distribution. Plot the distribution with both class counts and world counts visible; a few very large classes could dominate the latter.
2. Show how A classes split in B and how B classes split in C. Name representative world indices and action outcomes only after inspecting their signatures and structural rules. In particular, check whether C supplies meaningful further refinement beyond B; the Exp 01 short sample cannot settle that question.
3. Join the saved Exp 01 hidden-world indices to the Exp 02 class map. For each stage, compare Exp 01's recorded final survivor count with $n_s(w)$. A `singleton` or certified `equivalent` stop under full-candidate greedy should match exactly; investigate any mismatch as a computation or interpretation issue. Use the 28-world Stage-A example as a traceable case, not a representative estimate.
4. Use the exact, world-weighted Exp 02 frequencies to explain **how much final ambiguity is structurally unavoidable** under each stage. Keep Exp 01's stopping times and trajectories as separate evidence about the greedy policy. If B and C have the same terminal classes but different traces, that difference concerns action selection or speed, not identifiability.

## Computation and reproducibility

Start with a small subset of worlds and actions to check signature construction and resource use, then run the full catalog for the exact result. The pilot's partition is only a check of the implementation, not an estimate to report as a result. Use the numeric dataset and existing action catalog/response semantics; avoid changing `core/` or the JSONL reference merely for this analysis. Process response columns in stable world and action order with a memory-bounded method; do not assume the full world-by-1,296-action matrix fits comfortably in RAM. Any hash used to group signatures must have exact equality verification or another collision-free grouping step before calling the counts exact.

Save an exact partition artifact that maps each canonical world index to its class ID in A, B, and C, plus class sizes and parent-child relationships. Assign class IDs deterministically, for example by each class's smallest world index. Record the world-dataset identity/hash, action-catalog ordering and stage action counts, evaluator/code version, grouping method, output schema, and any cache conditions relevant to runtime. Derived tables and plots must be reproducible from the saved artifact without recomputing all responses. Validate that class sizes sum to 705,600 at each stage, that B refines A and C refines B, and that selected same-class/different-class pairs agree with their full action signatures. Record actual runtime and memory use as feasibility context, not as a scientific outcome.

## Limits and next decision

The exhaustive counts describe this finite generated population exactly; they do not need a sampling confidence interval. They do not show how common these patterns are in a different world generator, prior, `d,m`, or noisy observation model. They also do not isolate which individual intervention caused a split without inspecting the relevant response differences.

Use the result to decide whether later Stage A/B/C comparisons should emphasize irreducible ambiguity, steps needed to reach the stage limit, or both. If C adds little identifiability beyond B for this population, inspect its possible effect on trajectories separately before assigning it a benefit.
