# -*- coding: ascii; tab-width: 4; indent-tabs-mode: nil -*-
""" The resolver provides various mechanisms for doing things automatically
that might be found in the configuration file. For example, it handles matching
the [-v] in a file path to the various files it can match. """

import os, glob, commands
from helper import fstabGetRootDevice, fstabGetFilesystemOfDevice, fstabHasEntry

def bracketzap(instr, wild=True):
	""" Removes various bracket types from the input string. """
	wstart = instr.find("[")
	if wstart == -1:
		return instr
	wstop = instr.rfind("]")
	if wstop == -1:
		return instr
	if wstart > wstop:
		return instr
	if wild:
		if instr[wstart:wstop+1] == "[-v]":
			return instr[0:wstart]+"-*"+instr[wstop+1:]
		else:
			return instr[0:wstart]+instr[wstart+1:wstop]+instr[wstop+1:]
	else:
		return instr[0:wstart]+instr[wstop+1:]

class Resolver:

	# The resolver goes out and finds kernels and initrds. Then it is the job of the
	# extension to generate the proper boot-loader-specific configuration file based
	# on what the resolver found.

	def __init__(self, config):
		self.config = config
		self.mounted = {}

	def resolvedev(self, dev):
		if ((dev[0:5] == "UUID=") or (dev[0:6] == "LABEL=")):
			out = commands.getstatusoutput("/sbin/findfs " + dev)
			return out[1]
		else:
			return dev

	def GetMatchingKernels(self, scanpath, globlist, skip=[]):
		# find kernels in scanpath that match globs in globlist, and return them
		found=[]
		for pattern in globlist:
			#base_glob = os.path.normpath(scanpath+"/"+ pattern.replace("[-v]",""))
			base_glob = os.path.normpath(scanpath+"/"+ bracketzap(pattern,wild=False))
			#wild_glob = os.path.normpath(scanpath+"/"+ pattern.replace("[-v]","-*"))
			wild_glob = os.path.normpath(scanpath+"/"+ bracketzap(pattern,wild=True))
			for match in glob.glob(base_glob):
				if match not in skip and match not in found:
					# append the matching kernel, and "" representing that no
					# [-v] extension was used
					found.append([match,""])
			if base_glob != wild_glob:
				for match in glob.glob(wild_glob):
					if match not in skip and match not in found:
						# append the matching kernel, and the literal [-v]
						# extension that was found on this kernel
						found.append([match,match[len(wild_glob)-2:]])
		return found

	def FindInitrds(self,initrds,kernel,kext):
		found=[]
		base_path=os.path.dirname(kernel)
		for initrd in initrds.split():
			initrd=os.path.normpath(base_path+"/"+initrd.replace("[-v]",kext))
			if os.path.exists(initrd):
				found.append(initrd)
		return found

	def GetBootEntryString(self,sect,kname):
		return "%s - %s" % ( sect, os.path.basename(kname) )

	def DoRootAuto(self,params,ok,allmsgs):

		# properly handle the root=auto and real_root=auto parameters in the boot.conf config file:

		rootarg=None
		doauto=False
		if "root=auto" in params:
			params.remove("root=auto")
			rootarg="root"
			doauto=True
		if "real_root=auto" in params:
			params.remove("real_root=auto")
			rootarg="real_root"
			doauto=True
		if doauto:
			rootdev = fstabGetRootDevice()
			if ((rootdev[0:5] != "/dev/") and (rootdev[0:5] != "UUID=")
					and (rootdev[0:6] != "LABEL=")):
				ok = False
				allmsgs.append(["fatal","(root=auto) - / entry in /etc/fstab not recognized (%s)." % rootdev])
			else:
				params.append("%s=%s" % ( rootarg, rootdev ))
			return [ ok, allmsgs, rootdev ]
		else:
			# nothing to do - but we'll generate a warning if there is no root
			# or real_root specified in params, and return the root dev.
			for param in params:
				if (param[0:5] == "root="):
					return [ ok, allmsgs, param[5:] ]
				elif (param[0:10] == "real_root="):
					return [ ok, allmsgs, param[10:] ]
			# if we got here, we didn't find a root or real_root
			allmsgs.append(["warn","(root=auto) - cannot find a root= or real_root= setting in params."])
			return [ ok, allmsgs, None ]

	def ZapParam(self,params,param):
		pos = 0
		while pos < len(params):
			if params[pos][0:len(param)] == param:
				del params[pos]
				continue
			pos += 1

	def GetParam(self,params,param):
		pos = 0
		while pos < len(params):
			if params[pos][0:len(param)] == param:
				return params[pos][len(param):]
			pos += 1
		return None

	def DoRootfstypeAuto(self,params,ok,allmsgs):
		if "rootfstype=auto" in params:
			params.remove("rootfstype=auto")
			for item in params:
				if item[0:5] == "root=":
					myroot=item[5:]
					fstype = fstabGetFilesystemOfDevice(myroot)
					if fstype == "":
						ok = False
						allmsgs.append(["fatal","(rootfstype=auto) - cannot find a valid / entry in /etc/fstab."])
						return [ ok, allmsgs, None ]
					params.append("rootfstype=%s" % fstype)
					break
		else:
			for param in params:
				if param[0:11] == "rootfstype=":
					return [ ok, allmsgs, param[11:] ]
		return [ ok, allmsgs, None ]

	def GetMountPoint(self,  scanpath):
		"""Searches through scanpath for a matching mountpoint in /etc/fstab"""
		mountpoint = scanpath

		# Avoids problems
		if os.path.isabs(scanpath) == False:
			return None

		while True:
			if mountpoint == "/":
				return None
			elif  fstabHasEntry(mountpoint):
				return mountpoint
			else:
				# If we made it here, strip off last dir and try again
				mountpoint = os.path.dirname(mountpoint)

	def MountIfNecessary(self,scanpath):
		mesgs = []

		if os.path.normpath(scanpath) == "/boot":
			# /boot mounting is handled via another process, so skip:
			return mesgs

		# we record things to a self.mounted list, which is used later to track when we personally mounted
		# something, so we can unmount it. If it's already mounted, we leave it mounted:
		mountpoint = self.GetMountPoint(scanpath)
		if mountpoint in self.mounted:
			# already mounted, return
			return mesgs
		elif os.path.ismount(mountpoint):
			# mounted, but not in our list yet, so add, but don't unmount later:
			self.mounted[mountpoint] = {"unmount" : False}
			return mesgs
		else:
			# not mounted, and mountable, so we should mount it.
			out = commands.getstatusoutput("mount {mp}".format(mp = mountpoint))
			if out[0] != 0:
				mesgs.append(["fatal", "Error mounting {mp}".format(mp = mountpoint)])
				return mesgs
			else:
				self.mounted[mountpoint] = {"mount" : True}
				return mesgs

	def UnmountIfNecessary(self):
		mesgs = []
		for mountpoint, unmount in self.mounted.iteritems():
			if unmount == False:
				continue
			else:
				out = commands.getstatusoutput("umount {mp}".format(mp = mountpoint))
				if out[0] != 0:
					mesgs.append(["fatal", "Error unmounting {mp}".format(mp = mountpoint)])
		return mesgs

	def GenerateSections(self,l,sfunc,ofunc=None):
		c=self.config

		ok=True
		allmsgs=[]

		default = c.deburr(c["boot/default"])

		pos = 0
		defpos = None
		def_mtime = None
		defnames = []

		linuxsections = []
		othersections = []

		try:
			timeout = int(c["boot/timeout"])
		except ValueError:
			ok = False
			allmsgs.append(["fatal","Invalid value \"%s\" for boot/timeout."
							% timeout])
			return [ ok, allmsgs, None, None ]

		if timeout == 0:
			allmsgs.append(["warn","boot/timeout value is zero - boot menu will not appear!"])
		elif timeout < 3:
			allmsgs.append(["norm","boot/timeout value is below 3 seconds."])

		for sect in c.getSections():
			if sect not in c.builtins:
				if c["%s/%s" % (sect, "type")] == "linux":
					linuxsections.append(sect)
				else:
					othersections.append(sect)

		# if we have no linux boot entries, throw an error - force user to be
		# explicit.
		if len(linuxsections) + len(othersections) == 0:
			allmsgs.append(["fatal","No boot entries are defined in /etc/boot.conf."])
			ok=False
			return[ ok, allmsgs, None, None ]
		if len(linuxsections) == 0:
			allmsgs.append(["warn","No Linux boot entries are defined. You may not be able to re-enter Linux."])

		for sect in linuxsections:
			# Process boot entry section (which can generate multiple boot
			# entries if multiple kernel matches are found)
			findlist, skiplist = c.flagItemList("%s/%s" % ( sect, "kernel" ))
			findmatch=[]

			scanpaths = c.item(sect,"scan").split()


			for scanpath in scanpaths:
				mesgs = self.MountIfNecessary(scanpath)
				allmsgs += mesgs
				skipmatch = self.GetMatchingKernels(scanpath, skiplist)
				findmatch += self.GetMatchingKernels(scanpath, findlist, skipmatch)

			# Generate individual boot entry using extension-supplied function

			found_multi = False

			for kname, kext in findmatch:
				if (default == sect) or (default == os.path.basename(kname)):
					# default match
					if defpos != None:
						found_multi = True
						curtime = os.stat(kname)[8]
						if curtime > def_mtime:
							# this kernel is newer, use it instead
							defpos = pos
							def_mtime = curtime
					else:
						defpos = pos
						def_mtime = os.stat(kname)[8]
				defnames.append(kname)
				ok, msgs = sfunc(l,sect,kname,kext)
				allmsgs += msgs
				if not ok:
					break
				pos += 1

			if found_multi:
				allmsgs.append(["warn","multiple matches found for default \"%s\" - most recent used." % default])

		if ofunc:
			for sect in othersections:
				ok, msgs = ofunc(l,sect)
				allmsgs += msgs
				defnames.append(sect)
				if default == sect:
					if defpos != None:
						allmsgs.append(["warn","multiple matches found for default boot entry \"%s\" - first match used." % default])
					else:
						defpos = pos
				pos += 1
				if not ok:
					return [ ok, allmsgs, defpos, None ]

		if pos == 0:
			ok = False
			allmsgs.append(["fatal","No matching kernels or boot entries found in /etc/boot.conf."])
			defpos = None
			return [ ok, allmsgs, defpos, None ]
		elif defpos == None:
			allmsgs.append(["warn","No boot/default match found - using first boot entry by default."])
			# If we didn't find a specified default, use the first one
			defpos = 0
		return [ ok, allmsgs, defpos, defnames[defpos] ]

	def RelativePathTo(self,imagepath,mountpath):
		# we expect /boot to be mounted if it is available when this is run
		if os.path.ismount("/boot"):
			return "/"+os.path.relpath(imagepath,mountpath)
		else:
			return os.path.normpath(imagepath)

	def StripMountPoint(self,  scanpath):
		"""Strips mount point from scanpath"""

		mountpoint = self.GetMountPoint(scanpath)

		if mountpoint:
			split_path = scanpath.split(mountpoint, 1)
			if len(split_path) != 2:
				# TODO Handle error better
				# Couldn't strip mount point, just return original scanpath
				return scanpath
			else:
				return os.path.normpath(split_path[1])
		else:
			# No mount point, just return kname
			return scanpath
