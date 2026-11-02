"""One-episode execution and records for oracle baseline experiments."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike

from core.evaluator import Environment, encode_observation
from core.oracle import ExactOracle, Stage
from core.oracle_state import Experiment
from reuse.jsonl_reference.policies import GreedyInformationGainPolicy, Policy


def entropy_bits(probabilities: ArrayLike) -> float:
    """Return Shannon entropy in bits for a discrete probability vector."""

    values = np.asarray(probabilities, dtype=np.float64)
    if values.ndim != 1:
        raise TypeError("probabilities must be one-dimensional")
    if np.any(values < 0.0) or not np.isclose(values.sum(), 1.0):
        raise ValueError("probabilities must be non-negative and sum to 1")
    nonzero = values[values > 0.0]
    return float(-np.sum(nonzero * np.log2(nonzero)))


@dataclass(frozen=True)
class EpisodeConfig:
    """The controlled conditions for one episode."""

    stage: Stage
    budget: int
    seed: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "stage", Stage(self.stage))
        if self.budget < 1:
            raise ValueError("budget must be at least 1")
        if self.seed < 0:
            raise ValueError("seed must be non-negative")


@dataclass(frozen=True)
class StepRecord:
    """Measurements made around one action/observation update."""

    timestep: int
    action_id: int
    observation_code: int
    survivor_count_before: int
    survivor_count_after: int
    predictive_entropy_bits: float
    observed_surprisal_bits: float
    realized_information_gain_bits: float
    remaining_uncertainty_bits: float


@dataclass(frozen=True)
class EpisodeResult:
    """Complete immutable result of one episode."""

    world_index: int
    policy_name: str
    config: EpisodeConfig
    steps: tuple[StepRecord, ...]

    @property
    def final_survivor_count(self) -> int:
        return self.steps[-1].survivor_count_after


@dataclass(frozen=True)
class FullCandidateGreedyEpisodeResult:
    """Executed steps plus the certified full-budget uncertainty trajectory."""

    episode: EpisodeResult
    termination_reason: str  # "singleton", "equivalent", or "budget_exhausted"
    initial_world_count: int

    @property
    def final_survivor_count(self) -> int:
        """Include the valid case where the run stops before any action."""

        if not self.episode.steps:
            return self.initial_world_count
        return self.episode.steps[-1].survivor_count_after

    @property
    def uncertainty_trajectory_bits(self) -> tuple[float, ...]:
        """U_0 through U_budget; suffix values are inferred, not executed steps."""

        observed = (math.log2(self.initial_world_count),) + tuple(
            step.remaining_uncertainty_bits for step in self.episode.steps
        )
        return observed + (observed[-1],) * (
            self.episode.config.budget + 1 - len(observed)
        )


def run_episode(
    *,
    world_index: int,
    environment: Environment,
    oracle: ExactOracle,
    policy: Policy,
    config: EpisodeConfig,
) -> EpisodeResult:
    """Run one active-inference episode without exposing its world to policy."""

    result, _ = _run_episode(
        world_index=world_index,
        environment=environment,
        oracle=oracle,
        policy=policy,
        config=config,
        stop_when_uninformative=False,
    )
    return result


def run_full_candidate_greedy_episode(
    *,
    world_index: int,
    environment: Environment,
    oracle: ExactOracle,
    config: EpisodeConfig,
) -> FullCandidateGreedyEpisodeResult:
    """Run full-candidate greedy until exact identification or a proven plateau.

    This specialized runner requires the stage's full action budget. It never
    emits invented StepRecords for unexecuted actions; the separate trajectory
    property fills the certified constant suffix for plotting.
    """

    action_count = len(oracle.catalog.entries_for_stage(config.stage))
    if config.budget != action_count:
        raise ValueError(
            f"full-candidate greedy optimization requires the full stage "
            f"budget {action_count}, got {config.budget}"
        )
    policy = GreedyInformationGainPolicy(oracle)
    episode, reason = _run_episode(
        world_index=world_index,
        environment=environment,
        oracle=oracle,
        policy=policy,
        config=config,
        stop_when_uninformative=True,
    )
    return FullCandidateGreedyEpisodeResult(
        episode=episode,
        termination_reason=reason,
        initial_world_count=oracle.world_count,
    )


def _run_episode(
    *,
    world_index: int,
    environment: Environment,
    oracle: ExactOracle,
    policy: Policy,
    config: EpisodeConfig,
    stop_when_uninformative: bool,
) -> tuple[EpisodeResult, str]:
    """Shared episode mechanics; only the specialized caller may stop early."""

    if world_index < 0:
        raise ValueError("world_index must be non-negative")
    if environment.spec != oracle.catalog.spec:
        raise ValueError("environment and oracle specs differ")
    if config.stage != oracle.stage:
        raise ValueError("config stage and oracle stage differ")

    permitted_action_ids = tuple(
        entry.action_id
        for entry in oracle.catalog.entries_for_stage(config.stage)
    )
    if config.budget > len(permitted_action_ids):
        raise ValueError(
            f"budget {config.budget} exceeds the {len(permitted_action_ids)} "
            "distinct actions available at this stage"
        )

    state = oracle.initial_state()
    used_action_ids: set[int] = set()
    records: list[StepRecord] = []
    termination_reason = "budget_exhausted"

    for timestep in range(config.budget):
        if stop_when_uninformative and state.survivor_count == 1:
            termination_reason = "singleton"
            break
        available_action_ids = tuple(
            action_id
            for action_id in permitted_action_ids
            if action_id not in used_action_ids
        )
        action_id = policy.choose_action(
            state=state,
            available_action_ids=available_action_ids,
        )
        if action_id not in available_action_ids:
            raise ValueError(
                f"policy {policy.name!r} selected unavailable action {action_id}"
            )

        distribution = oracle.predict(state, action_id)
        if stop_when_uninformative and np.count_nonzero(distribution.counts) == 1:
            # Full-candidate greedy just scored every available action. Its
            # winner has one outcome, so no remaining action can split C_t.
            termination_reason = "equivalent"
            break
        predictive_entropy = entropy_bits(distribution.probabilities)
        survivor_count_before = state.survivor_count

        intervention = oracle.catalog[action_id].intervention
        observation = environment.step(intervention)
        observation_code = encode_observation(observation, environment.spec)
        observation_probability = distribution.probability_of(observation_code)
        if observation_probability <= 0.0:
            raise RuntimeError(
                "true environment produced an outcome excluded by the oracle"
            )

        state = oracle.update(
            state,
            Experiment(
                action_id=action_id,
                observation_code=observation_code,
            ),
        )
        used_action_ids.add(action_id)

        realized_information_gain = math.log2(
            survivor_count_before / state.survivor_count
        )
        records.append(
            StepRecord(
                timestep=timestep,
                action_id=action_id,
                observation_code=observation_code,
                survivor_count_before=survivor_count_before,
                survivor_count_after=state.survivor_count,
                predictive_entropy_bits=predictive_entropy,
                observed_surprisal_bits=-math.log2(observation_probability),
                realized_information_gain_bits=realized_information_gain,
                remaining_uncertainty_bits=math.log2(state.survivor_count),
            )
        )

    if stop_when_uninformative and state.survivor_count == 1:
        termination_reason = "singleton"

    return EpisodeResult(
        world_index=world_index,
        policy_name=policy.name,
        config=config,
        steps=tuple(records),
    ), termination_reason
