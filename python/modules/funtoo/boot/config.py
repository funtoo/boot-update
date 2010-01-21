from ..core import config

class BootConfigFile(config.ConfigFile):

	def inherit(self,cat):
		if cat not in self.builtins:
			return "default"
		return None

	def __init__(self,fn="/etc/boot.conf",existing=True):
		# builtins is our list of all those sections that we recognize as having config values and
		# not boot entries.
		self.builtins = [ "boot", "display", "default", "altboot", "color" ]
		config.ConfigFile.__init__(self,fn,existing)

	def validate(self):
		invalid=[]
		validmap={ 
				"boot" : [ "generate", "timeout", "default" ],
				"display" : [ "gfxmode", "background" ],
				"color" : [ "normal", "highlight" ],
				"default" : [ "scan", "kernel", "initrd", "params" ]
		}
		for cat  in self.obj.keys():
			if cat not in validmap.keys():
				cmpto="default"
			else:
				cmpto=cat
			for itemkey in self.obj[cat].keys():
				if itemkey not in validmap[cmpto]:
					invalid.append("%s/%s" % ( cat, itemkey ))
		return invalid			
