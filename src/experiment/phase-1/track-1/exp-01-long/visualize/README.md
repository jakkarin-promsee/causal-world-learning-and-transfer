# Exp 01 long visualizations

Run `python experiment/phase-1/track-1/exp-01-long/visualize/plot.py` from `src/` to regenerate three aggregate PNGs from the completed raw run. Pass `--run PATH` for another completed long-run artifact. The script does not create per-world plots or rerun the oracle.

All plots use the 2,124 completed paired hidden worlds and show action steps 0–18. Stage A ends at its budget of 16; longer B/C raw trajectories are clipped only for display. Solid mean segments reach the last executed step among worlds in that stage; dashed segments are inferred terminal suffixes. Each summary box reports the mean final uncertainty and mean raw survivor count, averaged separately.

- [`summarize.png`](summarize.png): stage mean with 10th–90th percentile bands and faint min/max lines across worlds. This shows common spread and extreme trajectories without drawing 2,124 individual lines on top of one another.
- [`summarize-mean-sd.png`](summarize-mean-sd.png): stage mean with one sample standard deviation across worlds. The band is between-world variation, not uncertainty of the estimated mean.
- [`stop-step-histogram.png`](stop-step-histogram.png): number of worlds by last actually executed action; hatching distinguishes a certified non-singleton equivalence class from a singleton.
