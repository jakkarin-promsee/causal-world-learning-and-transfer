"""Execution semantics and the hidden-world environment."""

from dataclasses import dataclass
from numbers import Integral

from core.operators import apply_operator
from core.types import Intervention, World, WorldSpec
from core.worldgen import validate_world


def evaluate(
    world: World,
    action: Intervention,
    spec: WorldSpec,
) -> tuple[int, ...]:
    """Return the endogenous observation produced by ``world`` under ``action``.

    ``world`` is expected to obey ``spec``. An intervention on ``y_i`` replaces
    its structural equation, and downstream nodes observe the intervened value.
    The returned tuple contains only ``(y_0, ..., y_(m-1))``; the exogenous
    action ``x`` is not part of the observation.
    """

    if len(world.nodes) != spec.m:
        raise ValueError(
            f"world has {len(world.nodes)} nodes, expected {spec.m}"
        )
    if len(action.x) != spec.d:
        raise ValueError(
            f"action has {len(action.x)} X values, expected {spec.d}"
        )
    if len(action.y) != spec.m:
        raise ValueError(
            f"action has {len(action.y)} Y interventions, expected {spec.m}"
        )

    pool = list(action.x)
    observation: list[int] = []

    for node_index, node in enumerate(world.nodes):
        intervened_value = action.y[node_index]
        if intervened_value is None:
            parent_values = tuple(pool[parent] for parent in node.parents)
            value = apply_operator(node.op, parent_values)
        else:
            value = intervened_value

        pool.append(value)
        observation.append(value)

    return tuple(observation)


def encode_observation(
    observation: tuple[int, ...],
    spec: WorldSpec,
) -> int:
    """Encode ``(y_0, ..., y_(m-1))`` as one integer outcome code.

    ``y_0`` is the most-significant bit. For example, ``(1, 0, 1)`` is
    encoded as binary ``101`` (the integer 5).
    """

    if len(observation) != spec.m:
        raise ValueError(
            f"observation has {len(observation)} values, expected {spec.m}"
        )

    code = 0
    for value in observation:
        if not isinstance(value, Integral) or value not in (0, 1):
            raise ValueError(
                f"observation values must be 0 or 1, got {observation}"
            )
        code = (code << 1) | int(value)
    return code


def decode_observation(code: int, spec: WorldSpec) -> tuple[int, ...]:
    """Invert :func:`encode_observation`."""

    outcome_count = 1 << spec.m
    if not isinstance(code, Integral) or not 0 <= code < outcome_count:
        raise ValueError(
            f"observation code must be in [0, {outcome_count}), got {code}"
        )
    return tuple(
        (int(code) >> shift) & 1
        for shift in range(spec.m - 1, -1, -1)
    )


@dataclass(frozen=True)
class Environment:
    """A deterministic environment that owns the episode's hidden world.

    The runner should expose only :meth:`step` to a policy. In particular, it
    must not pass ``true_world`` (or a dataset index for it) to the policy.
    """

    true_world: World
    spec: WorldSpec

    def __post_init__(self) -> None:
        validate_world(self.true_world, self.spec)

    def step(self, action: Intervention) -> tuple[int, ...]:
        """Perform ``action`` and return the resulting Y observation."""

        return evaluate(self.true_world, action, self.spec)
