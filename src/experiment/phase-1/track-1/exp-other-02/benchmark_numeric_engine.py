"""Compare JSONL and numeric response costs and estimate full-candidate startup.

Run from src: python experiment/phase-1/track-1/exp-other-02/benchmark_numeric_engine.py
This measures computation, not stage behavior or scientific performance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import tempfile
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import median

SOURCE_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(SOURCE_ROOT))

import numpy as np

from core.evaluator import Environment
from core.oracle import ActionCatalog, ExactOracle, OnDemandResponseStore, Stage
from core.storage import WorldDataset
from core.types import Intervention
from reuse.numeric_engine import NumericResponseStore, NumericWorldDataset
from reuse.numeric_engine.policies import GreedyInformationGainPolicy
from reuse.numeric_engine.runner import EpisodeConfig, run_full_candidate_greedy_episode

HERE = Path(__file__).resolve().parent
JSONL_DATASET = SOURCE_ROOT / "dataset" / "worldgen-4-4"
NUMERIC_DATASET = SOURCE_ROOT / "dataset" / "worldgen-4-4-npy"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def timed(call):
    start = time.perf_counter()
    value = call()
    return time.perf_counter() - start, value


def representative_actions(catalog: ActionCatalog) -> list[dict]:
    """One deterministic intervention per number of forced Y nodes."""
    x = (0,) * catalog.spec.d
    rows = []
    for forced_count in range(catalog.spec.m + 1):
        y = (1,) * forced_count + (None,) * (catalog.spec.m - forced_count)
        action_id = catalog.action_id_for(Intervention(x=x, y=y))
        rows.append({"forced_y": forced_count, "action_id": action_id})
    return rows


def stage_counts(catalog: ActionCatalog) -> dict[str, dict[int, int]]:
    return {
        stage.name: dict(sorted(Counter(
            sum(value is not None for value in entry.intervention.y)
            for entry in catalog.entries_for_stage(stage)
        ).items()))
        for stage in Stage
    }


def estimate(rows: list[dict], counts: dict[str, dict[int, int]]) -> dict:
    by_forced = {row["forced_y"]: row for row in rows}
    if set(by_forced) != set(range(5)):
        return {}
    result = {}
    for stage, strata in counts.items():
        result[stage] = {
            "action_count": sum(strata.values()),
            "jsonl_cold_columns_seconds": sum(
                count * by_forced[k]["jsonl_cold_seconds"] for k, count in strata.items()
            ),
            "numeric_cold_columns_seconds": sum(
                count * by_forced[k]["numeric_cold_seconds"] for k, count in strata.items()
            ),
            "numeric_disk_reload_seconds": sum(
                count * by_forced[k]["numeric_disk_reload_seconds"] for k, count in strata.items()
            ),
            "numeric_one_initial_greedy_score_seconds": sum(
                count * by_forced[k]["numeric_policy_score_seconds_per_candidate"]
                for k, count in strata.items()
            ),
        }
    return result


def benchmark_stage(stage: Stage, worlds: NumericWorldDataset, catalog: ActionCatalog, cache_dir: Path) -> dict:
    """One real full-budget episode and a second episode reusing its columns."""
    store = NumericResponseStore(worlds, catalog, cache_dir=cache_dir)
    oracle = ExactOracle(catalog, store, stage=stage)
    budget = len(catalog.entries_for_stage(stage))
    episodes = []
    for world_index in (0, 1):
        duration, result = timed(lambda: run_full_candidate_greedy_episode(
            world_index=world_index,
            environment=Environment(worlds.world_at(world_index), worlds.spec),
            oracle=oracle,
            config=EpisodeConfig(stage=stage, budget=budget, seed=0),
        ))
        episodes.append({
            "world_index": world_index,
            "seconds": duration,
            "executed_steps": len(result.episode.steps),
            "termination_reason": result.termination_reason,
            "final_survivors": result.final_survivor_count,
            "cached_columns_after": len(store.cached_action_ids),
        })
    return {"stage": stage.name, "budget": budget, "episodes": episodes}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jsonl-dataset", type=Path, default=JSONL_DATASET)
    parser.add_argument("--numeric-dataset", type=Path, default=NUMERIC_DATASET)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--warm-repeats", type=int, default=20)
    parser.add_argument("--chunk-size", type=int, default=100_000)
    parser.add_argument("--skip-episodes", action="store_true")
    args = parser.parse_args()
    if args.warm_repeats < 1 or args.chunk_size < 1:
        parser.error("--warm-repeats and --chunk-size must be positive")

    jsonl_load, jsonl = timed(lambda: WorldDataset(args.jsonl_dataset))
    numeric_load, numeric = timed(lambda: NumericWorldDataset(args.numeric_dataset))
    if jsonl.spec != numeric.spec or len(jsonl) != len(numeric):
        raise ValueError("JSONL and numeric datasets do not describe the same world family")
    if (numeric.spec.d, numeric.spec.m) != (4, 4):
        parser.error("the representative action strata are defined for d=4, m=4")
    catalog = ActionCatalog(numeric.spec)
    output = args.output or HERE / "runs" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output.mkdir(parents=True, exist_ok=False)
    try:
        git_revision = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=SOURCE_ROOT, capture_output=True,
            text=True, check=True, timeout=5,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        git_revision = None
    metadata = {
        "started_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_revision": git_revision,
        "python": platform.python_version(), "numpy": np.__version__,
        "platform": platform.platform(), "compute_device": "CPU",
        "spec": {"d": numeric.spec.d, "m": numeric.spec.m},
        "world_count": len(numeric), "policy": "full-candidate greedy",
        "candidate_limit": None, "seed": 0, "episode_unit": "hidden world",
        "warm_repeats": args.warm_repeats, "chunk_size": args.chunk_size,
        "jsonl_dataset": str(args.jsonl_dataset.resolve()),
        "numeric_dataset": str(args.numeric_dataset.resolve()),
        "numeric_worlds_sha256": numeric.worlds_sha256,
        "source_sha256": {
            str(path.relative_to(SOURCE_ROOT)): sha256_file(path)
            for path in (Path(__file__), SOURCE_ROOT / "core" / "oracle.py",
                         SOURCE_ROOT / "reuse" / "numeric_engine" / "responses.py",
                         SOURCE_ROOT / "reuse" / "numeric_engine" / "policies.py")
        },
    }
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    rows = []
    results = {"startup_seconds": {"jsonl_manifest": jsonl_load, "numeric_verified_load": numeric_load},
               "action_counts_by_forced_y": stage_counts(catalog), "actions": rows}
    results_path = output / "results.json"
    with tempfile.TemporaryDirectory(prefix="bbp-exp-other-02-") as temporary:
        temp = Path(temporary)
        old_store = OnDemandResponseStore(jsonl, len(jsonl), catalog)
        new_store = NumericResponseStore(numeric, catalog, cache_dir=temp / "sample-cache", chunk_size=args.chunk_size)
        numeric_oracle = ExactOracle(catalog, new_store, stage=Stage.C)
        initial_state = numeric_oracle.initial_state()
        policy = GreedyInformationGainPolicy(numeric_oracle)
        for sample in representative_actions(catalog):
            action_id = sample["action_id"]
            old_seconds, old_column = timed(lambda: old_store.outcomes_for_action(action_id))
            new_seconds, new_column = timed(lambda: new_store.outcomes_for_action(action_id))
            if not np.array_equal(old_column, new_column):
                raise AssertionError(f"response mismatch for action {action_id}")
            checksum = hashlib.sha256(new_column.tobytes()).hexdigest()
            old_warm = [timed(lambda: old_store.outcomes_for_action(action_id))[0]
                        for _ in range(args.warm_repeats)]
            new_warm = [timed(lambda: new_store.outcomes_for_action(action_id))[0]
                        for _ in range(args.warm_repeats)]
            new_store.clear_cache()
            disk_seconds, disk_column = timed(lambda: new_store.outcomes_for_action(action_id))
            if not np.array_equal(old_column, disk_column):
                raise AssertionError(f"disk reload mismatch for action {action_id}")
            scores = [timed(lambda: policy.choose_action(
                state=initial_state, available_action_ids=(action_id,)))[0]
                for _ in range(args.warm_repeats)]
            row = {**sample, "stage": catalog[action_id].minimum_stage.name,
                   "jsonl_cold_seconds": old_seconds, "numeric_cold_seconds": new_seconds,
                   "speedup_cold": old_seconds / new_seconds,
                   "jsonl_memory_hit_median_seconds": median(old_warm),
                   "numeric_memory_hit_median_seconds": median(new_warm),
                   "numeric_disk_reload_seconds": disk_seconds,
                   "numeric_policy_score_seconds_per_candidate": median(scores),
                   "column_bytes": new_column.nbytes, "column_sha256": checksum,
                   "responses_match": True}
            rows.append(row)
            results_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
            print(f"forced Y={sample['forced_y']}, action {action_id}: "
                  f"JSONL {old_seconds:.3f}s, numeric {new_seconds:.3f}s, "
                  f"disk {disk_seconds:.3f}s", flush=True)
        results["estimates"] = estimate(rows, results["action_counts_by_forced_y"])
        if not args.skip_episodes:
            results["stage_episodes_actual"] = []
            for stage in Stage:
                actual = benchmark_stage(stage, numeric, catalog, temp / f"stage-{stage.name.lower()}-cache")
                results["stage_episodes_actual"].append(actual)
                results_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
                print(f"Stage {stage.name} episodes:", actual["episodes"], flush=True)
        results_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(f"Results: {output}", flush=True)


if __name__ == "__main__":
    main()
