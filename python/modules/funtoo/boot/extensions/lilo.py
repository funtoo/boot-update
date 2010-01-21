#!/usr/bin/python2

import os, sys, commands

from ..extension import Extension
from ..resolver import Resolver
from ..helper import *

r=None

def getExtension(config):
	global r
	r=Resolver(config)
	return LILOExtension(config)

class LILOExtension(Extension):

	def __init__(self,config):
		self.fn = "/etc/lilo.conf"
		self.config = config
		self.bootitems = []

	def isAvailable(self):
		msgs=[]
		ok=True
		if not os.path.exists("/sbin/lilo"):
			msgs.append(["fatal","/sbin/lilo, required for boot/generate = lilo, does not exist"])
			ok=False
		return [ok, msgs]

	def updateBootLoader(self):
		msgs = [ [ "warn", "This version of coreboot requires that you run /sbin/lilo manually." ] ]
		return [True, msgs]

	def generateBootEntry(self,l,sect,kname,kext):
		global r

		ok=True
		allmsgs=[]

		l.append("")
		self.bootitems.append(kname)
		l.append("image=%s" % kname )
		
		params=self.config.item(sect,"params")
		myroot = None

		if "root=auto" in params:
			params.remove("root=auto")
			myroot = fstabGetRootDevice()
		else:
			for item in params:
				if item[0:5] == "root=":
					myroot = item[5:]
					params.remove(item)
					break
		
		if myroot == None:
			allmsgs.append(["warn","No root= parameter specified for boot entry \"%s\" - using current root filesystem." % sect])
			myroot=fstabGetRootDevice()
	
		if "rootfstype=auto" in params:
			params.remove("rootfstype=auto")
			params.append("rootfstype=%s" % fstabGetFilesystemOfDevice(myroot))

		l += [
			"	read-only",
			"	root=%s" % myroot,
			"	append=\"%s\"" % " ".join(params)
		]
		initrds=r.FindInitrds(sect, kname, kext)
		for initrd in initrds:
			l.append("	initrd=" % self.command.RelativePathTo(initrd,"/boot"))
		l.append("")

		return [ ok, allmsgs ]

	def generateConfigFile(self):
		l=[]
		c=self.config
		ok=True
		allmsgs=[]
		global r
		l.append(c.condSubItem("boot/timeout", "timeout=%s"))
		# pass our boot entry generator function to GenerateSections, and everything is taken care of for our boot entries

		ok, msgs, defpos, defname = r.GenerateSections(l,self.generateBootEntry)
		allmsgs += msgs
		if not ok:
			return [ ok, allmsgs, l]
		
		if defpos != None:
			l += [ 
				""
				"default=%s" % defname
			]
	
		allmsgs.append(["info","Configuration file %s generated - %s lines." % ( self.fn, len(l))])
		allmsgs.append(["info","Kernel \"%s\" will be booted by default." % defname])
		allmsgs.append(["warn","Please note that LILO support is *ALPHA* quality and is for testing only."])

		return [ok, allmsgs, l]
			
