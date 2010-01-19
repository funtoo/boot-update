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
		if not os.path.exists("/sbin/grub-install"):
			msgs.append(["fatal","/sbin/grub-install does not exist"])
			ok=False
		return [ok, msgs]

	def generateBootEntry(self,l,sect,kname,kext):
		global r

		ok=True
		allmsgs=[]

		l.append("")
		self.bootitems.append("%s - %s" % ( sect, kname))
		l.append("title %s - %s" % ( sect, kname ))
		
		kpath=r.RelativePathTo(kname,"/boot")
		params=self.config.item(sect,"params")
		
		if "root=auto" in params:
			params.remove("root=auto")
			params.append("root=%s" % fstabGetRootDevice())
		
		if "rootfstype=auto" in params:
			params.remove("rootfstype=auto")
			for item in params:
				if item[0:5] == "root=":
					params.append("rootfstype=%s" % fstabGetFilesystemOfDevice(item[5:]))
					break

		if fstabHasEntry("/boot"):
			rootfs="/boot"
		else:
			rootfs="/"

		rootdev=fstabGetDeviceOfFilesystem(rootfs)
		print "DEBUG: rootdev",rootdev
		print "DEBUG: rootdev 0 5", rootdev[0:5]
		print "DEBUG: rootdev 5-7", rootdev[5:7]
		if rootdev[0:5] != "/dev/":
			ok = False
			allmsgs.append(["fatal","The grub-legacy extension cannot find a valid / or /boot entry in your /etc/fstab."])
			return [ ok, allmsgs ]
		if rootdev[5:7] != "sd":
			allmsgs.append(["warn","The grub-legacy encountered \"%s\", a non-\"sd\" device. Root setting may not be accurate." % rootdev])
		rootmaj = ord(rootdev[7]) - ord('a')
		try:
			rootmin = int(rootdev[8:]) - 1
		except TypeError:
			ok = False
			allmsgs.append(["fatal","The grub-legacy extension couldn't calculate the root minor for \"%s\"." % rootdev])
			return [ ok, allmsgs ]
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
			return [ ok, allmsgs ]
		
		if defpos != None:
			l += [ 
				""
				"default %s" % defpos
			]
	
		allmsgs.append(["info","Configuration file %s generated - %s lines." % ( self.fn, len(l))])
		allmsgs.append(["info","Kernel \"%s\" will be booted by default." % defname])

		return [ok, allmsgs, l]
			
