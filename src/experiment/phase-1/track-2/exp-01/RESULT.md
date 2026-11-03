# Track 2 Exp 01 — result

Analyzed 2,124 paired hidden worlds from [`experiment/phase-1/track-1/exp-01-long/runs/20261103T062244Z/episodes.jsonl`](../../track-1/exp-01-long/runs/20261103T062244Z/episodes.jsonl). No episodes or oracle responses were recomputed. Raw SHA-256: `9ebf8dc154ffaee269af2b53514a2038900720fa30c264279e224f05f2a7f04e`.

Intervals are marginal 95% sampling intervals for this finite `d=4,m=4` world family under the saved random world order. The world is the unit; stages and budgets are paired within it. Wilson intervals describe identification rates and t intervals describe means. These intervals do not cover implementation error or other world families.

## Main reading

Stage B identified 2,038/2,124 worlds by budget 8 (95.95%; 95% Wilson interval 95.03–96.71%) and 2,109/2,124 by budget 9 (99.29%; interval 98.84–99.57%). For Stage B at budget 8, the ±1 percentage-point planning target holds from the measured `n=1,900` prefix onward. Several other stage/budget identification rates do not reach even ±2 points at 2,124 worlds; there is no single sufficient count for every metric and condition.

## All 2,124 worlds

| Stage | Budget | Identified | 95% Wilson CI | Mean U (bits) | 95% t CI |
| --- | ---: | ---: | ---: | ---: | ---: |
| A | 5 | 174/2124 (8.19%) | 7.10–9.44% | 2.539 | 2.473–2.605 |
| B | 5 | 179/2124 (8.43%) | 7.32–9.69% | 2.296 | 2.236–2.355 |
| C | 5 | 178/2124 (8.38%) | 7.28–9.64% | 2.293 | 2.234–2.352 |
| A | 6 | 561/2124 (26.41%) | 24.58–28.33% | 1.662 | 1.598–1.726 |
| B | 6 | 914/2124 (43.03%) | 40.94–45.15% | 0.898 | 0.855–0.941 |
| C | 6 | 925/2124 (43.55%) | 41.45–45.67% | 0.882 | 0.839–0.924 |
| A | 7 | 790/2124 (37.19%) | 35.16–39.27% | 1.433 | 1.369–1.498 |
| B | 7 | 1719/2124 (80.93%) | 79.21–82.55% | 0.245 | 0.221–0.270 |
| C | 7 | 1744/2124 (82.11%) | 80.42–83.68% | 0.229 | 0.206–0.253 |
| A | 8 | 835/2124 (39.31%) | 37.26–41.41% | 1.399 | 1.334–1.464 |
| B | 8 | 2038/2124 (95.95%) | 95.03–96.71% | 0.049 | 0.039–0.060 |
| C | 8 | 2047/2124 (96.37%) | 95.49–97.09% | 0.043 | 0.033–0.053 |
| A | 9 | 840/2124 (39.55%) | 37.49–41.64% | 1.396 | 1.331–1.461 |
| B | 9 | 2109/2124 (99.29%) | 98.84–99.57% | 0.007 | 0.004–0.011 |
| C | 9 | 2114/2124 (99.53%) | 99.14–99.74% | 0.005 | 0.002–0.008 |
| A | 10 | 840/2124 (39.55%) | 37.49–41.64% | 1.396 | 1.331–1.461 |
| B | 10 | 2123/2124 (99.95%) | 99.73–99.99% | 0.000 | 0.000–0.001 |
| C | 10 | 2124/2124 (100.00%) | 99.82–100.00% | 0.000 | 0.000–0.000 |

## Stage B budget 9: every small prefix

All values come from the same saved random order, with `n=20..150` in steps of 5. The first failure by action 9 enters at `n=85`; earlier 100% samples still have broad Wilson intervals.

