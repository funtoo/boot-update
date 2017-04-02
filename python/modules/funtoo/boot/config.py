# -*- coding: ascii -*-

from funtoo.core import config

class DefaultBootConfigFile(config.ConfigFile):

	def inherit(self,section):
		if section not in self.builtins:
			return "default"
		return None

	def __init__(self,fn="/etc/boot.conf.defaults",existing=True):
		self.builtins = ["boot", "default", "color", "grub", "grub-legacy", "lilo"]
		config.ConfigFile.__init__(self,fn,existing)



class BootConfigFile(config.ConfigFile):

	def inherit(self,section):
		if section not in self.builtins:
			return "default"
		return None

	def __init__(self,fn="/etc/boot.conf",existing=True):
		# builtins is our list of all those sections that we recognize as having config values and
		# not boot entries.
		self.builtins = ["boot", "display", "default", "altboot", "color", "grub", "grub-legacy", "lilo"]
		config.ConfigFile.__init__(self,fn,existing)
		self.parent=DefaultBootConfigFile()

	def validate(self):
		invalid=[]
		validmap={
				"boot" : ["path", "generate", "timeout", "default", "bootdev","terminal"],
				"display" : ["gfxmode", "background", "font"],
				"color" : ["normal", "highlight", "nonmenu"],
				"default" : ["scan", "gfxmode", "kernel", "initrd", "params", "type", "xenkernel", "xenparams"],
				"grub" : ["dir", "file", "grub-mkdevicemap", "grub-probe", "font_src"],
				"grub-legacy" : ["dir", "file"],
				"lilo" : ["file", "bin", "gparams"],
				"serial" : [ "parity", "port", "speed", "stop", "unit", "word" ]
		}
		for section in self.sectionData.keys():
			if section not in validmap.keys():
				cmpto="default"
			else:
				cmpto=section
			for itemkey in self.sectionData[section].keys():
				if itemkey not in validmap[cmpto]:
					invalid.append("{sect}/{name}".format(sect = section, name = itemkey ))
		return invalid
