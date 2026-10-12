"""Measure this machine's cost for representative oracle baseline workloads.

Run from src: python experiment/phase-1/track-0/benchmark_local.py --profile smoke
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any

SOURCE_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(SOURCE_ROOT))

import numpy as np
import psutil

from core.evaluator import Environment
from core.oracle import ActionCatalog, ExactOracle, OnDemandResponseStore, Stage
from core.storage import WorldDataset
from core.types import World
from reuse.policies import GreedyInformationGainPolicy, Policy, RandomPolicy
from reuse.runner import EpisodeConfig, run_episode

TRACK_ROOT = Path(__file__).resolve().parent
DEFAULT_DATASET = SOURCE_ROOT / "dataset" / "worldgen-4-4"
MIB = 1024 * 1024


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_value(*args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args], cwd=SOURCE_ROOT, capture_output=True,
            text=True, check=True, timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip()


def gpu_snapshot() -> dict[str, Any]:
    """System GPU usage, not memory attributable to this CPU-only process."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.used,driver_version",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, check=True, timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return {"available": False, "reason": "nvidia-smi unavailable"}
    devices = []
    for line in result.stdout.splitlines():
        fields = [field.strip() for field in line.split(",")]
        if len(fields) == 4:
            devices.append({
                "name": fields[0], "total_mib": int(fields[1]),
                "system_used_mib": int(fields[2]), "driver": fields[3],
            })
    return {"available": bool(devices), "devices": devices,
            "usage_scope": "whole GPU; this benchmark does not allocate GPU tensors"}


def cpu_name() -> str:
    if sys.platform == "win32":
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                 r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
            with key:
                return str(winreg.QueryValueEx(key, "ProcessorNameString")[0]).strip()
        except OSError:
            pass
    return platform.processor() or "unavailable"


def hardware_snapshot(dataset_path: Path) -> dict[str, Any]:
    memory = psutil.virtual_memory()
    battery = psutil.sensors_battery()
    disk = shutil.disk_usage(dataset_path)
    return {
        "os": platform.platform(), "python": platform.python_version(),
        "numpy": np.__version__, "psutil": psutil.__version__,
        "cpu_name": cpu_name(), "physical_cores": psutil.cpu_count(logical=False),
        "logical_cores": psutil.cpu_count(logical=True),
        "ram_total_bytes": memory.total, "ram_available_start_bytes": memory.available,
        "disk_free_start_bytes": disk.free,
        "battery_percent": None if battery is None else battery.percent,
        "power_plugged": None if battery is None else battery.power_plugged,
        "gpu": gpu_snapshot(),
        "execution_device": "CPU; NumPy and Python dataset streaming",
    }


class EventLog:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._output = path.open("x", encoding="utf-8", newline="")

    def write(self, kind: str, **fields: Any) -> None:
        self._output.write(json.dumps({"kind": kind, "utc": utc_now(), **fields},
                                      separators=(",", ":")) + "\n")
        self._output.flush()

    def close(self) -> None:
        self._output.close()


class MemorySampler:
    """Sample process RSS and system available RAM while a condition runs."""

    def __init__(self, interval_seconds: float = 0.2) -> None:
        self.interval_seconds = interval_seconds
        self.process = psutil.Process()
        self.stop_event = threading.Event()
        self.peak_rss_bytes = 0
        self.lowest_available_bytes = 0
        self.samples = 0
        self.thread = threading.Thread(target=self._sample, daemon=True)

    def _sample(self) -> None:
        while True:
            rss = self.process.memory_info().rss
            available = psutil.virtual_memory().available
            self.peak_rss_bytes = max(self.peak_rss_bytes, rss)
            self.lowest_available_bytes = min(self.lowest_available_bytes or available,
                                              available)
            self.samples += 1
            if self.stop_event.wait(self.interval_seconds):
                return

    def __enter__(self) -> MemorySampler:
        self.thread.start()
        return self

    def __exit__(self, *_: object) -> None:
        self.stop_event.set()
        self.thread.join()


@dataclass(frozen=True)
class Condition:
    stage: str
    policy: str
    candidate_limit: int | None
    budget: int
    episodes: int

    @property
    def id(self) -> str:
        limit = "full" if self.candidate_limit is None else str(self.candidate_limit)
        return f"{self.stage}-{self.policy}-limit{limit}-budget{self.budget}-episodes{self.episodes}"


