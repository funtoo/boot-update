# -*- coding: ascii -*-
""" The resolver provides various mechanisms for doing things automatically
that might be found in the configuration file. For example, it handles matching
the [-v] in a file path to the various files it can match. """

import glob
import os

from subprocess import Popen
from subprocess import PIPE
from subprocess import STDOUT

from funtoo.boot.helper import fstabGetRootDevice
from funtoo.boot.helper import fstabGetFilesystemOfDevice
from funtoo.boot.helper import fstabHasEntry

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
	"""
	The resolver goes out and finds kernels and initrds. Then it is the job of the
	extension to generate the proper boot-loader-specific configuration file based
	on what the resolver found.
	"""

	def __init__(self, config):
		self.config = config
		self.mounted = {}

		# The following 4 variables are for use in generating sections.
		self._pos = 0
		self._defpos = None
		self._defnames = []
		self._default = self.config.deburr(self.config["boot/default"])
		self.rootarg = None

	def resolvedev(self, dev):
		if ((dev[0:5] == "UUID=") or (dev[0:6] == "LABEL=")):
			cmdobj = Popen(["/sbin/findfs", dev], bufsize = -1, stdout = PIPE, stderr = PIPE, shell = False)
			output = cmdobj.communicate()
			return output[0].decode()
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
						found.append([match,match[len(scanpath)+1+pattern.find("["):]])
		return found

	def FindInitrds(self,initrds,kernel,kext):
		found=[]
		base_path=os.path.dirname(kernel)
		for initrd in initrds.split():
			# Split up initrd at bracket and replace glob with kernel version string if brackets exists.
			head1, sep1, tail1 = initrd.rpartition("[")
			if sep1:
				head2, sep2, tail2 = tail1.partition("]")
				if sep2:
					initrd = os.path.normpath("{base_path}/{initrd}{kext}{iext}".format(base_path = base_path, initrd = head1, kext = kext, iext = tail2))
				else:
					#Shouldn't be here. just add original initrd value
					initrd = os.path.normpath("{base_path}/{initrd}".format(base_path = base_path, initrd = initrd)) 
			else:
				initrd=os.path.normpath("{base_path}/{initrd}".format(base_path = base_path, initrd = tail1))

			if os.path.exists(initrd):
				found.append(initrd)
		return found

	def GetBootEntryString(self,sect,kname):
		return "{s} - {k}".format(s = sect, k = os.path.basename(kname) )

	def DoRootAuto(self,params,ok,allmsgs):
		""" Properly handle the root=auto and real_root=auto parameters in the boot.conf config file """

		doauto=False
		if "root=auto" in params:
			params.remove("root=auto")
			self.rootarg="root"
			doauto=True
		if "real_root=auto" in params:
			params.remove("real_root=auto")
			self.rootarg="real_root"
			doauto=True
		if doauto:
			rootdev = fstabGetRootDevice()
			if ((rootdev[0:5] != "/dev/") and (rootdev[0:5] != "UUID=")
					and (rootdev[0:6] != "LABEL=")):
				ok = False
				allmsgs.append(["fatal","(root=auto) - / entry in /etc/fstab not recognized ({dev}).".format(dev = rootdev)])
			else:
				params.append("{arg}={dev}".format(arg = self.rootarg, dev = rootdev ))
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
				if item.startswith("root=") or item.startswith("real_root="):
					myroot=item.split("root=")[1]
					fstype = fstabGetFilesystemOfDevice(myroot)
					if fstype == "":
						ok = False
						allmsgs.append(["fatal","(rootfstype=auto) - cannot find a valid / entry in /etc/fstab."])
						return [ ok, allmsgs, None ]
					params.append("rootfstype={fs}".format(fs = fstype))
					break
		else:
			for param in params:
				if param[0:11] == "rootfstype=":
					return [ ok, allmsgs, param[11:] ]
		return [ ok, allmsgs, None ]

	def GetMountPoint(self, scanpath):
		"""Searches through scanpath for a matching mountpoint in /etc/fstab"""
		mountpoint = scanpath

		# Avoids problems
		if os.path.isabs(mountpoint) == False:
			return None

		while True:
			if mountpoint == "/":
				break
			elif  fstabHasEntry(mountpoint):
				return mountpoint
			else:
				# If we made it here, strip off last dir and try again
				mountpoint = os.path.dirname(mountpoint)

		# If here, no entry in fstab. Let's try searching for it
		mountpoint = scanpath
		while True:
			if mountpoint == "/":
				return None
			elif os.path.ismount(mountpoint):
				return mountpoint
			else:
				# If we made it here, strip off last dir and try again
				mountpoint = os.path.dirname(mountpoint)

	def MountIfNecessary(self, scanpath):
		mesgs = []

		if os.path.normpath(scanpath) == "/boot":
			# /boot mounting is handled via another process, so skip:
			return mesgs

		# we record things to a self.mounted list, which is used later to track when we personally mounted
		# something, so we can unmount it. If it's already mounted, we leave it mounted:
		mountpoint = self.GetMountPoint(scanpath)
		if mountpoint:
			if mountpoint in self.mounted:
				# already mounted, return
				return mesgs
			elif os.path.ismount(mountpoint):
				# mounted, but not in our list yet, so add, but don't unmount later:
				self.mounted[mountpoint] = False
				return mesgs
			else:
				# not mounted, and mountable, so we should mount it.
				cmdobj = Popen(["mount",  mountpoint], bufsize = -1, stdout = PIPE, stderr = STDOUT, shell = False)
				output = cmdobj.communicate()
				if cmdobj.poll() != 0:
					mesgs.append(["fatal", "Error mounting {mp}, Output was :\n{out}".format(mp = mountpoint, out = output[0].decode())])
					return mesgs
				else:
					self.mounted[mountpoint] = True
					return mesgs
		else:
			# No mountpoint, just return mesgs
			return mesgs


	def UnmountIfNecessary(self):
		mesgs = []
		for mountpoint, we_mounted in iter(self.mounted.items()):
			if we_mounted == False:
				continue
			else:
				cmdobj = Popen(["umount", mountpoint], bufsize = -1, stdout = PIPE, stderr = STDOUT, shell = False)
				output = cmdobj.communicate()
				if cmdobj.poll() != 0:
					mesgs.append(["warn", "Error unmounting {mp}, Output was :\n{out}".format(mp = mountpoint, out = output[0].decode())])
		return mesgs

	def _GenerateLinuxSection(self, l, sect, sfunc):
		"""Generates section for Linux systems"""
		ok = True
		allmsgs = []
		def_mtime = None

		# Process boot entry section (which can generate multiple boot
		# entries if multiple kernel matches are found)
		findlist, skiplist = self.config.flagItemList("{s}/kernel".format(s = sect))
		findmatch=[]

		scanpaths = self.config.item(sect,"scan").split()

		for scanpath in scanpaths:
			mesgs = self.MountIfNecessary(scanpath)
			allmsgs += mesgs
			skipmatch = self.GetMatchingKernels(scanpath, skiplist)
			findmatch += self.GetMatchingKernels(scanpath, findlist, skipmatch)

		# Generate individual boot entry using extension-supplied function

		found_multi = False

		for kname, kext in findmatch:
			if (self._default == sect) or (self._default == os.path.basename(kname)):
				# default match
				if self._defpos != None:
					found_multi = True
					curtime = os.stat(kname)[8]
					if curtime > def_mtime:
						# this kernel is newer, use it instead
						self._defpos = self._pos
						def_mtime = curtime
				else:
					self._defpos = self._pos
					def_mtime = os.stat(kname)[8]
			self._defnames.append(kname)
			ok, msgs = sfunc(l,sect,kname,kext)
			allmsgs += msgs
			if not ok:
				break
			self._pos += 1

		if found_multi:
			allmsgs.append(["warn", "multiple matches found for default \"{name}\" - most recent used.".format(name = self._default)])

		return [ok, allmsgs]

	def _GenerateOtherSection(self, l, sect, ofunc):
		"""Generate section for non-Linux systems"""

		allmsgs = []

		ok, msgs = ofunc(l,sect)
		allmsgs += msgs
		self._defnames.append(sect)
		if self._default == sect:
			if self._defpos != None:
				allmsgs.append(["warn", "multiple matches found for default boot entry \"{name}\" - first match used.".format(name = self._default)])
			else:
				self._defpos = self._pos
		self._pos += 1
		return [ ok, allmsgs]

	def GenerateSections(self, l, sfunc, ofunc = None):
		"""Generates sections using passed in extension-supplied functions"""

		ok=True
		allmsgs=[]

		try:
			timeout = int(self.config["boot/timeout"])
		except ValueError:
			ok = False
			allmsgs.append(["fatal","Invalid value \"{t}\" for boot/timeout.".format(t = timeout)])
			return [ ok, allmsgs, None, None ]

		if timeout == 0:
			allmsgs.append(["warn","boot/timeout value is zero - boot menu will not appear!"])
		elif timeout < 3:
			allmsgs.append(["norm","boot/timeout value is below 3 seconds."])

		# Remove builtins from list of sections
		sections = self.config.getSections()
		for sect in sections[:]:
			if sect in self.config.builtins:
				sections.remove(sect)

		# If we have no boot entries, throw an error - force user to be
		# explicit.
		if len(sections) == 0:
			allmsgs.append(["fatal","No boot entries are defined in /etc/boot.conf."])
			ok=False
			return[ ok, allmsgs, None, None ]

		# Warn if there are no linux entries
		has_linux = False
		for sect in sections:
			if self.config["{s}/{t}" .format(s = sect, t = "type")] == "linux":
				has_linux = True
				break
		if has_linux == False:
			allmsgs.append(["warn","No Linux boot entries are defined. You may not be able to re-enter Linux."])

		# Generate sections
		for sect in sections:
			if self.config["{s}/type" .format(s = sect)] == "linux" or self.config["{s}/type" .format(s = sect)] == "xen":
				ok,  msgs = self. _GenerateLinuxSection(l, sect, sfunc)
			elif ofunc:
				ok, msgs = self._GenerateOtherSection(l, sect, ofunc)

			allmsgs += msgs

		if self._pos == 0:
			ok = False
			allmsgs.append(["fatal","No matching kernels or boot entries found in /etc/boot.conf."])
			self._defpos = None
			return [ ok, allmsgs, self._defpos, None ]
		elif self._defpos == None:
			allmsgs.append(["warn","No boot/default match found - using first boot entry by default."])
			# If we didn't find a specified default, use the first one
			self._defpos = 0

		return [ ok, allmsgs, self._defpos, self._defnames[self._defpos] ]

	def RelativePathTo(self,imagepath,mountpath):
		# we expect /boot to be mounted if it is available when this is run
		if os.path.ismount("/boot"):
			return "/"+os.path.relpath(imagepath,mountpath)
		else:
			return os.path.normpath(imagepath)

	def StripMountPoint(self, scanpath):
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
			# No mount point, just return scanpath
			return scanpath