| n | Identified | Rate | 95% Wilson CI | Maximum distance |
| ---: | ---: | ---: | ---: | ---: |
| 20 | 20/20 | 100.00% | 83.89–100.00% | 16.11 pp |
| 25 | 25/25 | 100.00% | 86.68–100.00% | 13.32 pp |
| 30 | 30/30 | 100.00% | 88.65–100.00% | 11.35 pp |
| 35 | 35/35 | 100.00% | 90.11–100.00% | 9.89 pp |
| 40 | 40/40 | 100.00% | 91.24–100.00% | 8.76 pp |
| 45 | 45/45 | 100.00% | 92.13–100.00% | 7.87 pp |
| 50 | 50/50 | 100.00% | 92.87–100.00% | 7.13 pp |
| 55 | 55/55 | 100.00% | 93.47–100.00% | 6.53 pp |
| 60 | 60/60 | 100.00% | 93.98–100.00% | 6.02 pp |
| 65 | 65/65 | 100.00% | 94.42–100.00% | 5.58 pp |
| 70 | 70/70 | 100.00% | 94.80–100.00% | 5.20 pp |
| 75 | 75/75 | 100.00% | 95.13–100.00% | 4.87 pp |
| 80 | 80/80 | 100.00% | 95.42–100.00% | 4.58 pp |
| 85 | 84/85 | 98.82% | 93.63–99.79% | 5.19 pp |
| 90 | 89/90 | 98.89% | 93.97–99.80% | 4.92 pp |
| 95 | 94/95 | 98.95% | 94.28–99.81% | 4.67 pp |
| 100 | 99/100 | 99.00% | 94.55–99.82% | 4.45 pp |
| 105 | 104/105 | 99.05% | 94.80–99.83% | 4.25 pp |
| 110 | 109/110 | 99.09% | 95.03–99.84% | 4.06 pp |
| 115 | 114/115 | 99.13% | 95.24–99.85% | 3.89 pp |
| 120 | 119/120 | 99.17% | 95.43–99.85% | 3.74 pp |
| 125 | 124/125 | 99.20% | 95.61–99.86% | 3.59 pp |
| 130 | 129/130 | 99.23% | 95.77–99.86% | 3.46 pp |
| 135 | 134/135 | 99.26% | 95.92–99.87% | 3.34 pp |
| 140 | 139/140 | 99.29% | 96.07–99.87% | 3.22 pp |
| 145 | 144/145 | 99.31% | 96.20–99.88% | 3.11 pp |
| 150 | 149/150 | 99.33% | 96.32–99.88% | 3.01 pp |

## Planning sample sizes

Smallest measured prefix after which every larger measured prefix also meets the indicated maximum distance from the estimate. `—` means not reached by 2,124 worlds. These are exploratory planning numbers from one sample, not independent validations.

| Stage | Budget | Rate ±2 pp | Rate ±1 pp | Mean U ±0.1 bit |
| --- | ---: | ---: | ---: | ---: |
| A | 5 | 950 | — | 1000 |
| A | 6 | 2000 | — | 950 |
| A | 7 | — | — | 950 |
| A | 8 | — | — | 1000 |
| A | 9 | — | — | 1000 |
| A | 10 | — | — | 1000 |
| B | 5 | 1000 | — | 800 |
| B | 6 | — | — | 450 |
| B | 7 | 1600 | — | 105 |
| B | 8 | 600 | 1900 | 20 |
| B | 9 | 300 | 700 | 20 |
| B | 10 | 250 | 500 | 20 |
| C | 5 | 1000 | — | 800 |
| C | 6 | — | — | 400 |
| C | 7 | 1550 | — | 105 |
| C | 8 | 600 | 1800 | 20 |
| C | 9 | 300 | 600 | 20 |
| C | 10 | 200 | 400 | 20 |

## Estimate stability versus precision

The stability column is the first measured prefix after which every later estimate stays within ±1 percentage point of this run's final 2,124-world estimate. It is an internal diagnostic using the same worlds, not an independent accuracy check. The Wilson columns require the entire 95% interval to stay within the indicated maximum distance from its own estimate; `—` means not reached.

| Stage | Budget | Estimate stable ±1 pp | Wilson precise ±2 pp | Wilson precise ±1 pp |
| --- | ---: | ---: | ---: | ---: |
| A | 5 | 400 | 950 | — |
| A | 6 | 1150 | 2000 | — |
| A | 7 | 1150 | — | — |
| A | 8 | 1150 | — | — |
| A | 9 | 1150 | — | — |
| A | 10 | 1150 | — | — |
| B | 5 | 300 | 1000 | — |
| B | 6 | 1000 | — | — |
| B | 7 | 700 | 1600 | — |
| B | 8 | 1000 | 600 | 1900 |
| B | 9 | 20 | 300 | 700 |
| B | 10 | 100 | 250 | 500 |
| C | 5 | 300 | 1000 | — |
| C | 6 | 1000 | — | — |
| C | 7 | 750 | 1550 | — |
| C | 8 | 400 | 600 | 1800 |
| C | 9 | 20 | 300 | 600 |
| C | 10 | 20 | 200 | 400 |

## Paired stage differences at all 2,124 worlds

