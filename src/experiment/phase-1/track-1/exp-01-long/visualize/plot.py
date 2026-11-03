"""Create aggregate plots from the completed Exp 01 long raw run, without per-world PNGs.

From src/: python experiment/phase-1/track-1/exp-01-long/visualize/plot.py
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))

from exp01_summary import load_run


DEFAULT_RUN = HERE.parent / "runs" / "20261103T062244Z"
STAGES = ("A", "B", "C")
COLORS = {"A": "#0072B2", "B": "#D55E00", "C": "#009E73"}
DISPLAY_END = 18


def stage_data(episodes: list[dict], stage: str) -> tuple[np.ndarray, np.ndarray, int]:
    rows = [episode["stages"][stage] for episode in episodes]
    stop = min(rows[0]["budget"], DISPLAY_END)
    x = np.arange(stop + 1)
    values = np.asarray([row["uncertainty_trajectory_bits"][: stop + 1] for row in rows], dtype=float)
    return x, values, max(row["executed_steps"] for row in rows)


def draw_mean(ax, x: np.ndarray, mean: np.ndarray, last_actual: int, *, stage: str) -> None:
    last = min(last_actual, x[-1])
    width = {"A": 4.5, "B": 3.2, "C": 2.0}[stage]
    ax.plot(x[: last + 1], mean[: last + 1], color=COLORS[stage], linewidth=width)
    if last < x[-1]:
        ax.plot(x[last:], mean[last:], color=COLORS[stage], linewidth=width, linestyle="--")


def style_axes(ax, initial_u: float) -> None:
    ax.set_xlim(0, DISPLAY_END)
    ax.set_ylim(-0.5, initial_u + 0.6)
    ax.set_xticks(np.arange(0, DISPLAY_END + 1, 2))
    ax.set_xlabel("Action step t")
    ax.set_ylabel(r"$U_t=\log_2 |C_t|$ (bits)")
    ax.grid(alpha=0.2)


def terminal_box(ax, episodes: list[dict]) -> None:
    lines = [f"Mean terminal state ({len(episodes):,} worlds)", "stage  last t  mean U_T  mean |C_T|"]
    for stage in STAGES:
        rows = [episode["stages"][stage] for episode in episodes]
        last = max(row["executed_steps"] for row in rows)
        mean_u = np.mean([row["uncertainty_trajectory_bits"][-1] for row in rows])
        mean_c = np.mean([row["final_survivor_count"] for row in rows])
        lines.append(f"  {stage}      {last:>2}      {mean_u:>5.2f}      {mean_c:>5.1f}")
    ax.text(
        0.98, 0.73, "\n".join(lines), transform=ax.transAxes, ha="right", va="top",
        fontsize=9, fontfamily="monospace",
        bbox={"facecolor": "white", "alpha": 0.92, "edgecolor": "#cccccc", "boxstyle": "round,pad=0.5"},
    )


def save_summary(episodes: list[dict], output: Path, *, mode: str) -> None:
    initial_u = episodes[0]["stages"]["A"]["initial_uncertainty_bits"]
    fig, ax = plt.subplots(figsize=(12, 6.5), layout="constrained")
    for stage in STAGES:
        x, values, last_actual = stage_data(episodes, stage)
        mean = values.mean(axis=0)
        if mode == "percentiles":
            lower, upper = np.percentile(values, [10, 90], axis=0)
            ax.fill_between(x, lower, upper, color=COLORS[stage], alpha=0.16, linewidth=0)
            ax.plot(x, values.min(axis=0), color=COLORS[stage], alpha=0.25, linewidth=0.8, linestyle=":")
            ax.plot(x, values.max(axis=0), color=COLORS[stage], alpha=0.25, linewidth=0.8, linestyle=":")
        else:
            sd = values.std(axis=0, ddof=1)
            ax.fill_between(
                x, np.maximum(0, mean - sd), np.minimum(initial_u, mean + sd),
                color=COLORS[stage], alpha=0.17, linewidth=0,
            )
        draw_mean(ax, x, mean, last_actual, stage=stage)
    style_axes(ax, initial_u)
    n = len(episodes)
    ax.set_title(
        f"Exp 01 long · mean and between-world variability ({n:,} worlds)" if mode == "percentiles"
        else f"Exp 01 long · mean ± sample standard deviation ({n:,} worlds)"
    )
    spread_key = (
        Patch(facecolor="#888888", alpha=0.2, label="10th–90th percentile; dotted min/max")
        if mode == "percentiles" else Patch(facecolor="#888888", alpha=0.2, label="±1 SD across worlds")
    )
    ax.legend(handles=[
        *(Line2D([0], [0], color=COLORS[stage], linewidth=2.5, label=f"Stage {stage}") for stage in STAGES),
        spread_key,
        Line2D([0], [0], color="#555555", linewidth=2, linestyle="--", label="Beyond last executed step"),
    ], loc="upper right", fontsize=9)
    terminal_box(ax, episodes)
    fig.savefig(output, dpi=180)
    plt.close(fig)


def save_stop_histogram(episodes: list[dict], output: Path) -> None:
    stops = [episode["stages"][stage]["executed_steps"] for episode in episodes for stage in STAGES]
    steps = np.arange(min(stops), max(stops) + 1)
    fig, ax = plt.subplots(figsize=(11, 6), layout="constrained")
    bar_width = 0.24
    maximum = 0
    hatches = {"singleton": "", "equivalent": "///", "budget_exhausted": "xx"}
    for stage_index, stage in enumerate(STAGES):
        counts = Counter(
            (episode["stages"][stage]["executed_steps"], episode["stages"][stage]["termination_reason"])
            for episode in episodes
        )
        x = steps + (stage_index - 1) * bar_width
        bottoms = np.zeros(len(steps), dtype=int)
        for reason, hatch in hatches.items():
            heights = np.asarray([counts[(int(step), reason)] for step in steps])
            ax.bar(x, heights, bar_width, bottom=bottoms, color=COLORS[stage], edgecolor="#333333", linewidth=0.5, hatch=hatch, alpha=0.85)
            bottoms += heights
        maximum = max(maximum, int(bottoms.max()))
        for xpos, total in zip(x, bottoms):
            if total:
                ax.text(xpos, total + maximum * 0.012, str(total), ha="center", va="bottom", fontsize=8)
    ax.set_xticks(steps)
    ax.set_xlim(steps[0] - 0.6, steps[-1] + 0.6)
    ax.set_ylim(0, maximum * 1.2)
    ax.set_xlabel("Last executed action step (t_stop)")
    ax.set_ylabel(f"Number of hidden worlds (out of {len(episodes):,})")
    ax.set_title("Exp 01 long · when full-candidate greedy certified a terminal state")
    ax.grid(axis="y", alpha=0.2)
    ax.set_axisbelow(True)
    ax.legend(handles=[
        *(Patch(facecolor=COLORS[stage], edgecolor="#333333", label=f"Stage {stage}") for stage in STAGES),
        Patch(facecolor="#bbbbbb", edgecolor="#333333", label="Singleton: one survivor"),
        Patch(facecolor="#bbbbbb", edgecolor="#333333", hatch="///", label="Equivalent: no remaining action splits survivors"),
    ], loc="upper right", fontsize=9)
    fig.savefig(output, dpi=180)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, default=DEFAULT_RUN, help="completed Exp 01 long run directory")
    args = parser.parse_args()
    _, episodes, _ = load_run(args.run, expected_run_name="exp-01-long")
    for name, mode in (("summarize.png", "percentiles"), ("summarize-mean-sd.png", "sd")):
        output = HERE / name
        save_summary(episodes, output, mode=mode)
        print(output, flush=True)
    output = HERE / "stop-step-histogram.png"
    save_stop_histogram(episodes, output)
    print(output, flush=True)


if __name__ == "__main__":
    main()
