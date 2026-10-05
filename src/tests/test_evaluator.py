import unittest

from core.evaluator import evaluate
from core.types import Intervention, NodeRule, Op, World, WorldSpec


class WorldOracleTest(unittest.TestCase):
    spec = WorldSpec(d=2, m=4)

    def generate_sample_world(self) -> World:
        # x0, x1
        # y0 = and(x0, x1)
        # y1 = or(x0, x1)
        # y2 = not(y0)
        # y3 = not(y1)

        return World(
            (
                NodeRule(Op.AND, (0, 1)),
                NodeRule(Op.OR, (0, 1)),
                NodeRule(Op.NOT, (2, )),
                NodeRule(Op.NOT, (3, ))
            )
        )

    # case 1 -> do(X)
    def test_evaluate_c1(self) -> None:
        w = self.generate_sample_world()

        no_y = (None, None, None, None)
        self.assertEqual(
            evaluate(w, Intervention((0, 0), no_y), self.spec),
            (0, 0, 1, 1),
        )
        self.assertEqual(
            evaluate(w, Intervention((0, 1), no_y), self.spec),
            (0, 1, 1, 0),
        )
        self.assertEqual(
            evaluate(w, Intervention((1, 1), no_y), self.spec),
            (1, 1, 0, 0),
        )

    # case 2 -> do(X, one Y)
    def test_evaluate_c2(self) -> None:
        w = self.generate_sample_world()

        cases = (
            ((0, 0), (1, None, None, None), (1, 0, 0, 1)),
            ((0, 0), (None, 1, None, None), (0, 1, 1, 0)),
            ((0, 0), (None, None, 0, None), (0, 0, 0, 1)),
            ((0, 0), (None, None, None, 0), (0, 0, 1, 0)),
            ((0, 1), (1, None, None, None), (1, 1, 0, 0)),
        )
        for x, y, expected in cases:
            with self.subTest(x=x, y=y):
                self.assertEqual(
                    evaluate(w, Intervention(x, y), self.spec),
                    expected,
                )

    
    # case 3 -> do(X, arbitrary Y)
    def test_evaluate_c3(self) -> None:
        w = self.generate_sample_world()

        cases = (
            ((1, None, 1, None), (1, 0, 1, 1)),
            ((None, 1, 0, None), (0, 1, 0, 0)),
            ((1, None, 0, 0), (1, 0, 0, 0)),
            ((1, 1, 1, 1), (1, 1, 1, 1)),
            ((0, 0, 0, 0), (0, 0, 0, 0)),
        )
        for y, expected in cases:
            with self.subTest(y=y):
                self.assertEqual(
                    evaluate(w, Intervention((0, 0), y), self.spec),
                    expected,
                )

    def test_rejects_action_with_wrong_shape(self) -> None:
        w = self.generate_sample_world()

        with self.assertRaisesRegex(ValueError, "X values"):
            evaluate(w, Intervention((0,), (None, None, None, None)), self.spec)
        with self.assertRaisesRegex(ValueError, "Y interventions"):
            evaluate(w, Intervention((0, 0), (None, None, None)), self.spec)

    def test_rejects_non_boolean_intervention_values(self) -> None:
        with self.assertRaisesRegex(ValueError, "X values must be 0 or 1"):
            Intervention((0, 2), (None, None, None, None))
        with self.assertRaisesRegex(ValueError, "Y interventions must be"):
            Intervention((0, 1), (None, -1, None, None))

if __name__ == "__main__":
    unittest.main()
