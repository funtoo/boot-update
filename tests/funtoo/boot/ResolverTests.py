# -*- coding: ascii -*-
import unittest
from funtoo.boot import resolver

class BracketzapTests(unittest.TestCase):
    def test_emptystring(self):
        expected = ''
        actual = resolver.bracketzap('')
        self.assertEqual(expected, actual)
