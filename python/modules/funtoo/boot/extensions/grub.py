# -*- coding: ascii -*-

import os
import shlex

from subprocess import Popen
from subprocess import PIPE
from subprocess import STDOUT

from funtoo.boot.extension import Extension
from funtoo.boot.extension import ExtensionError

def getExtension(config):
	""" Gets the extension based on the configuration """
	return GRUBExtension(config)

class GRUBExtension(Extension):
	""" Implements an extension for the grub bootloader """

	def __init__(self, config, testing = False):
		Extension.__init__(self,config)
		self.grubpath =  "{path}/{dir}".format(path = self.config["boot/path"], dir = self.config["grub/dir"])
		self.fn = "{path}/{file}".format(path = self.grubpath, file = self.config["grub/file"])
		self.bootitems = []
		self.testing = testing
		self.GuppyMap()
		self.defpos = 0
		self.defname = "undefined"

	def grubProbe(self):
		gprobe = "/usr/sbin/grub-probe"
		if not os.path.exists(gprobe):
			gprobe = "/sbin/grub-probe"
		if not os.path.exists(gprobe):
			raise ExtensionError("couldn't find grub-probe")
		return gprobe

	def generateOtherBootEntry(self, l, sect):
		""" Generates the boot entry for other systems """
		ok = True
		msgs = []
		mytype = self.config["{s}/type".format(s = sect)].lower()
		if mytype in ["dos", "msdos"]:
			mytype = "dos"
		elif mytype in ["windows", "windows 2000", "win2000", "windows xp", "winxp"]:
			mytype = "winxp"
		elif mytype in ["windows vista", "vista"]:
			mytype = "vista"
		elif mytype in ["windows 7", "win7"]:
			mytype = "win7"
		elif mytype in [ "windows 8", "win8" ]:
			mytype = "win8"
		elif mytype in ["haiku", "haiku os"]:
			mytype = "haiku"
		else:
			ok = False
			msgs.append(["fatal", "Unrecognized boot entry type \"{mt}\"".format(mt = mytype)])
			return [ ok, msgs ]
		params = self.config["{s}/params".format(s = sect)].split()
		myroot = self.r.GetParam(params, "root=")
		myname = sect
		# TODO check for valid root entry
		l.append("")
		l.append("menuentry \"{mn}\" {{".format(mn = myname))
		self.PrepareGRUBForDevice(myroot, l)
		self.bootitems.append(myname)
		self.DeviceGRUB(myroot)
		if mytype in [ "win7", "win8" ]:
			l.append("  chainloader +4")
		elif mytype in ["vista", "dos", "winxp", "haiku"]:
			l.append("  chainloader +1")
		l.append("}")
		return [ ok, msgs ]

	def generateBootEntry(self, l, sect, kname, kext):
		""" Generates the boot entry """
		ok = True
		allmsgs = []
		mytype = self.config["{s}/type" .format(s = sect)]
		l.append("")
		label = self.r.GetBootEntryString( sect, kname )
		l.append("menuentry \"{l}\" {{".format(l = label))

		# self.bootitems records all our boot items
		self.bootitems.append(label)

		self.PrepareGRUBForFilesystem(self.config["{s}/scan".format(s = sect)], l)

		# Populate xen variables if type is xen
		if  mytype == "xen":
			xenkernel = self.config["{s}/xenkernel".format(s = sect)]
			# Add leading / if needed
			if not xenkernel.startswith("/"):
				xenkernel = "/{xker}".format(xker = xenkernel)
			xenpath = self.r.StripMountPoint(xenkernel)
			xenparams = self.config["{s}/xenparams".format(s = sect)].split()

		kpath = self.r.StripMountPoint(kname)
		params = self.config["{s}/params".format(s = sect)].split()

		ok, allmsgs, myroot = self.r.DoRootAuto(params, ok, allmsgs)
		if not ok:
			return [ ok, allmsgs ]
		ok, allmsgs, fstype = self.r.DoRootfstypeAuto(params, ok, allmsgs)
		if not ok:
			return [ ok, allmsgs ]
		if fstype == "btrfs":
			params.append('%sflags=subvol=%s' % i( self.r.rootarg, self.BtrfsSubvol()))

		initrds = self.config.item(sect, "initrd")
		initrds = self.r.FindInitrds(initrds, kname, kext)
		if myroot and ('root=' + myroot) in params and 0 == len(initrds):
			params.remove('root=' + myroot)
			params.append('root=' + self.r.resolvedev(myroot))

		# Append kernel lines based on type
		if mytype == "xen" :
			l.append("  multiboot {xker} {xparams}".format(xker = xenpath, xparams = " ".join(xenparams)))
			l.append("  module {ker} {params}".format(ker = kpath, params = " ".join(params)))
			for initrd in initrds:
				l.append("  module {initrd}".format(initrd = self.r.StripMountPoint(initrd)))
		else :
			l.append("  linux {k} {par}".format(k = kpath, par = " ".join(params)))
			if initrds:
				initrds = (self.r.StripMountPoint(initrd) for initrd in initrds)
				l.append("  initrd {rds}".format(rds = " ".join(initrds)))

		# Append graphics line
		if self.config.hasItem("{s}/gfxmode".format(s = sect)):
			l.append("  set gfxpayload={gm}".format(gm = self.config.item(sect, "gfxmode")))
		l.append("}")

		return [ ok, allmsgs ]

	def generateConfigFile(self):
		l = []
		c = self.config
		ok = True
		allmsgs = []
		l.append(c.condFormatSubItem("boot/timeout", "set timeout={s}"))
		# pass our boot entry generator function to GenerateSections,
		# and everything is taken care of for our boot entries

		if c.hasItem("display/gfxmode"):

			l.append("")
			self.PrepareGRUBForFilesystem(c["boot/path"], l)
			if c.hasItem("display/font"):
				font = c["display/font"]
			else:
				font = "unifont.pf2"

			src_font = "{src}/{f}".format(src = c["grub/font_src"], f = font)
			dst_font = "{path}/{f}".format(path = self.grubpath, f = font)

			if not os.path.exists(dst_font):
				if os.path.exists(src_font):
					# copy from /usr/share location to /boot/grub:
					import shutil
					shutil.copy(src_font,dst_font)
				else:
					allmsgs.append(["fatal", "specified font \"{ft}\" not found at {dst}; aborting.".format(ft = font, dst = dst_font)] )
					return [False, allmsgs, l]

			l += [ "if loadfont {dst}; then".format(dst = self.r.RelativePathTo(dst_font,c["boot/path"])),
				"   set gfxmode={gfx}".format(gfx = c["display/gfxmode"]),
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

					rel_cfgpath = "{path}/{img}".format(path = c["boot/path"], img = bgimg)

					# first, look for absolute path, because our relative path
					# can eval to "/boot/boot/foo.png" which
					# due to the /boot/boot symlink will "exist".

					if bgimg[0] == "/" and os.path.exists(bgimg):
						# user specified absolute path to file on disk:
						l += [
							"   insmod {bg}".format(bg = bgext),
							"   background_image {img}".format(img = self.r.RelativePathTo(bgimg, c["boot/path"] ))
						]
					elif os.path.exists(rel_cfgpath):
						# user specified path relative to /boot:
						l += [
							"   insmod {ext}".format(ext = bgext),
							"   background_image {img}".format(img = self.r.RelativePathTo(rel_cfgpath , c["boot/path"] ))
						]
					else:
						allmsgs.append(["warn","background image \"{img}\" does not exist - skipping.".format(img = bgimg)])
				else:
					allmsgs.append(["warn","background image \"{img}\" (format \"{ext}\") not recognized - skipping.".format(img = bgimg, ext = bgext)])
			l += [ "fi",
				"",
				c.condFormatSubItem("color/normal", "set menu_color_normal={s}"),
				c.condFormatSubItem("color/highlight", "set menu_color_highlight={s}"),
			]
		else:
			if c.hasItem("display/background"):
				allmsgs.append(["warn","display/gfxmode not provided - display/background \"{bg}\" will not be displayed.".format(bg = c["display/background"])] )

		ok, msgs, self.defpos, self.defname = self.r.GenerateSections(l, self.generateBootEntry, self.generateOtherBootEntry)
		allmsgs += msgs
		if not ok:
			return [ ok, allmsgs, l]

		l += [
			""
			"set default={pos}".format(pos = self.defpos)
		]

		return [ok, allmsgs, l]

	def GuppyMap(self):
		""" Creates the device map """
		gmkdevmap = "/sbin/grub-mkdevicemap"
		if not os.path.exists(gmkdevmap):
			# grub-2.00 and above does not have mkdevicemap - so skip it if we don't see it.
			return
		cmdobj = None
		if self.testing:
			cmdstr = "{gm} --no-floppy --device-map=/dev/null".format(gm = gmkdevmap)
			cmdobj = Popen(cmdstr, bufsize = -1, stdout = PIPE,  stderr = STDOUT, shell = True)
		else:
			cmdobj = Popen([gmkdevmap, "--no-floppy"], bufsize = -1, stdout = PIPE,  stderr = STDOUT, shell = False)
		output = cmdobj.communicate()
		if cmdobj.poll() != 0:
			raise ExtensionError("{cmd}\n{out}".format(cmd = gmkdevmap, out = output[0].decode()))

	def Guppy(self, argstring, fatal=True):
		""" Probes a device """
		gprobe = self.grubProbe()
		cmd = shlex.split("{gcmd} {args}".format(gcmd = gprobe, args = argstring))
		cmdobj = Popen(cmd, bufsize=-1, stdout=PIPE, stderr=PIPE, shell=False)
		output = cmdobj.communicate()
		retval = cmdobj.poll()
		if fatal and retval != 0:
			raise ExtensionError("{cmd} {args}\n{out}".format(cmd = gprobe, args = argstring, out = output[0].decode()))
		else:
			return retval, output[0].decode().strip("\n")

	def BtrfsSubvol(self):
		cmdobj = Popen("btrfs subvol list /", bufsize=-1, stdout=PIPE, stderr=PIPE, shell=False)
		output = cmdobj.communicate()[0].decode()
		retval = cmdobj.poll()
		if retval != 0:
			raise ExtensionError("btrfs command failed: %s" % output)
		return output.split()[6]	

	def RequiredGRUBModules(self, dev):
		""" Determines required grub modules """
		mods = []
		for targ in [ "abstraction", "partmap", "fs" ]:
			for mod in self.DeviceProbe(dev, targ):
				# grub-1.98 will return "part_gpt", while 2.00 will return "gpt" -- accommodate this:
				if targ == "partmap" and mod[:5] != "part_":
					mod = "part_" + mod
				mods.append(mod)
		return mods

	def DeviceProbe(self, dev, targ):
		""" Determines the device details """
		retval, mods = self.Guppy(" --device {d} --target={t}".format(d = dev, t = targ))
		if retval == 0:
			return mods.split()
		else:
			return []

	def DeviceOfFilesystem(self, fs):
		""" Determines the device of a filesystem """
		retval, out = self.Guppy(" --target=device {f}".format(f = fs))
		return retval, out

	def DeviceUUID(self, dev):
		""" Determines the UUID of the filesystem """
		retval, out = self.Guppy(" --device {d} --target=fs_uuid".format(d = dev))
		return retval, out

	def DeviceGRUB(self, dev):
		""" Determines the Grub device for a Linux device """
		retval, out = self.Guppy(" --device {d} --target=drive".format(d = dev))
		return retval, out

	def PrepareGRUBForFilesystem(self, fs, l):
		""" Prepares Grub for the filesystem """
		retval, dev = self.DeviceOfFilesystem(fs)
		return self.PrepareGRUBForDevice(dev, l)

	def PrepareGRUBForDevice(self, dev, l):
		""" Prepares Grub for the device """
		for mod in self.RequiredGRUBModules(dev):
			l.append("  insmod {m}".format(m = mod))
		retval, grubdev = self.DeviceGRUB(dev)
		l.append("  set root={dev}".format(dev = grubdev))
		retval, uuid = self.DeviceUUID(dev)
		if retval == 0:
			l.append("  search --no-floppy --fs-uuid --set {u}".format(u = uuid ))
		# TODO: add error handling for retvals
