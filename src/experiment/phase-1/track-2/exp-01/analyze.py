"""Analyze Track 1 Exp 01 long without rerunning any episodes.

Run from src/: python experiment/phase-1/track-2/exp-01/analyze.py
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import t as student_t

HERE = Path(__file__).resolve().parent
TRACK1 = HERE.parents[1] / "track-1"
sys.path.insert(0, str(TRACK1))
from exp01_summary import load_run  # noqa: E402


RUN = TRACK1 / "exp-01-long" / "runs" / "20261103T062244Z"
STAGES = ("A", "B", "C")
BUDGETS = tuple(range(5, 11))
PAIRS = (("A", "B"), ("B", "C"))
Z = 1.959963984540054
COLORS = {"A": "#0072B2", "B": "#D55E00", "C": "#009E73"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def wilson(successes: int, n: int) -> tuple[float, float]:
    p = successes / n
    denom = 1 + Z * Z / n
    center = (p + Z * Z / (2 * n)) / denom
    half = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / denom
    return center - half, center + half


def mean_interval(values: np.ndarray) -> tuple[float, float, float]:
    n = len(values)
    mean = float(np.mean(values))
    sd = float(np.std(values, ddof=1))
    half = float(student_t.ppf(0.975, n - 1) * sd / math.sqrt(n))
    return mean, mean - half, mean + half


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as destination:
        writer = csv.DictWriter(destination, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def prepare(episodes: list[dict]) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    u = {}
    identified = {}
    for stage in STAGES:
        values = np.asarray(
            [[episode["stages"][stage]["uncertainty_trajectory_bits"][t] for t in BUDGETS] for episode in episodes],
            dtype=float,
        )
        if not np.isfinite(values).all() or (values < -1e-10).any():
            raise ValueError(f"invalid uncertainty in Stage {stage}")
        if (np.diff(values, axis=1) > 1e-10).any():
            raise ValueError(f"uncertainty rises within Stage {stage}")
        u[stage] = values
        identified[stage] = np.isclose(values, 0, atol=1e-10).astype(np.int8)
    return u, identified


def analyze(episodes: list[dict]) -> tuple[list[dict], list[dict]]:
    total = len(episodes)
    sizes = sorted(set(range(20, 151, 5)) | set(range(200, total + 1, 50)))
    if sizes[-1] != total:
        sizes.append(total)
    u, identified = prepare(episodes)
    stage_rows = []
    pair_rows = []
    for n in sizes:
        for j, budget in enumerate(BUDGETS):
            for stage in STAGES:
                successes = int(identified[stage][:n, j].sum())
                low, high = wilson(successes, n)
                mean, mean_low, mean_high = mean_interval(u[stage][:n, j])
                stage_rows.append({
                    "n": n, "budget": budget, "stage": stage,
                    "identified_count": successes, "identified_rate": successes / n,
                    "identified_ci_low": low, "identified_ci_high": high,
                    "identified_ci_max_distance": max(successes / n - low, high - successes / n),
                    "mean_u_bits": mean, "mean_u_ci_low": mean_low, "mean_u_ci_high": mean_high,
                    "mean_u_ci_halfwidth": (mean_high - mean_low) / 2,
                })
            for first, second in PAIRS:
                for metric, arrays in (("identified_rate", identified), ("mean_u_bits", u)):
                    delta = arrays[second][:n, j].astype(float) - arrays[first][:n, j].astype(float)
                    mean, low, high = mean_interval(delta)
                    discordant = int(np.count_nonzero(delta))
                    pair_rows.append({
                        "n": n, "budget": budget, "pair": f"{second}-{first}", "metric": metric,
                        "mean_difference": mean, "ci_low": low, "ci_high": high,
                        "ci_halfwidth": (high - low) / 2,
                        "discordant_count": discordant,
                        "discordant_rate_wilson_upper": wilson(discordant, n)[1],
                    })
    return stage_rows, pair_rows


def threshold_n(rows: list[dict], field: str, limit: float) -> int | None:
    for index, row in enumerate(rows):
        if all(later[field] <= limit for later in rows[index:]):
            return int(row["n"])
    return None


def stability_rows(stage_rows: list[dict]) -> list[dict]:
    """Describe one saved order; the final sample estimate is a reference, not truth."""
    result = []
    for stage in STAGES:
        for budget in BUDGETS:
            rows = [row for row in stage_rows if row["stage"] == stage and row["budget"] == budget]
            reference = rows[-1]["identified_rate"]
            drift = [
                {"n": row["n"], "distance": abs(row["identified_rate"] - reference)}
                for row in rows
            ]
            result.append({
                "stage": stage, "budget": budget, "full_sample_rate": reference,
                "estimate_stable_1pp_n": threshold_n(drift, "distance", 0.01),
                "wilson_precise_2pp_n": threshold_n(rows, "identified_ci_max_distance", 0.02),
                "wilson_precise_1pp_n": threshold_n(rows, "identified_ci_max_distance", 0.01),
            })
    return result


def plot_metric(rows: list[dict], *, metric: str, output: Path, width_only: bool) -> None:
    fig, axes = plt.subplots(2, 3, figsize=(14, 7.5), sharex=True, layout="constrained")
    for ax, budget in zip(axes.flat, BUDGETS):
        for stage in STAGES:
            selected = [row for row in rows if row["budget"] == budget and row["stage"] == stage]
            x = np.asarray([row["n"] for row in selected])
            if metric == "identified":
                y = np.asarray([row["identified_rate"] for row in selected]) * 100
                low = np.asarray([row["identified_ci_low"] for row in selected]) * 100
                high = np.asarray([row["identified_ci_high"] for row in selected]) * 100
                width = np.asarray([row["identified_ci_max_distance"] for row in selected]) * 100
            else:
                y = np.asarray([row["mean_u_bits"] for row in selected])
                low = np.asarray([row["mean_u_ci_low"] for row in selected])
                high = np.asarray([row["mean_u_ci_high"] for row in selected])
                width = np.asarray([row["mean_u_ci_halfwidth"] for row in selected])
            if width_only:
                ax.plot(x, width, color=COLORS[stage], label=f"Stage {stage}", linewidth=1.8)
            else:
                ax.plot(x, y, color=COLORS[stage], label=f"Stage {stage}", linewidth=1.8)
                ax.fill_between(x, low, high, color=COLORS[stage], alpha=0.1)
        if width_only:
            if metric == "identified":
                ax.axhline(1, color="#888888", linestyle="--", linewidth=0.8)
                ax.axhline(2, color="#aaaaaa", linestyle=":", linewidth=0.8)
            else:
                ax.axhline(0.1, color="#888888", linestyle="--", linewidth=0.8)
        ax.set_title(f"Budget {budget}")
        ax.grid(alpha=0.2)
        ax.set_xlim(20, max(row["n"] for row in rows))
    axes[0, 0].legend(loc="best", fontsize=8)
    for ax in axes[-1, :]:
        ax.set_xlabel("Sampled hidden worlds n")
    ylabel = (
        "95% CI max distance (percentage points)" if metric == "identified" else "95% CI half-width (bits)"
    ) if width_only else (
        "Identified worlds (%)" if metric == "identified" else "Mean remaining uncertainty (bits)"
    )
    for ax in axes[:, 0]:
        ax.set_ylabel(ylabel)
    fig.suptitle(f"Track 2 Exp 01: {metric} {'precision' if width_only else 'estimate and 95% CI'}")
    fig.savefig(output, dpi=160)
    plt.close(fig)


def plot_budget9_small_n(rows: list[dict], output: Path) -> None:
    selected = [row for row in rows if row["stage"] == "B" and row["budget"] == 9 and row["n"] <= 150]
    x = np.asarray([row["n"] for row in selected])
    estimate = np.asarray([row["identified_rate"] for row in selected]) * 100
    low = np.asarray([row["identified_ci_low"] for row in selected]) * 100
    high = np.asarray([row["identified_ci_high"] for row in selected]) * 100
    distance = np.asarray([row["identified_ci_max_distance"] for row in selected]) * 100
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), layout="constrained")
    axes[0].plot(x, estimate, color=COLORS["B"], marker="o", markersize=3)
    axes[0].fill_between(x, low, high, color=COLORS["B"], alpha=0.18)
    axes[0].set_title("Stage B, budget 9: estimate and 95% Wilson CI")
    axes[0].set_ylabel("Identified worlds (%)")
    axes[0].set_ylim(80, 101)
    axes[1].plot(x, distance, color=COLORS["B"], marker="o", markersize=3)
    axes[1].axhline(2, color="#888888", linestyle="--", label="±2 pp target")
    axes[1].axhline(1, color="#555555", linestyle=":", label="±1 pp target")
    axes[1].set_title("Largest distance to a 95% interval endpoint")
    axes[1].set_ylabel("Percentage points")
    axes[1].legend(fontsize=8)
    for ax in axes:
        ax.set_xlabel("Sampled hidden worlds n")
        ax.set_xticks([*range(20, 141, 20), 150])
        ax.grid(alpha=0.2)
    fig.savefig(output, dpi=160)
    plt.close(fig)


def report(stage_rows: list[dict], pair_rows: list[dict], stability: list[dict], raw_path: Path, output: Path) -> None:
    total = max(row["n"] for row in stage_rows)
    b8 = next(row for row in stage_rows if row["n"] == total and row["stage"] == "B" and row["budget"] == 8)
    b9 = next(row for row in stage_rows if row["n"] == total and row["stage"] == "B" and row["budget"] == 9)
    b8_prefixes = [row for row in stage_rows if row["stage"] == "B" and row["budget"] == 8]
    b8_n1 = threshold_n(b8_prefixes, "identified_ci_max_distance", 0.01)
    lines = [
        "# Track 2 Exp 01 — result", "",
        f"Analyzed {total:,} paired hidden worlds from [`{raw_path.relative_to(HERE.parents[3]).as_posix()}`](../../track-1/exp-01-long/runs/20261103T062244Z/episodes.jsonl). No episodes or oracle responses were recomputed. Raw SHA-256: `{sha256(raw_path)}`.", "",
        "Intervals are marginal 95% sampling intervals for this finite `d=4,m=4` world family under the saved random world order. The world is the unit; stages and budgets are paired within it. Wilson intervals describe identification rates and t intervals describe means. These intervals do not cover implementation error or other world families.", "",
        "## Main reading", "",
        f"Stage B identified {b8['identified_count']:,}/{total:,} worlds by budget 8 ({100*b8['identified_rate']:.2f}%; 95% Wilson interval {100*b8['identified_ci_low']:.2f}–{100*b8['identified_ci_high']:.2f}%) and {b9['identified_count']:,}/{total:,} by budget 9 ({100*b9['identified_rate']:.2f}%; interval {100*b9['identified_ci_low']:.2f}–{100*b9['identified_ci_high']:.2f}%). For Stage B at budget 8, the ±1 percentage-point planning target holds from the measured `n={b8_n1:,}` prefix onward. Several other stage/budget identification rates do not reach even ±2 points at 2,124 worlds; there is no single sufficient count for every metric and condition.", "",
        "## All 2,124 worlds", "",
        "| Stage | Budget | Identified | 95% Wilson CI | Mean U (bits) | 95% t CI |", "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in stage_rows:
        if row["n"] == total:
            lines.append(
                f"| {row['stage']} | {row['budget']} | {row['identified_count']}/{total} ({100*row['identified_rate']:.2f}%) "
                f"| {100*row['identified_ci_low']:.2f}–{100*row['identified_ci_high']:.2f}% "
                f"| {row['mean_u_bits']:.3f} | {max(0, row['mean_u_ci_low']):.3f}–{row['mean_u_ci_high']:.3f} |"
            )
    lines += ["", "## Stage B budget 9: every small prefix", "", "All values come from the same saved random order, with `n=20..150` in steps of 5. The first failure by action 9 enters at `n=85`; earlier 100% samples still have broad Wilson intervals.", "", "| n | Identified | Rate | 95% Wilson CI | Maximum distance |", "| ---: | ---: | ---: | ---: | ---: |"]
    for row in stage_rows:
        if row["stage"] == "B" and row["budget"] == 9 and row["n"] <= 150:
            lines.append(
                f"| {row['n']} | {row['identified_count']}/{row['n']} | {100*row['identified_rate']:.2f}% "
                f"| {100*row['identified_ci_low']:.2f}–{100*row['identified_ci_high']:.2f}% "
                f"| {100*row['identified_ci_max_distance']:.2f} pp |"
            )
    lines += ["", "## Planning sample sizes", "", "Smallest measured prefix after which every larger measured prefix also meets the indicated maximum distance from the estimate. `—` means not reached by 2,124 worlds. These are exploratory planning numbers from one sample, not independent validations.", "", "| Stage | Budget | Rate ±2 pp | Rate ±1 pp | Mean U ±0.1 bit |", "| --- | ---: | ---: | ---: | ---: |"]
    for stage in STAGES:
        for budget in BUDGETS:
            selected = [row for row in stage_rows if row["stage"] == stage and row["budget"] == budget]
            needed = [threshold_n(selected, "identified_ci_max_distance", target) for target in (0.02, 0.01)]
            needed.append(threshold_n(selected, "mean_u_ci_halfwidth", 0.1))
            rendered = [str(n) if n is not None else "—" for n in needed]
            lines.append(f"| {stage} | {budget} | {' | '.join(rendered)} |")
    lines += ["", "## Estimate stability versus precision", "", "The stability column is the first measured prefix after which every later estimate stays within ±1 percentage point of this run's final 2,124-world estimate. It is an internal diagnostic using the same worlds, not an independent accuracy check. The Wilson columns require the entire 95% interval to stay within the indicated maximum distance from its own estimate; `—` means not reached.", "", "| Stage | Budget | Estimate stable ±1 pp | Wilson precise ±2 pp | Wilson precise ±1 pp |", "| --- | ---: | ---: | ---: | ---: |"]
    for row in stability:
        values = [row[key] for key in ("estimate_stable_1pp_n", "wilson_precise_2pp_n", "wilson_precise_1pp_n")]
        lines.append(f"| {row['stage']} | {row['budget']} | {' | '.join(str(value) if value is not None else '—' for value in values)} |")
    lines += ["", "## Paired stage differences at all 2,124 worlds", "", "Difference is second stage minus first stage on the same hidden world. A zero discordant count is accompanied by the Wilson upper bound, since a zero-width t interval is not proof of equality.", "", "| Pair | Budget | Metric | Mean difference | 95% t CI | Discordant worlds |", "| --- | ---: | --- | ---: | ---: | ---: |"]
    for row in pair_rows:
        if row["n"] == total:
            scale = 100 if row["metric"] == "identified_rate" else 1
            unit = " pp" if scale == 100 else " bits"
            lines.append(
                f"| {row['pair']} | {row['budget']} | {row['metric']} "
                f"| {scale*row['mean_difference']:.3f}{unit} "
                f"| [{scale*row['ci_low']:.3f}, {scale*row['ci_high']:.3f}]{unit} "
                f"| {row['discordant_count']} (95% Wilson upper {100*row['discordant_rate_wilson_upper']:.2f}%) |"
            )
    lines += ["", "## Plots and full tables", "", "- `identified-estimate.png` and `identified-precision.png`", "- `mean-u-estimate.png` and `mean-u-precision.png`", "- `budget9-small-n.png` zooms into Stage B at `n=20..150`.", "- `stage-prefix.csv` and `paired-prefix.csv` contain every measured prefix, stage, and budget; `minimum-n.csv` contains the stability and Wilson-precision thresholds.", "", "The ±1 and ±2 percentage-point thresholds and ±0.1-bit threshold were chosen after Track 1. Stage A's exact identification ceiling and Stage B/C's exact action-set limits are in Track 1 Exp 02; a sampled budget result is a different quantity. Do not interpret the 18 marginal intervals as one simultaneous 95% guarantee or infer that an unseen rare event is impossible.", ""]
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    metadata, episodes, raw_path = load_run(RUN, expected_run_name="exp-01-long")
    if len(episodes) != 2124 or metadata["candidate_limit"] is not None:
        raise ValueError("unexpected Track 1 long sample or policy")
    stage_rows, pair_rows = analyze(episodes)
    stability = stability_rows(stage_rows)
    write_csv(HERE / "stage-prefix.csv", stage_rows)
    write_csv(HERE / "paired-prefix.csv", pair_rows)
    write_csv(HERE / "minimum-n.csv", stability)
    for metric in ("identified", "mean-u"):
        for width_only in (False, True):
            suffix = "precision" if width_only else "estimate"
            plot_metric(stage_rows, metric=metric, output=HERE / f"{metric}-{suffix}.png", width_only=width_only)
    plot_budget9_small_n(stage_rows, HERE / "budget9-small-n.png")
    report(stage_rows, pair_rows, stability, raw_path, HERE / "RESULT.md")
    print(f"Analyzed {len(episodes):,} paired worlds; wrote RESULT.md, 3 CSV tables, and 5 plots in {HERE}")


if __name__ == "__main__":
    main()
