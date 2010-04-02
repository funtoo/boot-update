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
		self.config = config
		self.fn = "%s/grub/grub.cfg" % self.config["boot/path"]
		self.bootitems = []
		self.GuppyMap()

	def isAvailable(self):
		msgs=[]
		ok=True
		if not os.path.exists("/sbin/grub-probe"):
			msgs.append(["fatal","/sbin/grub-probe, required for boot/generate = grub,  does not exist"])
			ok=False
		return [ok, msgs]
	
	def generateOtherBootEntry(self,l,sect):
		global r
		ok=True
		msgs=[]
		mytype = self.config["%s/type" % sect ].lower()
		if mytype in [ "dos", "msdos", ]:
			mytype = "dos"
		elif mytype in [ "windows", "windows 2000", "win2000", "windows xp", "winxp" ]:
			mytype = "winxp"
		elif mytype in [ "windows vista", "vista" ]:
			mytype = "vista"
		elif mytype in [ "windows 7", "win7" ]:
			mytype = "win7"
		else:
			ok = False
			msgs.append(["fatal","Unrecognized boot entry type \"%s\"" % mytype])
			return [ ok, msgs ]
		params=self.config["%s/params" % sect].split()
		myroot = r.GetParam(params,"root=")
		myname = sect
		# TODO check for valid root entry
		l.append("")
		l.append("menuentry \"%s\" {" % myname )
		self.PrepareGRUBForDevice(myroot,l)
		self.bootitems.append(myname)
		retval, mygrubroot = self.DeviceGRUB(myroot)
		if mytype == "win7":
			l.append("	chainloader +4")
		elif mytype in [ "vista", "dos", "winxp" ]:
			l.append("	chainloader +1")
		l.append("}")
		return [ ok, msgs ]

	def generateBootEntry(self,l,sect,kname,kext):
		global r

		ok=True
		allmsgs=[]

		l.append("")
		label = r.GetBootEntryString( sect, kname ) 

		l.append("menuentry \"%s\" {" % label )
		# self.bootitems records all our boot items
		self.bootitems.append(label)
	
		self.PrepareGRUBForFilesystem(self.config["%s/scan" % sect],l)
		kpath=r.RelativePathTo(kname,self.config["%s/scan" % sect])
		params=self.config["%s/params" % sect].split()

		ok, allmsgs, myroot = r.DoRootAuto(params,ok,allmsgs)
		if not ok:
			return [ ok, allmsgs ]
		ok, allmsgs, fstype = r.DoRootfstypeAuto(params,ok,allmsgs)
		if not ok:
			return [ ok, allmsgs ]

		l.append("	linux %s %s" % ( kpath," ".join(params) ))
		initrds=self.config.item(sect,"initrd")
		initrds=r.FindInitrds(initrds, kname, kext)
		for initrd in initrds:
			l.append("	initrd %s" % r.RelativePathTo(initrd,self.config["%s/scan" % sect]))
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
			self.PrepareGRUBForFilesystem(c["boot/path"],l)
			font = None
			if c.hasItem("display/font"):
				font = c["display/font"]
				if not os.path.exists(font):
					allmsgs.append(["warn","specified font \"%s\" does not exist, using default." % font] )
					font = None
			if font == None:
				font = "%s/grub/unifont.pf2" % c["boot/path"]
			l += [ "if loadfont %s; then" % r.RelativePathTo(font,c["boot/path"]),
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
							" background_image %s" % r.RelativePathTo(bgimg,c["path/boot"])
						]
					elif os.path.exists("%s/%s" % ( c["path/boot"], bgimg)):
						l += [
							" insmod %s" % bgext,
							" background_image %s" % r.RelativePathTo("%s/%s" % ( c["path/boot"], bgimg ))
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


		ok, msgs, self.defpos, self.defname = r.GenerateSections(l,self.generateBootEntry,self.generateOtherBootEntry)
		allmsgs += msgs
		if not ok:
			return [ ok, allmsgs, l]
		
		l += [ 
			""
			"set default=%s" % self.defpos
		]
	
		return [ok, allmsgs, l]
			
	def GuppyMap(self):
		out=commands.getstatusoutput("/sbin/grub-mkdevicemap")
		if out[0] != 0:
			print "grub-mkdevicemap"
			print out[1]
			sys.exit(1)

	def Guppy(self,argstring,fatal=True):
		out=commands.getstatusoutput("/sbin/grub-probe "+argstring)
		if fatal and out[0] != 0:
			print "grub-probe "+argstring
			print out[1]
			sys.exit(1)
		else:
			return out

	def RequiredGRUBModules(self,dev):
		mods=[]
		for targ in [ "abstraction", "fs" ]:
			for mod in self.DeviceProbe(dev,targ):
				mods.append(mod)
		return mods

	def DeviceProbe(self,dev,targ):
		retval, mods = self.Guppy(" --device %s --target=%s" % (dev, targ))
		if retval == 0:
			return mods.split()
		else:
			return []

	def DeviceOfFilesystem(self,fs):
		retval,out=self.Guppy(" --target=device %s" % fs)
		return retval,out

	def DeviceUUID(self,dev):
		retval,out=self.Guppy(" --device %s --target=fs_uuid 2> /dev/null" % dev)
		return retval,out

	def DeviceGRUB(self,dev):
		retval,out=self.Guppy(" --device %s --target=drive" % dev) 
		return retval,out

	def PrepareGRUBForFilesystem(self,fs,l):
		retval, dev = self.DeviceOfFilesystem(fs)
		return self.PrepareGRUBForDevice(dev,l)

	def PrepareGRUBForDevice(self,dev,l):
		for mod in self.RequiredGRUBModules(dev):
			l.append("	insmod %s" % mod)
		retval, grubdev = self.DeviceGRUB(dev)
		l.append("	set root=%s" % grubdev)
		retval, uuid = self.DeviceUUID(dev)
		if retval == 0:
			l.append("	search --no-floppy --fs-uuid --set %s" % uuid )
		# TODO: add error handling for retvals	
