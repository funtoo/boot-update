# -*- coding: ascii -*-

import sys
import random
import unittest

try:
	import StringIO
except ImportError:
	import io as StringIO

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

		# For py2 compatibility
		if hasattr(__builtins__, "xrange"):
			myrange = xrange
		else:
			myrange = range

		for i in myrange(fuzzcount):
			argument1 = ''
			argument2 = ''
			length1 = random.randint(0, maxlength)
			length2 = random.randint(0, maxlength)
			for i in myrange(length1):
				character = random.randint(0, 255)
				argument1 = argument1 + chr(character)
			for i in myrange(length2):
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

	def test_template(self):
		cf = config.ConfigFile()
		cf.template('foo')

	def test_inherit(self):
		cf = config.ConfigFile()
		self.assertEqual(None, cf.inherit('foo'))

	def test_setter_getter(self):
		cf = config.ConfigFile()
		cf['foo'] = 'foo'
		self.assertEqual('foo', cf['foo'])

	def test_local_item(self):
		cf = config.ConfigFile()
		cf['foo'] = 'foo'
		self.assertEqual(True, cf.hasLocalItem('foo'))
		self.assertEqual(False, cf.hasLocalItem('bar'))

	def test_subitem(self):
		cf = config.ConfigFile()
		cf['foo/bar'] = 'foobar'
		self.assertEqual('blah foobar blah', cf.subItem('foo/bar', 'blah %s blah'))
		self.assertEqual('', cf.subItem('notthere', 'blah %s blah', True))

	def test_sections(self):
		cf = config.ConfigFile()
		self.assertEqual([], cf.getSections())

	def test_condsubitem(self):
		cf = config.ConfigFile()
		cf['foo'] = 'foo'
		self.assertEqual('foo', cf.condSubItem('foo', '%s'))

	def test_printdump(self):
		cf = config.ConfigFile()
		oldstdout = sys.stdout
		sys.stdout = StringIO.StringIO()
		cf.printDump()
		output = sys.stdout.getvalue()
		sys.stdout.close()
		self.assertEqual('', output)
		sys.stdout = StringIO.StringIO()
		cf['foo'] = 'foo'
		cf['foo/bar'] = 'foobar1'
		cf['foo\\bar'] = 'foobar2'
		cf.printDump()
		output = sys.stdout.getvalue()
		sys.stdout.close()
		sys.stdout = oldstdout
		self.assertEqual('section  {\n}\n\nsection foo {\n}\n', output)

	def test_read(self):
		cf = config.ConfigFile()
		cf.readFromLines('section  {\n}\n\nsection foo {\n}\n')
