"""Run ten paired full-candidate Stage A/B/C episodes. Execute from src/."""

from __future__ import annotations

import secrets
import sys
from pathlib import Path

import numpy as np

SOURCE_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(SOURCE_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from exp01_base import create_run, run_worlds


def main() -> None:
    seed = secrets.randbits(63)
    indices = np.random.default_rng(seed).permutation(705_600)[:10]
    run_dir, metadata = create_run(
        name="exp-01-short", folder=Path(__file__).resolve().parent,
        world_indices=indices, sampling_seed=seed,
    )
    print(f"Raw result: {run_dir}", flush=True)
    run_worlds(run_dir, metadata)


if __name__ == "__main__":
    main()
