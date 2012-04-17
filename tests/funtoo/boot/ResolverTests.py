# -*- coding: ascii -*-

import random
import unittest
from funtoo.boot import resolver

class BracketzapTests(unittest.TestCase):



	def test_emptystring(self):
		expected = ''
		actual = resolver.bracketzap('')
		self.assertEqual(expected, actual)

	def test_emptystringnonwild(self):
		expected = ''
		actual = resolver.bracketzap('', False)
		self.assertEqual(expected, actual)

	def test_oneopenbracket(self):
		expected = '['
		actual = resolver.bracketzap('[')
		self.assertEqual(expected, actual)

	def test_oneopenbracketnonwild(self):
		expected = '['
		actual = resolver.bracketzap('[', False)
		self.assertEqual(expected, actual)

	def test_oneclosebracket(self):
		expected = ']'
		actual = resolver.bracketzap(']')
		self.assertEqual(expected, actual)

	def test_oneclosebracketnonwild(self):
		expected = ']'
		actual = resolver.bracketzap(']', False)
		self.assertEqual(expected, actual)

	def test_emptymatchedbrackets(self):
		expected = ''
		actual = resolver.bracketzap('[]')
		self.assertEqual(expected, actual)

	def test_emptymatchedbracketsnonwild(self):
		expected = ''
		actual = resolver.bracketzap('[]', False)
		self.assertEqual(expected, actual)

	def test_emptyreversedbrackets(self):
		expected = ']['
		actual = resolver.bracketzap('][')
		self.assertEqual(expected, actual)

	def test_emptyreversedbracketsnonwild(self):
		expected = ']['
		actual = resolver.bracketzap('][', False)
		self.assertEqual(expected, actual)

	def test_vmatch(self):
		expected = '-*'
		actual = resolver.bracketzap('[-v]')
		self.assertEqual(expected, actual)

	def test_vmatchnonwild(self):
		expected = ''
		actual = resolver.bracketzap('[-v]', False)
		self.assertEqual(expected, actual)

	def test_fuzz(self):
		fuzzcount = 1000
		maxlength = 1000

		# For py2 compatibility
		if hasattr(__builtins__, "xrange"):
			myrange = xrange
		else:
			myrange = range

		for i in myrange(fuzzcount):
			argument = ''
			length = random.randint(0, maxlength)
			for i in myrange(length):
				character = random.randint(0, 255)
				argument = argument + chr(character)
			wildint = random.randint(0, 1)
			wild = (wildint == 0)
			resolver.bracketzap(argument, wild)
