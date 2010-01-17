#!/usr/bin/python

from ..base/extension import extension

import os, sys

def getExtension(config):
	return GRUBExtension(config)

# Add exception definition here to be used by a Guppy failure. -- ExtensionError?

class GRUBHelper:
	def __init__(self):
		self.info={}

	def Guppy(self,argstring):
		out=commands.getstatusoutput("/sbin/grub-probe "+argstring)
		if out[0] != 0:
			print "error: guppy fail! fail bad!"
			print "grub-probe "+argstring
			sys.exit(1)
		else:
			return out[1]

	def RequiredGRUBModules(self,dev):
		mods=[]
		for targ in [ "abstraction", "fs" ]:
			for mod in self.Guppy(" --device "+dev+" --target="+targ).split():
				mods.append(mod)
		return mods

	def BootDeviceDev(self):
		if not self.info.has_key("bootdevice/dev"):
			self.info["bootdevice/dev"]=self.Guppy(" --target=device /boot")
		return self.info["bootdevice/dev"]

	def BootDeviceUUID(self):
		if not self.info.has_key("bootdevice/UUID"):	
			self.info["bootdevice/UUID"]=self.Guppy(" --device "+self.BootDeviceDev()+" --target=fs_uuid 2> /dev/null")
		return self.info["bootdevice/UUID"]

	def BootDeviceGRUB(self):
		if not self.info.has_key("bootdevice/GRUB"):	
			self.info["bootdevice/GRUB"]=self.Guppy(" --device "+self.BootDeviceDev()+" --target=drive")
		return self.info["bootdevice/GRUB"]

class GRUBExtension(extension):

	def init(self,config):
		self.config = config
		self.helper = GRUBHelper()
		if self.isAvailable():
			self.config.addSection("grub",self.helper.exportInfo)

	def isAvailable(self):
		if os.path.exists("/sbin/grub-probe") and os.path.exists("/sbin/grub-install"):
			return True
		return False
			

def init(foo):
	global config, grub, resolver
	config=foo
	grub=GRUB(config)

get_default_boot() {
	local def="`cat $boot/grub/grub.cfg | grep "^set default=" | cut -f2 -d=`"
	if [ "$def" = "" ]
	then
		echo "-1"
	else
		echo $def
	fi
}

list_menuentries() {
	local defboot=`get_default_boot`
	local count=0
	local line
	while read line
	do

		line=$( echo "$line" | sed -e 's/menuentry "\(.*\)"$/\1/' )
		if [ "$defboot" -eq "$count" ]
		then
			mesg ${CYANN}$line ${CYAN}[DEFAULT]${OFF}
		else
			mesg $line
		fi
		count=$(( $count + 1 ))
	done
	if [ $count -eq 0 ] 
	then
		warn "No kernels found -- system not ready to boot."
		qprint "            Please specify a valid ${CYANN}GRUB_SEARCH${OFF} value in ${CYANN}/etc/default/grub${OFF}"
		qprint "            and ensure that you have a valid kernel in ${CYANN}${boot}${OFF}."
	fi
}

	def GetDevFSType(self,dev):
		fn=open("/etc/fstab","r")
		for line in fn.readlines():
			split=line.split()
			if (len(split) != 6):
				continue
			if split[0] == dev:
				return split[2]
		return ""

	def GetRootFSDev(self):
		fn=open("/etc/fstab","r")
		for line in fn.readlines():
			split=line.split()
			if (len(split) != 6):
				continue
			if split[1] == "/":
				return split[0]
		return ""

