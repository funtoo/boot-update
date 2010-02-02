#!/usr/bin/python2

import os, sys, commands

from ..extension import Extension
from ..resolver import Resolver
from ..helper import *

r=None

def getExtension(config):
	global r
	r=Resolver(config)
	return GRUBExtension(config)

# Add exception definition here to be used by a Guppy failure. -- ExtensionError?
class GRUBExtension(Extension):

	def __init__(self,config):
		self.fn = "/boot/grub/grub.cfg"
		self.config = config
		self.command = GRUBCommand()
		self.bootitems = []

	def isAvailable(self):
		msgs=[]
		ok=True
		if not os.path.exists("/sbin/grub-probe"):
			msgs.append(["fatal","/sbin/grub-probe, required for boot/generate = grub,  does not exist"])
			ok=False
		return [ok, msgs]

	def generateBootEntry(self,l,sect,kname,kext):
		global r

		ok=True
		allmsgs=[]

		l.append("")
		self.bootitems.append("%s - %s" % (sect, kname))
		l.append("menuentry \"%s - %s\" {" % ( sect, kname ))
		for mod in self.command.RequiredGRUBModules(self.command.BootDeviceDev()):
			l.append("	insmod %s" % mod)
		l.append("	set root=%s" % self.command.BootDeviceGRUB())
		l.append("	search --no-floppy --fs-uuid --set %s" % self.command.BootDeviceUUID())
		
		kpath=r.RelativePathTo(kname,"/boot")
		params=self.config.item(sect,"params").split()
		
		if "root=auto" in params:
			params.remove("root=auto")
			rootdev = fstabGetRootDevice()
			if rootdev[0:5] != "/dev/":
				ok = False
				allmsgs.append(["fatal","(root=auto) grub - cannot find a valid / entry in /etc/fstab."])
				return [ ok, allmsgs ]	
			params.append("root=%s" % rootdev)
		
		if "rootfstype=auto" in params:
			params.remove("rootfstype=auto")
			for item in params:
				if item[0:5] == "root=":
					myroot=item[5:]
					fstype = fstabGetFilesystemOfDevice(myroot)
					if fstype == "":
						ok = False
						allmsgs.append(["fatal","(rootfstype=auto) grub - cannot find a valid / entry in /etc/fstab."])
						return [ ok, allmsgs ]
					params.append("rootfstype=%s" % fstype)
					break

		l.append("	linux %s %s" % ( kpath," ".join(params) ))
		initrds=r.FindInitrds(sect, kname, kext)
		for initrd in initrds:
			l.append("	initrd %s" % self.command.RelativePathTo(initrd,"/boot"))
		if self.config.hasItem("%s/gfxmode" % sect):
			l.append("	set gfxpayload=%s" % self.config.item(sect,"gfxmode"))
		else:
			l.append("	set gfxpayload=keep")
		l.append("}")

		return [ ok, allmsgs ]

	def generateConfigFile(self):
		l=[]
		c=self.config
		ok=True
		allmsgs=[]
		global r
		l.append(c.condSubItem("boot/timeout", "set timeout=%s"))
		# pass our boot entry generator function to GenerateSections, and everything is taken care of for our boot entries

		if c.hasItem("display/gfxmode"):
			l.append("")
			for mod in self.command.RequiredGRUBModules(self.command.BootDeviceDev()):
				l.append("insmod %s" % mod)
			l.append("set root=%s" % self.command.BootDeviceGRUB())
			l.append("search --no-floppy --fs-uuid --set "+self.command.BootDeviceUUID())
			font = None
			if c.hasItem("display/font"):
				font = c["display/font"]
				if not os.path.exists(font):
					allmsgs.append(["warn","specified font \"%s\" does not exist, using default." % font] )
					font = None
			if font == None:
				font = "/boot/grub/unifont.pf2"
			l += [ "if loadfont %s; then" % r.RelativePathTo(font,"/boot"),
				"	set gfxmode=%s" % c["display/gfxmode"],
				"	insmod gfxterm",
				"	insmod vbe",
				"	terminal_output gfxterm" ]
			bg = c.item("display","background").split()
			if len(bg):
				if len(bg) == 1:
					bgimg = bg[0]
					bgext = bg[0].rsplit(".")[-1].lower()
				elif len(bg) == 2:
					bgimg, bgext = bg
				if bgext == "jpg":
					bgext = "jpeg"
				if bgext in [ "jpeg", "png", "tga" ]:
					if os.path.exists(bgimg):
						l += [ 
							" insmod %s" % bgext,
							" background_image %s" % r.RelativePathTo(bgimg,"/boot")
						]
					else:
						allmsgs.append(["warn","background image \"%s\" does not exist - skipping." % bgimg])
				else:
					allmsgs.append(["warn","background image \"%s\" (format \"%s\") not recognized - skipping." % (bgimg, bgext)])
			l += [ "fi",
				"",
				c.condSubItem("color/normal", "set menu_color_normal=%s"),
				c.condSubItem("color/highlight", "set menu_color_highlight=%s"),
			]


		ok, msgs, defpos, defname = r.GenerateSections(l,self.generateBootEntry)
		allmsgs += msgs
		if not ok:
			return [ ok, allmsgs, l ]
		
		if defpos != None:
			l += [ 
				""
				"set default=%s" % defpos
			]
	
		allmsgs.append(["info","Configuration file %s generated - %s lines." % ( self.fn, len(l))])
		allmsgs.append(["info","Kernel \"%s\" will be booted by default." % defname])

		return [ok, allmsgs, l]
			
class GRUBCommand:

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

