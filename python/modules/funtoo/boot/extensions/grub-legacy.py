#!/usr/bin/python2
# -*- coding: ascii -*-
import os, commands

from ..extension import Extension

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
		myroot = self.r.GetParam(params,"root=")
		myname = sect
		# TODO check for valid root entry
		l.append("title %s" % myname )
		#self.PrepareGRUBForDevice(myroot,l)
		self.bootitems.append(myname)
		mygrubroot = self.DeviceGRUB(myroot)
		if mygrubroot == None:
			msgs.append(["fatal","Couldn't determine root device using grub-probe"])
			return [ False, msgs ]
		l.append("root %s" % mygrubroot )
		if mytype == "win7":
			l.append("chainloader +4")
		elif mytype in [ "vista", "dos", "winxp" ]:
			l.append("chainloader +1")
		l.append("")
		return [ ok, msgs ]

	def DeviceOfFilesystem(self,fs):
		return self.Guppy(" --target=device %s" % fs)

	def Guppy(self,argstring,fatal=True):
		# grub-probe is from grub-1.97+ -- we use it here as well
		if not os.path.exists("{path}/{dir}/device.map".format(path = self.config["boot/path"], dir = self.config["grub/dir"])):
			out = commands.getstatusoutput("{cmd} --no-floppy".format(self.config["grub/grub-mkdevicemap"]))
			if out[0] != 0:
				print("ERROR calling {cmd}".format(self.config["grub/grub-mkdevicemap"]))
				return None
		retval,out=commands.getstatusoutput("{cmd} {args}".format(cmd = self.config["grub/grub-probe"], args = argstring))
		if retval:
			print("ERROR calling {cmd}".format(cmd = self.config["grub/grub-probe"]))
			return None
		else:
			return out

	def DeviceGRUB(self,dev):
		out=self.Guppy(" --device %s --target=drive" % dev)
		# Convert GRUB "count from 1" (hdx,y) format to legacy "count from 0" format
		if out == None:
			return None
		mys = out[1:-1].split(",")
		mys = ( mys[0], repr(int(mys[1]) - 1) )
		out = "(%s,%s)" % mys
		return out

	def generateBootEntry(self,l,sect,kname,kext):

		ok=True
		allmsgs=[]

		label = self.r.GetBootEntryString( sect, kname )

		l.append("title %s" % label)
		self.bootitems.append(label)

		kpath=self.r.RelativePathTo(kname,"/boot")
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
		l.append("root %s" % mygrubroot )
		l.append("kernel %s %s" % ( kpath," ".join(params) ))
		initrds=self.config.item(sect,"initrd")
		initrds=self.r.FindInitrds(initrds, kname, kext)
		for initrd in initrds:
			l.append("initrd %s" % self.r.RelativePathTo(initrd,"/boot"))
		l.append("")

		return [ ok, allmsgs ]

	def generateConfigFile(self):
		l=[]
		c=self.config
		ok=True
		allmsgs=[]
		# pass our boot entry generator function to GenerateSections, and everything is taken care of for our boot entries

		ok, msgs, self.defpos, self.defname = self.r.GenerateSections(l,self.generateBootEntry, self.generateOtherBootEntry)
		allmsgs += msgs
		if not ok:
			return [ ok, allmsgs, l ]

		l = [
			c.condSubItem("boot/timeout", "timeout %s"),
			"default %s" % self.defpos,
			""
		] + l

		return [ok, allmsgs, l ]