Difference is second stage minus first stage on the same hidden world. A zero discordant count is accompanied by the Wilson upper bound, since a zero-width t interval is not proof of equality.

| Pair | Budget | Metric | Mean difference | 95% t CI | Discordant worlds |
| --- | ---: | --- | ---: | ---: | ---: |
| B-A | 5 | identified_rate | 0.235 pp | [-0.616, 1.087] pp | 85 (95% Wilson upper 4.92%) |
| B-A | 5 | mean_u_bits | -0.243 bits | [-0.278, -0.208] bits | 980 (95% Wilson upper 48.26%) |
| C-B | 5 | identified_rate | -0.047 pp | [-0.207, 0.113] pp | 3 (95% Wilson upper 0.41%) |
| C-B | 5 | mean_u_bits | -0.003 bits | [-0.008, 0.002] bits | 37 (95% Wilson upper 2.39%) |
| B-A | 6 | identified_rate | 16.620 pp | [14.763, 18.477] pp | 463 (95% Wilson upper 23.60%) |
| B-A | 6 | mean_u_bits | -0.764 bits | [-0.811, -0.717] bits | 1270 (95% Wilson upper 61.86%) |
| C-B | 6 | identified_rate | 0.518 pp | [0.076, 0.960] pp | 23 (95% Wilson upper 1.62%) |
| C-B | 6 | mean_u_bits | -0.016 bits | [-0.024, -0.008] bits | 78 (95% Wilson upper 4.56%) |
| B-A | 7 | identified_rate | 43.738 pp | [41.528, 45.948] pp | 979 (95% Wilson upper 48.22%) |
| B-A | 7 | mean_u_bits | -1.188 bits | [-1.244, -1.132] bits | 1318 (95% Wilson upper 64.09%) |
| C-B | 7 | identified_rate | 1.177 pp | [0.588, 1.766] pp | 41 (95% Wilson upper 2.61%) |
| C-B | 7 | mean_u_bits | -0.016 bits | [-0.023, -0.009] bits | 60 (95% Wilson upper 3.62%) |
| B-A | 8 | identified_rate | 56.638 pp | [54.509, 58.768] pp | 1213 (95% Wilson upper 59.20%) |
| B-A | 8 | mean_u_bits | -1.350 bits | [-1.412, -1.288] bits | 1291 (95% Wilson upper 62.84%) |
| C-B | 8 | identified_rate | 0.424 pp | [0.091, 0.756] pp | 13 (95% Wilson upper 1.04%) |
| C-B | 8 | mean_u_bits | -0.006 bits | [-0.010, -0.002] bits | 19 (95% Wilson upper 1.39%) |
| B-A | 9 | identified_rate | 59.746 pp | [57.658, 61.833] pp | 1269 (95% Wilson upper 61.81%) |
| B-A | 9 | mean_u_bits | -1.388 bits | [-1.453, -1.324] bits | 1284 (95% Wilson upper 62.51%) |
| C-B | 9 | identified_rate | 0.235 pp | [0.029, 0.442] pp | 5 (95% Wilson upper 0.55%) |
| C-B | 9 | mean_u_bits | -0.003 bits | [-0.005, -0.000] bits | 6 (95% Wilson upper 0.61%) |
| B-A | 10 | identified_rate | 60.405 pp | [58.323, 62.486] pp | 1283 (95% Wilson upper 62.46%) |
| B-A | 10 | mean_u_bits | -1.395 bits | [-1.460, -1.330] bits | 1284 (95% Wilson upper 62.51%) |
| C-B | 10 | identified_rate | 0.047 pp | [-0.045, 0.139] pp | 1 (95% Wilson upper 0.27%) |
| C-B | 10 | mean_u_bits | -0.000 bits | [-0.001, 0.000] bits | 1 (95% Wilson upper 0.27%) |

## Plots and full tables

- `identified-estimate.png` and `identified-precision.png`
- `mean-u-estimate.png` and `mean-u-precision.png`
- `budget9-small-n.png` zooms into Stage B at `n=20..150`.
- `stage-prefix.csv` and `paired-prefix.csv` contain every measured prefix, stage, and budget; `minimum-n.csv` contains the stability and Wilson-precision thresholds.

The ±1 and ±2 percentage-point thresholds and ±0.1-bit threshold were chosen after Track 1. Stage A's exact identification ceiling and Stage B/C's exact action-set limits are in Track 1 Exp 02; a sampled budget result is a different quantity. Do not interpret the 18 marginal intervals as one simultaneous 95% guarantee or infer that an unseen rare event is impossible.
