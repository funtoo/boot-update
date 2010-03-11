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
		self.fn = "/boot/grub-legacy/grub.conf"
		self.config = config
		self.bootitems = []

	def isAvailable(self):
		msgs=[]
		ok=True
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
		l.append("title %s" % myname )
		#self.PrepareGRUBForDevice(myroot,l)
		self.bootitems.append(myname)
		retval, mygrubroot = self.DeviceGRUB(myroot)
		l.append("root %s" % mygrubroot )
		if mytype == "win7":
			l.append("chainloader +4")
		elif mytype in [ "vista", "dos", "winxp" ]:
			l.append("chainloader +1")
		l.append("")
		return [ ok, msgs ]

	def Guppy(self,argstring,fatal=True):
		# grub-probe is from grub-1.97+ -- we use it here as well
		out=commands.getstatusoutput("/sbin/grub-probe "+argstring)
		if fatal and out[0] != 0:
			print "grub-probe "+argstring
			print out[1]
			sys.exit(1)
		else:
			return out

	def DeviceGRUB(self,dev):
		retval,out=self.Guppy(" --device %s --target=drive" % dev) 
		if retval == 0:
			# Convert GRUB "count from 1" (hdx,y) format to legacy "count from 0" format
			mys = out[1:-1].split(",")
			mys = ( mys[0], repr(int(mys[1]) - 1) )
			out = "(%s,%s)" % mys
		return retval,out

	def generateBootEntry(self,l,sect,kname,kext):
		global r

		ok=True
		allmsgs=[]

		label = r.GetBootEntryString( sect, kname )
		
		l.append("title %s" % label)
		self.bootitems.append(label)

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

		retval, mygrubroot = self.DeviceGRUB(rootdev)	
		# print out our grub-ified root setting
		l.append("root %s" % mygrubroot )
		l.append("kernel %s %s" % ( kpath," ".join(params) ))
		initrds=self.config.item(sect,"initrd")
		initrds=r.FindInitrds(initrds, kname, kext)
		for initrd in initrds:
			l.append("initrd %s" % r.RelativePathTo(initrd,"/boot"))
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

		ok, msgs, self.defpos, self.defname = r.GenerateSections(l,self.generateBootEntry, self.generateOtherBootEntry)
		allmsgs += msgs
		if not ok:
			return [ ok, allmsgs, l ]
		
		l += [ 
			""
			"default %s" % self.defpos
		]
	
		return [ok, allmsgs, l ]
			
