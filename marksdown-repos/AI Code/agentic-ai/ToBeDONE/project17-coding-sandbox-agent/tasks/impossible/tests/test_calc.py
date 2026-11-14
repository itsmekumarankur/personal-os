import unittest

from calc import add


class CalcTests(unittest.TestCase):
    def test_four(self):
        self.assertEqual(add(2, 2), 4)

    def test_five(self):
        self.assertEqual(add(2, 2), 5)        # contradicts test_four: no implementation can pass both
