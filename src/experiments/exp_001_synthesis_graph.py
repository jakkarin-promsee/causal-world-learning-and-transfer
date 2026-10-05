"""Plot episode trajectories recorded by Experiment 001.

Run from ``src`` after ``exp_001_stage_comparison`` has written JSONL::

    python -m experiments.exp_001_synthesis_graph results/exp001-stage-a.jsonl

The figure contains one line per (stage, policy) condition.  Pale lines show
individual worlds; the darker line and band show an across-episode mean and
an approximate 95% confidence interval.  Compatible-world counts use a
geometric mean because that panel is displayed on a logarithmic scale.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")  # This is an experiment artifact, not an interactive UI.
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes


@dataclass(frozen=True)
class EpisodeTrajectory:
    """Measurements from one JSONL episode, arranged for plotting."""

    stage: str
    policy: str
    world_index: int
    survivors: np.ndarray
    uncertainty_bits: np.ndarray
    predictive_entropy_bits: np.ndarray
    realized_information_gain_bits: np.ndarray

    @property
    def label(self) -> str:
        return f"Stage {self.stage} · {self.policy.replace('_', ' ')}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "inputs",
        nargs="+",
        type=Path,
        help="one or more JSONL files written by exp_001_stage_comparison",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="PNG destination (default: next to the first input, with .png)",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=180,
        help="PNG resolution (default: 180)",
    )
    args = parser.parse_args()
    if args.dpi < 72:
        parser.error("--dpi must be at least 72")
    return args


def _require(mapping: dict[str, Any], key: str, *, source: str) -> Any:
    if key not in mapping:
        raise ValueError(f"{source}: missing {key!r}")
    return mapping[key]


def parse_episode(record: object, *, source: str) -> EpisodeTrajectory:
    """Validate one JSON object and turn its step records into arrays."""

    if not isinstance(record, dict):
        raise ValueError(f"{source}: expected a JSON object")
    config = _require(record, "config", source=source)
    steps = _require(record, "steps", source=source)
    if not isinstance(config, dict) or not isinstance(steps, list) or not steps:
        raise ValueError(f"{source}: config must be an object and steps a non-empty list")

    stage = _require(config, "stage", source=source)
    policy = _require(record, "policy_name", source=source)
    world_index = _require(record, "world_index", source=source)
    if not isinstance(stage, str) or not isinstance(policy, str) or not isinstance(world_index, int):
        raise ValueError(f"{source}: invalid stage, policy_name, or world_index")

    survivors: list[float] = []
    uncertainty_bits: list[float] = []
    predictive_entropy_bits: list[float] = []
    realized_information_gain_bits: list[float] = []
    for expected_timestep, step in enumerate(steps):
        if not isinstance(step, dict):
            raise ValueError(f"{source}: step {expected_timestep} is not an object")
        timestep = _require(step, "timestep", source=source)
        if timestep != expected_timestep:
            raise ValueError(f"{source}: steps must have consecutive timesteps from zero")
        before = _require(step, "survivor_count_before", source=source)
        after = _require(step, "survivor_count_after", source=source)
        remaining = _require(step, "remaining_uncertainty_bits", source=source)
        predictive = _require(step, "predictive_entropy_bits", source=source)
        realized = _require(step, "realized_information_gain_bits", source=source)
        values = (before, after, remaining, predictive, realized)
        if any(not isinstance(value, (int, float)) for value in values):
            raise ValueError(f"{source}: step {expected_timestep} contains a non-numeric measurement")
        if before < 1 or after < 1:
            raise ValueError(f"{source}: survivor counts must be positive")
        if expected_timestep == 0:
            survivors.append(float(before))
            uncertainty_bits.append(math.log2(before))
        elif int(before) != int(survivors[-1]):
            raise ValueError(f"{source}: survivor counts do not connect between steps")
        survivors.append(float(after))
        uncertainty_bits.append(float(remaining))
        predictive_entropy_bits.append(float(predictive))
        realized_information_gain_bits.append(float(realized))

    return EpisodeTrajectory(
        stage=stage,
        policy=policy,
        world_index=world_index,
        survivors=np.asarray(survivors),
        uncertainty_bits=np.asarray(uncertainty_bits),
        predictive_entropy_bits=np.asarray(predictive_entropy_bits),
        realized_information_gain_bits=np.asarray(realized_information_gain_bits),
    )


def load_episodes(paths: list[Path]) -> list[EpisodeTrajectory]:
    """Load all non-empty JSONL records, with locations in parse errors."""

    episodes: list[EpisodeTrajectory] = []
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(f"input JSONL file does not exist: {path}")
        with path.open(encoding="utf-8") as input_file:
            for line_number, line in enumerate(input_file, start=1):
                if not line.strip():
                    continue
                source = f"{path}:{line_number}"
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as error:
                    raise ValueError(f"{source}: invalid JSON ({error.msg})") from error
                episodes.append(parse_episode(record, source=source))
    if not episodes:
        raise ValueError("input files contained no episode records")
    return episodes


def grouped(episodes: list[EpisodeTrajectory]) -> dict[tuple[str, str], list[EpisodeTrajectory]]:
    groups: dict[tuple[str, str], list[EpisodeTrajectory]] = defaultdict(list)
    for episode in episodes:
        groups[(episode.stage, episode.policy)].append(episode)
    return dict(sorted(groups.items()))


def padded_matrix(values: list[np.ndarray]) -> np.ndarray:
    """Pad possibly different episode budgets with NaN for aligned aggregation."""

    longest = max(len(value) for value in values)
    matrix = np.full((len(values), longest), np.nan)
    for row, value in enumerate(values):
        matrix[row, : len(value)] = value
    return matrix


def mean_and_ci(matrix: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return mean and approximate normal 95% CI, ignoring padded values."""

    count = np.sum(~np.isnan(matrix), axis=0)
    average = np.nanmean(matrix, axis=0)
    squared_deviation = np.nansum((matrix - average) ** 2, axis=0)
    sample_variance = np.divide(
        squared_deviation,
        count - 1,
        out=np.zeros_like(average),
        where=count > 1,
    )
    sample_std = np.sqrt(sample_variance)
    standard_error = np.divide(
        sample_std,
        np.sqrt(count),
        out=np.zeros_like(average),
        where=count > 1,
    )
    interval = 1.96 * standard_error
    return average, average - interval, average + interval


