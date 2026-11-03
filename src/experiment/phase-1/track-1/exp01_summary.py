"""Shared numerical summaries for paired Exp 01 short and long raw runs."""

from __future__ import annotations

import hashlib
import json
import math
import statistics
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


STAGES = ("A", "B", "C")
PAIRS = (("A", "B"), ("A", "C"), ("B", "C"))
PATTERNS = ("all_equal", "b_c_equal_a_differs", "c_differs_both", "a_c_equal_b_differs")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def count_rate(count: int, denominator: int) -> dict:
    return {"count": count, "denominator": denominator, "percent": 100 * count / denominator if denominator else None}


def mean_sd(values: list[int | float]) -> dict:
    return {
        "mean": statistics.mean(values),
        "sample_sd": statistics.stdev(values) if len(values) > 1 else None,
        "min": min(values),
        "max": max(values),
    }


def load_run(run_dir: Path, *, expected_run_name: str) -> tuple[dict, list[dict], Path]:
    metadata = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
    if metadata["schema"] != "track1-exp01-raw-v1" or metadata["run_name"] != expected_run_name:
        raise ValueError(f"expected a {expected_run_name} raw run")
    allowed_statuses = {"complete"} if expected_run_name == "exp-01-short" else {"time_cap_reached", "complete"}
    if metadata["status"] not in allowed_statuses:
        raise ValueError(f"run status is {metadata['status']!r}, expected a completed run")
    indices_path = run_dir / metadata["selected_world_indices_file"]
    if sha256_file(indices_path) != metadata["selected_world_indices_sha256"]:
        raise ValueError("saved world order does not match metadata hash")
    indices = np.load(indices_path, allow_pickle=False)
    raw_path = run_dir / "episodes.jsonl"
    with raw_path.open(encoding="utf-8") as source:
        episodes = [json.loads(line) for line in source]
    if len(episodes) > len(indices) or len(episodes) != metadata["completed_worlds"]:
        raise ValueError("episode count does not match saved order and metadata")
    if not episodes:
        raise ValueError("run has no completed worlds")
    for position, episode in enumerate(episodes):
        if episode["sample_position"] != position or episode["world_index"] != int(indices[position]):
            raise ValueError(f"episode {position + 1} is out of sample order")
        if set(episode["stages"]) != set(STAGES):
            raise ValueError(f"episode {position + 1} lacks a stage")
        for stage in STAGES:
            row = episode["stages"][stage]
            if row["executed_steps"] != len(row["steps"]):
                raise ValueError("executed step count differs from action trace")
            if row["budget"] != metadata["budgets"][stage]:
                raise ValueError("stage budget differs from metadata")
            if len(row["uncertainty_trajectory_bits"]) != row["budget"] + 1:
                raise ValueError("terminal trajectory is incomplete")
            if not math.isclose(row["uncertainty_trajectory_bits"][-1], math.log2(row["final_survivor_count"]), abs_tol=1e-10):
                raise ValueError("final U does not match final survivor count")
            reason = row["termination_reason"]
            if (reason == "singleton") != (row["final_survivor_count"] == 1):
                raise ValueError("singleton reason and final survivor count disagree")
            if reason not in {"singleton", "equivalent", "budget_exhausted"}:
                raise ValueError(f"unknown termination reason: {reason}")
    return metadata, episodes, raw_path


def equality_pattern(a, b, c) -> str:
    if a == b == c:
        return "all_equal"
    if b == c:
        return "b_c_equal_a_differs"
    if c != a and c != b:
        return "c_differs_both"
    return "a_c_equal_b_differs"


def action_ids(episode: dict, stage: str) -> tuple[int, ...]:
    return tuple(step["action_id"] for step in episode["stages"][stage]["steps"])