def conditions_for(profile: str) -> tuple[Condition, ...]:
    if profile == "smoke":
        return (
            Condition("A", "random", None, 1, 1),
            Condition("B", "random", None, 1, 1),
            Condition("C", "random", None, 1, 1),
            Condition("C", "sampled_information_gain", 2, 1, 1),
        )
    if profile == "standard":
        return (
            *(Condition(stage, "random", None, 2, 3) for stage in "ABC"),
            Condition("A", "greedy_information_gain", None, 2, 2),
            *(Condition(stage, "sampled_information_gain", 4, 2, 2) for stage in "ABC"),
            *(Condition(stage, "sampled_information_gain", 16, 1, 1) for stage in "BC"),
        )
    raise ValueError(f"unknown profile: {profile}")


class TimedResponseStore:
    """Observe the public response-store boundary without changing inference."""

    def __init__(self, base: OnDemandResponseStore, events: EventLog,
                 condition_id: str) -> None:
        self.base = base
        self.spec = base.spec
        self.world_count = base.world_count
        self.events = events
        self.condition_id = condition_id
        self.cache_bytes = 0
        self.cold_columns = 0
        self.warm_accesses = 0
        self.cold_seconds: list[float] = []

    def outcomes_for_action(self, action_id: int) -> np.ndarray:
        cold = action_id not in self.base.cached_action_ids
        process = psutil.Process()
        rss_before = process.memory_info().rss
        cpu_before = time.process_time()
        start = time.perf_counter()
        column = self.base.outcomes_for_action(action_id)
        elapsed = time.perf_counter() - start
        if cold:
            self.cold_columns += 1
            self.cache_bytes += column.nbytes
            self.cold_seconds.append(elapsed)
        else:
            self.warm_accesses += 1
        self.events.write(
            "response_column", condition_id=self.condition_id, action_id=action_id,
            cold=cold, wall_seconds=elapsed,
            process_cpu_seconds=time.process_time() - cpu_before,
            rss_before_bytes=rss_before, rss_after_bytes=process.memory_info().rss,
            column_bytes=column.nbytes, cache_columns=self.cold_columns,
            cache_bytes=self.cache_bytes,
        )
        return column


class TimedPolicy:
    def __init__(self, base: Policy, events: EventLog, condition_id: str,
                 episode_index: int, responses: TimedResponseStore) -> None:
        self.base = base
        self.name = base.name
        self.events = events
        self.condition_id = condition_id
        self.episode_index = episode_index
        self.responses = responses

    def choose_action(self, *, state: Any, available_action_ids: Any) -> int:
        cold_before = self.responses.cold_columns
        start = time.perf_counter()
        selected = self.base.choose_action(state=state,
                                           available_action_ids=available_action_ids)
        self.events.write(
            "policy_choice", condition_id=self.condition_id,
            episode_index=self.episode_index, timestep=state.timestep,
            selected_action_id=selected, available_actions=len(available_action_ids),
            wall_seconds=time.perf_counter() - start,
            new_response_columns=self.responses.cold_columns - cold_before,
        )
        return selected


def selected_worlds(dataset: WorldDataset, count: int, seed: int,
                    events: EventLog) -> tuple[list[int], dict[int, World]]:
    rng = np.random.default_rng(seed)
    indices = [int(i) for i in rng.choice(len(dataset), size=count, replace=False)]
    wanted = set(indices)
    found: dict[int, World] = {}
    start = time.perf_counter()
    for index, world in enumerate(dataset):
        if index in wanted:
            found[index] = world
            if len(found) == count:
                break
    if len(found) != count:
        raise RuntimeError("dataset ended before selected worlds were found")
    events.write("world_selection", indices=indices,
                 wall_seconds=time.perf_counter() - start,
                 rss_after_bytes=psutil.Process().memory_info().rss)
    return indices, found


