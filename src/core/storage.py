"""Versioned, streaming storage for structural-world datasets."""

from __future__ import annotations

import gzip
import json
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import IO, Any

from core.types import NodeRule, Op, World, WorldSpec
from core.worldgen import iter_worlds, validate_world, world_count


FORMAT_NAME = "beyond-backprop.structural-worlds"
FORMAT_VERSION = 1


def _world_to_record(world: World) -> list[list[int]]:
    return [[int(rule.op), *rule.parents] for rule in world.nodes]


def _record_to_world(record: Any) -> World:
    if not isinstance(record, list):
        raise ValueError("world record must be a list")
    try:
        nodes = tuple(
            NodeRule(op=Op(raw_rule[0]), parents=tuple(raw_rule[1:]))
            for raw_rule in record
        )
    except (IndexError, TypeError, ValueError) as error:
        raise ValueError(f"invalid world record: {record!r}") from error
    return World(nodes=nodes)


def _open_text(path: Path, mode: str, compressed: bool) -> IO[str]:
    if compressed:
        return gzip.open(path, mode + "t", encoding="utf-8", newline="")
    return path.open(mode, encoding="utf-8", newline="")


def save_world_dataset(
    output_dir: str | Path,
    spec: WorldSpec,
    worlds: Iterable[World] | None = None,
    *,
    shard_size: int = 100_000,
    compressed: bool = True,
) -> Path:
    """Write worlds and return the path to the completed manifest.

    The output directory must be empty. The manifest is written last, so its
    presence means all declared shards were completed.
    """

    if shard_size < 1:
        raise ValueError("shard_size must be at least 1")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    if any(output_path.iterdir()):
        raise FileExistsError(f"output directory is not empty: {output_path}")

    source = iter_worlds(spec) if worlds is None else iter(worlds)
    suffix = ".jsonl.gz" if compressed else ".jsonl"
    shards: list[dict[str, int | str]] = []
    total_count = 0
    shard_index = -1
    shard_count = 0
    handle: IO[str] | None = None

    try:
        for world in source:
            validate_world(world, spec)
            if handle is None or shard_count == shard_size:
                if handle is not None:
                    handle.close()
                    shards[-1]["count"] = shard_count
                shard_index += 1
                shard_count = 0
                filename = f"worlds-{shard_index:05d}{suffix}"
                shards.append({"file": filename, "count": 0})
                handle = _open_text(output_path / filename, "w", compressed)

            json.dump(_world_to_record(world), handle, separators=(",", ":"))
            handle.write("\n")
            shard_count += 1
            total_count += 1
    finally:
        if handle is not None:
            handle.close()

    if shards:
        shards[-1]["count"] = shard_count

    manifest = {
        "format": FORMAT_NAME,
        "version": FORMAT_VERSION,
        "spec": {"d": spec.d, "m": spec.m},
        "world_count": total_count,
        "canonical_world_count": world_count(spec),
        "compressed": compressed,
        "shard_size": shard_size,
        "shards": shards,
    }
    manifest_path = output_path / "manifest.json"
    with manifest_path.open("w", encoding="utf-8", newline="") as output:
        json.dump(manifest, output, indent=2)
        output.write("\n")
    return manifest_path


class WorldDataset:
    """A reusable streaming reader for a saved structural-world dataset."""

    def __init__(self, dataset_dir: str | Path, *, validate: bool = True) -> None:
        self.path = Path(dataset_dir)
        manifest_path = self.path / "manifest.json"
        with manifest_path.open(encoding="utf-8") as source:
            manifest = json.load(source)

        if manifest.get("format") != FORMAT_NAME:
            raise ValueError(f"unsupported dataset format in {manifest_path}")
        if manifest.get("version") != FORMAT_VERSION:
            raise ValueError(
                f"unsupported dataset version: {manifest.get('version')}"
            )

        self.spec = WorldSpec(**manifest["spec"])
        self.compressed = bool(manifest["compressed"])
        self.shards = tuple(manifest["shards"])
        self.world_count = int(manifest["world_count"])
        self.canonical_world_count = int(manifest["canonical_world_count"])
        self.validate = validate

        declared_count = sum(int(shard["count"]) for shard in self.shards)
        if declared_count != self.world_count:
            raise ValueError(
                f"manifest shard counts sum to {declared_count}, "
                f"not {self.world_count}"
            )

    def __len__(self) -> int:
        return self.world_count

    def __iter__(self) -> Iterator[World]:
        seen_total = 0
        for shard in self.shards:
            filename = str(shard["file"])
            if Path(filename).name != filename:
                raise ValueError(f"invalid shard filename: {filename!r}")

            seen_shard = 0
            with _open_text(self.path / filename, "r", self.compressed) as source:
                for line_number, line in enumerate(source, start=1):
                    try:
                        world = _record_to_world(json.loads(line))
                        if self.validate:
                            validate_world(world, self.spec)
                    except (json.JSONDecodeError, ValueError) as error:
                        raise ValueError(
                            f"invalid record in {filename}:{line_number}"
                        ) from error
                    seen_shard += 1
                    seen_total += 1
                    yield world

            expected = int(shard["count"])
            if seen_shard != expected:
                raise ValueError(
                    f"{filename} contains {seen_shard} worlds, expected {expected}"
                )

        if seen_total != self.world_count:
            raise ValueError(
                f"dataset contains {seen_total} worlds, expected {self.world_count}"
            )
