"""Exact enumeration of the structural hypothesis space Omega."""

from itertools import combinations, product
from math import comb, prod
from typing import Iterator

from core.operators import arity
from core.types import NodeRule, Op, World, WorldSpec


def node_rule_count(parent_pool_size: int) -> int:
    """Return the number of canonical rules available to one node.

    AND and OR take two distinct parents and are commutative. NOT takes
    one parent. Thus the count is 2*C(k, 2) + k = k**2.
    """

    if parent_pool_size < 1:
        raise ValueError("parent_pool_size must be at least 1")
    return sum(comb(parent_pool_size, arity(op)) for op in Op)


def iter_node_rules(parent_pool_size: int) -> Iterator[NodeRule]:
    """Yield every canonical rule for a node in deterministic order."""

    if parent_pool_size < 1:
        raise ValueError("parent_pool_size must be at least 1")

    parent_ids = range(parent_pool_size)
    for op in Op:
        for parents in combinations(parent_ids, arity(op)):
            yield NodeRule(op=op, parents=parents)


def world_count(spec: WorldSpec) -> int:
    """Return |Omega| without materializing any worlds."""

    return prod(
        node_rule_count(spec.parent_pool_size(i))
        for i in range(spec.m)
    )


def iter_worlds(spec: WorldSpec) -> Iterator[World]:
    """Lazily yield every world in Omega in deterministic order."""

    rule_spaces = (
        tuple(iter_node_rules(spec.parent_pool_size(i)))
        for i in range(spec.m)
    )
    for nodes in product(*rule_spaces):
        yield World(nodes=nodes)


def validate_world(world: World, spec: WorldSpec) -> None:
    """Raise ValueError when a world violates the generation contract."""

    if len(world.nodes) != spec.m:
        raise ValueError(
            f"world has {len(world.nodes)} nodes, expected {spec.m}"
        )

    for node_index, rule in enumerate(world.nodes):
        expected_arity = arity(rule.op)
        if len(rule.parents) != expected_arity:
            raise ValueError(
                f"y_{node_index}: {rule.op.name} expects {expected_arity} "
                f"parents, got {len(rule.parents)}"
            )
        if tuple(sorted(rule.parents)) != rule.parents:
            raise ValueError(f"y_{node_index}: parents are not canonical")
        if len(set(rule.parents)) != len(rule.parents):
            raise ValueError(f"y_{node_index}: duplicate parents are not allowed")

        pool_size = spec.parent_pool_size(node_index)
        if any(parent < 0 or parent >= pool_size for parent in rule.parents):
            raise ValueError(
                f"y_{node_index}: parent must be in [0, {pool_size}), "
                f"got {rule.parents}"
            )
