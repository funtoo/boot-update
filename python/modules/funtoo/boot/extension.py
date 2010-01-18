class Extension:
	def __init__(self):
		# initialization should always succeed.
		pass
	
	def APIVersion(self):
		# return API version, a monotonically increasing integer
		return 1

	def isAvailable(self):
		# check to ensure boot loader is available for use
		pass

	def generateConfigFile(self):
		# generate new config file based on config data.
		pass

	def validateConfigFile(self):
		# validate config file, return menu list, other info such as
		# default boot entry, timeout, and any identified errors (need
		# struct for this)
		pass

	def updateBootLoader(self):
		# for LILO, re-run it to update the boot loader map. For
		# grub, probably do nothing.
		pass
