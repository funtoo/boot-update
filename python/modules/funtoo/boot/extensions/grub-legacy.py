# -*- coding: ascii -*-

import os
import shlex

from subprocess import Popen
from subprocess import PIPE
from subprocess import STDOUT

from funtoo.boot.extension import Extension

def getExtension(config):
	return GRUBLegacyExtension(config)

class GRUBLegacyExtension(Extension):

	def __init__(self,config):
		Extension.__init__(self,config)
		self.fn = "{path}/{dir}/{file}".format(path = self.config["boot/path"], dir = self.config["grub-legacy/dir"], file = self.config["grub-legacy/file"])
		self.bootitems = []

	def isAvailable(self):
		msgs=[]
		ok=True
		return [ok, msgs]

	def generateOtherBootEntry(self,l,sect):
		ok=True
		msgs=[]
		mytype = self.config["{s}/type".format(s = sect)].lower()
		if mytype in ["dos", "msdos"]:
			mytype = "dos"
		elif mytype in ["windows", "windows 2000", "win2000", "windows xp", "winxp"]:
			mytype = "winxp"
		elif mytype in ["windows vista", "vista"]:
			mytype = "vista"
		elif mytype in ["windows 7", "win7"]:
			mytype = "win7"
		elif mytype in [ "windows 8", "win8"]:
			mytype = "win8"
		elif mytype in ["haiku", "haiku os"]:
			mytype = "haiku"
		else:
			ok = False
			msgs.append(["fatal","Unrecognized boot entry type \"{type}\"".format(type = mytype)])
			return [ ok, msgs ]
		params=self.config["{s}/params".format(s = sect)].split()
		myroot = self.r.GetParam(params,"root=")
		# TODO check for valid root entry
		l.append("title {s}".format(s = sect))
		#self.PrepareGRUBForDevice(myroot,l)
		self.bootitems.append(sect)
		mygrubroot = self.DeviceGRUB(myroot)
		if mygrubroot == None:
			msgs.append(["fatal","Couldn't determine root device using grub-probe"])
			return [ False, msgs ]
		if mytype == "haiku" :
			l.append("  rootnoverify {dev}".format(dev = mygrubroot))
		else :
			l.append("  root {dev}".format(dev = mygrubroot))
		if mytype in [ "win7", "win8" ]:
			l.append("  chainloader +4")
		elif mytype in ["vista", "dos", "winxp", "haiku"]:
			l.append("  chainloader +1")
		l.append("")
		return [ ok, msgs ]

	def DeviceOfFilesystem(self,fs):
		return self.Guppy(" --target=device {f}".format(f = fs))

	def Guppy(self,argstring,fatal=True):
		gprobe = "/usr/sbin/grub-probe"
		if not os.path.exists(gprobe):
			gprobe = "/sbin/grub-probe"
		if not os.path.exists(gprobe):
			raise ExtensionError("couldn't find grub-probe")
		cmd = shlex.split("{gcmd} {args}".format(gcmd = gprobe, args = argstring))
		cmdobj = Popen(cmd, bufsize = -1, stdout = PIPE, stderr = STDOUT, shell = False)
		output = cmdobj.communicate()
		if cmdobj.poll() != 0:
			print("ERROR calling {cmd} {args}, Output was:\n{out}".format(cmd = gprobe, args = argstring, out = output[0].decode()))
			return None
		else:
			return output[0].decode().strip("\n")

	def DeviceGRUB(self,dev):
		out=self.Guppy(" --device {d} --target=drive".format(d = dev))
		# Convert GRUB "count from 1" (hdx,y) format to legacy "count from 0" format
		if out == None:
			return None
		mys = out[1:-1].split(",")
		partnum = mys[1]
		if partnum[:-1] == "msdos":
			partnum = partnum[:-1]
		try:
			partnum = int(partnum)
		except ValueError:
			print("ERROR: could not parse: %s" % out)
			return None
		mys = ( mys[0], partnum - 1 )
		out = "({d},{p})".format(d = mys[0], p = mys[1])
		return out

	def generateBootEntry(self,l,sect,kname,kext):

		ok = True
		allmsgs = []
		mytype = self.config["{s}/type" .format(s = sect)]
		label = self.r.GetBootEntryString( sect, kname )

		l.append("title {name}".format(name = label))
		self.bootitems.append(label)

		# Populate xen variables if type is xen
		if  mytype == "xen":
			xenkernel = self.config["{s}/xenkernel".format(s = sect)]
			# Add leading / if needed
			if not xenkernel.startswith("/"):
				xenkernel = "/{xker}".format(xker = xenkernel)
			xenpath = self.r.StripMountPoint(xenkernel)
			xenparams = self.config["{s}/xenparams".format(s = sect)].split()

		# Get kernel and params
		kpath = self.r.StripMountPoint(kname)
		params=self.config.item(sect,"params").split()

		ok, allmsgs, myroot = self.r.DoRootAuto(params,ok,allmsgs)
		if not ok:
			return [ ok, allmsgs ]
		ok, allmsgs, fstype = self.r.DoRootfstypeAuto(params,ok,allmsgs)
		if not ok:
			return [ ok, allmsgs ]

		mygrubroot = self.DeviceGRUB(self.DeviceOfFilesystem(self.config["boot/path"]))
		if mygrubroot == None:
			allmsgs.append(["fatal","Could not determine device of filesystem using grub-probe"])
			return [ False, allmsgs ]

		# print out our grub-ified root setting
		l.append("  root {dev}".format(dev = mygrubroot ))

		# Get initrds
		initrds = self.config.item(sect, "initrd")
		initrds = self.r.FindInitrds(initrds, kname, kext)

		# Append kernel lines based on type
		if mytype == "xen" :
			l.append("  kernel {xker} {xparams}".format(xker = xenpath, xparams = " ".join(xenparams)))
			l.append("  module {ker} {params}".format(ker = kpath, params = " ".join(params)))
			for initrd in initrds:
				l.append("  module {initrd}".format(initrd = self.r.StripMountPoint(initrd)))
		else :
			l.append("  kernel {k} {par}".format(k = kpath, par = " ".join(params)))
			for initrd in initrds:
				l.append("  initrd {rd}".format(rd = self.r.StripMountPoint(initrd)))

		l.append("")

		return [ ok, allmsgs ]

	def generateConfigFile(self):
		l=[]
		ok=True
		allmsgs=[]
		# pass our boot entry generator function to GenerateSections, and everything is taken care of for our boot entries

		ok, msgs, self.defpos, self.defname = self.r.GenerateSections(l,self.generateBootEntry, self.generateOtherBootEntry)
		allmsgs += msgs
		if not ok:
			return [ ok, allmsgs, l ]

		l = [
			self.config.condFormatSubItem("boot/timeout", "timeout {s}"),
			"default {pos}".format(pos = self.defpos),
			""
		] + l

		return [ok, allmsgs, l ]

