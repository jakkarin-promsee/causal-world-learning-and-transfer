# Track 1: Stage behavior

What do the uncertainty trajectories of Stage A, B, and C look like under a limited action budget? I want to separate limits of each stage's action space from the choices made by a policy and from variation across hidden worlds. A few episode traces can help me shape the question; a general comparison needs the precision check from Track 2. No experiment design is frozen yet.

## Local computation diagnostic

[Exp other 01](exp-other-01/README.md) measures the CPU cost of building representative response columns for planning a full-candidate run. Its [local result](exp-other-01/LOCAL_RESULT.md) found that reading, decoding, and validating the dataset was the larger measured component for four tested actions. This is a runtime result, not a Stage A/B/C behavior comparison. Track 1 still has no stage-level scientific result.

[Exp other 02](exp-other-02/README.md) compares the JSONL reference with the numeric engine on matched response columns and times complete full-candidate numeric episodes in all three stages. The [local result](exp-other-02/LOCAL_RESULT.md) gives measured cold/cached episode times and explicitly labeled planning extrapolations for future runs. It remains a computation benchmark, not the planned uncertainty-trajectory experiment.
