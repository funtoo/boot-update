# -*- coding: ascii; tab-width: 4; indent-tabs-mode: nil -*-
import unittest
from funtoo.core import config

class ErrorTests(unittest.TestCase):
    def test_noarg(self):
        error = config.ConfigFileError()
        expected = "(no message)"
        self.assertEqual(expected, str(error))

    def test_onearg(self):
        error = config.ConfigFileError('test')
        expected = "test"
        self.assertEqual(expected, str(error))

    def test_twoargs(self):
        error = config.ConfigFileError('test1', 'test2')
        expected = "(no message)"
        self.assertEqual(expected, str(error))

class ConfigFileConstructionTests(unittest.TestCase):
    def test_empty(self):
        cf = config.ConfigFile()
        self.assertEqual(False, cf.fileExists())
        expectedDump = []
        self.assertEqual(expectedDump, cf.dump())
