"""Shared raw-record writer for Track 1 Exp 01. Run scripts from src/."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from core.evaluator import Environment
from core.oracle import ActionCatalog, ExactOracle, Stage
from reuse.numeric_engine import NumericResponseStore, NumericWorldDataset
from reuse.numeric_engine.runner import EpisodeConfig, run_full_candidate_greedy_episode


SOURCE_ROOT = Path(__file__).resolve().parents[3]
DATASET = SOURCE_ROOT / "dataset" / "worldgen-4-4-npy"
CACHE = SOURCE_ROOT / "dataset" / "response-cache-exp01"
STAGES = (Stage.A, Stage.B, Stage.C)
SCHEMA = "track1-exp01-raw-v1"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json_atomic(path: Path, value: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def source_identity() -> dict:
    try:
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=SOURCE_ROOT, capture_output=True,
            text=True, check=True, timeout=5,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        revision = None
    paths = [
        Path(__file__),
        SOURCE_ROOT / "core" / "oracle.py",
        SOURCE_ROOT / "core" / "evaluator.py",
        SOURCE_ROOT / "reuse" / "numeric_engine" / "runner.py",
        SOURCE_ROOT / "reuse" / "numeric_engine" / "policies.py",
        SOURCE_ROOT / "reuse" / "numeric_engine" / "responses.py",
    ]
    return {
        "git_revision": revision,
        "source_sha256": {str(path.relative_to(SOURCE_ROOT)): sha256_file(path) for path in paths},
    }


def create_run(*, name: str, folder: Path, world_indices: np.ndarray, sampling_seed: int) -> tuple[Path, dict]:
    folder.mkdir(parents=True, exist_ok=True)
    run_dir = folder / "runs" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir.mkdir(parents=True, exist_ok=False)
    indices_path = run_dir / "selected_world_indices.npy"
    np.save(indices_path, world_indices.astype(np.int32, copy=False), allow_pickle=False)
    worlds = NumericWorldDataset(DATASET)
    if (worlds.spec.d, worlds.spec.m, len(worlds)) != (4, 4, 705_600):
        raise ValueError("Exp 01 requires the canonical d=4,m=4 world family")
    catalog = ActionCatalog(worlds.spec)
    metadata = {
        "schema": SCHEMA,
        "run_name": name,
        "status": "running",
        "started_utc": utc_now(),
        "finished_utc": None,
        "elapsed_seconds": 0.0,
        "completed_worlds": 0,
        "selected_world_count": int(len(world_indices)),
        "selected_world_indices_file": indices_path.name,
        "selected_world_indices_sha256": sha256_file(indices_path),
        "sampling_method": "numpy.random.Generator.permutation; without replacement",
        "sampling_seed": sampling_seed,
        "dataset": str(DATASET.resolve()),
        "worlds_sha256": worlds.worlds_sha256,
        "world_count": len(worlds),
        "spec": {"d": 4, "m": 4},
        "policy": "full-candidate greedy information gain",
        "candidate_limit": None,
        "budgets": {stage.name: len(catalog.entries_for_stage(stage)) for stage in STAGES},
        "episode_unit": "hidden world; paired Stage A/B/C",
        "python": platform.python_version(),
        "numpy": np.__version__,
        "compute_device": "CPU",
        "response_cache": str(CACHE.resolve()),
        **source_identity(),
    }
    write_json_atomic(run_dir / "metadata.json", metadata)
    return run_dir, metadata


def run_worlds(run_dir: Path, metadata: dict, *, max_seconds: float | None = None) -> dict:
    indices_path = run_dir / metadata["selected_world_indices_file"]
    if sha256_file(indices_path) != metadata["selected_world_indices_sha256"]:
        raise ValueError("selected world indices changed")
    indices = np.load(indices_path, allow_pickle=False)
    worlds = NumericWorldDataset(DATASET)
    if worlds.worlds_sha256 != metadata["worlds_sha256"]:
        raise ValueError("dataset changed since run creation")
    catalog = ActionCatalog(worlds.spec)
    store = NumericResponseStore(worlds, catalog, cache_dir=CACHE)
    oracles = {stage: ExactOracle(catalog, store, stage=stage) for stage in STAGES}
    start = time.perf_counter()
    completed = metadata["completed_worlds"]
    with (run_dir / "episodes.jsonl").open("a", encoding="utf-8") as output:
        for position in range(completed, len(indices)):
            if max_seconds is not None and metadata["elapsed_seconds"] + time.perf_counter() - start >= max_seconds:
                metadata["status"] = "time_cap_reached"
                break
            index = int(indices[position])
            stage_results = {}
            for stage in STAGES:
                budget = metadata["budgets"][stage.name]
                stage_start = time.perf_counter()
                result = run_full_candidate_greedy_episode(
                    world_index=index,
                    environment=Environment(worlds.world_at(index), worlds.spec),
                    oracle=oracles[stage],
                    config=EpisodeConfig(stage=stage, budget=budget, seed=metadata["sampling_seed"]),
                )
                steps = []
                for step in result.episode.steps:
                    action = catalog[step.action_id].intervention
                    steps.append({
                        **asdict(step),
                        "action_step": step.timestep + 1,
                        "intervention": {"x": list(action.x), "y": list(action.y)},
                    })
                stage_results[stage.name] = {
                    "budget": budget,
                    "executed_steps": len(steps),
                    "termination_reason": result.termination_reason,
                    "final_survivor_count": result.final_survivor_count,
                    "initial_uncertainty_bits": float(np.log2(len(worlds))),
                    "uncertainty_trajectory_bits": list(result.uncertainty_trajectory_bits),
                    "inferred_suffix_from_step": len(steps) + 1 if len(steps) < budget else None,
                    "steps": steps,
                    "seconds": time.perf_counter() - stage_start,
                }
            record = {"schema": SCHEMA, "sample_position": position, "world_index": index, "stages": stage_results}
            output.write(json.dumps(record, separators=(",", ":")) + "\n")
            output.flush()
            os.fsync(output.fileno())
            completed += 1
            metadata["completed_worlds"] = completed
            metadata["elapsed_seconds"] += time.perf_counter() - start
            start = time.perf_counter()
            write_json_atomic(run_dir / "metadata.json", metadata)
            print(f"{metadata['run_name']}: {completed}/{len(indices)} worlds; index={index}; steps="
                  + "/".join(str(stage_results[s.name]["executed_steps"]) for s in STAGES), flush=True)
        else:
            metadata["status"] = "complete"
    metadata["elapsed_seconds"] += time.perf_counter() - start
    metadata["finished_utc"] = utc_now()
    write_json_atomic(run_dir / "metadata.json", metadata)
    return metadata
