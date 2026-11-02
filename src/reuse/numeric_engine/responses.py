"""Vectorized, persistent on-demand response columns from numeric worlds."""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from core.oracle import ActionCatalog
from core.types import Op, WorldSpec
from reuse.numeric_engine.worlds import NumericWorldDataset

CACHE_FORMAT = "beyond-backprop.numeric-responses"
CACHE_VERSION = 1


def _outcome_dtype(spec: WorldSpec) -> np.dtype:
    if spec.m <= 8:
        return np.dtype(np.uint8)
    if spec.m <= 16:
        return np.dtype(np.uint16)
    if spec.m <= 32:
        return np.dtype(np.uint32)
    if spec.m <= 64:
        return np.dtype(np.uint64)
    raise ValueError("encoded observations currently support at most 64 Y nodes")


def _catalog_hash(catalog: ActionCatalog) -> str:
    actions = [
        [entry.action_id, list(entry.intervention.x), list(entry.intervention.y)]
        for entry in catalog
    ]
    payload = json.dumps(actions, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _logic_hash() -> str:
    """Invalidate disk columns when the vectorized or reference semantics change."""

    digest = hashlib.sha256()
    source_root = Path(__file__).resolve().parents[2]
    for path in (
        Path(__file__),
        source_root / "core" / "evaluator.py",
        source_root / "core" / "types.py",
    ):
        digest.update(path.read_bytes())
    return digest.hexdigest()


class NumericResponseStore:
    """Compute one action column in vectorized world batches, then reuse it.

    The cache is bound to the numeric world file and stable ActionCatalog. Disk
    columns are optional and are stored as individual .npy files so a run only
    pays for actions it actually scores.
    """

    def __init__(
        self,
        worlds: NumericWorldDataset,
        catalog: ActionCatalog,
        *,
        cache_dir: str | Path | None = None,
        chunk_size: int = 100_000,
    ) -> None:
        if worlds.spec != catalog.spec:
            raise ValueError("numeric world dataset and catalog specs differ")
        if chunk_size < 1:
            raise ValueError("chunk_size must be positive")
        self.spec = worlds.spec
        self.world_count = len(worlds)
        self.catalog = catalog
        self.worlds = worlds
        self.chunk_size = chunk_size
        self.dtype = _outcome_dtype(self.spec)
        self._cache: dict[int, NDArray[np.unsignedinteger]] = {}
        self.cache_dir = Path(cache_dir) if cache_dir is not None else None

        if self.cache_dir is not None:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            expected = {
                "format": CACHE_FORMAT,
                "version": CACHE_VERSION,
                "worlds_sha256": worlds.worlds_sha256,
                "spec": {"d": self.spec.d, "m": self.spec.m},
                "world_count": self.world_count,
                "catalog_sha256": _catalog_hash(catalog),
                "logic_sha256": _logic_hash(),
                "dtype": self.dtype.name,
            }
            manifest_path = self.cache_dir / "manifest.json"
            if manifest_path.exists():
                actual = json.loads(manifest_path.read_text(encoding="utf-8"))
                if actual != expected:
                    raise ValueError("response cache does not match numeric worlds or action catalog")
            elif any(self.cache_dir.iterdir()):
                raise ValueError("response cache directory has files but no manifest")
            else:
                manifest_path.write_text(
                    json.dumps(expected, indent=2) + "\n", encoding="utf-8"
                )

    def outcomes_for_action(self, action_id: int) -> NDArray[np.unsignedinteger]:
        entry = self.catalog[action_id]
        action_id = entry.action_id
        cached = self._cache.get(action_id)
        if cached is not None:
            return cached

        path = self._column_path(action_id)
        checksum_path = path.with_suffix(".sha256") if path is not None else None
        if path is not None and path.exists() != checksum_path.exists():
            raise ValueError("cached response column or checksum is missing")
        if path is not None and path.exists():
            outcomes = np.load(path, allow_pickle=False)
            self._validate_column(outcomes)
            actual_checksum = hashlib.sha256(outcomes.tobytes()).hexdigest()
            if actual_checksum != checksum_path.read_text(encoding="ascii").strip():
                raise ValueError("cached response column checksum mismatch")
            outcomes.flags.writeable = False
        else:
            outcomes = self._compute_column(action_id)
            if path is not None:
                temporary = path.with_name(path.name + f".{uuid.uuid4().hex}.tmp")
                checksum_temporary = checksum_path.with_name(
                    checksum_path.name + f".{uuid.uuid4().hex}.tmp"
                )
                try:
                    with temporary.open("wb") as output:
                        np.save(output, outcomes, allow_pickle=False)
                    checksum_temporary.write_text(
                        hashlib.sha256(outcomes.tobytes()).hexdigest() + "\n",
                        encoding="ascii",
                    )
                    os.replace(temporary, path)
                    os.replace(checksum_temporary, checksum_path)
                finally:
                    temporary.unlink(missing_ok=True)
                    checksum_temporary.unlink(missing_ok=True)
            outcomes.flags.writeable = False
        self._cache[action_id] = outcomes
        return outcomes

    @property
    def cached_action_ids(self) -> tuple[int, ...]:
        """Action columns loaded into this process."""

        return tuple(self._cache)

    def clear_cache(self) -> None:
        """Drop in-process references; persisted columns remain on disk."""

        self._cache.clear()

    def _column_path(self, action_id: int) -> Path | None:
        if self.cache_dir is None:
            return None
        return self.cache_dir / f"action-{action_id:05d}.npy"

    def _validate_column(self, outcomes: np.ndarray) -> None:
        if outcomes.shape != (self.world_count,) or outcomes.dtype != self.dtype:
            raise ValueError("cached response column shape or dtype mismatch")
        if outcomes.size and int(outcomes.max()) >= (1 << self.spec.m):
            raise ValueError("cached response column contains invalid observation")

    def _compute_column(self, action_id: int) -> NDArray[np.unsignedinteger]:
        action = self.catalog[action_id].intervention
        outcomes = np.empty(self.world_count, dtype=self.dtype)
        for start in range(0, self.world_count, self.chunk_size):
            stop = min(start + self.chunk_size, self.world_count)
            rules = self.worlds.rules[start:stop]
            size = stop - start
            row_indices = np.arange(size)
            values = np.empty((size, self.spec.d + self.spec.m), dtype=np.uint8)
            values[:, : self.spec.d] = action.x
            codes = np.zeros(size, dtype=self.dtype)

            for node_index, forced in enumerate(action.y):
                if forced is not None:
                    result = np.full(size, forced, dtype=np.uint8)
                else:
                    operators = rules[:, node_index, 0]
                    if np.any(operators > int(Op.NOT)):
                        raise ValueError("numeric world dataset contains invalid operator")
                    first = values[row_indices, rules[:, node_index, 1]]
                    second_ids = np.where(
                        operators == int(Op.NOT), 0, rules[:, node_index, 2]
                    )
                    second = values[row_indices, second_ids]
                    result = np.where(
                        operators == int(Op.AND),
                        first & second,
                        np.where(
                            operators == int(Op.OR), first | second, 1 - first
                        ),
                    ).astype(np.uint8, copy=False)
                values[:, self.spec.d + node_index] = result
                codes <<= 1
                codes |= result
            outcomes[start:stop] = codes
        return outcomes
