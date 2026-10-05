from enum import IntEnum
from dataclasses import dataclass


class Op(IntEnum):
    AND = 0
    OR = 1
    NOT = 2


@dataclass(frozen=True)
class NodeRule:
    """The structural equation for one endogenous variable."""

    op: Op
    parents: tuple[int, ...]


@dataclass(frozen=True)
class World:
    """Rules for y_0, ..., y_(m-1), stored in topological order."""

    nodes: tuple[NodeRule, ...]


@dataclass(frozen=True)
class WorldSpec:
    """Shape of a bounded family of Boolean worlds.

    Variable ids use one global namespace:
    x_j has id j, and y_i has id d + i.
    """

    d: int
    m: int

    def __post_init__(self) -> None:
        if self.d < 1:
            raise ValueError("d must be at least 1")
        if self.m < 1:
            raise ValueError("m must be at least 1")

    def parent_pool_size(self, node_index: int) -> int:
        if not 0 <= node_index < self.m:
            raise IndexError(f"node index out of range: {node_index}")
        return self.d + node_index


@dataclass(frozen=True)
class Intervention:
    """An intervention on a world.
    
    0|1 = set to
    None = do not set

    Stage A: do(X) -> count_non_none(y) == 0
    Stage B: do(X, one Y) -> count_non_none(y) <= 1
    Stage C: do(X, arbitrary Y) -> count_non_none(y) <= m
    """

    x: tuple[int, ...]
    y: tuple[int | None, ...]

    def __post_init__(self) -> None:
        if any(value not in (0, 1) for value in self.x):
            raise ValueError(f"X values must be 0 or 1, got {self.x}")
        if any(value is not None and value not in (0, 1) for value in self.y):
            raise ValueError(
                f"Y interventions must be None, 0, or 1, got {self.y}"
            )
