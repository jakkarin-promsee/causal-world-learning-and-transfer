import tempfile
import unittest
from pathlib import Path

from core.operators import apply_operator
from core.storage import WorldDataset, save_world_dataset
from core.types import Op, WorldSpec
from core.worldgen import iter_worlds, node_rule_count, validate_world, world_count


class WorldGenerationTests(unittest.TestCase):
    def test_operator_contract(self) -> None:
        self.assertEqual(apply_operator(Op.AND, (1, 0)), 0)
        self.assertEqual(apply_operator(Op.OR, (1, 0)), 1)
        self.assertEqual(apply_operator(Op.NOT, (0,)), 1)
        with self.assertRaises(ValueError):
            apply_operator(Op.NOT, (0, 1))

    def test_rule_and_world_counts(self) -> None:
        self.assertEqual(node_rule_count(4), 16)
        self.assertEqual(world_count(WorldSpec(d=2, m=2)), 36)
        self.assertEqual(world_count(WorldSpec(d=4, m=4)), 705_600)

    def test_every_small_world_obeys_contract(self) -> None:
        spec = WorldSpec(d=2, m=2)
        worlds = list(iter_worlds(spec))
        self.assertEqual(len(worlds), 36)
        self.assertEqual(len(set(worlds)), 36)
        for world in worlds:
            validate_world(world, spec)

    def test_storage_round_trip(self) -> None:
        spec = WorldSpec(d=2, m=2)
        expected = list(iter_worlds(spec))

        for compressed in (False, True):
            with self.subTest(compressed=compressed), tempfile.TemporaryDirectory() as tmp:
                dataset_path = Path(tmp) / "worlds"
                manifest_path = save_world_dataset(
                    dataset_path,
                    spec,
                    shard_size=7,
                    compressed=compressed,
                )
                self.assertTrue(manifest_path.is_file())

                dataset = WorldDataset(dataset_path)
                self.assertEqual(dataset.spec, spec)
                self.assertEqual(len(dataset), 36)
                self.assertEqual(dataset.canonical_world_count, 36)
                self.assertEqual(list(dataset), expected)


if __name__ == "__main__":
    unittest.main()
