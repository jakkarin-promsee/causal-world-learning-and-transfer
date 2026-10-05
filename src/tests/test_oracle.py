import unittest

import numpy as np

from core.evaluator import Environment, decode_observation, encode_observation
from core.oracle import (
    ActionCatalog,
    ExactOracle,
    InconsistentObservationError,
    OnDemandResponseStore,
    Stage,
)
from core.oracle_state import Experiment
from core.types import Intervention, WorldSpec
from core.worldgen import iter_worlds


class ActionCatalogTests(unittest.TestCase):
    def test_stage_sizes_and_stable_prefixes(self) -> None:
        catalog = ActionCatalog(WorldSpec(d=4, m=4))

        stage_a = catalog.entries_for_stage(Stage.A)
        stage_b = catalog.entries_for_stage(Stage.B)
        stage_c = catalog.entries_for_stage(Stage.C)

        self.assertEqual(len(stage_a), 16)
        self.assertEqual(len(stage_b), 144)
        self.assertEqual(len(stage_c), 1_296)
        self.assertEqual(stage_b[:16], stage_a)
        self.assertEqual(stage_c[:144], stage_b)
        self.assertEqual(
            [entry.action_id for entry in stage_c],
            list(range(1_296)),
        )

    def test_catalog_round_trip(self) -> None:
        spec = WorldSpec(d=2, m=2)
        catalog = ActionCatalog(spec)
        intervention = Intervention((1, 0), (None, 1))

        action_id = catalog.action_id_for(intervention)

        self.assertEqual(catalog[action_id].intervention, intervention)
        self.assertEqual(catalog[action_id].minimum_stage, Stage.B)


class ObservationEncodingTests(unittest.TestCase):
    def test_encode_decode_round_trip(self) -> None:
        spec = WorldSpec(d=2, m=4)
        for observation in (
            (0, 0, 0, 0),
            (0, 1, 1, 0),
            (1, 0, 0, 1),
            (1, 1, 1, 1),
        ):
            with self.subTest(observation=observation):
                code = encode_observation(observation, spec)
                self.assertEqual(decode_observation(code, spec), observation)


class ExactOracleTests(unittest.TestCase):
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
            stage=Stage.C,
        )

    def experiment_from_environment(
        self,
        environment: Environment,
        intervention: Intervention,
    ) -> Experiment:
        action_id = self.catalog.action_id_for(intervention)
        observation = environment.step(intervention)
        return Experiment(
            action_id=action_id,
            observation_code=encode_observation(observation, self.spec),
        )

    def test_initial_state_contains_all_worlds_and_is_read_only(self) -> None:
        state = self.oracle.initial_state()

        self.assertEqual(state.history, ())
        self.assertEqual(state.timestep, 0)
        self.assertEqual(state.survivor_count, len(self.worlds))
        with self.assertRaises(ValueError):
            state.survivors[0] = False

    def test_update_is_monotone_and_keeps_true_world(self) -> None:
        true_world_index = 17
        environment = Environment(self.worlds[true_world_index], self.spec)
        state_0 = self.oracle.initial_state()
        experiment = self.experiment_from_environment(
            environment,
            Intervention((0, 1), (None, None)),
        )

        state_1 = self.oracle.update(state_0, experiment)

        self.assertEqual(state_1.history, (experiment,))
        self.assertLessEqual(state_1.survivor_count, state_0.survivor_count)
        self.assertTrue(np.all(state_1.survivors <= state_0.survivors))
        self.assertTrue(state_1.survivors[true_world_index])
        # update returned a new value; the old state was not mutated.
        self.assertEqual(state_0.survivor_count, len(self.worlds))

    def test_replay_and_repeated_experiment_invariants(self) -> None:
        environment = Environment(self.worlds[9], self.spec)
        experiment = self.experiment_from_environment(
            environment,
            Intervention((1, 0), (None, None)),
        )
        state_1 = self.oracle.update(self.oracle.initial_state(), experiment)
        state_2 = self.oracle.update(state_1, experiment)
        replayed = self.oracle.replay(state_2.history)

        np.testing.assert_array_equal(state_2.survivors, state_1.survivors)
        np.testing.assert_array_equal(replayed.survivors, state_2.survivors)

    def test_predict_is_a_probability_distribution(self) -> None:
        state = self.oracle.initial_state()
        query_id = self.catalog.action_id_for(
            Intervention((0, 0), (None, None))
        )

        distribution = self.oracle.predict(state, query_id)

        self.assertEqual(int(distribution.counts.sum()), state.survivor_count)
        self.assertAlmostEqual(float(distribution.probabilities.sum()), 1.0)
        self.assertTrue(np.all(distribution.probabilities >= 0.0))

    def test_impossible_but_well_formed_observation_is_rejected(self) -> None:
        # Intervening y=(0, 0) forces observation code 0 in every world.
        action_id = self.catalog.action_id_for(
            Intervention((0, 0), (0, 0))
        )
        impossible = Experiment(action_id=action_id, observation_code=1)

        with self.assertRaises(InconsistentObservationError):
            self.oracle.update(self.oracle.initial_state(), impossible)

    def test_action_outside_configured_stage_is_rejected(self) -> None:
        stage_a_oracle = ExactOracle(
            self.catalog,
            self.responses,
            stage=Stage.A,
        )
        stage_b_action = self.catalog.action_id_for(
            Intervention((0, 0), (1, None))
        )

        with self.assertRaisesRegex(ValueError, "requires Stage B"):
            stage_a_oracle.predict(
                stage_a_oracle.initial_state(),
                stage_b_action,
            )

    def test_response_columns_are_lazy_cached_values(self) -> None:
        action_id = self.catalog.action_id_for(
            Intervention((1, 1), (None, None))
        )
        self.assertEqual(self.responses.cached_action_ids, ())

        first = self.responses.outcomes_for_action(action_id)
        second = self.responses.outcomes_for_action(action_id)

        self.assertIs(first, second)
        self.assertEqual(self.responses.cached_action_ids, (action_id,))
        with self.assertRaises(ValueError):
            first[0] = 0


if __name__ == "__main__":
    unittest.main()
