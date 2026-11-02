import tempfile
import unittest
from pathlib import Path

import numpy as np

from core.evaluator import Environment
from core.oracle import ActionCatalog, ExactOracle, OnDemandResponseStore, Stage
from core.types import WorldSpec
from core.worldgen import iter_worlds
from reuse.jsonl_reference.runner import (
    EpisodeConfig as OriginalEpisodeConfig,
    run_full_candidate_greedy_episode as run_original_greedy,
)
from reuse.numeric_engine.responses import NumericResponseStore
from reuse.numeric_engine.worlds import NumericWorldDataset, save_numeric_worlds
from reuse.numeric_engine.runner import EpisodeConfig, run_full_candidate_greedy_episode


class NumericWorldTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.spec = WorldSpec(d=2, m=2)
        save_numeric_worlds(self.root / "worlds", self.spec)
        self.dataset = NumericWorldDataset(self.root / "worlds", verify_hash=True)
        self.worlds = tuple(iter_worlds(self.spec))
        self.catalog = ActionCatalog(self.spec)

    def test_world_order_and_values_match_original(self) -> None:
        self.assertEqual(len(self.dataset), len(self.worlds))
        self.assertEqual(self.dataset.rules.dtype, np.uint8)
        for index, world in enumerate(self.worlds):
            self.assertEqual(self.dataset.world_at(index), world)

    def test_world_dataset_rejects_modified_npy(self) -> None:
        path = self.root / "worlds" / "worlds.npy"
        altered = np.load(path, allow_pickle=False)
        altered[0, 0, 0] = (int(altered[0, 0, 0]) + 1) % 3
        np.save(path, altered, allow_pickle=False)

        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            NumericWorldDataset(self.root / "worlds")

    def test_every_stage_c_response_matches_original_and_persists(self) -> None:
        reference = OnDemandResponseStore(self.worlds, len(self.worlds), self.catalog)
        cache_dir = self.root / "responses"
        numeric = NumericResponseStore(
            self.dataset, self.catalog, cache_dir=cache_dir, chunk_size=7
        )

        for entry in self.catalog.entries_for_stage(Stage.C):
            with self.subTest(action_id=entry.action_id):
                np.testing.assert_array_equal(
                    numeric.outcomes_for_action(entry.action_id),
                    reference.outcomes_for_action(entry.action_id),
                )

        reopened = NumericResponseStore(
            self.dataset, self.catalog, cache_dir=cache_dir, chunk_size=7
        )
        loaded = reopened.outcomes_for_action(0)
        np.testing.assert_array_equal(loaded, reference.outcomes_for_action(0))
        self.assertFalse(loaded.flags.writeable)
        self.assertEqual(reopened.cached_action_ids, (0,))

    def test_response_cache_rejects_valid_shaped_modified_column(self) -> None:
        cache_dir = self.root / "responses"
        numeric = NumericResponseStore(self.dataset, self.catalog, cache_dir=cache_dir)
        original = numeric.outcomes_for_action(0)
        altered = original.copy()
        altered[0] = (int(altered[0]) + 1) % (1 << self.spec.m)
        np.save(cache_dir / "action-00000.npy", altered, allow_pickle=False)

        reopened = NumericResponseStore(self.dataset, self.catalog, cache_dir=cache_dir)
        with self.assertRaisesRegex(ValueError, "checksum mismatch"):
            reopened.outcomes_for_action(0)

    def test_response_cache_rejects_incomplete_column_pair(self) -> None:
        cache_dir = self.root / "responses"
        numeric = NumericResponseStore(self.dataset, self.catalog, cache_dir=cache_dir)
        numeric.outcomes_for_action(0)
        (cache_dir / "action-00000.sha256").unlink()

        reopened = NumericResponseStore(self.dataset, self.catalog, cache_dir=cache_dir)
        with self.assertRaisesRegex(ValueError, "checksum is missing"):
            reopened.outcomes_for_action(0)

    def test_oracle_and_full_greedy_trajectory_match_original(self) -> None:
        numeric_store = NumericResponseStore(self.dataset, self.catalog)
        reference_store = OnDemandResponseStore(
            self.worlds, len(self.worlds), self.catalog
        )
        numeric_oracle = ExactOracle(self.catalog, numeric_store, stage=Stage.C)
        reference_oracle = ExactOracle(self.catalog, reference_store, stage=Stage.C)
        config = EpisodeConfig(
            stage=Stage.C,
            budget=len(self.catalog.entries_for_stage(Stage.C)),
            seed=19,
        )
        numeric_result = run_full_candidate_greedy_episode(
            world_index=3,
            environment=Environment(self.dataset.world_at(3), self.spec),
            oracle=numeric_oracle,
            config=config,
        )
        reference_result = run_original_greedy(
            world_index=3,
            environment=Environment(self.worlds[3], self.spec),
            oracle=reference_oracle,
            config=OriginalEpisodeConfig(
                stage=config.stage, budget=config.budget, seed=config.seed
            ),
        )
        self.assertEqual(numeric_result.termination_reason, reference_result.termination_reason)
        self.assertEqual(numeric_result.final_survivor_count, reference_result.final_survivor_count)
        self.assertEqual(
            numeric_result.uncertainty_trajectory_bits,
            reference_result.uncertainty_trajectory_bits,
        )
        self.assertEqual(
            [vars(step) for step in numeric_result.episode.steps],
            [vars(step) for step in reference_result.episode.steps],
        )

    def test_response_cache_rejects_other_world_dataset(self) -> None:
        cache_dir = self.root / "responses"
        NumericResponseStore(self.dataset, self.catalog, cache_dir=cache_dir)
        manifest_path = self.root / "worlds" / "manifest.json"
        manifest = manifest_path.read_text(encoding="utf-8")
        manifest_path.write_text(
            manifest.replace(self.dataset.worlds_sha256, "0" * 64),
            encoding="utf-8",
        )
        altered = NumericWorldDataset(self.root / "worlds", verify_hash=False)
        with self.assertRaisesRegex(ValueError, "does not match"):
            NumericResponseStore(altered, self.catalog, cache_dir=cache_dir)


if __name__ == "__main__":
    unittest.main()
