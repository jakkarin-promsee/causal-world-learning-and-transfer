"""Small independent examples for the Exp 02 partition and denominators."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import numpy as np

FOLDER = Path(__file__).resolve().parents[1] / "experiment" / "phase-1" / "track-1" / "exp-02"


def load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, FOLDER / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runner = load_script("run")
summarizer = load_script("summarize_raw")


class Exp02EquivalenceTests(unittest.TestCase):
    def test_refinement_uses_complete_response_prefix(self) -> None:
        labels = np.zeros(5, dtype=np.int32)
        labels = runner.refine(labels, np.array([0, 0, 1, 1, 1], dtype=np.uint8), 2)
        labels = runner.refine(labels, np.array([0, 1, 0, 0, 0], dtype=np.uint8), 2)
        self.assertEqual(labels.tolist(), [0, 1, 2, 2, 2])

    def test_world_weighted_denominators_include_singletons_only_in_all_worlds(self) -> None:
        # Classes of sizes 1, 2, 3: equivalent worlds = 5.
        labels = np.array([0, 1, 1, 2, 2, 2], dtype=np.int32)
        result = summarizer.summarize_stage(labels, np.array([1, 2, 3], dtype=np.int32), 6)
        self.assertEqual(result["equivalent_world_count"], 5)
        self.assertAlmostEqual(result["avg_class_amount_world_weighted_equivalent_only"], 13 / 5)
        self.assertAlmostEqual(result["avg_class_amount_world_weighted_all_worlds"], 14 / 6)

    def test_refinement_rejects_merges(self) -> None:
        parent = np.array([0, 0, 1, 1], dtype=np.int32)
        child = np.array([0, 1, 1, 2], dtype=np.int32)
        with self.assertRaises(ValueError):
            summarizer.validate_refinement(parent, child, 3)


if __name__ == "__main__":
    unittest.main()