def run_condition(condition: Condition, *, dataset: WorldDataset,
                  catalog: ActionCatalog, indices: list[int], worlds: dict[int, World],
                  seed: int, events: EventLog) -> dict[str, Any]:
    stage = Stage[condition.stage]
    base_responses = OnDemandResponseStore(dataset, len(dataset), catalog)
    responses = TimedResponseStore(base_responses, events, condition.id)
    oracle = ExactOracle(catalog, responses, stage=stage)
    process = psutil.Process()
    start_cpu = time.process_time()
    start = time.perf_counter()
    episode_seconds: list[float] = []
    events.write("condition_start", condition_id=condition.id,
                 config=asdict(condition), action_space_size=len(catalog.entries_for_stage(stage)),
                 cache_mode="fresh at condition start, retained across its episodes",
                 rss_start_bytes=process.memory_info().rss, gpu_start=gpu_snapshot())
    with MemorySampler() as memory:
        for episode_index, world_index in enumerate(indices[:condition.episodes]):
            policy_seed = seed + 1_000_003 * episode_index + 10_007 * int(stage)
            if condition.policy == "random":
                policy: Policy = RandomPolicy(policy_seed)
            else:
                policy = GreedyInformationGainPolicy(
                    oracle, candidate_limit=condition.candidate_limit, seed=policy_seed)
            timed_policy = TimedPolicy(policy, events, condition.id, episode_index, responses)
            cold_before = responses.cold_columns
            cpu_before = time.process_time()
            episode_start = time.perf_counter()
            result = run_episode(
                world_index=world_index,
                environment=Environment(worlds[world_index], dataset.spec),
                oracle=oracle, policy=timed_policy,
                config=EpisodeConfig(stage=stage, budget=condition.budget, seed=policy_seed),
            )
            wall = time.perf_counter() - episode_start
            episode_seconds.append(wall)
            events.write(
                "episode_end", condition_id=condition.id, episode_index=episode_index,
                world_index=world_index, policy_seed=policy_seed,
                wall_seconds=wall, cumulative_episode_seconds=sum(episode_seconds),
                process_cpu_seconds=time.process_time() - cpu_before,
                new_response_columns=responses.cold_columns - cold_before,
                cache_columns=responses.cold_columns, cache_bytes=responses.cache_bytes,
                rss_after_bytes=process.memory_info().rss,
                steps=[asdict(step) for step in result.steps],
            )
    summary = {
        "condition_id": condition.id, "config": asdict(condition),
        "wall_seconds": time.perf_counter() - start,
        "process_cpu_seconds": time.process_time() - start_cpu,
        "episode_seconds": episode_seconds,
        "cold_columns": responses.cold_columns,
        "warm_column_accesses": responses.warm_accesses,
        "median_cold_column_seconds": median(responses.cold_seconds)
        if responses.cold_seconds else None,
        "cache_bytes": responses.cache_bytes,
        "peak_process_rss_bytes": memory.peak_rss_bytes,
        "lowest_system_available_bytes": memory.lowest_available_bytes,
        "memory_samples": memory.samples,
        "gpu_end": gpu_snapshot(),
    }
    events.write("condition_end", **summary)
    return summary


