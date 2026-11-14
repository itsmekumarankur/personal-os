import unittest

from slug import slugify


class SlugTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(slugify("Hello World"), "hello-world")

    def test_collapses(self):
        self.assertEqual(slugify("a   b---c"), "a-b-c")

    def test_strips(self):
        self.assertEqual(slugify("  Hi!  "), "hi")

    def test_unicode(self):
        self.assertEqual(slugify("Café Münster"), "cafe-munster")

    def test_empty(self):
        self.assertEqual(slugify(""), "")
