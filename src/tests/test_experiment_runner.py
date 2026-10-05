import unittest

import numpy as np

from core.evaluator import Environment
from core.oracle import ActionCatalog, ExactOracle, OnDemandResponseStore, Stage
from core.types import WorldSpec
from core.worldgen import iter_worlds
from experiments.policies import GreedyInformationGainPolicy, RandomPolicy
from experiments.runner import EpisodeConfig, entropy_bits, run_episode


class OrderedPolicy:
    name = "ordered"

    def choose_action(self, *, state, available_action_ids) -> int:
        del state
        return int(available_action_ids[0])


class ExperimentRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.spec = WorldSpec(d=2, m=2)
        self.worlds = list(iter_worlds(self.spec))
        self.catalog = ActionCatalog(self.spec)
        self.responses = OnDemandResponseStore(
            self.worlds,
            len(self.worlds),
            self.catalog,
        )
        self.oracle = ExactOracle(
            self.catalog,
            self.responses,
            stage=Stage.A,
        )

    def test_entropy_bits(self) -> None:
        self.assertAlmostEqual(entropy_bits([0.5, 0.5]), 1.0)
        self.assertAlmostEqual(entropy_bits([1.0, 0.0]), 0.0)
        with self.assertRaises(ValueError):
            entropy_bits([0.4, 0.4])

    def test_runner_records_monotone_updates_without_repeated_actions(self) -> None:
        result = run_episode(
            world_index=7,
            environment=Environment(self.worlds[7], self.spec),
            oracle=self.oracle,
            policy=OrderedPolicy(),
            config=EpisodeConfig(stage=Stage.A, budget=3, seed=11),
        )

        self.assertEqual(len(result.steps), 3)
        self.assertEqual([step.action_id for step in result.steps], [0, 1, 2])
        for step in result.steps:
            self.assertLessEqual(
                step.survivor_count_after,
                step.survivor_count_before,
            )
            self.assertAlmostEqual(
                step.observed_surprisal_bits,
                step.realized_information_gain_bits,
            )

    def test_runner_rejects_policy_action_outside_available_set(self) -> None:
        class InvalidPolicy:
            name = "invalid"

            def choose_action(self, *, state, available_action_ids) -> int:
                del state, available_action_ids
                return len(self.catalog)  # type: ignore[attr-defined]

        invalid = InvalidPolicy()
        invalid.catalog = self.catalog
        with self.assertRaisesRegex(ValueError, "unavailable action"):
            run_episode(
                world_index=0,
                environment=Environment(self.worlds[0], self.spec),
                oracle=self.oracle,
                policy=invalid,
                config=EpisodeConfig(stage=Stage.A, budget=1, seed=0),
            )

    def test_random_policy_is_reproducible(self) -> None:
        available = tuple(range(10))
        state = self.oracle.initial_state()
        first = RandomPolicy(123).choose_action(
            state=state,
            available_action_ids=available,
        )
        second = RandomPolicy(123).choose_action(
            state=state,
            available_action_ids=available,
        )
        self.assertEqual(first, second)
        self.assertIn(first, available)

    def test_greedy_policy_maximizes_predictive_entropy(self) -> None:
        state = self.oracle.initial_state()
        available = tuple(
            entry.action_id
            for entry in self.catalog.entries_for_stage(Stage.A)
        )
        expected = min(
            available,
            key=lambda action_id: (
                -entropy_bits(
                    self.oracle.predict(state, action_id).probabilities
                ),
                action_id,
            ),
        )
        policy = GreedyInformationGainPolicy(self.oracle)

        actual = policy.choose_action(
            state=state,
            available_action_ids=available,
        )

        self.assertEqual(actual, expected)

    def test_sampled_greedy_returns_an_available_action(self) -> None:
        state = self.oracle.initial_state()
        available = tuple(range(4))
        policy = GreedyInformationGainPolicy(
            self.oracle,
            candidate_limit=2,
            seed=9,
        )

        action_id = policy.choose_action(
            state=state,
            available_action_ids=available,
        )

        self.assertIn(action_id, available)
        self.assertEqual(policy.name, "sampled_information_gain_2")


if __name__ == "__main__":
    unittest.main()
