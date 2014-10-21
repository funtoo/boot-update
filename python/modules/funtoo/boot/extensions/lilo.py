# -*- coding: ascii -*-

import os

from subprocess import Popen
from subprocess import PIPE
from subprocess import STDOUT

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
		""" Runs lilo command to update the boot loader map """
		ok = True
		allmsgs = [[ "info", "Now running {lilo}" .format(lilo = self.lilo_cmd)]]

		cmdobj = Popen(self.lilo_cmd, bufsize=-1, stdout=PIPE,  stderr=STDOUT, shell=False)
		output = cmdobj.communicate()
		if cmdobj.poll() != 0:
			ok = False
			allmsgs.append(["fatal", "Error running {cmd} :\n{out}".format(cmd = self.lilo_cmd,  out = output[0].decode())])
			return [ok, allmsgs]
		else:
			allmsgs.append(["info",  "Successfully ran {cmd}. Output was :\n\n{out}\n".format(cmd = self.lilo_cmd, out = output[0].decode())])
			return [ok, allmsgs]

	def generateOtherBootEntry(self,l,sect):
		ok = True
		allmsgs = []

		# Name can not be longer than 15 characters
		if len(sect) > 15 :
			ok = False
			allmsgs.append(["fatal", "'{name}' is too long. Section names in /etc/boot.conf for non-linux OS must not exceed 15 characters when using lilo".format(name = sect)])
			return [ ok, allmsgs  ]

		self.bootitems.append(sect)
		params=self.config["{s}/params".format(s = sect)].split()
		myroot = self.r.GetParam(params,"root=")

		l.append("")
		l.append("other={dev}".format(dev = myroot))

		# Make sure we change any spaces in name to "_". Lilo doesn't like spaces.
		l.append("	label=\"{name}\"".format(name = sect.replace(" ", "_")))

		return [ ok, allmsgs  ]

	def generateBootEntry(self,l,sect,kname,kext):

		ok=True
		allmsgs=[]

		# Type 'xen' isn't supported in lilo
		if  self.config["{s}/type" .format(s = sect)] == "xen" :
			ok = False
			allmsgs.append([ "fatal", "Type 'xen' is not supported in lilo" ])
			return [ ok, allmsgs ]

                # 'Label' has a character limit, not kernel name.
		if len(os.path.basename(sect)) > 15:
			ok = False
			allmsgs.append(["fatal", "'{name}' is too long. Kernel names must not exceed 15 characters when using lilo".format(name =(os.path.basename(kname)))])
			return [ ok, allmsgs ]

		l.append("")
		self.bootitems.append(kname)
		l.append("image={k}".format(k = kname ))

		params=self.config.item(sect,"params").split()

		ok, allmsgs, myroot = self.r.DoRootAuto(params,ok,allmsgs)
		if not ok:
			return [ ok, allmsgs ]
		ok, allmsgs, myfstype = self.r.DoRootfstypeAuto(params,ok,allmsgs)
		if not ok:
			return [ ok, allmsgs ]

		self.r.ZapParam(params,"root=")

		l += [
                        "	label=\"{name}\"".format(name = sect.replace(" ", "_")),
			"	read-only",
			"	root={dev}".format(dev = myroot),
			"	append=\"{par}\"".format(par = " ".join(params))
		]
		initrds=self.config.item(sect,"initrd")
		initrds=self.r.FindInitrds(initrds, kname, kext)
		for initrd in initrds:
			l.append("  initrd={rd}".format(self.r.RelativePathTo(initrd,"/boot")))

		return [ ok, allmsgs ]

	def generateConfigFile(self):
		l=[]
		c=self.config
		ok=True
		allmsgs=[]

		# Warn if no boot entry.
		if c.hasItem("boot/bootdev"):
			l.append("boot={dev}".format(dev = c["boot/bootdev"]))
		else:
			allmsgs.append(["warn", "No 'bootdev' entry specified in section 'boot'. Lilo will install itself to the current root partition. See `man 5 boot.conf` for more info"])

		# Append global lilo params
		for gparam in c["lilo/gparams"].split() :
			l.append(gparam)

		# Pass our boot entry generator function to GenerateSections, and everything is taken care of for our boot entries

		ok, msgs, self.defpos, self.defname = self.r.GenerateSections(l,self.generateBootEntry, self.generateOtherBootEntry)
		allmsgs += msgs
		if not ok:
			return [ ok, allmsgs, l]

		# Lilo's config uses 1/10 secs.
		if c.hasItem("boot/timeout") :
			timeout = "timeout={time}".format(time = int(c["boot/timeout"]) * 10)
		else:
			timeout = ""

		#Global options need to come first
		l = [
			timeout,
			# Replace spaces with "_" in default name. Lilo doesn't like spaces
			"default=\"{name}\"" .format(name=self.defname.replace(" ", "_")),
		] + l

		allmsgs.append(["warn","Please note that LILO support is *BETA* quality and is for testing only."])

		return [ok, allmsgs, l]