def compare_actions(first: tuple[int, ...], second: tuple[int, ...]) -> dict:
    comparable = min(len(first), len(second))
    same = sum(first[t] == second[t] for t in range(comparable))
    prefix = 0
    for first_id, second_id in zip(first, second):
        if first_id != second_id:
            break
        prefix += 1
    return {
        "comparable_steps": comparable,
        "same_action_id": count_rate(same, comparable),
        "different_action_id": count_rate(comparable - same, comparable),
        "shared_prefix": count_rate(prefix, comparable),
        "extra_actions_first": len(first) - comparable,
        "extra_actions_second": len(second) - comparable,
    }


def aggregate_action_comparisons(records: list[dict], pair: str) -> dict:
    rows = [record["action_comparisons"][pair] for record in records]
    comparable = sum(row["comparable_steps"] for row in rows)
    same = sum(row["same_action_id"]["count"] for row in rows)
    prefix = sum(row["shared_prefix"]["count"] for row in rows)
    return {
        "episodes": len(rows),
        "comparable_steps": comparable,
        "same_action_id": count_rate(same, comparable),
        "different_action_id": count_rate(comparable - same, comparable),
        "shared_prefix": count_rate(prefix, comparable),
        "extra_actions_first": sum(row["extra_actions_first"] for row in rows),
        "extra_actions_second": sum(row["extra_actions_second"] for row in rows),
    }


def compare_stop_steps(records: list[dict], first: str, second: str) -> dict:
    """Compare terminal action counts within one action-trace category."""
    deltas = [
        record["terminal_by_stage"][second]["stop_step"]
        - record["terminal_by_stage"][first]["stop_step"]
        for record in records
    ]
    n = len(deltas)
    return {
        "episodes": n,
        "first_earlier": count_rate(sum(delta > 0 for delta in deltas), n),
        "tie": count_rate(sum(delta == 0 for delta in deltas), n),
        "second_earlier": count_rate(sum(delta < 0 for delta in deltas), n),
        "signed_delta_second_minus_first_steps": mean_sd(deltas) if deltas else None,
        "absolute_delta_steps": mean_sd([abs(delta) for delta in deltas]) if deltas else None,
    }


def compare_stops_by_final_u(records: list[dict], first: str, second: str) -> dict:
    """Keep stop order and terminal equality separate within a trace group."""
    result = compare_stop_steps(records, first, second)
    equality = {}
    for label, same in (("same_final_u", True), ("different_final_u", False)):
        selected = [
            record for record in records
            if (
                record["terminal_by_stage"][first]["final_survivor_count"]
                == record["terminal_by_stage"][second]["final_survivor_count"]
            ) == same
        ]
        equality[label] = {
            "share_of_trace_group": count_rate(len(selected), len(records)),
            **compare_stop_steps(selected, first, second),
        }
    result["by_final_u_equality"] = equality
    return result


