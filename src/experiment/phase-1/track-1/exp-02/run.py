"""Enumerate exact stage-specific observational equivalence classes. Run from src/."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

SOURCE_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(SOURCE_ROOT))

from core.oracle import ActionCatalog, Stage
from reuse.numeric_engine import NumericResponseStore, NumericWorldDataset

DATASET = SOURCE_ROOT / "dataset" / "worldgen-4-4-npy"
SCHEMA = "track1-exp02-partition-v1"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def refine(labels: np.ndarray, outcomes: np.ndarray, outcome_count: int) -> np.ndarray:
    """Group worlds by (previous signature, next outcome), without hashing."""
    if labels.shape != outcomes.shape:
        raise ValueError("labels and outcomes must align with world order")
    key = labels.astype(np.int64) * outcome_count + outcomes
    _, inverse = np.unique(key, return_inverse=True)
    return inverse.astype(np.int32)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="New output directory (default: timestamped runs directory)")
    parser.add_argument("--stop-stage", choices=("A", "B", "C"), default="C", help="A for a short smoke run")
    args = parser.parse_args()

    worlds = NumericWorldDataset(DATASET)
    if (worlds.spec.d, worlds.spec.m, len(worlds)) != (4, 4, 705_600):
        raise ValueError("Exp 02 requires the canonical d=4,m=4 world family")
    catalog = ActionCatalog(worlds.spec)
    stop = Stage[args.stop_stage]
    output = args.output or Path(__file__).resolve().parent / "runs" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output.mkdir(parents=True, exist_ok=False)
    labels = np.zeros(len(worlds), dtype=np.int32)
    arrays: dict[str, np.ndarray] = {}
    stage_info: dict[str, dict] = {}
    store = NumericResponseStore(worlds, catalog)
    started = time.perf_counter()
    previous_classes = 1

    for stage in (Stage.A, Stage.B, Stage.C):
        if stage > stop:
            break
        stage_started = time.perf_counter()
        entries = [entry for entry in catalog if entry.minimum_stage == stage]
        evaluated = 0
        singleton_after_action_id = None
        for position, entry in enumerate(entries, start=1):
            if previous_classes == len(worlds):
                break
            column = store.outcomes_for_action(entry.action_id)
            labels = refine(labels, column, 1 << worlds.spec.m)
            store.clear_cache()
            evaluated = position
            class_count = int(labels.max()) + 1
            if position == len(entries) or position % 100 == 0:
                print(f"{stage.name}: {position}/{len(entries)} new actions; {class_count} classes", flush=True)
            if class_count == len(worlds):
                singleton_after_action_id = entry.action_id
                print(f"{stage.name}: all worlds singleton after action {entry.action_id}; remaining actions cannot refine", flush=True)
                break
        sizes = np.bincount(labels).astype(np.int32)
        if int(sizes.sum()) != len(worlds) or len(sizes) < previous_classes:
            raise AssertionError("invalid stage partition")
        arrays[f"class_id_{stage.name}"] = labels.copy()
        arrays[f"class_size_{stage.name}"] = sizes
        stage_info[stage.name] = {
            "action_count": len(catalog.entries_for_stage(stage)),
            "evaluated_new_actions": evaluated,
            "singleton_after_action_id": singleton_after_action_id,
            "class_count": len(sizes),
            "elapsed_seconds": round(time.perf_counter() - stage_started, 3),
        }
        previous_classes = len(sizes)

    raw_path = output / "partitions.npz"
    np.savez_compressed(raw_path, **arrays)
    metadata = {
        "schema": SCHEMA,
        "status": "complete" if stop == Stage.C else "smoke_partial_stages",
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "dataset": str(DATASET.resolve()),
        "worlds_sha256": worlds.worlds_sha256,
        "world_count": len(worlds),
        "spec": {"d": worlds.spec.d, "m": worlds.spec.m},
        "action_order": "ActionCatalog.action_id ascending; stable stage prefixes",
        "class_id_rule": "sorted (previous class ID, observation code) after each action",
        "stages": stage_info,
        "raw_file": raw_path.name,
        "raw_sha256": sha256(raw_path),
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "source_sha256": {
            str(path.relative_to(SOURCE_ROOT)): sha256(path)
            for path in (Path(__file__), SOURCE_ROOT / "core" / "oracle.py", SOURCE_ROOT / "core" / "evaluator.py", SOURCE_ROOT / "reuse" / "numeric_engine" / "responses.py")
        },
    }
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(f"Raw result: {output}", flush=True)


if __name__ == "__main__":
    main()
