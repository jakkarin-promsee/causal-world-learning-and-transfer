"""Action-selection policies for exact-oracle baseline experiments.

Policies never receive the environment, true world, or world index.  Their
only episode-specific evidence is the same history-derived ``OracleState``
that an exact Bayesian decision maker would have.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

import numpy as np

from core.oracle import ExactOracle
from core.oracle_state import OracleState


class Policy(Protocol):
    """Minimal interface consumed by :func:`experiments.runner.run_episode`."""

    name: str

    def choose_action(
        self,
        *,
        state: OracleState,
        available_action_ids: Sequence[int],
    ) -> int:
        """Choose one id from ``available_action_ids``."""


class RandomPolicy:
    """Uniformly sample one action that has not yet been used."""

    name = "random"

    def __init__(self, seed: int) -> None:
        self._rng = np.random.default_rng(seed)

    def choose_action(
        self,
        *,
        state: OracleState,
        available_action_ids: Sequence[int],
    ) -> int:
        del state  # Random is deliberately independent of posterior evidence.
        if not available_action_ids:
            raise ValueError("no actions are available")
        index = int(self._rng.integers(len(available_action_ids)))
        return int(available_action_ids[index])


class GreedyInformationGainPolicy:
    """Choose the action with the largest posterior-predictive entropy.

    In the project's deterministic environment with a uniform posterior over
    surviving worlds, ``H(O | H_t, a)`` equals the expected information gain
    about the exact world.  ``candidate_limit=None`` evaluates every available
    action and is therefore exact.  A finite limit uniformly samples candidate
    actions before scoring them; this is useful for early Stage-B/C runs where
    evaluating the full action catalog is expensive.
    """

    def __init__(
        self,
        oracle: ExactOracle,
        *,
        candidate_limit: int | None = None,
        seed: int = 0,
    ) -> None:
        if candidate_limit is not None and candidate_limit < 1:
            raise ValueError("candidate_limit must be at least 1 or None")
        self._oracle = oracle
        self._candidate_limit = candidate_limit
        self._rng = np.random.default_rng(seed)
        self.name = (
            "greedy_information_gain"
            if candidate_limit is None
            else f"sampled_information_gain_{candidate_limit}"
        )

    def choose_action(
        self,
        *,
        state: OracleState,
        available_action_ids: Sequence[int],
    ) -> int:
        if not available_action_ids:
            raise ValueError("no actions are available")

        candidates = tuple(int(action_id) for action_id in available_action_ids)
        if (
            self._candidate_limit is not None
            and len(candidates) > self._candidate_limit
        ):
            sampled_indices = self._rng.choice(
                len(candidates),
                size=self._candidate_limit,
                replace=False,
            )
            candidates = tuple(candidates[int(index)] for index in sampled_indices)

        # Sorting supplies a stable tie break: the lowest action id wins.
        best_action_id = min(candidates)
        best_entropy = -1.0
        for action_id in sorted(candidates):
            distribution = self._oracle.predict(state, action_id)
            probabilities = distribution.probabilities
            nonzero = probabilities[probabilities > 0.0]
            action_entropy = float(-np.sum(nonzero * np.log2(nonzero)))
            if action_entropy > best_entropy:
                best_entropy = action_entropy
                best_action_id = action_id

        return best_action_id
