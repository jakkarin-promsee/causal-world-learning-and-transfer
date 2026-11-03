"""Summarize an Exp 02 partitions.npz without evaluating worlds again."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

SCHEMA = "track1-exp02-partition-v1"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def summarize_stage(labels: np.ndarray, sizes: np.ndarray, world_count: int) -> dict:
    if labels.shape != (world_count,) or labels.dtype.kind not in "iu":
        raise ValueError("class IDs must be one integer per world")
    if sizes.ndim != 1 or sizes.dtype.kind not in "iu" or np.any(sizes <= 0):
        raise ValueError("class sizes must be positive integers")
    if np.any(labels < 0) or np.any(labels >= len(sizes)):
        raise ValueError("class ID out of range")
    if not np.array_equal(np.bincount(labels, minlength=len(sizes)), sizes):
        raise ValueError("class IDs and sizes disagree")
    if int(sizes.sum()) != world_count:
        raise ValueError("class sizes do not sum to the world count")

    equivalent = sizes > 1
    equivalent_worlds = int(sizes[equivalent].sum())
    # A uniformly selected world in a class of size n observes amount n.
    sum_squared_equivalent = int(np.sum(sizes[equivalent].astype(np.int64) ** 2))
    sum_squared_all = int(np.sum(sizes.astype(np.int64) ** 2))
    counts_by_size = np.bincount(sizes)
    return {
        "world_count": world_count,
        "class_count": int(len(sizes)),
        "singleton_class_count": int(np.count_nonzero(sizes == 1)),
        "equivalent_class_count": int(np.count_nonzero(equivalent)),
        "equivalent_world_count": equivalent_worlds,
        "equivalent_world_fraction": equivalent_worlds / world_count,
        "avg_class_amount_world_weighted_equivalent_only": (
            sum_squared_equivalent / equivalent_worlds if equivalent_worlds else None
        ),
        "avg_class_amount_world_weighted_all_worlds": sum_squared_all / world_count,
        "max_class_amount": int(sizes.max()),
        "class_count_by_amount": {str(n): int(count) for n, count in enumerate(counts_by_size) if count},
    }


def validate_refinement(parent: np.ndarray, child: np.ndarray, child_count: int) -> None:
    first_parent = np.full(child_count, -1, dtype=np.int32)
    np.maximum.at(first_parent, child, parent)
    if np.any(first_parent[child] != parent):
        raise ValueError("later stage does not refine earlier stage")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()
    metadata = json.loads((args.run_dir / "metadata.json").read_text(encoding="utf-8"))
    if metadata.get("schema") != SCHEMA:
        raise ValueError("unsupported Exp 02 raw schema")
    raw_path = args.run_dir / metadata["raw_file"]
    if sha256(raw_path) != metadata["raw_sha256"]:
        raise ValueError("raw NPZ checksum mismatch")
    world_count = int(metadata["world_count"])
    results = {}
    previous = None
    with np.load(raw_path, allow_pickle=False) as raw:
        for stage in ("A", "B", "C"):
            if stage not in metadata["stages"]:
                continue
            labels = raw[f"class_id_{stage}"]
            sizes = raw[f"class_size_{stage}"]
            results[stage] = summarize_stage(labels, sizes, world_count)
            if results[stage]["class_count"] != metadata["stages"][stage]["class_count"]:
                raise ValueError("class count disagrees with metadata")
            if previous is not None:
                validate_refinement(previous, labels, len(sizes))
            previous = labels

    summary = {
        "source_schema": SCHEMA,
        "raw_sha256": metadata["raw_sha256"],
        "status": metadata["status"],
        "definitions": {
            "equivalent": "class size > 1 under all available actions in that stage",
            "equivalent_world_count": "sum of class sizes over classes with size > 1",
            "avg_class_amount_world_weighted_equivalent_only": "sum(size^2 for size > 1) / sum(size for size > 1); null if no equivalent worlds",
            "avg_class_amount_world_weighted_all_worlds": "sum(size^2 for every class) / world_count; singleton amount = 1",
        },
        "stages": results,
    }
    output = args.run_dir / "numeric-summary.json"
    output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({stage: {key: value for key, value in result.items() if key != "class_count_by_amount"} for stage, result in results.items()}, indent=2))
    print(f"Summary: {output}")


if __name__ == "__main__":
    main()
