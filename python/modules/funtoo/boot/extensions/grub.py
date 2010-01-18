#!/usr/bin/python2

import os, sys, commands

from ..extension import Extension
from ..resolver import Resolver

r=None

def getExtension(config):
	global r
	r=Resolver(config)
	return GRUBExtension(config)

# Add exception definition here to be used by a Guppy failure. -- ExtensionError?
class GRUBExtension(Extension):

	def __init__(self,config):
		self.config = config
		self.helper = GRUBHelper()

	def isAvailable(self):
		if os.path.exists("/sbin/grub-probe") and os.path.exists("/sbin/grub-install"):
			return True
		return False

	def generateBootEntry(self,l,sect,kname,kext):
		global r
		l.append("")
		l.append("menuentry \"%s - %s\" {" % ( sect, kname ))
		for mod in self.helper.RequiredGRUBModules(self.helper.BootDeviceDev()):
			l.append(" insmod %s" % mod)
		l.append(" set root=%s" % self.helper.BootDeviceGRUB())
		l.append(" search --no-floppy --fs-uuid --set %s" % self.helper.BootDeviceUUID())
		
		kpath=r.RelativePathTo(kname,"/boot")
		params=self.config.item(sect,"params")
		
		if "root=auto" in params:
			params.remove("root=auto")
			params.append("root=%s" % r.GetRootFSDev())
		
		if "rootfstype=auto" in params:
			params.remove("rootfstype=auto")
			for item in params:
				if item[0:5] == "root=":
					params.append("rootfstype=%s" % r.GetDevFSType(item[5:]))
					break

		l.append(" linux %s %s" % ( kpath," ".join(params) ))
		initrds=r.FindInitrds(sect, kname, kext)
		for initrd in initrds:
			l.append(" initrd %s" % self.helper.RelativePathTo(initrd,"/boot"))
		if self.config.hasItem("%s/gfxmode" % sect):
			l.append(" set gfxpayload=%s" % self.config.item(sect,"gfxmode"))
		else:
			l.append(" set gfxpayload=keep")
		l.append("}")

	def generateConfigFile(self,output="/boot/grub/grub.cfg"):
		l=[]
		c=self.config
		global r
		l.append(c.condSubItem("boot/timeout", "set timeout=%s"))
		# pass our boot entry generator function to GenerateSections, and everything is taken care of for our boot entries
		r.GenerateSections(l,self.generateBootEntry)
		
		if c.hasItem("display/gfxmode"):
			l.append("")
			for mod in self.helper.RequiredGRUBModules(self.helper.BootDeviceDev()):
				l.append("insmod %s" % mod)
			l.append("set root=%s" % self.helper.BootDeviceGRUB())
			l.append("search --no-floppy --fs-uuid --set "+self.helper.BootDeviceUUID())
			if c.hasItem("display/font"):
				font = c["display/font"]
			else:
				font = "/boot/grub/unifont.pf2"
			l += [ "if loadfont %s; then" % r.RelativePathTo(font,"/boot"),
				" set gfxmode=%s" % c["display/gfxmode"],
				" insmod gfxterm"
				" insmod vbe"
				" terminal_output gfxterm" ]
			bg = c.item("display","background")
			if len(bg):
				if len(bg) == 1:
					bgimg = bg[0]
					bgext = bg[0].rsplit(".")[-1]
				elif len(bg) == 2:
					bgimg, bgext = bg
				if bgext == "jpg":
					bgext = "jpeg"
				if bgext in [ "jpeg", "png", "tga" ]:
					l += [ 
						" insmod %s" % bgext,
						" background_image %s" % r.RelativePathTo(bgimg,"/boot")
					]
				else:
					print "Warning: background image %s (format %s) not recognized - skipping." % (bgimg, bgext)
			l += [ "fi",
				"",
				c.condSubItem("color/normal", "set menu_color_normal=%s"),
				c.condSubItem("color/highlight", "set menu_color_highlight=%s"),
				""
			]
		
		return l
			
class GRUBHelper:

	"""
		This class provides an interface to the command-line GRUB utilities, as well as misc. functions used by the GRUB
		config file generator.
	"""

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

"""
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
"""
