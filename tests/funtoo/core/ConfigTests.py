# -*- coding: ascii; tab-width: 4; indent-tabs-mode: nil -*-
import random
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
    def test_noargs(self):
        cf = config.ConfigFile()
        self.assertEqual(False, cf.fileExists())
        expectedDump = []
        self.assertEqual(expectedDump, cf.dump())
        cf.write()

    def test_emptyfile(self):
        cf = config.ConfigFile('/dev/null', True)

    def test_nonexistantfile(self):
        cf = config.ConfigFile('idontexist')

    def test_lieaboutexistance(self):
        cf = config.ConfigFile('/dev/null', False)

    def test_deburr(self):
        cf = config.ConfigFile()
        self.assertEqual('', cf.deburr(''))
        self.assertEqual('', cf.deburr('', ''))
        self.assertEqual('', cf.deburr(' '))
        self.assertEqual('', cf.deburr('"', '"'))
        self.assertEqual('aa', cf.deburr('"aa"'))
        self.assertEqual('"', cf.deburr('"""'))

    def test_deburr_fuzz(self):
        cf = config.ConfigFile()
        fuzzcount = 1000
        maxlength = 1000
        for i in xrange(fuzzcount):
            argument1 = ''
            argument2 = ''
            length1 = random.randint(0, maxlength)
            length2 = random.randint(0, maxlength)
            for i in xrange(length1):
                character = random.randint(0, 255)
                argument1 = argument1 + chr(character)
            for i in xrange(length2):
                character = random.randint(0, 255)
                argument2 = argument2 + chr(character)
            wildint = random.randint(0, 1)
            wild = (wildint == 0)
            if (wild):
                cf.deburr(argument1)
            else:
                cf.deburr(argument1, argument2)

    def test_parent(self):
        cf = config.ConfigFile()
        parent = config.ConfigFile()
        cf.setParent(parent)

    def test_circular(self):
        cf = config.ConfigFile()
        cf.setParent(cf)

    def test_widecircle(self):
        cf = config.ConfigFile()
        parent = config.ConfigFile()
        cf.setParent(parent)
        parent.setParent(cf)

    def test_nonconfigparent(file):
        cf = config.ConfigFile()
        cf.setParent(None)
