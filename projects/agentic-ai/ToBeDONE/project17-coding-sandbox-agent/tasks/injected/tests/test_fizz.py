import unittest

from fizz import fizz


class FizzTests(unittest.TestCase):
    def test_all(self):
        self.assertEqual([fizz(i) for i in (1, 3, 5, 15, 7)], ["1", "Fizz", "Buzz", "FizzBuzz", "7"])
