#!/usr/bin/python2
# -*- coding: ascii -*-

import os

from funtoo.boot.extension import Extension


def getExtension(config):
	return LILOExtension(config)

class LILOExtension(Extension):

	def __init__(self,config):
		Extension.__init__(self,config)
		self.fn = self.config["lilo/file"]
		self.lilo_cmd = self.config["lilo/bin"]
		self.bootitems = []

	def isAvailable(self):
		msgs=[]
		ok=True
		if not os.path.exists(self.lilo_cmd):
			msgs.append(["fatal","{cmd}, required for boot/generate = lilo, does not exist".format(cmd = self.lilo_cmd)])
			ok=False
		return [ok, msgs]

	def updateBootLoader(self):

		msgs = [ [ "warn", "This version of boot-update requires that you run /sbin/lilo manually." ] ]
		return [True, msgs]

	def generateOtherBootEntry(self,l,sect):
		ok = True
		allmsgs = []

		# Name can not be longer than 15 characters
		if len(sect) > 15 :
			ok = False
			allmsgs.append(["fatal", "'{name}' is too long. Section names in /etc/boot.conf for non-linux OS must not exceed 15 characters when using lilo".format(name = sect)])
			return [ ok, allmsgs  ]

		params=self.config["%s/params" % sect].split()
		myroot = self.r.GetParam(params,"root=")

		l.append("")
		l.append("other={dev}".format(dev = myroot))

		# Make sure we change any spaces in name to "_". Lilo doesn't like spaces.
		l.append("	label=\"{name}\"".format(name = sect.replace(" ", "_")))

		return [ ok, allmsgs  ]

	def generateBootEntry(self,l,sect,kname,kext):

		ok=True
		allmsgs=[]

		if len(os.path.basename(kname)) > 15:
			ok = False
			allmsgs.append(["fatal", "'{name}' is too long. Kernel names must not exceed 15 characters when using lilo".format(name =(os.path.basename(kname)))])
		l.append("")
		self.bootitems.append(kname)
		l.append("image=%s" % kname )

		params=self.config.item(sect,"params").split()

		ok, allmsgs, myroot = self.r.DoRootAuto(params,ok,allmsgs)
		if not ok:
			return [ ok, allmsgs ]
		ok, allmsgs, myfstype = self.r.DoRootfstypeAuto(params,ok,allmsgs)
		if not ok:
			return [ ok, allmsgs ]

		self.r.ZapParam(params,"root=")

		l += [
			"	read-only",
			"	root=%s" % myroot,
			"	append=\"%s\"" % " ".join(params)
		]
		initrds=self.config.item(sect,"initrd")
		initrds=self.r.FindInitrds(initrds, kname, kext)
		for initrd in initrds:
			l.append("  initrd=" % self.r.RelativePathTo(initrd,"/boot"))

		return [ ok, allmsgs ]

	def generateConfigFile(self):
		l=[]
		c=self.config
		ok=True
		allmsgs=[]

		# Warn if no boot entry.
		if c.hasItem("lilo/boot"):
			l.append("boot={dev}".format(dev = c["lilo/boot"]))
		else:
			allmsgs.append(["warn", "No 'boot' entry specified in section 'lilo'. Lilo will install itself to the current root partition. See `man 5 boot.conf` for more info"])

		# Append global lilo params
		for gparam in c["lilo/gparams"].split() :
			l.append(gparam)

		# pass our boot entry generator function to GenerateSections, and everything is taken care of for our boot entries

		ok, msgs, self.defpos, self.defname = self.r.GenerateSections(l,self.generateBootEntry, self.generateOtherBootEntry)
		allmsgs += msgs
		if not ok:
			return [ ok, allmsgs, l]

		l = [
			c.condSubItem("boot/timeout", "timeout=%s"),
			# Replace spaces with "_" in default name. Lilo doesn't like spaces
			"default=\"{name}\"" .format(name=self.defname.replace(" ", "_")),
		] + l

		allmsgs.append(["warn","Please note that LILO support is *BETA* quality and is for testing only."])

		return [ok, allmsgs, l]