def plot_trajectory(
    axis: Axes,
    values: list[np.ndarray],
    *,
    label: str,
    color: str,
    log_scale: bool = False,
    line_style: str = "-",
) -> None:
    """Draw per-world trajectories plus their aggregate mean and CI."""

    matrix = padded_matrix(values)
    x = np.arange(matrix.shape[1])
    for row in matrix:
        valid = ~np.isnan(row)
        axis.plot(x[valid], row[valid], color=color, alpha=0.14, linewidth=1)
    if log_scale:
        # Count data span several orders of magnitude.  Computing the interval
        # in log space keeps its lower bound positive and makes the summary
        # match the visual scale.  Back-transforming gives a geometric mean.
        average, lower, upper = mean_and_ci(np.log10(matrix))
        average, lower, upper = (10.0**average, 10.0**lower, 10.0**upper)
    else:
        average, lower, upper = mean_and_ci(matrix)
    valid = ~np.isnan(average)
    axis.plot(x[valid], average[valid], color=color, linewidth=2.5, linestyle=line_style, label=label)
    axis.fill_between(x[valid], lower[valid], upper[valid], color=color, alpha=0.16)
    if log_scale:
        axis.set_yscale("log")


def create_figure(episodes: list[EpisodeTrajectory]) -> plt.Figure:
    """Create the four-panel experiment summary figure."""

    conditions = grouped(episodes)
    figure, axes = plt.subplots(2, 2, figsize=(13, 9), constrained_layout=True)
    survivor_axis, uncertainty_axis, gain_axis, information_axis = axes.flat
    colors = plt.get_cmap("tab10")

    for index, ((_, _), group) in enumerate(conditions.items()):
        color = colors(index % 10)
        label = group[0].label
        plot_trajectory(
            survivor_axis,
            [episode.survivors for episode in group],
            label=label,
            color=color,
            log_scale=True,
        )
        plot_trajectory(
            uncertainty_axis,
            [episode.uncertainty_bits for episode in group],
            label=label,
            color=color,
        )
        plot_trajectory(
            gain_axis,
            [episode.realized_information_gain_bits for episode in group],
            label=label,
            color=color,
        )
        plot_trajectory(
            information_axis,
            [episode.predictive_entropy_bits for episode in group],
            label=f"{label} expected",
            color=color,
            line_style="--",
        )
        plot_trajectory(
            information_axis,
            [episode.realized_information_gain_bits for episode in group],
            label=f"{label} realized",
            color=color,
        )

    survivor_axis.set_title("Compatible worlds remaining")
    survivor_axis.set_ylabel("worlds (log scale)")
    uncertainty_axis.set_title("Posterior uncertainty remaining")
    uncertainty_axis.set_ylabel("bits")
    gain_axis.set_title("Realized information gained per action")
    gain_axis.set_ylabel("bits")
    information_axis.set_title("Expected vs. realized information per action")
    information_axis.set_ylabel("bits")

    for axis in axes.flat:
        axis.set_xlabel("actions used")
        axis.grid(alpha=0.25)
    gain_axis.set_xlabel("action number (the gain after that action)")
    information_axis.set_xlabel("action number (the score before that action)")
    survivor_axis.legend(fontsize=9)
    uncertainty_axis.legend(fontsize=9)
    gain_axis.legend(fontsize=9)
    information_axis.legend(fontsize=8, ncols=2)
    figure.suptitle(
        "Experiment 001: intervention-stage and policy trajectories\n"
        "dark line = episode mean (geometric for worlds); shaded band = approximate 95% CI; "
        "pale lines = individual worlds",
        fontsize=14,
    )
    return figure


def main() -> None:
    args = parse_args()
    episodes = load_episodes(args.inputs)
    output = args.output or args.inputs[0].with_suffix(".png")
    output.parent.mkdir(parents=True, exist_ok=True)
    figure = create_figure(episodes)
    figure.savefig(output, dpi=args.dpi, bbox_inches="tight")
    plt.close(figure)
    print(f"wrote {output} ({len(episodes)} episodes, {len(grouped(episodes))} conditions)")


if __name__ == "__main__":
    main()
