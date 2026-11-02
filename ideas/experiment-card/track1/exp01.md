# Track 1 — Experiment 01: Stage A/B/C baseline behavior

## Status and question

**Status:** Initial draft. The hidden-world sample size, sampling schedule, run plan, and feasibility of full Stage-C computation are not frozen yet.

With full-candidate greedy information gain, how does uncertainty change from the first action to the maximum number of available actions in each stage? At a shared action step, how different are the stages on the same hidden world? How much do the trajectories vary between hidden worlds?

This experiment records a broad baseline for later interpretation alongside Track 2 (measurement precision) and Track 3 (candidate sampling). A difference in the plots is an observation; explaining whether it comes from the action space, the greedy choices, or properties of particular worlds requires looking at the action and observation traces.

## Experimental conditions

- **World family:** `d=4, m=4`; the enumerated population contains `|Ω| = 705,600` canonical worlds under the current uniform prior and deterministic observations.
- **Policy:** full-candidate `GreedyInformationGainPolicy` (`candidate_limit=None`) in every stage. It chooses the action with the highest *one-step* expected information gain; this does not make the whole action sequence globally optimal. Ties use the lowest action ID.
- **Changed factor:** Stage A, B, or C, which changes the available intervention set.
- **Maximum action budget:** Stage A has 16 distinct actions, Stage B has 144, and Stage C has 1,296. Record `t=0` before any action. Cross-stage comparisons use only shared values of `t`; the longer tail of B or C is read within that stage.
- **Main sampling unit:** one hidden world. Use the **same sampled hidden-world indices** in all three stages so world-by-world comparisons are paired. Do not pass those indices to the policy.
- **Number of sampled hidden worlds:** `N = TBD`. Start with a small pilot to inspect traces and computation; use Track 2 to evaluate whether the resulting estimates are precise enough for later conclusions. A different policy seed on the same world is not a new independent world; the full-candidate policy itself is deterministic here.
- **World sampling and run seed schedule:** `TBD`; record the method, indices, seeds, dataset identity, and code version before the main run.

## Measurements and raw records

For hidden world `i`, stage `s`, and action step `t`, let `C_{i,s,t}` be the surviving worlds after `t` actions. The primary measurement is:

$$U_{i,s,t}=\log_2 |C_{i,s,t}|.$$

Also retain the normalized form $U^{\mathrm{norm}}_{i,s,t}=U_{i,s,t}/\log_2|\Omega|$ for later comparisons with other world sizes. With `d=4, m=4` fixed in this experiment, normalization only rescales the same curve; it is not a second independent outcome.

Keep a step-level trace for each episode: hidden-world index in **result metadata only**, stage, timestep, selected action ID and intervention, observation, survivor counts before and after, predictive entropy, realized information gain, and remaining uncertainty. Keep the condition, sampling schedule, dataset, and code version with the raw result so later analyses can be rebuilt without rerunning the oracle.

## Analysis plan

1. Plot each world's $U_{i,s,t}$ trajectory, grouped by stage. Compare Stage A/B/C **on the same hidden world at the same step** to find cases worth inspecting.
2. Plot the stage-wise mean trajectory $\bar U_{s,t}=\frac{1}{N}\sum_{i=1}^{N}U_{i,s,t}$, alongside a view of the between-world spread (individual lines, quantiles, or standard deviation). Do not treat timesteps within one episode as independent worlds.
3. For a stage and step, define the deviation $e_{i,s,t}=U_{i,s,t}-\bar U_{s,t}$. Summarize between-world variation with $\mathrm{MAE}_{s,t}=\frac{1}{N}\sum_i|e_{i,s,t}|$ and/or the sample standard deviation $s_{s,t}=\sqrt{\frac{1}{N-1}\sum_i e_{i,s,t}^{2}}$ for `N > 1`. These describe how much hidden worlds differ; they are **not** the estimation error or confidence interval of the mean. Decide which spread summary is useful after the pilot rather than reporting both by default.
4. For striking paired differences or outlier worlds, inspect their chosen actions, observations, and survivor-count changes. Write a short note about any plausible mechanism, distinguishing a checked explanation from a hypothesis. Do not infer the reason from a mean curve alone.
5. Use Track 2 to check precision across independently sampled hidden worlds, and Track 3 to compare sampled information gain against this full-candidate reference on matched worlds and steps where feasible.

## Completion and feasibility notes

The target is a trajectory through every available action in each stage. Two different terminal cases must be distinguished:

1. **Exact identification:** `|C_t| = 1`. No action can reduce the survivor count further, so the curve stays at $U_t=0$.
2. **Stage-level observational equivalence:** `|C_t| > 1`, but every remaining permitted action predicts the same single outcome for every surviving world. No action in this stage can distinguish those worlds, so the curve stays at $U_t=\log_2|C_t|>0$. This is a plateau, not exact identification or a failure of the oracle.

For full-candidate greedy, a maximum predictive entropy of zero across **all remaining actions** certifies the second terminal case. Prefer checking that each response distribution has exactly one nonzero outcome count rather than relying on an exact floating-point entropy comparison. Checking only the chosen action is insufficient unless it is known to be the maximum over the full candidate set. Actions already used cannot further split the survivors because their outcomes are fixed by the episode history. The computation may stop at either terminal case and extend the plotted $U$ value as a proven constant through that stage's maximum step; mark the extension separately from actions actually executed and record the terminal reason and survivor count. The raw action trace ends at the stopping point.

The ordinary `run_episode()` executes exactly its configured budget. The optional `run_full_candidate_greedy_episode()` provides this terminal check for a full-candidate greedy run with the stage's maximum budget. It returns the actual action records, the terminal reason, and a full-length uncertainty trajectory whose constant suffix is marked as inferred rather than executed. The core oracle still represents individual surviving worlds; it does not explicitly merge equivalence classes.

Track 0 measured roughly 11–14 seconds to build a new response column on this computer. Its 4–5 hour estimate for all Stage-C columns covers column construction only, not repeated full-candidate scoring across steps and episodes. Run a small pilot and record cold/warm cache behavior before committing to the full run; keep the policy full-candidate rather than silently substituting sampled information gain.

## Interpretation boundaries and open decisions

- This finite sample describes the sampled worlds first. A population-level claim needs the precision check in Track 2.
- Stage comparisons at the same step keep the policy rule and sampled worlds fixed, but the stages offer different action sets; a trajectory difference alone does not isolate a unique causal mechanism.
- Even after all actions, surviving worlds may be observationally indistinguishable under that stage. A nonzero final $U$ does not automatically mean the greedy policy failed.
- **Still to decide:** pilot `N`, world-sampling method and seed schedule, the main-run `N` after Track 2, the practical Stage-C run plan, and which between-world spread display is most readable.
