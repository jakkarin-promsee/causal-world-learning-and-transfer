import unittest

import numpy as np

from core.evaluator import Environment
from core.oracle import ActionCatalog, ExactOracle, OnDemandResponseStore, Stage
from core.types import NodeRule, Op, World, WorldSpec
from core.worldgen import iter_worlds
from reuse.policies import GreedyInformationGainPolicy, RandomPolicy
from reuse.runner import (
    EpisodeConfig,
    entropy_bits,
    run_episode,
    run_full_candidate_greedy_episode,
)


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


class FullCandidateGreedyOptimizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.spec = WorldSpec(d=2, m=2)
        shared_y0 = NodeRule(Op.AND, (0, 1))
        self.first = World((shared_y0, NodeRule(Op.AND, (0, 2))))
        self.equivalent_in_a = World((shared_y0, NodeRule(Op.AND, (0, 1))))
        self.distinct_in_a = World((
            NodeRule(Op.OR, (0, 1)), NodeRule(Op.AND, (0, 2))
        ))
        self.catalog = ActionCatalog(self.spec)

    def oracle_for(self, worlds, stage):
        responses = OnDemandResponseStore(worlds, len(worlds), self.catalog)
        return ExactOracle(self.catalog, responses, stage=stage)

    def run_pair(self, worlds, stage):
        oracle = self.oracle_for(worlds, stage)
        config = EpisodeConfig(
            stage=stage,
            budget=len(self.catalog.entries_for_stage(stage)),
            seed=7,
        )
        environment = Environment(worlds[0], self.spec)
        original = run_episode(
            world_index=0,
            environment=environment,
            oracle=oracle,
            policy=GreedyInformationGainPolicy(oracle),
            config=config,
        )
        optimized = run_full_candidate_greedy_episode(
            world_index=0,
            environment=environment,
            oracle=oracle,
            config=config,
        )
        return original, optimized

    def test_equivalent_worlds_stop_without_claiming_singleton(self) -> None:
        original, optimized = self.run_pair(
            [self.first, self.equivalent_in_a], Stage.A
        )

        self.assertEqual(optimized.termination_reason, "equivalent")
        self.assertEqual(optimized.episode.steps, ())
        self.assertEqual(optimized.final_survivor_count, 2)
        self.assertEqual(optimized.uncertainty_trajectory_bits, (1.0,) * 5)
        self.assertEqual(original.final_survivor_count, 2)
        self.assertTrue(all(step.realized_information_gain_bits == 0 for step in original.steps))

    def test_singleton_at_initial_state_needs_no_action(self) -> None:
        original, optimized = self.run_pair([self.first], Stage.A)

        self.assertEqual(optimized.termination_reason, "singleton")
        self.assertEqual(optimized.episode.steps, ())
        self.assertEqual(optimized.final_survivor_count, 1)
        self.assertEqual(optimized.uncertainty_trajectory_bits, (0.0,) * 5)
        self.assertEqual(original.final_survivor_count, 1)

    def test_equivalent_plateau_after_an_informative_action(self) -> None:
        original, optimized = self.run_pair(
            [self.first, self.equivalent_in_a, self.distinct_in_a], Stage.A
        )

        self.assertEqual(optimized.termination_reason, "equivalent")
        self.assertEqual(len(optimized.episode.steps), 1)
        self.assertEqual(optimized.episode.steps, original.steps[:1])
        self.assertEqual(optimized.final_survivor_count, 2)
        self.assertEqual(
            optimized.uncertainty_trajectory_bits,
            (np.log2(3),) + (1.0,) * 4,
        )
        self.assertEqual(
            optimized.uncertainty_trajectory_bits,
            (np.log2(3),) + tuple(
                step.remaining_uncertainty_bits for step in original.steps
            ),
        )

    def test_later_stages_distinguish_worlds_equivalent_in_stage_a(self) -> None:
        for stage in (Stage.B, Stage.C):
            with self.subTest(stage=stage):
                original, optimized = self.run_pair(
                    [self.first, self.equivalent_in_a], stage
                )

                self.assertEqual(optimized.termination_reason, "singleton")
                self.assertEqual(len(optimized.episode.steps), 1)
                self.assertEqual(optimized.episode.steps, original.steps[:1])
                self.assertEqual(optimized.final_survivor_count, 1)
                self.assertEqual(
                    optimized.uncertainty_trajectory_bits,
                    (1.0,) + (0.0,) * original.config.budget,
                )

    def test_optimized_runner_requires_full_stage_budget(self) -> None:
        worlds = [self.first, self.equivalent_in_a]
        with self.assertRaisesRegex(ValueError, "full stage budget"):
            run_full_candidate_greedy_episode(
                world_index=0,
                environment=Environment(worlds[0], self.spec),
                oracle=self.oracle_for(worlds, Stage.A),
                config=EpisodeConfig(stage=Stage.A, budget=1, seed=7),
            )


if __name__ == "__main__":
    unittest.main()
