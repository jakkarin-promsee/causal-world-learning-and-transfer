"""Exact Bayesian inference for deterministic structural Boolean worlds.

The implementation deliberately keeps the first version small:

* :class:`ActionCatalog` gives every intervention one stable integer id.
* :class:`OnDemandResponseStore` evaluates all worlds lazily for an action.
* :class:`ExactOracle` is stateless; callers pass and receive OracleState.

Under a uniform prior and deterministic observations, the posterior is uniform
over the surviving worlds. Consequently a boolean survivor mask is sufficient;
we do not need to store one floating-point probability per world.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from enum import IntEnum
from itertools import product
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from core.evaluator import encode_observation, evaluate
from core.oracle_state import Experiment, OracleState
from core.types import Intervention, World, WorldSpec


class Stage(IntEnum):
    """Largest family of interventions available to an episode."""

    A = 0  # do(X)
    B = 1  # do(X, at most one Y)
    C = 2  # do(X, arbitrary Y)


@dataclass(frozen=True)
class ActionEntry:
    """One stable catalog entry."""

    action_id: int
    intervention: Intervention
    minimum_stage: Stage


class ActionCatalog:
    """Canonical, stage-aware mapping between action ids and interventions.

    Entries are grouped by minimum stage. This makes all Stage-A ids a prefix
    of Stage-B ids, which are themselves a prefix of Stage-C ids. Expanding an
    experiment therefore never changes an existing action id.
    """

    def __init__(self, spec: WorldSpec) -> None:
        self.spec = spec
        entries: list[ActionEntry] = []

        x_values = tuple(product((0, 1), repeat=spec.d))
        no_y = (None,) * spec.m

        # Stage A: every do(X) action.
        for x in x_values:
            entries.append(
                ActionEntry(
                    action_id=len(entries),
                    intervention=Intervention(x=x, y=no_y),
                    minimum_stage=Stage.A,
                )
            )

        # New Stage-B actions: intervene on exactly one Y.
        for x in x_values:
            for node_index in range(spec.m):
                for value in (0, 1):
                    y = list(no_y)
                    y[node_index] = value
                    entries.append(
                        ActionEntry(
                            action_id=len(entries),
                            intervention=Intervention(x=x, y=tuple(y)),
                            minimum_stage=Stage.B,
                        )
                    )

        # New Stage-C actions: intervene on two or more Y variables.
        for x in x_values:
            for y in product((None, 0, 1), repeat=spec.m):
                if sum(value is not None for value in y) < 2:
                    continue # remove stage A and B
                
                entries.append(
                    ActionEntry(
                        action_id=len(entries),
                        intervention=Intervention(x=x, y=y),
                        minimum_stage=Stage.C,
                    )
                )

        self._entries = tuple(entries)
        self._ids_by_intervention = {
            entry.intervention: entry.action_id for entry in self._entries
        }

    def __len__(self) -> int:
        return len(self._entries)

    def __iter__(self) -> Iterator[ActionEntry]:
        return iter(self._entries)

    def __getitem__(self, action_id: int) -> ActionEntry:
        if not isinstance(action_id, (int, np.integer)):
            raise TypeError("action_id must be an integer")
        if not 0 <= int(action_id) < len(self):
            raise IndexError(f"action_id out of range: {action_id}")
        return self._entries[int(action_id)]

    def action_id_for(self, intervention: Intervention) -> int:
        """Return the stable id for ``intervention``."""

        try:
            return self._ids_by_intervention[intervention]
        except KeyError as error:
            raise ValueError(
                f"intervention does not match catalog spec {self.spec}"
            ) from error

    def entries_for_stage(self, stage: Stage) -> tuple[ActionEntry, ...]:
        """Return every action permitted at ``stage``."""

        stage = Stage(stage)
        return tuple(
            entry for entry in self._entries if entry.minimum_stage <= stage
        )

    def validate_for_stage(self, action_id: int, stage: Stage) -> ActionEntry:
        """Return an entry, rejecting actions not yet available at ``stage``."""

        entry = self[action_id]
        if entry.minimum_stage > stage:
            raise ValueError(
                f"action {action_id} requires Stage {entry.minimum_stage.name}, "
                f"but oracle is restricted to Stage {stage.name}"
            )
        return entry


class ResponseStore(Protocol):
    """Minimal boundary between exact inference and response computation."""

    spec: WorldSpec
    world_count: int

    def outcomes_for_action(self, action_id: int) -> NDArray[np.unsignedinteger]:
        """Return one encoded outcome per world, in stable world order."""


def _outcome_dtype(spec: WorldSpec) -> np.dtype[np.unsignedinteger]:
    if spec.m <= 8:
        return np.dtype(np.uint8)
    if spec.m <= 16:
        return np.dtype(np.uint16)
    if spec.m <= 32:
        return np.dtype(np.uint32)
    if spec.m <= 64:
        return np.dtype(np.uint64)
    raise ValueError("encoded observations currently support at most 64 Y nodes")


class OnDemandResponseStore:
    """Compute a response column when it is first requested, then cache it.

    ``worlds`` must be re-iterable and preserve the same order on every pass.
    Both ``list[World]`` and :class:`core.storage.WorldDataset` satisfy this
    contract. Only requested action columns are materialized, so Stage A for the
    705,600-world dataset needs about 11 MB rather than a full Stage-C matrix.
    """

    def __init__(
        self,
        worlds: Iterable[World],
        world_count: int,
        catalog: ActionCatalog,
    ) -> None:
        if world_count < 1:
            raise ValueError("world_count must be at least 1")
        self._worlds = worlds
        self.world_count = world_count
        self.catalog = catalog
        self.spec = catalog.spec
        self._dtype = _outcome_dtype(self.spec)
        self._cache: dict[int, NDArray[np.unsignedinteger]] = {}

    def outcomes_for_action(
        self,
        action_id: int,
    ) -> NDArray[np.unsignedinteger]:
        entry = self.catalog[action_id]
        cached = self._cache.get(entry.action_id)
        if cached is not None:
            return cached

        outcomes = np.empty(self.world_count, dtype=self._dtype)
        seen = 0
        for seen, world in enumerate(self._worlds, start=1):
            if seen > self.world_count:
                raise ValueError(
                    "world source yielded more worlds than world_count"
                )
            observation = evaluate(world, entry.intervention, self.spec)
            outcomes[seen - 1] = encode_observation(observation, self.spec)

        if seen != self.world_count:
            raise ValueError(
                f"world source yielded {seen} worlds, expected {self.world_count}"
            )

        outcomes.flags.writeable = False
        self._cache[entry.action_id] = outcomes
        return outcomes

    @property
    def cached_action_ids(self) -> tuple[int, ...]:
        """Expose cache contents for diagnostics, not inference logic."""

        return tuple(self._cache)

    def clear_cache(self) -> None:
        """Drop derived response columns without changing oracle semantics."""

        self._cache.clear()


@dataclass(frozen=True)
class OutcomeDistribution:
    """Posterior-predictive distribution over encoded observations."""

    counts: NDArray[np.int64]
    probabilities: NDArray[np.float64]

    def __post_init__(self) -> None:
        counts = np.asarray(self.counts, dtype=np.int64).copy()
        probabilities = np.asarray(self.probabilities, dtype=np.float64).copy()
        if counts.ndim != 1 or probabilities.ndim != 1:
            raise TypeError("counts and probabilities must be one-dimensional")
        if counts.shape != probabilities.shape:
            raise ValueError("counts and probabilities must have the same shape")
        counts.flags.writeable = False
        probabilities.flags.writeable = False
        object.__setattr__(self, "counts", counts)
        object.__setattr__(self, "probabilities", probabilities)

    def probability_of(self, observation_code: int) -> float:
        """Return p(observation_code | H_t, action)."""

        if not 0 <= observation_code < len(self.probabilities):
            raise ValueError(f"observation_code out of range: {observation_code}")
        return float(self.probabilities[observation_code])


class InconsistentObservationError(ValueError):
    """Raised when no currently surviving world explains an experiment."""


class ExactOracle:
    """A stateless exact-inference engine over a fixed response store."""

    def __init__(
        self,
        catalog: ActionCatalog,
        responses: ResponseStore,
        *,
        stage: Stage = Stage.A,
    ) -> None:
        if responses.spec != catalog.spec:
            raise ValueError("response store and action catalog specs differ")
        if responses.world_count < 1:
            raise ValueError("response store must contain at least one world")

        self.catalog = catalog
        self.responses = responses
        self.stage = Stage(stage)
        self.world_count = responses.world_count
        self.outcome_count = 1 << catalog.spec.m

    def initial_state(self) -> OracleState:
        """Return H_0 = empty and C_0 = Omega."""

        return OracleState(
            history=(),
            survivors=np.ones(self.world_count, dtype=np.bool_),
        )

    def update(
        self,
        state: OracleState,
        experiment: Experiment,
    ) -> OracleState:
        """Filter C_t and return a new state for H_(t+1)."""

        self._validate_state(state)
        if not isinstance(experiment, Experiment):
            raise TypeError("experiment must be an Experiment")
        self.catalog.validate_for_stage(experiment.action_id, self.stage)
        if experiment.observation_code >= self.outcome_count:
            raise ValueError(
                "observation_code must be in "
                f"[0, {self.outcome_count}), got {experiment.observation_code}"
            )

        expected = self.responses.outcomes_for_action(experiment.action_id)
        self._validate_response_column(expected)
        next_survivors = state.survivors & (
            expected == experiment.observation_code
        )

        if not np.any(next_survivors):
            raise InconsistentObservationError(
                "no surviving world explains "
                f"action {experiment.action_id} with observation "
                f"{experiment.observation_code}"
            )

        return OracleState(
            history=state.history + (experiment,),
            survivors=next_survivors,
        )

    def predict(
        self,
        state: OracleState,
        action_id: int,
    ) -> OutcomeDistribution:
        """Return p(o | H_t, action_id) under the uniform surviving posterior."""

        self._validate_state(state)
        self.catalog.validate_for_stage(action_id, self.stage)
        outcomes = self.responses.outcomes_for_action(action_id)
        self._validate_response_column(outcomes)

        counts = np.bincount(
            outcomes[state.survivors].astype(np.int64, copy=False),
            minlength=self.outcome_count,
        ).astype(np.int64, copy=False)
        probabilities = counts.astype(np.float64) / state.survivor_count
        return OutcomeDistribution(counts=counts, probabilities=probabilities)

    def replay(self, history: Iterable[Experiment]) -> OracleState:
        """Reconstruct state using only an experiment history."""

        state = self.initial_state()
        for experiment in history:
            if not isinstance(experiment, Experiment):
                raise TypeError("history must contain only Experiment values")
            state = self.update(state, experiment)
        return state

    def _validate_state(self, state: OracleState) -> None:
        if not isinstance(state, OracleState):
            raise TypeError("state must be an OracleState")
        if state.survivors.shape != (self.world_count,):
            raise ValueError(
                f"state has {state.survivors.size} worlds, "
                f"oracle expects {self.world_count}"
            )
        if state.survivor_count == 0:
            raise ValueError("OracleState cannot have an empty survivor set")

    def _validate_response_column(self, outcomes: NDArray[np.unsignedinteger]) -> None:
        if outcomes.shape != (self.world_count,):
            raise ValueError(
                f"response column has shape {outcomes.shape}, "
                f"expected ({self.world_count},)"
            )
        if not np.issubdtype(outcomes.dtype, np.unsignedinteger):
            raise TypeError("response outcomes must use an unsigned integer dtype")
        if np.any(outcomes >= self.outcome_count):
            raise ValueError("response store returned an invalid observation code")
