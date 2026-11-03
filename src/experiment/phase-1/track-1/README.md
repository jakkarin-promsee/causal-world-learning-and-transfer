# Track 1 — Behavior of Stage A/B/C

## Question

With full-candidate greedy information gain, how does uncertainty change as actions are used in Stages A, B, and C? Which differences come from the stage's action set rather than the greedy policy?

## Findings

[Exp 01 long](exp-01-long/README.md) ran the same 2,124 sampled hidden worlds in all three stages. B and C chose identical action traces in 1,984/2,124 worlds (93.4%) and had similar uncertainty trajectories; A often ended with unresolved worlds. These are sample results, and Track 2 will check their precision.

| Stage | Mean stop step | Mean final $U_T$ (bits) | Mean final $\lvert C_T\rvert$ | Singleton endings |
| --- | ---: | ---: | ---: | ---: |
| A | 5.93 | 1.396 | 6.187 | 840/2,124 (39.5%) |
| B | 6.72 | 0 | 1 | 2,124/2,124 (100%) |
| C | 6.70 | 0 | 1 | 2,124/2,124 (100%) |

The executed action-ID traces were identical across A/B/C in **464/2,124 worlds (21.8%)**; B=C but A differed in **1,520 (71.6%)**; C differed from both in **140 (6.6%)**. In the B=C-but-A-different group, B/C matched A on 6,748/8,878 comparable executed steps (76.0%). In the C-different group, B and C matched on 747/1,004 comparable steps (74.4%). These action-step percentages describe trace overlap, not independent world samples. [Detailed numerical result](exp-01-long/numeric-summary.json) · [aggregate plots](exp-01-long/visualize/README.md).

[Exp 02](exp-02/README.md) independently partitioned **all 705,600 worlds** by their complete action responses. Its counts are exact for this finite world family and do not depend on greedy choices or the Exp 01 sample.

| Stage | Worlds in non-singleton classes | Mean class size within those worlds | Mean class size over all worlds |
| ----- | ------------------------------: | ----------------------------------: | ------------------------------: |
| A     |              424,872 (60.2143%) |                             10.0209 |                          6.4319 |
| B     |                   368 (0.0522%) |                              2.0000 |                          1.0005 |
| C     |                               0 |             Undefined (empty group) |                          1.0000 |

The last column is the expected terminal survivor count for a world drawn uniformly from this enumerated family, after every action available in that stage is considered. It is a mean, not the probability of drawing a particular class size. [Exact partition result](exp-02/README.md) · [machine-readable summary](exp-02/runs/20261103T121204Z/numeric-summary.json).

## Decision

Use **Stage B as the baseline for subsequent experiments** in this `d=4,m=4` family. Stage A cannot identify a world in 60.2143% of the finite family. Stage B identifies all but 0.0522% while offering 144 possible actions versus Stage C's 1,296. With full-candidate greedy information gain, Stage B stopped after **6.723 ± 0.982 actions (mean ± 1 sample SD)** in Exp 01 long, suggesting an initial budget of about **8 actions**; this is a planning estimate, not a completion guarantee. Stage C distinguishes every world in this family, but its Exp 01 mean stop step was only 0.024 lower than B's; that small sample difference is not evidence of a meaningful speed advantage. Keep C as an identifiability reference when needed, rather than the routine baseline.
