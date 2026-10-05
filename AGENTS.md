# Repository instructions

## Project and current phase

This is a research project about learning/intervening on a finite family of
structural Boolean worlds. The early topic exploration lives in `ideas/`; the
core baseline implementation is now working, and the current focus is moving
toward controlled experiments. Do not casually redesign working core code while
doing experiment work.

Start code-oriented work by reading `src/ARCHITECTURE_OVERVIEW.md`. It is the
canonical fast index of the current implementation, its data classes, execution
flow, and invariants.

## Research notes

The `ideas/` directory is an Obsidian scratch book. Links and Markdown there may
use Obsidian syntax. Enter through `ideas/main.md`.

- `ideas/my-first-ideas.md` — **low priority** background, inspiration, and
  unproven ideas.
- `ideas/stage-1-explore-the-problem.md` — **high priority** research direction,
  definitions, architecture, and model.
- `ideas/stage-2-model-and-implementation.md` — **high priority** concrete model
  definitions and the current working stage.

Treat claims in the scratch book as hypotheses unless the notes or experiments
support them. Keep a clear distinction between definitions, assumptions,
observations, and conclusions.

## Markdown formatting

- Do not hard-wrap prose in Markdown. Keep each paragraph, blockquote, and list item on one continuous line; start a new line only for a new paragraph, heading, or list item. Preserve intentional line-oriented structures such as tables, fenced code blocks, and display math.

## Core architecture contracts

- `Environment` is the only episode object that owns the hidden `true_world`.
  Never expose it or its dataset index to a policy.
- `OracleState.history` is the source of truth. `survivors` is a derived,
  read-only cache and must be reproducible with `ExactOracle.replay()`.
- Dataset world order, response-column order, and survivor-mask indices must
  remain aligned and deterministic.
- `ExactOracle` is stateless across steps: callers pass in an `OracleState` and
  receive a new one.
- Action IDs are stable prefixes across Stages A, B, and C.
- The current exact-inference argument assumes a finite enumerated hypothesis
  space, a uniform prior, and deterministic observations.
- Distinguish exact greedy information gain from sampled information gain in
  code, filenames, tables, and written conclusions.

The checked-in `src/worldgen-4-4/` dataset represents `d=4`, `m=4` and contains
705,600 canonical worlds. Response columns are intentionally evaluated lazily
and cached per action; Stage B/C can therefore be computationally expensive.

## Experiment work

- Prefer small smoke runs before expensive sweeps.
- Record stage, budget, policy name, seed, and candidate limit (when used).
- Use reproducible seeds and make the unit of analysis explicit.
- A finite `candidate_limit` makes `GreedyInformationGainPolicy` approximate;
  report it as sampled information gain.
- `src/experiments/exp_001_stage_comparison.py` and
  `src/experiments/exp_001_synthesis_graph.py` are exploratory scripts, not
  canonical architecture. Inspect or modify them only when a task specifically
  concerns those scripts.

Run Python commands from `src/`, where `core` and `experiments` resolve as
top-level packages. The main regression suite is:

```powershell
python -m unittest discover -s tests -v
```

## How to collaborate with the researcher

The researcher is a third-year student whose goals are both research insight and
practice with a realistic ML-research workflow. Explain decisions at a junior
level, including the reason behind an abstraction, metric, or experimental
control. Offer opinions about sound research process, but do not rush ahead or
take over all implementation: the researcher also wants to write code and build
the skill personally.
