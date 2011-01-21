# -*- coding: ascii -*-
import os
from resolver import Resolver

class Extension:
	def __init__(self):
		# initialization should always succeed.
		self.r = Resolver(config)

	def APIVersion(self):
		# return API version, a monotonically increasing integer
		return 1

	def isAvailable(self):
		# check to ensure boot loader is available for use and all required local dependencies are satisfied.
		# True = OK, Fals = not OK
		return [True,[]]

	def generateConfigFile(self):
		# generate new config file based on config data. returns a list of all lines of the config file, without trailing newlines
		return [True, [] ,[]]

	def writeConfigFile(self,lines):

		# create a new config file on disk - rather than call generateConfigFile() ourselves, we are passed the
		# lines we want to print. This allows us to only generate them once, allowing validateConfigFile() to
		# take a look at them first to print any warnings, etc.

		out=open(self.fn,"w")
		for line in lines:
			out.write(line+"\n")
		out.close()
		return [ True, []]

	def mesg(self,type,line):
		# this used for all informational messages, and can be overridden (as we do in boot-update to unify the output)
		print "*",type,line

	def backupConfigFile(self):
		
		# create backup as necessary

		oldfn = self.fn+".old"
		if os.path.exists(self.fn):
			if os.path.exists(oldfn):
				os.unlink(oldfn)
			os.rename(self.fn,oldfn)
		return [ True, []]


	def validateConfigFile(self,lines):
	
		# This method should be overridden - it looks at the config file specified in the "lines" list, and
		# prints any warnings or throws any errors as required. 
		
		# Return values:
		#       [ True, [list of warnings] ] - OK
		#       [ False, [list of warnings, errors] - Not OK, should abort.

		return [ True, []]

	def updateBootLoader(self):
		# for LILO, re-run it to update the boot loader map. For grub, probably do nothing.
		return [ True, []]


	def regenerate(self):
		# This performs the main loop that calls all our sub-steps - you should not need to override this method. If you do, an API upgrade is probably in order.
	
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
		
		allmsgs.append(["info","Configuration file %s generated - %s lines." % ( self.fn, len(l))])

		# TRY VALIDATING CONFIG FILE    

		self.mesg("info","Validating config file %s" % self.fn)

		ok, msgs = self.validateConfigFile(l)
		allmsgs += msgs
		if not ok:
			return [ "validation", ok, allmsgs ] 

		# TRY BACKING UP CONFIG FILE
	
		self.mesg("info","Backing up original config file to %s.old" % self.fn)

		ok, msgs = self.backupConfigFile()
		allmsgs += msgs
		if not ok:
			return [ "config file backup", ok, allmsgs ]

		# TRY WRITING CONFIG FILE
	
		self.mesg("info","Writing new config file to %s" % self.fn)

		ok, msgs = self.writeConfigFile(l)
		allmsgs += msgs
		if not ok:
			return [ "config file write", ok, allmsgs ]

		# TRY UPDATING BOOT LOADER
	
		ok, msgs = self.updateBootLoader()
		allmsgs += msgs
		if not ok:
			return [ "boot loader update", ok, allmsgs ]

		self.mesg("info","Done.")

		return [ "complete", True, allmsgs ]