def summarize(run_dir: Path, *, expected_run_name: str) -> dict:
    metadata, episodes, raw_path = load_run(run_dir, expected_run_name=expected_run_name)
    n = len(episodes)
    per_episode = []
    for episode in episodes:
        actions = {stage: action_ids(episode, stage) for stage in STAGES}
        survivors = {stage: episode["stages"][stage]["final_survivor_count"] for stage in STAGES}
        stops = {stage: episode["stages"][stage]["executed_steps"] for stage in STAGES}
        per_episode.append({
            "episode": episode["sample_position"] + 1,
            "world_index": episode["world_index"],
            "action_trace_pattern": equality_pattern(*(actions[s] for s in STAGES)),
            "final_survivor_pattern": equality_pattern(*(survivors[s] for s in STAGES)),
            "terminal_by_stage": {
                stage: {
                    "stop_step": stops[stage],
                    "final_uncertainty_bits": episode["stages"][stage]["uncertainty_trajectory_bits"][-1],
                    "final_survivor_count": survivors[stage],
                    "termination_reason": episode["stages"][stage]["termination_reason"],
                }
                for stage in STAGES
            },
            "action_comparisons": {
                f"{first}_vs_{second}": compare_actions(actions[first], actions[second])
                for first, second in PAIRS
            },
        })

    terminal = {}
    for stage in STAGES:
        rows = [record["terminal_by_stage"][stage] for record in per_episode]
        reasons = Counter(row["termination_reason"] for row in rows)
        terminal[stage] = {
            "final_uncertainty_bits": mean_sd([row["final_uncertainty_bits"] for row in rows]),
            "final_survivor_count": mean_sd([row["final_survivor_count"] for row in rows]),
            "stop_step": mean_sd([row["stop_step"] for row in rows]),
            "termination_reason": {reason: count_rate(reasons[reason], n) for reason in ("singleton", "equivalent", "budget_exhausted")},
        }

    pattern_results = {}
    for key, field in (("action_trace", "action_trace_pattern"), ("final_survivor", "final_survivor_pattern")):
        pattern_results[key] = {
            pattern: {
                **count_rate(sum(record[field] == pattern for record in per_episode), n),
                "episodes": [record["episode"] for record in per_episode if record[field] == pattern],
            }
            for pattern in PATTERNS
        }
        if sum(row["count"] for row in pattern_results[key].values()) != n:
            raise AssertionError("equality patterns do not partition episodes")

    stop_order = {}
    for first, second in PAIRS:
        first_steps = [r["terminal_by_stage"][first]["stop_step"] for r in per_episode]
        second_steps = [r["terminal_by_stage"][second]["stop_step"] for r in per_episode]
        stop_order[f"{first}_vs_{second}"] = {
            f"{first}_earlier": count_rate(sum(a < b for a, b in zip(first_steps, second_steps)), n),
            "tie": count_rate(sum(a == b for a, b in zip(first_steps, second_steps)), n),
            f"{second}_earlier": count_rate(sum(a > b for a, b in zip(first_steps, second_steps)), n),
        }
    strict_first = {}
    for stage in STAGES:
        count = sum(
            all(record["terminal_by_stage"][stage]["stop_step"] < record["terminal_by_stage"][other]["stop_step"]
                for other in STAGES if other != stage)
            for record in per_episode
        )
        strict_first[stage] = count_rate(count, n)
    strict_first["tie_for_first"] = count_rate(n - sum(row["count"] for row in strict_first.values()), n)
    grouped_stop_order = {
        pattern: {
            f"{first}_vs_{second}": compare_stops_by_final_u(
                [record for record in per_episode if record["action_trace_pattern"] == pattern], first, second
            )
            for first, second in PAIRS
        }
        for pattern in PATTERNS
    }

    return {
        "schema": "track1-exp01-numeric-summary-v4",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": {
            "run_name": metadata["run_name"],
            "run_status": metadata["status"],
            "elapsed_seconds": metadata["elapsed_seconds"],
            "run_directory": str(run_dir.resolve()),
            "episodes_jsonl_sha256": sha256_file(raw_path),
            "selected_world_indices_sha256": metadata["selected_world_indices_sha256"],
            "worlds_sha256": metadata["worlds_sha256"],
            "policy": metadata["policy"],
            "candidate_limit": metadata["candidate_limit"],
        },
        "worlds": n,
        "definitions": {
            "unit": "paired hidden world",
            "sd": "sample standard deviation across worlds (ddof=1)",
            "action_trace_equal": "same number and ordered IDs of actually executed actions",
            "action_match_denominator": "steps at which both compared stages executed an action; extra actions excluded",
            "shared_prefix": "consecutive same action IDs from step 1 until the first mismatch, divided by comparable executed steps; aggregate ratio pools numerator and denominator across worlds",
            "percentage_denominator": "completed paired worlds for episode counts; comparable steps for action-ID matches; worlds within the named action-trace category for grouped stop order",
            "stop_step": "number of actually executed actions before singleton or certified equivalence",
            "grouped_stop_delta": "second-stage stop step minus first-stage stop step; positive means the first stage stopped earlier; absolute delta avoids cancellation",
            "final_u_equality": "exact equality of final survivor counts, equivalent to equality of log2 survivor counts; subgroup stop percentages use subgroup worlds",
            "mean_terminal_u_and_c": "computed separately across worlds; mean U is not log2(mean C)",
        },
        "terminal_by_stage": terminal,
        "equality_patterns": pattern_results,
        "inclusive_equality": {
            key: {
                "B_equals_C": count_rate(sum(r[field] in {"all_equal", "b_c_equal_a_differs"} for r in per_episode), n),
                "A_equals_B_equals_C": pattern_results[key]["all_equal"],
            }
            for key, field in (("action_trace", "action_trace_pattern"), ("final_survivor", "final_survivor_pattern"))
        },
        "action_comparisons": {
            "all_worlds": {
                f"{a}_vs_{b}": aggregate_action_comparisons(per_episode, f"{a}_vs_{b}") for a, b in PAIRS
            },
            "by_action_trace_pattern": {
                pattern: {
                    f"{a}_vs_{b}": aggregate_action_comparisons(
                        [r for r in per_episode if r["action_trace_pattern"] == pattern], f"{a}_vs_{b}"
                    )
                    for a, b in PAIRS
                }
                for pattern in PATTERNS
            },
        },
        "stop_order": {"pairwise": stop_order, "strict_first": strict_first, "by_action_trace_pattern": grouped_stop_order},
        "per_episode": per_episode,
    }


