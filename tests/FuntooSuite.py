# -*- coding: ascii -*-
import sys
import os
import unittest

class FuntooSuite(unittest.TestSuite):
	def __init__(self, root = 'funtoo'):
		unittest.TestSuite.__init__(self)
		for current, dirs, files in os.walk(root):
			print("Building suite for " + current)
			sys.path = [current] + sys.path
			for filename in files:
				root, ext = os.path.splitext(filename)
				if ".py" == ext:
					print(filename)
					testmodule = __import__(root)
					newsuite = unittest.defaultTestLoader.loadTestsFromModule(testmodule)
					self.addTest(newsuite)

if "__main__" == __name__:
	result = unittest.TextTestRunner().run(FuntooSuite())
	sys.exit(not result.wasSuccessful())
