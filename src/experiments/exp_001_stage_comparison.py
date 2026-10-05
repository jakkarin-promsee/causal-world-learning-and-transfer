"""Experiment 001: compare intervention stages and action policies.

Safe smoke run from ``src``::

    python -m experiments.exp_001_stage_comparison

An early Stage-A comparison with both policies::

    python -m experiments.exp_001_stage_comparison \
        --stages A --policies random information-gain \
        --episodes 10 --budget 8 --output results/exp001-stage-a.jsonl

Stage B/C exact information-gain search can be expensive.  Start with
``--candidate-limit 32`` and report it as sampled information gain, not exact
greedy information gain.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from statistics import mean

import numpy as np

from core.evaluator import Environment
from core.oracle import ActionCatalog, ExactOracle, OnDemandResponseStore, Stage
from core.storage import WorldDataset
from core.types import World
from experiments.policies import GreedyInformationGainPolicy, RandomPolicy
from experiments.runner import EpisodeConfig, EpisodeResult, run_episode


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    default_dataset = Path(__file__).resolve().parents[1] / "datasets" / "worldgen-4-4"
    parser.add_argument("--dataset", type=Path, default=default_dataset)
    parser.add_argument("--stages", nargs="+", choices=("A", "B", "C"), default=["A"])
    parser.add_argument(
        "--policies",
        nargs="+",
        choices=("random", "information-gain"),
        default=["random"],
    )
    parser.add_argument("--episodes", type=int, default=1)
    parser.add_argument("--budget", type=int, default=1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--candidate-limit",
        type=int,
        default=None,
        help="sample this many candidate actions per information-gain step",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="optional JSONL destination; an existing file is never overwritten",
    )
    args = parser.parse_args()
    if args.episodes < 1:
        parser.error("--episodes must be at least 1")
    if args.budget < 1:
        parser.error("--budget must be at least 1")
    if args.seed < 0:
        parser.error("--seed must be non-negative")
    if args.candidate_limit is not None and args.candidate_limit < 1:
        parser.error("--candidate-limit must be at least 1")
    return args


def sample_world_indices(
    world_count: int,
    episode_count: int,
    seed: int,
) -> tuple[int, ...]:
    if episode_count > world_count:
        raise ValueError("episode count exceeds the number of available worlds")
    rng = np.random.default_rng(seed)
    indices = rng.choice(world_count, size=episode_count, replace=False)
    return tuple(int(index) for index in indices)


def load_selected_worlds(
    dataset: WorldDataset,
    indices: tuple[int, ...],
) -> dict[int, World]:
    wanted = set(indices)
    selected: dict[int, World] = {}
    for world_index, world in enumerate(dataset):
        if world_index in wanted:
            selected[world_index] = world
            if len(selected) == len(wanted):
                break
    if len(selected) != len(wanted):
        missing = sorted(wanted - selected.keys())
        raise RuntimeError(f"dataset did not contain requested worlds: {missing}")
    return selected


def make_policy(
    policy_kind: str,
    oracle: ExactOracle,
    *,
    seed: int,
    candidate_limit: int | None,
):
    if policy_kind == "random":
        return RandomPolicy(seed)
    if policy_kind == "information-gain":
        return GreedyInformationGainPolicy(
            oracle,
            candidate_limit=candidate_limit,
            seed=seed,
        )
    raise ValueError(f"unknown policy: {policy_kind}")


def result_record(result: EpisodeResult) -> dict[str, object]:
    record = asdict(result)
    config = record["config"]
    assert isinstance(config, dict)
    config["stage"] = result.config.stage.name
    return record


def write_results(path: Path, results: list[EpisodeResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="") as output:
        for result in results:
            json.dump(result_record(result), output, separators=(",", ":"))
            output.write("\n")


def print_summary(results: list[EpisodeResult]) -> None:
    groups: dict[tuple[str, str], list[EpisodeResult]] = {}
    for result in results:
        key = (result.config.stage.name, result.policy_name)
        groups.setdefault(key, []).append(result)

    print("stage\tpolicy\tepisodes\tmean_final_survivors\tmean_final_bits")
    for (stage, policy_name), group in sorted(groups.items()):
        print(
            f"{stage}\t{policy_name}\t{len(group)}\t"
            f"{mean(item.final_survivor_count for item in group):.3f}\t"
            f"{mean(item.steps[-1].remaining_uncertainty_bits for item in group):.3f}"
        )


def main() -> None:
    args = parse_args()
    dataset = WorldDataset(args.dataset)
    catalog = ActionCatalog(dataset.spec)
    responses = OnDemandResponseStore(dataset, len(dataset), catalog)
    world_indices = sample_world_indices(len(dataset), args.episodes, args.seed)
    selected_worlds = load_selected_worlds(dataset, world_indices)

    results: list[EpisodeResult] = []
    for stage_name in args.stages:
        stage = Stage[stage_name]
        oracle = ExactOracle(catalog, responses, stage=stage)
        action_count = len(catalog.entries_for_stage(stage))
        if args.budget > action_count:
            raise ValueError(
                f"budget {args.budget} exceeds Stage {stage.name}'s "
                f"{action_count} actions"
            )

        for policy_index, policy_kind in enumerate(args.policies):
            for episode_index, world_index in enumerate(world_indices):
                episode_seed = (
                    args.seed
                    + 1_000_003 * episode_index
                    + 10_007 * int(stage)
                    + 101 * policy_index
                )
                policy = make_policy(
                    policy_kind,
                    oracle,
                    seed=episode_seed,
                    candidate_limit=args.candidate_limit,
                )
                result = run_episode(
                    world_index=world_index,
                    environment=Environment(
                        selected_worlds[world_index],
                        dataset.spec,
                    ),
                    oracle=oracle,
                    policy=policy,
                    config=EpisodeConfig(
                        stage=stage,
                        budget=args.budget,
                        seed=episode_seed,
                    ),
                )
                results.append(result)

    print_summary(results)
    if args.output is not None:
        write_results(args.output, results)
        print(f"wrote {len(results)} episode records to {args.output}")


if __name__ == "__main__":
    main()
