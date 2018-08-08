# -*- coding: ascii -*-

import os

from funtoo.boot.resolver import Resolver

class ExtensionError(Exception):
	def __init__(self, *args):
		self.args = args
	def __str__(self):
		if len(self.args) == 1:
			return str(self.args[0])
		else:
			return "(no message)"

class Extension:
	def __init__(self,config):
		# initialization should always succeed.
		self.config = config
		self.r = Resolver(config)

	def APIVersion(self):
		""" Returns API version, a monotonically increasing integer. """
		return 1

	def isAvailable(self):
		""" Checks to ensure boot loader is available for use and all required local dependencies are satisfied. True = OK, False = not OK """
		return [True,[]]

	def generateConfigFile(self):
		""" Generate new config file based on config data. Returns a list of all lines of the config file, without trailing newlines. """
		return [True, [] ,[]]

	def writeConfigFile(self,lines):
		"""
		Create a new config file on disk - rather than call generateConfigFile() ourselves, we are passed the
		lines we want to print. This allows us to only generate them once, allowing validateConfigFile() to
		take a look at them first to print any warnings, etc.
		"""
		out=open(self.fn,"w")
		for line in lines:
			out.write(line+"\n")
		out.close()
		return [ True, []]

	def mesg(self,type,line):
		""" This used for all informational messages, and can be overridden (as we do in boot-update to unify the output)"""
		print("*",type,line)

	def backupConfigFile(self):
		""" Create backup as necessary """
		oldfn = self.fn+".old"
		if os.path.exists(self.fn):
			if os.path.exists(oldfn):
				os.unlink(oldfn)
			os.rename(self.fn,oldfn)
		return [ True, []]


	def validateConfigFile(self,lines):
		"""
		This method should be overridden - it looks at the config file specified in the "lines" list, and
		prints any warnings or throws any errors as required.

		Return values:
			[ True, [list of warnings] ] - OK
			[ False, [list of warnings, errors] - Not OK, should abort.
		"""
		return [ True, []]

	def updateBootLoader(self):
		""" This method should be overridden. For LILO, run it to update the boot loader map. For grub, probably do nothing. """
		return [ True, []]

	def regenerate(self):
		""" This method performs the main loop that calls all our sub-steps - you should not need to override this method. If you do, an API upgrade is probably in order. """

		allmsgs = []

		# CHECK DEPENDENCIES

		ok, msgs = self.isAvailable()
		allmsgs += msgs
		if not ok:
			return [ "dependency check", ok, allmsgs ]

		# TRY GENERATING CONFIG FILE - in memory, not yet written to disk

		ok, msgs, l = self.generateConfigFile()
		allmsgs += msgs
		if not ok:
			return [ "config generation", ok, allmsgs ]

		allmsgs.append(["info","Configuration file {name} generated - {num} lines.".format(name = self.fn, num = len(l))])

		# TRY VALIDATING CONFIG FILE

		self.mesg("debug","Validating config file {name}".format(name = self.fn))

		ok, msgs = self.validateConfigFile(l)
		allmsgs += msgs
		if not ok:
			return [ "validation", ok, allmsgs ]

		# TRY BACKING UP CONFIG FILE

		self.mesg("debug","Backing up original config file to {name}.old".format(name = self.fn))

		ok, msgs = self.backupConfigFile()
		allmsgs += msgs
		if not ok:
			return [ "config file backup", ok, allmsgs ]

		# TRY WRITING CONFIG FILE

		self.mesg("debug","Writing new config file to {name}".format(name = self.fn))

		ok, msgs = self.writeConfigFile(l)
		allmsgs += msgs
		if not ok:
			return [ "config file write", ok, allmsgs ]

		# TRY UPDATING BOOT LOADER

		ok, msgs = self.updateBootLoader()
		allmsgs += msgs
		if not ok:
			return [ "boot loader update", ok, allmsgs ]

		return [ "complete", True, allmsgs ]

# vim: ts=4 sw=4 noet
