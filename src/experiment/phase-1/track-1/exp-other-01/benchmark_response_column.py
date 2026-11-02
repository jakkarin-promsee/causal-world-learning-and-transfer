"""Measure where cold response-column construction spends time.

Run from src: python experiment/phase-1/track-1/exp-other-01/benchmark_response_column.py
This is a local CPU diagnostic, not a Stage-1 policy experiment.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from itertools import islice
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(SOURCE_ROOT))

import numpy as np

from core.evaluator import encode_observation, evaluate
from core.oracle import ActionCatalog, OnDemandResponseStore, Stage
from core.storage import WorldDataset
from core.types import Intervention

TRACK_ROOT = Path(__file__).resolve().parent
DEFAULT_DATASET = SOURCE_ROOT / "dataset" / "worldgen-4-4"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def selected_actions(catalog: ActionCatalog) -> tuple[tuple[str, Stage, int], ...]:
    x = (0,) * catalog.spec.d
    no_y = (None,) * catalog.spec.m
    one_y = (1,) + no_y[1:]
    two_y = (1, 0) + no_y[2:]
    all_y = (1,) * catalog.spec.m
    return tuple(
        (name, stage, catalog.action_id_for(Intervention(x, y)))
        for name, stage, y in (
            ("A_no_y_forced", Stage.A, no_y),
            ("B_one_y_forced", Stage.B, one_y),
            ("C_two_y_forced", Stage.C, two_y),
            ("C_all_y_forced", Stage.C, all_y),
        )
    )


def measure_split(
    dataset: WorldDataset,
    catalog: ActionCatalog,
    action_id: int,
    chunk_size: int,
) -> tuple[dict[str, object], np.ndarray]:
    """Time batched dataset retrieval separately from evaluation and encoding."""

    action = catalog[action_id].intervention
    outcomes = np.empty(len(dataset), dtype=np.uint8)
    iterator = iter(dataset)
    offset = 0
    read_seconds = 0.0
    evaluate_seconds = 0.0
    started = time.perf_counter()
    cpu_started = time.process_time()

    while offset < len(dataset):
        read_started = time.perf_counter()
        batch = list(islice(iterator, min(chunk_size, len(dataset) - offset)))
        read_seconds += time.perf_counter() - read_started
        if not batch:
            raise ValueError(f"dataset ended after {offset} worlds")

        evaluate_started = time.perf_counter()
        for index, world in enumerate(batch, start=offset):
            outcomes[index] = encode_observation(
                evaluate(world, action, dataset.spec), dataset.spec
            )
        evaluate_seconds += time.perf_counter() - evaluate_started
        offset += len(batch)

    # Verify that the source does not silently yield extra worlds.
    try:
        next(iterator)
    except StopIteration:
        pass
    else:
        raise ValueError("dataset yielded more worlds than its manifest declares")

    total_seconds = time.perf_counter() - started
    return {
        "action_id": action_id,
        "intervention": {"x": action.x, "y": action.y},
        "worlds": offset,
        "read_decode_validate_seconds": read_seconds,
        "evaluate_encode_store_seconds": evaluate_seconds,
        "other_seconds": total_seconds - read_seconds - evaluate_seconds,
        "total_wall_seconds": total_seconds,
        "total_process_cpu_seconds": time.process_time() - cpu_started,
        "column_bytes": outcomes.nbytes,
        "column_sha256": hashlib.sha256(outcomes.tobytes()).hexdigest(),
    }, outcomes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--chunk-size", type=int, default=4096)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.chunk_size < 1:
        parser.error("--chunk-size must be positive")

    dataset = WorldDataset(args.dataset)
    if (dataset.spec.d, dataset.spec.m) != (4, 4):
        parser.error("this diagnostic's representative actions require d=4, m=4")
    catalog = ActionCatalog(dataset.spec)
    actions = selected_actions(catalog)

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = args.output or TRACK_ROOT / "runs" / run_id
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
        "dataset_path": str(args.dataset.resolve()),
        "dataset_spec": {"d": dataset.spec.d, "m": dataset.spec.m},
        "world_count": len(dataset),
        "dataset_file_sha256": {
            path.name: sha256_file(path)
            for path in [args.dataset / "manifest.json"]
            + [args.dataset / shard["file"] for shard in dataset.shards]
        },
        "code_file_sha256": {
            str(path.relative_to(SOURCE_ROOT)): sha256_file(path)
            for path in (
                Path(__file__), SOURCE_ROOT / "core" / "storage.py",
                SOURCE_ROOT / "core" / "evaluator.py",
                SOURCE_ROOT / "core" / "oracle.py",
                SOURCE_ROOT / "core" / "operators.py",
            )
        },
        "git_revision": git_revision,
        "python": platform.python_version(),
        "numpy": np.__version__,
        "platform": platform.platform(),
        "chunk_size": args.chunk_size,
        "compute_device": "CPU",
        "episode_count": 0,
        "policy": None,
        "candidate_limit": None,
        "seed": None,
        "action_budget": 0,
        "timing_method": "perf_counter around batched dataset retrieval and evaluate/encode/store; process_time for whole pass",
    }
    (output / "metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )

    # The actual store is measured once and compared against the instrumented
    # Stage-A pass to ensure the diagnostic retains response order and values.
    store = OnDemandResponseStore(dataset, len(dataset), catalog)
    baseline_started = time.perf_counter()
    baseline_column = store.outcomes_for_action(actions[0][2])
    baseline_seconds = time.perf_counter() - baseline_started
    baseline_sha256 = hashlib.sha256(baseline_column.tobytes()).hexdigest()
    print(f"Reference store Stage A: {baseline_seconds:.2f} s", flush=True)

    rows = []
    for name, stage, action_id in actions:
        row, column = measure_split(dataset, catalog, action_id, args.chunk_size)
        row.update({"condition": name, "stage": stage.name})
        if name == "A_no_y_forced":
            if not np.array_equal(column, baseline_column):
                raise AssertionError("instrumented Stage-A column differs from reference store")
            row["matches_reference_store"] = True
        rows.append(row)
        print(
            f"{name}: read {row['read_decode_validate_seconds']:.2f} s, "
            f"evaluate {row['evaluate_encode_store_seconds']:.2f} s, "
            f"total {row['total_wall_seconds']:.2f} s",
            flush=True,
        )
        (output / "results.json").write_text(
            json.dumps({
                "reference_stage_a": {
                    "action_id": actions[0][2],
                    "total_wall_seconds": baseline_seconds,
                    "column_sha256": baseline_sha256,
                },
                "conditions": rows,
            }, indent=2) + "\n", encoding="utf-8"
        )

    print(f"Results: {output}", flush=True)


if __name__ == "__main__":
    main()
