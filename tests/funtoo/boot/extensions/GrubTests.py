# -*- coding: ascii; tab-width: 4; indent-tabs-mode: nil -*-
import unittest
from funtoo.boot.extensions import grub
from funtoo.boot import config

class GrubTests(unittest.TestCase):
	def test_missing_defname(self):
		ext = grub.GRUBExtension(config.DefaultBootConfigFile(), True)
		ext.defname
		ext.defpos
