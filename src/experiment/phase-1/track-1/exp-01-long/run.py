"""Run paired Stage A/B/C worlds until a six-hour cap, checkpointing each world.

From src/: python experiment/phase-1/track-1/exp-01-long/run.py
Resume:    python experiment/phase-1/track-1/exp-01-long/run.py --resume PATH_TO_RUN
"""

from __future__ import annotations

import argparse
import json
import secrets
import sys
from pathlib import Path

import numpy as np

SOURCE_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(SOURCE_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from exp01_base import SCHEMA, create_run, run_worlds, write_json_atomic


def reconcile_checkpoint(run_dir: Path, metadata: dict) -> None:
    """Recover a fully synced world line if interrupted before metadata update."""
    indices = np.load(run_dir / metadata["selected_world_indices_file"], allow_pickle=False)
    path = run_dir / "episodes.jsonl"
    count = 0
    if path.exists():
        with path.open("r", encoding="utf-8") as source:
            for line in source:
                row = json.loads(line)
                if row["schema"] != SCHEMA or row["sample_position"] != count:
                    raise ValueError(f"invalid checkpoint row {count}")
                if row["world_index"] != int(indices[count]) or set(row["stages"]) != {"A", "B", "C"}:
                    raise ValueError(f"unpaired or wrong world at checkpoint row {count}")
                count += 1
    if count < metadata["completed_worlds"]:
        raise ValueError("raw checkpoint has fewer worlds than metadata")
    if count > metadata["completed_worlds"]:
        metadata["completed_worlds"] = count
        write_json_atomic(run_dir / "metadata.json", metadata)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resume", type=Path, help="existing long-run directory")
    parser.add_argument("--hours", type=float, default=6.0, help="cumulative time cap; default 6")
    args = parser.parse_args()
    if args.hours <= 0:
        parser.error("--hours must be positive")
    if args.resume:
        run_dir = args.resume.resolve()
        metadata = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
        if metadata["run_name"] != "exp-01-long" or metadata["schema"] != SCHEMA:
            parser.error("--resume does not point to an Exp 01 long run")
        reconcile_checkpoint(run_dir, metadata)
    else:
        seed = secrets.randbits(63)
        indices = np.random.default_rng(seed).permutation(705_600)
        run_dir, metadata = create_run(
            name="exp-01-long", folder=Path(__file__).resolve().parent,
            world_indices=indices, sampling_seed=seed,
        )
        metadata["planned_time_cap_seconds"] = args.hours * 3600
        write_json_atomic(run_dir / "metadata.json", metadata)
    if metadata["status"] == "complete":
        print(f"Already complete: {run_dir}", flush=True)
        return
    print(f"Raw result: {run_dir}", flush=True)
    run_worlds(run_dir, metadata, max_seconds=args.hours * 3600)


if __name__ == "__main__":
    main()
