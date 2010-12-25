#!/usr/bin/python2
# -*- coding: ascii -*-
import os

from ..extension import Extension
from ..resolver import Resolver

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
		
		params=self.config.item(sect,"params").split()

		ok, allmsgs, myroot = r.DoRootAuto(params,ok,allmsgs)
		if not ok:
			return [ ok, allmsgs ]
		ok, allmsgs, myfstype = r.DoRootfstypeAuto(params,ok,allmsgs)
		if not ok:
			return [ ok, allmsgs ]

		r.ZapParam(params,"root=")

		l += [
			"   read-only",
			"   root=%s" % myroot,
			"   append=\"%s\"" % " ".join(params)
		]
		initrds=self.config.item(sect,"initrd")
		initrds=r.FindInitrds(initrds, kname, kext)
		for initrd in initrds:
			l.append("  initrd=" % r.RelativePathTo(initrd,"/boot"))
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
			return [ ok, allmsgs, l, None]
		
		l += [ 
			""
			"default=%s" % defname
		]
	
		allmsgs.append(["warn","Please note that LILO support is *ALPHA* quality and is for testing only."])

		return [ok, allmsgs, l, defname]
			