def rate_text(rate: dict) -> str:
    return f"{rate['count']}/{rate['denominator']} ({rate['percent']:.1f}%)" if rate["percent"] is not None else "0/0 (n/a)"


def append_overlap(lines: list[str], label: str, row: dict, first: str, second: str) -> None:
    lines.append(f"    {label}")
    lines.append(f"      same-step IDs: {rate_text(row['same_action_id'])}; different: {rate_text(row['different_action_id'])}")
    lines.append(f"      shared prefix: {rate_text(row['shared_prefix'])}; extra actions: {first}={row['extra_actions_first']}, {second}={row['extra_actions_second']}")


def append_stop_timing(lines: list[str], row: dict, first: str, second: str) -> None:
    lines.append(f"      terminal stop: {first} earlier {rate_text(row['first_earlier'])}; {second} earlier {rate_text(row['second_earlier'])}; tie {rate_text(row['tie'])}")
    if row["episodes"]:
        signed = row["signed_delta_second_minus_first_steps"]["mean"]
        absolute = row["absolute_delta_steps"]["mean"]
        lines.append(f"      mean (t_{second} - t_{first}) = {signed:+.2f} steps; mean absolute gap = {absolute:.2f} steps")
    for label, title in (("same_final_u", "same final U_T"), ("different_final_u", "different final U_T")):
        subgroup = row["by_final_u_equality"][label]
        lines.append(f"      {title}: {rate_text(subgroup['share_of_trace_group'])} of this trace group")
        if subgroup["episodes"]:
            signed = subgroup["signed_delta_second_minus_first_steps"]["mean"]
            absolute = subgroup["absolute_delta_steps"]["mean"]
            lines.append(f"        {first} earlier {rate_text(subgroup['first_earlier'])}; {second} earlier {rate_text(subgroup['second_earlier'])}; tie {rate_text(subgroup['tie'])}")
            lines.append(f"        mean signed gap {signed:+.2f} steps; mean absolute gap {absolute:.2f} steps")


