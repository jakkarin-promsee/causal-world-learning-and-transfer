"""Canonical numeric world dataset for the main numeric engine."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from core.types import NodeRule, Op, World, WorldSpec
from core.worldgen import iter_worlds, world_count

FORMAT = "beyond-backprop.numeric-worlds"
VERSION = 1
NO_SECOND_PARENT = 255


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def save_numeric_worlds(output_dir: str | Path, spec: WorldSpec) -> Path:
    """Write worlds.npy in canonical iter_worlds order, then its manifest."""

    if spec.d + spec.m - 2 >= NO_SECOND_PARENT:
        raise ValueError("uint8 parent ids require d + m - 2 < 255")
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    if any(target.iterdir()):
        raise FileExistsError(f"output directory is not empty: {target}")

    count = world_count(spec)
    path = target / "worlds.npy"
    array = np.lib.format.open_memmap(
        path, mode="w+", dtype=np.uint8, shape=(count, spec.m, 3)
    )
    written = 0
    for world_index, world in enumerate(iter_worlds(spec)):
        for node_index, rule in enumerate(world.nodes):
            array[world_index, node_index] = (
                int(rule.op),
                rule.parents[0],
                rule.parents[1] if len(rule.parents) == 2 else NO_SECOND_PARENT,
            )
        written += 1
    if written != count:
        raise ValueError(f"world generator yielded {written} worlds, expected {count}")
    array.flush()
    del array

    manifest = {
        "format": FORMAT,
        "version": VERSION,
        "spec": {"d": spec.d, "m": spec.m},
        "world_count": count,
        "shape": [count, spec.m, 3],
        "dtype": "uint8",
        "node_fields": ["op", "parent1", "parent2"],
        "no_second_parent": NO_SECOND_PARENT,
        "world_order": "core.worldgen.iter_worlds",
        "worlds_sha256": _sha256(path),
    }
    manifest_path = target / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest_path


class NumericWorldDataset:
    """Numeric rules loaded once in canonical world order."""

    def __init__(self, dataset_dir: str | Path, *, verify_hash: bool = True) -> None:
        self.path = Path(dataset_dir)
        manifest = json.loads((self.path / "manifest.json").read_text(encoding="utf-8"))
        if manifest.get("format") != FORMAT or manifest.get("version") != VERSION:
            raise ValueError("unsupported numeric world dataset format")
        self.spec = WorldSpec(**manifest["spec"])
        self.world_count = int(manifest["world_count"])
        expected_shape = (self.world_count, self.spec.m, 3)
        if tuple(manifest["shape"]) != expected_shape or manifest["dtype"] != "uint8":
            raise ValueError("numeric world manifest shape or dtype mismatch")
        if self.world_count != world_count(self.spec):
            raise ValueError("numeric dataset does not contain the full world family")
        if manifest.get("world_order") != "core.worldgen.iter_worlds":
            raise ValueError("numeric dataset world order is not canonical")
        self.worlds_sha256 = str(manifest["worlds_sha256"])
        world_path = self.path / "worlds.npy"
        if verify_hash and _sha256(world_path) != self.worlds_sha256:
            raise ValueError("numeric world dataset hash mismatch")
        self.rules = np.load(world_path, allow_pickle=False)
        if self.rules.shape != expected_shape or self.rules.dtype != np.uint8:
            raise ValueError("numeric world array shape or dtype mismatch")
        self.rules.flags.writeable = False

    def __len__(self) -> int:
        return self.world_count

    def world_at(self, index: int) -> World:
        """Materialize only the episode's hidden world for Environment."""

        if not 0 <= index < self.world_count:
            raise IndexError(index)
        nodes = []
        for op_code, first, second in self.rules[index]:
            op = Op(int(op_code))
            parents = (int(first),) if op == Op.NOT else (int(first), int(second))
            nodes.append(NodeRule(op=op, parents=parents))
        return World(nodes=tuple(nodes))
