import unittest

from enlightenme.utils import camel_case


class TestCamelCase(unittest.TestCase):
    def test_typical(self):
        self.assertEqual("AbBc", camel_case("ab-bc"))