def write_summary(path: Path, *, metadata: dict[str, Any],
                  conditions: list[dict[str, Any]], status: str) -> None:
    lines = [
        "# Local Track-0 benchmark", "",
        f"- Status: **{status}**", f"- UTC start: {metadata['started_utc']}",
        f"- Profile: `{metadata['profile']}`", f"- Dataset: `{metadata['dataset_relative']}`",
        f"- Worlds: {metadata['world_count']:,}; `d={metadata['d']}, m={metadata['m']}`",
        f"- CPU: {metadata['hardware']['cpu_name']} ({metadata['hardware']['physical_cores']} physical / {metadata['hardware']['logical_cores']} logical cores)",
        f"- RAM: {metadata['hardware']['ram_total_bytes'] / (1024**3):.1f} GiB",
        f"- GPU: {', '.join(device['name'] for device in metadata['hardware']['gpu'].get('devices', [])) or 'unavailable'}; **benchmark code uses CPU only**",
        f"- Python {metadata['hardware']['python']}; NumPy {metadata['hardware']['numpy']}",
        f"- Git commit: `{metadata['git_commit']}`; dirty working tree: `{metadata['git_dirty']}`",
        "- Raw event log: [`events.jsonl`](events.jsonl). It includes every response-column access, policy choice, episode, cache size, RSS sample summary, and GPU snapshot.",
        "", "## Conditions", "",
        "| Condition | Episodes | Wall time | Cold columns | Median cold column | Peak process RSS | Cache |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in conditions:
        cold = item["median_cold_column_seconds"]
        cold_label = f"{cold:.2f} s" if cold is not None else "n/a"
        lines.append(
            f"| `{item['condition_id']}` | {len(item['episode_seconds'])} | "
            f"{item['wall_seconds']:.1f} s | {item['cold_columns']} | "
            f"{cold_label} | {item['peak_process_rss_bytes'] / MIB:.1f} MiB | "
            f"{item['cache_bytes'] / MIB:.1f} MiB |"
        )
    lines += [
        "", "Each condition starts with an empty response cache and retains it between episodes. Cold-column time includes streaming and evaluating every world. The first episode and later episodes therefore have different cache states. The GPU numbers in `events.jsonl` are whole-device VRAM usage and cannot be attributed to this CPU-only Python process. These are local planning measurements, not evidence that one policy or stage is scientifically better.",
        "", "For a future run, estimate the number of **new** response columns it may request, then use the matching cold-column times here as a rough starting point. Do not multiply one episode's warm time by a new workload with an empty cache.", "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("smoke", "standard"), default="smoke")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-minutes", type=float, default=90.0,
                        help="stop between conditions after this wall-time limit")
    parser.add_argument("--output-dir", type=Path, default=None,
                        help="new directory; default is a timestamped folder under track-0/runs")
    args = parser.parse_args()
    if args.seed < 0 or args.max_minutes <= 0:
        parser.error("seed must be non-negative and max-minutes must be positive")
    dataset_path = args.dataset.resolve()
    dataset = WorldDataset(dataset_path)
    conditions = conditions_for(args.profile)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + f"-{os.getpid()}"
    output_dir = args.output_dir or TRACK_ROOT / "runs" / run_id
    output_dir.mkdir(parents=True, exist_ok=False)
    events = EventLog(output_dir / "events.jsonl")
    started = time.perf_counter()
    metadata = {
        "started_utc": utc_now(), "profile": args.profile,
        "seed": args.seed, "max_minutes": args.max_minutes,
        "dataset_relative": os.path.relpath(dataset_path, SOURCE_ROOT),
        "dataset_manifest_sha256": file_sha256(dataset_path / "manifest.json"),
        "d": dataset.spec.d, "m": dataset.spec.m, "world_count": len(dataset),
        "git_commit": git_value("rev-parse", "HEAD"),
        "git_dirty": bool(git_value("status", "--porcelain")),
        "code_sha256": {
            str(path.relative_to(SOURCE_ROOT)): file_sha256(path)
            for path in (SOURCE_ROOT / "core" / "oracle.py", SOURCE_ROOT / "reuse" / "policies.py",
                         SOURCE_ROOT / "reuse" / "runner.py", Path(__file__).resolve())
        },
        "hardware": hardware_snapshot(dataset_path),
        "conditions": [asdict(condition) for condition in conditions],
    }
    (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n",
                                               encoding="utf-8")
    events.write("run_start", metadata_file="metadata.json", profile=args.profile)
    summaries: list[dict[str, Any]] = []
    status = "completed"
    try:
        selection_count = max(condition.episodes for condition in conditions)
        indices, worlds = selected_worlds(dataset, selection_count, args.seed, events)
        catalog = ActionCatalog(dataset.spec)
        for condition in conditions:
            if (time.perf_counter() - started) / 60 >= args.max_minutes:
                status = "time limit reached between conditions"
                break
            print(f"Starting {condition.id}", flush=True)
            summaries.append(run_condition(condition, dataset=dataset, catalog=catalog,
                                           indices=indices, worlds=worlds, seed=args.seed,
                                           events=events))
            write_summary(output_dir / "summary.md", metadata=metadata,
                          conditions=summaries, status="in progress")
            print(f"Finished {condition.id}: {summaries[-1]['wall_seconds']:.1f} s", flush=True)
    except KeyboardInterrupt:
        status = "interrupted"
    except Exception as error:
        status = f"failed: {type(error).__name__}: {error}"
        events.write("run_error", error=status)
        raise
    finally:
        events.write("run_end", status=status, wall_seconds=time.perf_counter() - started,
                     completed_conditions=len(summaries))
        events.close()
        write_summary(output_dir / "summary.md", metadata=metadata,
                      conditions=summaries, status=status)
        print(f"Log: {output_dir / 'events.jsonl'}", flush=True)
        print(f"Summary: {output_dir / 'summary.md'}", flush=True)


if __name__ == "__main__":
    main()