def format_report(result: dict) -> str:
    lines = [f"{result['source']['run_name']} numeric summary | {result['worlds']} paired hidden worlds", ""]
    lines.append("1. LAST-STEP INFORMATION (mean +/- sample SD)")
    lines.append("Stage | final U_T bits | final |C_T| worlds | stop step")
    for stage in STAGES:
        row = result["terminal_by_stage"][stage]
        u, c, t = (row[key] for key in ("final_uncertainty_bits", "final_survivor_count", "stop_step"))
        lines.append(f"  {stage}   | {u['mean']:.3f} +/- {u['sample_sd']:.3f} | {c['mean']:.3f} +/- {c['sample_sd']:.3f} | {t['mean']:.3f} +/- {t['sample_sd']:.3f}")
        reasons = row["termination_reason"]
        lines.append(f"      singleton {rate_text(reasons['singleton'])}; equivalent {rate_text(reasons['equivalent'])}; budget exhausted {rate_text(reasons['budget_exhausted'])}")

    trace = result["equality_patterns"]["action_trace"]
    grouped = result["action_comparisons"]["by_action_trace_pattern"]
    grouped_stops = result["stop_order"]["by_action_trace_pattern"]
    lines.extend(["", "2. ACTION-TRACE PATTERNS (exclusive; denominator = paired worlds)"])
    lines.append(f"  A=B=C: {rate_text(trace['all_equal'])}")
    lines.append(f"  B=C, A differs: {rate_text(trace['b_c_equal_a_differs'])}")
    append_overlap(lines, "B/C vs A:", grouped["b_c_equal_a_differs"]["A_vs_B"], "A", "B/C each")
    append_stop_timing(lines, grouped_stops["b_c_equal_a_differs"]["A_vs_B"], "A", "B/C")
    lines.append(f"  C differs from A and B: {rate_text(trace['c_differs_both'])}")
    append_overlap(lines, "B vs A:", grouped["c_differs_both"]["A_vs_B"], "A", "B")
    append_overlap(lines, "C vs A:", grouped["c_differs_both"]["A_vs_C"], "A", "C")
    append_overlap(lines, "C vs B:", grouped["c_differs_both"]["B_vs_C"], "B", "C")
    append_stop_timing(lines, grouped_stops["c_differs_both"]["B_vs_C"], "B", "C")
    residual = trace["a_c_equal_b_differs"]
    if residual["count"]:
        lines.append(f"  A=C, B differs (outside requested hierarchy): {rate_text(residual)}")
    lines.append(f"  B=C inclusive (includes A=B=C): {rate_text(result['inclusive_equality']['action_trace']['B_equals_C'])}")

    final = result["equality_patterns"]["final_survivor"]
    lines.extend(["", "3. FINAL-SURVIVOR PATTERNS (exclusive; denominator = paired worlds)"])
    lines.append(f"  A=B=C: {rate_text(final['all_equal'])}")
    lines.append(f"  B=C, A differs: {rate_text(final['b_c_equal_a_differs'])}")
    lines.append(f"  C differs from A and B: {rate_text(final['c_differs_both'])}")
    residual = final["a_c_equal_b_differs"]
    if residual["count"]:
        lines.append(f"  A=C, B differs (outside requested hierarchy): {rate_text(residual)}")
    lines.append(f"  B=C inclusive (includes A=B=C): {rate_text(result['inclusive_equality']['final_survivor']['B_equals_C'])}")

    lines.extend(["", "4. STOP-STEP ORDER (denominator = paired worlds)"])
    for first, second in PAIRS:
        row = result["stop_order"]["pairwise"][f"{first}_vs_{second}"]
        lines.append(f"  {first} earlier than {second}: {rate_text(row[f'{first}_earlier'])}; tie: {rate_text(row['tie'])}; {second} earlier: {rate_text(row[f'{second}_earlier'])}")
    lines.append("Strictly first to stop (before both other stages):")
    for key, row in result["stop_order"]["strict_first"].items():
        lines.append(f"  {key}: {rate_text(row)}")

    lines.append("")
    lines.append("Action overlap uses steps both stages executed; grouped stop percentages use worlds in that group. A stop may be a singleton or certified equivalence.")
    return "\n".join(lines)
