"""Dynamic state owned by one exact-oracle episode.

``history`` is the source of truth. ``survivors`` is the cached result of
replaying that history against every candidate world.
"""

from dataclasses import dataclass
from numbers import Integral

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class Experiment:
    """One action/observation pair in an episode history."""

    action_id: int
    observation_code: int

    def __post_init__(self) -> None:
        if not isinstance(self.action_id, Integral) or self.action_id < 0:
            raise ValueError("action_id must be a non-negative integer")
        if (
            not isinstance(self.observation_code, Integral)
            or self.observation_code < 0
        ):
            raise ValueError(
                "observation_code must be a non-negative integer"
            )

        # NumPy integer scalars are accepted, but state records use plain ints.
        object.__setattr__(self, "action_id", int(self.action_id))
        object.__setattr__(
            self,
            "observation_code",
            int(self.observation_code),
        )


@dataclass(frozen=True)
class OracleState:
    """The complete dynamic state for one exact-oracle episode.

    A private, read-only copy of ``survivors`` prevents callers from silently
    changing an old state after it has been returned by the oracle.
    """

    history: tuple[Experiment, ...]
    survivors: NDArray[np.bool_]

    def __post_init__(self) -> None:
        if not isinstance(self.history, tuple) or any(
            not isinstance(item, Experiment) for item in self.history
        ):
            raise TypeError("history must be a tuple of Experiment values")

        survivors = np.asarray(self.survivors)
        if survivors.dtype != np.bool_ or survivors.ndim != 1:
            raise TypeError("survivors must be a one-dimensional boolean array")

        owned_survivors = survivors.copy()
        owned_survivors.flags.writeable = False
        object.__setattr__(self, "survivors", owned_survivors)

    @property
    def survivor_count(self) -> int:
        """Return |C_t|."""

        return int(np.count_nonzero(self.survivors))

    @property
    def timestep(self) -> int:
        """Return t, the number of completed experiments."""

        return len(self.history)
