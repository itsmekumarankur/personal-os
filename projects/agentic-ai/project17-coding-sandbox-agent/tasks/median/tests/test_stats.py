import unittest

from stats import median


class MedianTests(unittest.TestCase):
    def test_odd(self):
        self.assertEqual(median([3, 1, 2]), 2)

    def test_even(self):
        self.assertEqual(median([4, 1, 3, 2]), 2.5)

    def test_empty(self):
        with self.assertRaises(ValueError):
            median([])

    def test_does_not_mutate(self):
        xs = [3, 1, 2]
        median(xs)
        self.assertEqual(xs, [3, 1, 2])
