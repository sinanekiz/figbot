import unittest

from software.vision.transforms import apply_transform, inverse_transform


class TransformTests(unittest.TestCase):
    def test_translation_and_round_trip(self):
        transform = (
            (1, 0, 0, 0.2),
            (0, 1, 0, -0.1),
            (0, 0, 1, 0.5),
            (0, 0, 0, 1),
        )
        point = (0.3, 0.2, 0.1)
        moved = apply_transform(transform, point)
        restored = apply_transform(inverse_transform(transform), moved)
        for expected, actual in zip(point, restored):
            self.assertAlmostEqual(expected, actual)

    def test_rejects_scaled_rotation(self):
        invalid = (
            (2, 0, 0, 0),
            (0, 1, 0, 0),
            (0, 0, 1, 0),
            (0, 0, 0, 1),
        )
        with self.assertRaises(ValueError):
            apply_transform(invalid, (0, 0, 0))


if __name__ == "__main__":
    unittest.main()

