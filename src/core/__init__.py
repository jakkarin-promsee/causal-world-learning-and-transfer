"""Core exact-world tools for the beyond-backprop research project."""

from core.evaluator import Environment, decode_observation, encode_observation
from core.oracle import (
    ActionCatalog,
    ExactOracle,
    OnDemandResponseStore,
    OutcomeDistribution,
    Stage,
)
from core.oracle_state import Experiment, OracleState
from core.types import Intervention, NodeRule, Op, World, WorldSpec
from core.worldgen import iter_worlds, world_count

__all__ = [
    "ActionCatalog",
    "Environment",
    "ExactOracle",
    "Experiment",
    "Intervention",
    "NodeRule",
    "OnDemandResponseStore",
    "Op",
    "OracleState",
    "OutcomeDistribution",
    "Stage",
    "World",
    "WorldSpec",
    "decode_observation",
    "encode_observation",
    "iter_worlds",
    "world_count",
]
