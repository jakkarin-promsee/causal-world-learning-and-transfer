"""Plot the saved Exp 01 short-run raw trajectories without rerunning episodes.

From src/: python experiment/phase-1/track-1/exp-01-short/visualize/plot.py
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Patch


HERE = Path(__file__).resolve().parent
DEFAULT_RUN = HERE.parent / "runs" / "20261103T061845Z"
COLORS = {"A": "#0072B2", "B": "#D55E00", "C": "#009E73"}
STAGES = ("A", "B", "C")
DISPLAY_END = 18


def load_run(run_dir: Path) -> tuple[dict, list[dict]]:
    metadata = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
    if metadata["schema"] != "track1-exp01-raw-v1" or metadata["run_name"] != "exp-01-short":
        raise ValueError("expected an Exp 01 short raw run")
    indices = np.load(run_dir / metadata["selected_world_indices_file"], allow_pickle=False)
    with (run_dir / "episodes.jsonl").open(encoding="utf-8") as source:
        episodes = [json.loads(line) for line in source]
    if metadata["status"] != "complete" or len(episodes) != 10 or len(indices) != 10:
        raise ValueError("short run must have ten complete episodes")
    for position, episode in enumerate(episodes):
        if episode["sample_position"] != position or episode["world_index"] != int(indices[position]):
            raise ValueError(f"episode {position + 1} does not match saved sample order")
        if set(episode["stages"]) != set(STAGES):
            raise ValueError(f"episode {position + 1} lacks a stage")
        for stage in STAGES:
            row = episode["stages"][stage]
            if row["budget"] != metadata["budgets"][stage]:
                raise ValueError("stage budget differs from metadata")
            if len(row["uncertainty_trajectory_bits"]) != row["budget"] + 1:
                raise ValueError("trajectory length differs from budget")
            if row["executed_steps"] != len(row["steps"]):
                raise ValueError("executed-step count differs from raw steps")
            if not np.allclose(
                row["uncertainty_trajectory_bits"][1 : row["executed_steps"] + 1],
                [step["remaining_uncertainty_bits"] for step in row["steps"]],
            ):
                raise ValueError("trajectory differs from executed steps")
            if not np.isclose(row["uncertainty_trajectory_bits"][-1], np.log2(row["final_survivor_count"])):
                raise ValueError("terminal U differs from final survivor count")
    return metadata, episodes


def draw_segmented(ax, x: np.ndarray, y: np.ndarray, last_actual: int, *, color: str, width: float, alpha: float = 1.0) -> None:
    ax.plot(x[: last_actual + 1], y[: last_actual + 1], color=color, linewidth=width, alpha=alpha)
    if last_actual < len(x) - 1:
        ax.plot(x[last_actual:], y[last_actual:], color=color, linewidth=width, linestyle="--", alpha=alpha)


def style_axes(ax, initial_u: float) -> None:
    ax.set_xlim(0, DISPLAY_END)
    ax.set_ylim(-0.5, initial_u + 0.6)
    ax.set_xlabel("Action step t")
    ax.set_ylabel(r"$U_t=\log_2 |C_t|$ (bits)")
    ax.set_xticks(np.arange(0, DISPLAY_END + 1, 2))
    ax.grid(alpha=0.2)


def terminal_box(ax, lines: list[str]) -> None:
    ax.text(
        0.98, 0.73, "\n".join(lines), transform=ax.transAxes,
        ha="right", va="top", fontsize=9, fontfamily="monospace",
        bbox={"facecolor": "white", "alpha": 0.92, "edgecolor": "#cccccc", "boxstyle": "round,pad=0.5"},
    )


def save_episode(episode: dict, output: Path) -> None:
    initial_u = episode["stages"]["A"]["initial_uncertainty_bits"]
    fig, ax = plt.subplots(figsize=(12, 6.5), layout="constrained")

    def draw(target) -> None:
        for stage in STAGES:
            row = episode["stages"][stage]
            y = np.asarray(row["uncertainty_trajectory_bits"], dtype=float)
            x = np.arange(len(y))
            width = {"A": 5.0, "B": 3.5, "C": 2.0}[stage]
            draw_segmented(target, x, y, row["executed_steps"], color=COLORS[stage], width=width)

    draw(ax)
    style_axes(ax, initial_u)
    ax.set_title(f"Episode {episode['sample_position'] + 1} · hidden-world index {episode['world_index']}")
    ax.legend(handles=[
        *(Line2D([0], [0], color=COLORS[s], linewidth=2.5, label=f"Stage {s} (budget {episode['stages'][s]['budget']})") for s in STAGES),
        Line2D([0], [0], color="#555555", linewidth=2, label="Executed actions"),
        Line2D([0], [0], color="#555555", linewidth=2, linestyle="--", label="Certified inferred suffix"),
    ], loc="upper right", fontsize=9)
    terminal_box(ax, [
        "Terminal state: last actual step",
        "stage  t_stop  U_T bits  |C_T|",
        *(f"  {stage}      {episode['stages'][stage]['executed_steps']:>2}     "
          f"{episode['stages'][stage]['uncertainty_trajectory_bits'][-1]:>5.2f}    "
          f"{episode['stages'][stage]['final_survivor_count']:>4}"
          for stage in STAGES),
    ])
    fig.savefig(output, dpi=180)
    plt.close(fig)


def stage_arrays(episodes: list[dict], stage: str) -> tuple[np.ndarray, np.ndarray, int]:
    rows = [episode["stages"][stage] for episode in episodes]
    trajectories = np.asarray([row["uncertainty_trajectory_bits"] for row in rows], dtype=float)
    return np.arange(trajectories.shape[1]), trajectories, max(row["executed_steps"] for row in rows)


def save_summary(episodes: list[dict], output: Path, *, mode: str) -> None:
    initial_u = episodes[0]["stages"]["A"]["initial_uncertainty_bits"]
    fig, ax = plt.subplots(figsize=(12, 6.5), layout="constrained")

    def draw(target) -> None:
        for stage in STAGES:
            x, trajectories, last_actual = stage_arrays(episodes, stage)
            mean = trajectories.mean(axis=0)
            if mode == "individual":
                for episode, y in zip(episodes, trajectories):
                    k = episode["stages"][stage]["executed_steps"]
                    draw_segmented(target, x, y, k, color=COLORS[stage], width=0.9, alpha=0.18)
            else:
                sd = trajectories.std(axis=0, ddof=1)
                target.fill_between(
                    x, np.maximum(0, mean - sd), np.minimum(initial_u, mean + sd),
                    color=COLORS[stage], alpha=0.17, linewidth=0,
                )
            width = {"A": 5.0, "B": 3.5, "C": 2.0}[stage]
            draw_segmented(target, x, mean, last_actual, color=COLORS[stage], width=width)

    draw(ax)
    style_axes(ax, initial_u)
    if mode == "individual":
        ax.set_title("Exp 01 short · average trend and between-world variability (10 worlds)")
        variability_key = Line2D([0], [0], color="#888888", linewidth=1, alpha=0.5, label="Thin: individual worlds; thick: mean")
    else:
        ax.set_title("Exp 01 short · mean ± sample standard deviation (10 worlds)")
        variability_key = Patch(facecolor="#888888", alpha=0.2, label="±1 SD across worlds")
    ax.legend(handles=[
        *(Line2D([0], [0], color=COLORS[s], linewidth=2.5, label=f"Stage {s}") for s in STAGES),
        variability_key,
        Line2D([0], [0], color="#555555", linewidth=2, linestyle="--", label="Beyond last executed step"),
    ], loc="upper right", fontsize=9)
    terminal_box(ax, [
        "Mean terminal state (10 worlds)",
        "stage  last t  mean U_T  mean |C_T|",
        *(f"  {stage}      {max(e['stages'][stage]['executed_steps'] for e in episodes):>2}      "
          f"{np.mean([e['stages'][stage]['uncertainty_trajectory_bits'][-1] for e in episodes]):>5.2f}      "
          f"{np.mean([e['stages'][stage]['final_survivor_count'] for e in episodes]):>5.1f}"
          for stage in STAGES),
    ])
    fig.savefig(output, dpi=180)
    plt.close(fig)


def save_stop_histogram(episodes: list[dict], output: Path) -> None:
    """Count hidden worlds by the last executed action and terminal proof."""
    stops = [e["stages"][s]["executed_steps"] for e in episodes for s in STAGES]
    steps = np.arange(min(stops), max(stops) + 1)
    fig, ax = plt.subplots(figsize=(11, 6), layout="constrained")
    bar_width = 0.24
    reasons = ("singleton", "equivalent", "budget_exhausted")
    hatches = {"singleton": "", "equivalent": "///", "budget_exhausted": "xx"}
    for stage_index, stage in enumerate(STAGES):
        counts = Counter(
            (episode["stages"][stage]["executed_steps"], episode["stages"][stage]["termination_reason"])
            for episode in episodes
        )
        x = steps + (stage_index - 1) * bar_width
        bottoms = np.zeros(len(steps), dtype=int)
        for reason in reasons:
            heights = np.asarray([counts[(int(t), reason)] for t in steps])
            ax.bar(
                x, heights, bar_width, bottom=bottoms, color=COLORS[stage],
                edgecolor="#333333", linewidth=0.6, hatch=hatches[reason], alpha=0.85,
            )
            bottoms += heights
        for xpos, total in zip(x, bottoms):
            if total:
                ax.text(xpos, total + 0.08, str(total), ha="center", va="bottom", fontsize=9)
    ax.set_xticks(steps)
    ax.set_xlim(steps[0] - 0.6, steps[-1] + 0.6)
    ax.set_ylim(0, 6)
    ax.set_yticks(np.arange(0, 7))
    ax.set_xlabel("Last executed action step (t_stop)")
    ax.set_ylabel("Number of hidden worlds (out of 10)")
    ax.set_title("Exp 01 short · when full-candidate greedy certified a terminal state")
    ax.grid(axis="y", alpha=0.2)
    ax.set_axisbelow(True)
    ax.legend(handles=[
        *(Patch(facecolor=COLORS[s], edgecolor="#333333", label=f"Stage {s}") for s in STAGES),
        Patch(facecolor="#bbbbbb", edgecolor="#333333", label="Singleton: one survivor"),
        Patch(facecolor="#bbbbbb", edgecolor="#333333", hatch="///", label="Equivalent: no remaining action splits survivors"),
    ], loc="upper right", fontsize=9)
    fig.savefig(output, dpi=180)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, default=DEFAULT_RUN, help="saved Exp 01 short run directory")
    args = parser.parse_args()
    _, episodes = load_run(args.run)
    raw_dir = HERE / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    for episode in episodes:
        path = raw_dir / f"ep-{episode['sample_position'] + 1}.png"
        save_episode(episode, path)
        print(path, flush=True)
    for name, mode in (("summarize.png", "individual"), ("summarize-mean-sd.png", "sd")):
        path = HERE / name
        save_summary(episodes, path, mode=mode)
        print(path, flush=True)
    path = HERE / "stop-step-histogram.png"
    save_stop_histogram(episodes, path)
    print(path, flush=True)


if __name__ == "__main__":
    main()
