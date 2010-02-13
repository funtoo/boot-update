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
		l.append("")
		l.append("title %s" % myname )
		#self.PrepareGRUBForDevice(myroot,l)
		self.bootitems.append(myname)
		retval, mygrubroot = self.DeviceGRUB(myroot)
		if mytype == "win7":
			l.append("	chainloader +4")
		elif mytype in [ "vista", "dos", "winxp" ]:
			l.append("	chainloader +1")
		l.append("")
		return [ ok, msgs ]

	def Guppy(self,argstring,fatal=True):
		out=commands.getstatusoutput("/sbin/grub-probe "+argstring)
		if fatal and out[0] != 0:
			print "grub-probe "+argstring
			print out[1]
			sys.exit(1)
		else:
			return out

	def DeviceGRUB(self,dev):
		retval,out=self.Guppy(" --device %s --target=drive" % dev) 
		return retval,out

	def generateBootEntry(self,l,sect,kname,kext):
		global r

		ok=True
		allmsgs=[]

		l.append("")
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
			"default %s" % defpos
		]
	
		return [ok, allmsgs, l ]
			
