#!/usr/bin/python2

import os, sys, commands

from ..extension import Extension
from ..resolver import Resolver
from ..helper import *

r=None

def getExtension(config):
	global r
	r=Resolver(config)
	return GRUBLegacyExtension(config)

class GRUBLegacyExtension(Extension):

	def __init__(self,config):
		self.fn = "/boot/grub/grub.conf"
		self.config = config
		self.bootitems = []

	def isAvailable(self):
		msgs=[]
		ok=True
		return [ok, msgs]

	def generateBootEntry(self,l,sect,kname,kext):
		global r

		ok=True
		allmsgs=[]

		l.append("")
		label = r.GetBootEntryString( sect, kname )
		
		l.append("title %s" % label)
		self.bootitems.append(label)

		if config.item(sect,"type") == "chainloader":
			l.append("chainloader +1")	

		kpath=r.RelativePathTo(kname,"/boot")
		params=self.config.item(sect,"params").split()

		ok, allmsgs, myroot = r.DoRootAuto(params,ok,allmsgs)
		if not ok:
			return [ ok, allmsgs ]
		ok, allmsgs, fstype = r.DoRootfstypeAuto(params,ok,allmsgs)
		if not ok:
			return [ ok, allmsgs ]
	
		if fstabHasEntry("/boot"):
			# If /boot exists, then this is our grub "root" (where we look for boot loader stages and kernels)
			rootfs="/boot"
			rootdev=myroot
		else:
			# If /boot doesn't exist, the root filesystem is treated as grub's "root"
			rootfs = "/"
			rootdev = r.GetParam(params,"root=")
		
		# Now that we have the grub root in /dev/sd?? format, attempt to convert it to (hd?,?) format
		if rootdev[0:5] != "/dev/":
			ok = False
			allmsgs.append(["fatal","grub-legacy - %s is not a valid GRUB root - ensure /etc/fstab is correct or specify a root= parameter." % rootdev ] )
			return [ ok, allmsgs ]
		if rootdev[5:7] != "sd":
			allmsgs.append(["warn","grub-legacy - encountered \"%s\", a non-\"sd\" device. Root setting may not be accurate." % rootdev])
		rootmaj = ord(rootdev[7]) - ord('a')
		try:
			rootmin = int(rootdev[8:]) - 1
		except TypeError:
			ok = False
			allmsgs.append(["fatal","grub-legacy - couldn't calculate the root minor for \"%s\"." % rootdev])
			return [ ok, allmsgs ]
		# print out our grub-ified root setting
		l.append("root (hd%s,%s)" % (rootmaj, rootmin ))
		l.append("kernel %s %s" % ( kpath," ".join(params) ))
		initrds=r.FindInitrds(sect, kname, kext)
		for initrd in initrds:
			l.append("initrd %s" % self.command.RelativePathTo(initrd,"/boot"))
		l.append("")

		return [ ok, allmsgs ]

	def generateConfigFile(self):
		l=[]
		c=self.config
		ok=True
		allmsgs=[]
		global r
		l.append(c.condSubItem("boot/timeout", "timeout %s"))
		# pass our boot entry generator function to GenerateSections, and everything is taken care of for our boot entries

		ok, msgs, defpos, defname = r.GenerateSections(l,self.generateBootEntry)
		allmsgs += msgs
		if not ok:
			return [ ok, allmsgs, l, None ]
		
		l += [ 
			""
			"default %s" % defpos
		]
	
		return [ok, allmsgs, l, defname]
			
