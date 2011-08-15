#!/usr/bin/python2
# -*- coding: ascii; tab-width: 4; indent-tabs-mode: nil -*-
""" extension for handling grub """
import os, sys, commands

from ..extension import Extension

def getExtension(config):
	""" gets the extension based on the configuration """
	return GRUBExtension(config)

# Add exception definition here to be used by a Guppy failure.
# -- ExtensionError?
class GRUBExtension(Extension):
	""" implements an extension for the grub bootloader """
	def __init__(self, config, testing = False):
		Extension.__init__(self,config)
		self.fn = "%s/grub/grub.cfg" % self.config["boot/path"]
		self.bootitems = []
		self.testing = testing
		self.GuppyMap()
		self.defpos = 0
		self.defname = "undefined"

	def isAvailable(self):
		msgs = []
		ok = True
		if not os.path.exists("/sbin/grub-probe"):
			msgs.append(["fatal", "/sbin/grub-probe, required for boot/generate = grub,  does not exist"])
			ok = False
		return [ok, msgs]
	
	def generateOtherBootEntry(self, l, sect):
		""" generates the boot entry for other systems """
		ok = True
		msgs = []
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
			msgs.append(["fatal", "Unrecognized boot entry type \"%s\"" % mytype])
			return [ ok, msgs ]
		params = self.config["%s/params" % sect].split()
		myroot = self.r.GetParam(params, "root=")
		myname = sect
		# TODO check for valid root entry
		l.append("")
		l.append("menuentry \"%s\" {" % myname )
		self.PrepareGRUBForDevice(myroot, l)
		self.bootitems.append(myname)
		self.DeviceGRUB(myroot)
		if mytype == "win7":
			l.append("  chainloader +4")
		elif mytype in [ "vista", "dos", "winxp" ]:
			l.append("  chainloader +1")
		l.append("}")
		return [ ok, msgs ]

	def generateBootEntry(self, l, sect, kname, kext):
		""" generates the boot entry """
		ok = True
		allmsgs = []

		l.append("")
		label = self.r.GetBootEntryString( sect, kname ) 

		l.append("menuentry \"%s\" {" % label )
		# self.bootitems records all our boot items
		self.bootitems.append(label)
	
		self.PrepareGRUBForFilesystem(self.config["%s/scan" % sect], l)
		kpath = self.r.RelativePathTo(kname, self.config["%s/scan" % sect])
		params = self.config["%s/params" % sect].split()

		ok, allmsgs, myroot = self.r.DoRootAuto(params, ok, allmsgs)
		if not ok:
			return [ ok, allmsgs ]
		ok, allmsgs, fstype = self.r.DoRootfstypeAuto(params, ok, allmsgs)
		if not ok:
			return [ ok, allmsgs ]

		initrds = self.config.item(sect, "initrd")
		initrds = self.r.FindInitrds(initrds, kname, kext)
		if myroot and ('root=' + myroot) in params and 0 == len(initrds):
			params.remove('root=' + myroot)
			params.append('root=' + self.r.resolvedev(myroot))
		l.append("  linux %s %s" % ( kpath, " ".join(params) ))
		for initrd in initrds:
			l.append("  initrd %s" % self.r.RelativePathTo(initrd, self.config["%s/scan" % sect]))
		if self.config.hasItem("%s/gfxmode" % sect):
			l.append("  set gfxpayload=%s" % self.config.item(sect, "gfxmode"))
		else:
			l.append("  set gfxpayload=keep")
		l.append("}")
		return [ ok, allmsgs ]

	def generateConfigFile(self):
		l = []
		c = self.config
		ok = True
		allmsgs = []
		l.append(c.condSubItem("boot/timeout", "set timeout=%s"))
		# pass our boot entry generator function to GenerateSections,
		# and everything is taken care of for our boot entries

		if c.hasItem("display/gfxmode"):

			l.append("")
			self.PrepareGRUBForFilesystem(c["boot/path"], l)
			if c.hasItem("display/font"):
				font = c["display/font"]
			else:
				font = "unifont.pf2"

			src_font = "/usr/share/grub/fonts/%s" % font
			dst_font = "%s/grub/%s" % (c["boot/path"], font)
	
			if not os.path.exists(dst_font):
				if os.path.exists(src_font):
					# copy from /usr/share location to /boot/grub:
					import shutil
					shutil.copy(src_font,dst_font)
				else:
					allmsgs.append(["fatal", "specified font \"%s\" not found at %s; aborting." % ( font, dst_font)] )
					return (False, allmsgs)

			l += [ "if loadfont %s; then" %
				   self.r.RelativePathTo(dst_font,c["boot/path"]),
				"   set gfxmode=%s" % c["display/gfxmode"],
				"   insmod gfxterm",
				"   insmod vbe",
				"   terminal_output gfxterm" ]
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
					
					rel_cfgpath = "%s/%s" % ( c["boot/path"], bgimg)
					
					# first, look for absolute path, because our relative path
					# can eval to "/boot/boot/foo.png" which
					# due to the /boot/boot symlink will "exist".

					if bgimg[0] == "/" and os.path.exists(bgimg):
						# user specified absolute path to file on disk:
						l += [
							"   insmod %s" % bgext,
							"   background_image %s" %
							self.r.RelativePathTo(bgimg, c["boot/path"] )
						]
					elif os.path.exists(rel_cfgpath):
						# user specified path relative to /boot:
						l += [
							"   insmod %s" % bgext,
							"   background_image %s" %
							self.r.RelativePathTo(rel_cfgpath , c["boot/path"] )
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
		else:
			if c.hasItem("display/background"):
				allmsgs.append(["warn","display/gfxmode not provided - display/background \"%s\" will not be displayed." % c["display/background"]] )

		ok, msgs, self.defpos, self.defname = self.r.GenerateSections(l, self.generateBootEntry, self.generateOtherBootEntry)
		allmsgs += msgs
		if not ok:
			return [ ok, allmsgs, l]
		
		l += [ 
			""
			"set default=%s" % self.defpos
		]
	
		return [ok, allmsgs, l]
			
	def GuppyMap(self):
		""" creates the device map """
		out = None
		if self.testing:
			out = commands.getstatusoutput("/sbin/grub-mkdevicemap --no-floppy -m /dev/null")
		else:
			out = commands.getstatusoutput("/sbin/grub-mkdevicemap --no-floppy")
		if out[0] != 0:
			print "grub-mkdevicemap"
			print out[1]
			sys.exit(1)

	def Guppy(self, argstring, fatal=True):
		""" probes a device """
		out = commands.getstatusoutput("/sbin/grub-probe " + argstring)
		if fatal and out[0] != 0:
			print "grub-probe " + argstring
			print out[1]
			sys.exit(1)
		else:
			return out

	def RequiredGRUBModules(self, dev):
		""" determines required grub modules """
		mods = []
		for targ in [ "abstraction", "partmap", "fs" ]:
			for mod in self.DeviceProbe(dev, targ):
				if targ == "partmap":
					mods.append("part_%s" % mod)
				else:
					mods.append(mod)
		return mods

	def DeviceProbe(self, dev, targ):
		""" determines the device details """
		retval, mods = self.Guppy(" --device %s --target=%s" % (dev, targ))
		if retval == 0:
			return mods.split()
		else:
			return []

	def DeviceOfFilesystem(self, fs):
		""" determines the device of a filesystem """
		retval, out = self.Guppy(" --target=device %s" % fs)
		return retval, out

	def DeviceUUID(self, dev):
		""" determines the UUID of the filesystem """
		retval, out = self.Guppy(" --device %s --target=fs_uuid 2> /dev/null" % dev)
		return retval, out

	def DeviceGRUB(self, dev):
		""" determines the Grub device for a Linux device """
		retval, out = self.Guppy(" --device %s --target=drive" % dev) 
		return retval, out

	def PrepareGRUBForFilesystem(self, fs, l):
		""" prepares Grub for the filesystem """
		retval, dev = self.DeviceOfFilesystem(fs)
		return self.PrepareGRUBForDevice(dev, l)

	def PrepareGRUBForDevice(self, dev, l):
		""" prepares Grub for the device """
		for mod in self.RequiredGRUBModules(dev):
			l.append("  insmod %s" % mod)
		retval, grubdev = self.DeviceGRUB(dev)
		l.append("  set root=%s" % grubdev)
		retval, uuid = self.DeviceUUID(dev)
		if retval == 0:
			l.append("  search --no-floppy --fs-uuid --set %s" % uuid )
		# TODO: add error handling for retvals  
