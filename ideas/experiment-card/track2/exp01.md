# Track 2 — Experiment 01: Episode count and measurement precision

## Question

For full-candidate greedy information gain on `d=4, m=4`, how many sampled hidden worlds give useful precision for Stage A/B/C results at action budgets 5–10?

## Data and unit

Reuse the 2,124 paired hidden worlds in [Track 1 Exp 01 long](../../../src/experiment/phase-1/track-1/exp-01-long/README.md); do not rerun the oracle. Each hidden world is one independent sampling unit, observed under all three stages. The policy is deterministic, so this experiment measures hidden-world sampling variation, not policy-seed variation. Preserve the saved random world order and use its first `n` completed worlds for each sample size. Early-stop trajectory values are certified constant suffixes, not extra executed actions.

## Measurements

For each stage `s`, budget `t ∈ {5, 6, 7, 8, 9, 10}`, and sample size `n`:

- **Identification rate:** `P(|C_{s,t}| = 1)`, estimated as the fraction of sampled worlds with one survivor at step `t`; report a 95% Wilson interval.
- **Mean remaining uncertainty:** mean `U_{s,t} = log₂|C_{s,t}|` in bits; report a 95% t interval using worlds as observations.
- **Paired stage differences:** calculate B−A and C−B *within each world* for identification (0/1) and `U`, then report the mean difference and its 95% t interval. If every sampled difference is zero, report a Wilson upper bound on the fraction of worlds with any difference instead of calling the zero-width t interval certainty. Never treat stages or timesteps from one world as independent samples.

Use [Track 1 Exp 02](../../../src/experiment/phase-1/track-1/exp-02/README.md) for exact, whole-population stage equivalence limits; those counts need no sampling interval. Identification at budget `t` is different from eventual identifiability under every permitted action.

## Sample-size analysis

Compute the measurements for prefixes `n = 20, 25, …, 150, 200, 250, …, 2,100, 2,124` of the saved random order. Plot estimates and 95% interval widths against `n`, with separate panels for stages and budgets so 18 curves remain readable. Report the smallest measured `n` after which all larger prefixes meet ±2 or ±1 percentage points for identification, or ±0.1 bit for mean `U`; report `not reached by 2,124` when appropriate. Also report the interval width at all 2,124 worlds. These are planning precision targets, not guarantees of an effect or a universal episode count. Judge paired differences against a stated practically meaningful difference before making a stage-comparison claim.

## Interpretation and limits

Judge adequacy by interval width relative to the intended decision, not by whether adjacent prefix estimates look similar. Prefixes overlap and are views of one run, not independent replications; resampling the 2,124 saved worlds cannot create new independent evidence. This analysis is exploratory because the precision targets were chosen after seeing Track 1. A later independent sample is needed only if a target remains unmet or a newly chosen decision rule requires confirmation. Do not infer a rare event is absent merely because it does not appear in the sample.

Save a compact table of estimates, interval bounds, and `n` for every stage and budget, plus the sample-size plot and the raw-run path/hash. Do not add the 10-world short run to the long-run sample.
