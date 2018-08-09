# -*- coding: ascii -*-
""" The resolver provides various mechanisms for doing things automatically
that might be found in the configuration file. For example, it handles matching
the [-v] in a file path to the various files it can match. """

import glob
import os
from subprocess import PIPE
from subprocess import Popen
from subprocess import STDOUT
from subprocess import getstatusoutput, getoutput

from funtoo.boot.helper import fstabInfo

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
		if instr[wstart:wstop + 1] == "[-v]":
			return instr[0:wstart] + "-*" + instr[wstop + 1:]
		else:
			return instr[0:wstart] + instr[wstart + 1:wstop] + instr[wstop + 1:]
	else:
		return instr[0:wstart] + instr[wstop + 1:]


class Resolver:
	"""
	The resolver goes out and finds kernels and initrds. Then it is the job of the
	extension to generate the proper boot-loader-specific configuration file based
	on what the resolver found.
	"""
	
	def __init__(self, config, msgs):
		self.config = config
		self.mounted = {}
		self.fstabinfo = fstabInfo()
		# The following 4 variables are for use in generating sections:
		# a position counter -- if 0, we processed no kernels...
		self._pos = 0
		self._defpos = None
		self._defnames = []
		self._default, self._default_mode = self.config.get_default_boot_setting()
		self.rootarg = None
		self.intel_cpio = False
		self.is_intel = self.isIntel()
		if self.is_intel:
			if os.path.exists("/lib/firmware/intel-ucode"):
				self.intel_cpio = self.generateIntelInitramfs()
		self.msgs = msgs
		self.idmapper = self.config.idmapper
	
	def resolvedev(self, dev):
		if ((dev[0:5] == "UUID=") or (dev[0:6] == "LABEL=")):
			cmdobj = Popen(["/sbin/findfs", dev], bufsize=-1, stdout=PIPE, stderr=PIPE, shell=False)
			output = cmdobj.communicate()
			return output[0].decode()
		else:
			return dev
	
	def GetMatchingKernels(self, scanpath, globlist, skip=None):
		# find kernels in scanpath that match globs in globlist, and return them
		found = []
		if skip is None:
			skip = []
		for pattern in globlist:
			base_glob = os.path.normpath(scanpath + "/" + bracketzap(pattern, wild=False))
			wild_glob = os.path.normpath(scanpath + "/" + bracketzap(pattern, wild=True))
			for match in glob.glob(base_glob):
				if match not in skip and match not in found:
					if not os.path.exists(match):
						self.msgs.append(["warn", "Could not read file %s -- skipping" % match])
						continue
					# append the matching kernel, and "" representing that no
					# [-v] extension was used
					found.append([match, "", os.path.getmtime(match)])
			if base_glob != wild_glob:
				for match in glob.glob(wild_glob):
					if match not in skip and match not in found:
						if not os.path.exists(match):
							self.msgs.append(["warn", "Could not read file %s -- skipping" % match])
							continue
						# append the matching kernel, and the literal [-v]
						# extension that was found on this kernel
						found.append([match, match[len(scanpath) + 1 + pattern.find("["):], os.path.getmtime(match)])
		return found
	
	def isIntel(self):
		a = getoutput("/usr/bin/lscpu | grep ^Vendor")
		return a.endswith("GenuineIntel")
	
	def generateIntelInitramfs(self):
		s, o = getstatusoutput(
			"rm -f /boot/early_ucode.cpio; /usr/sbin/iucode_tool --write-earlyfw=/boot/early_ucode.cpio /lib/firmware/intel-ucode/* >/dev/null 2>&1")
		if s == 0:
			return self.StripMountPoint("/boot/early_ucode.cpio")
		return False
	
	def FindInitrds(self, initrds, kernel, kext):
		found = []
		base_path = os.path.dirname(kernel)
		if self.intel_cpio is not False:
			found.append(self.intel_cpio)
		for initrd in initrds.split():
			# Split up initrd at bracket and replace glob with kernel version string if brackets exists.
			head1, sep1, tail1 = initrd.rpartition("[")
			if sep1:
				head2, sep2, tail2 = tail1.partition("]")
				if sep2:
					initrd = os.path.normpath("{base_path}/{initrd}{kext}{iext}".format(base_path=base_path, initrd=head1, kext=kext, iext=tail2))
				else:
					# Shouldn't be here. just add original initrd value
					initrd = os.path.normpath("{base_path}/{initrd}".format(base_path=base_path, initrd=initrd))
			else:
				initrd = os.path.normpath("{base_path}/{initrd}".format(base_path=base_path, initrd=tail1))
			
			if os.path.exists(initrd):
				found.append(initrd)
		return found
	
	def GetBootEntryString(self, sect, kname):
		return "{s} - {k}".format(s=sect, k=os.path.basename(kname))
	
	single_flags = set(
		["async", "atime", "noatime", "auto", "noauto", "defaults", "rw", "ro", "suid", "nosuid", "dev", "nodev", "exec", "noexec", "nouser", "diratime",
		 "nodiratime", "dirsync", "group", "iversion", "noiversion", "mand", "nomand", "_netdev", "relatime", "norelatime", "strictatime", "nostrictatime",
		 "lazytime", "silent", "loud", "owner", "remount", "sync", "user", "nouser", "users", "user_xattr", "nouser_xattr"])
	arg_flags = ["context", "fscontext", "defcontext", "rootcontext"]
	
	def filterRootFlags(self, flags):
		# filter out non-fs-specific mount flags. These can cause the Linux kernel to choke on boot and should not appear on the
		# cmdline.
		new_flags = []
		for f in flags.split(','):
			if f in self.single_flags:
				continue
			else:
				for af in self.arg_flags:
					if f.startswith(af + "="):
						continue
			if f.startswith("x-"):
				continue
			new_flags.append(f)
		return ",".join(new_flags)
	
	def calculate_rootfs_for_section(self, params):
		""" Properly handle the root=auto and real_root=auto parameters in the boot.conf config file. This method also
		 modifies params, setting root= or real_root= appropriately. Self.rootarg gets set to either "root" or "real_root".
		 
		 Returns;
		 	boolean(success/fail),
		 	the actual root device string, or None if we could not determine it.
		"""
		ok = True
		doauto = False
		if "root=auto" in params:
			params.remove("root=auto")
			self.rootarg = "root"
			doauto = True
		if "real_root=auto" in params:
			params.remove("real_root=auto")
			self.rootarg = "real_root"
			doauto = True
		if doauto:
			rootdev = self.fstabinfo.getRootDevice()
			rootflags = self.fstabinfo.getRootMountFlags()
			# filter out ones that the kernel can't handle:
			rootflags = self.filterRootFlags(rootflags)
			if ((rootdev[0:5] != "/dev/") and (rootdev[0:5] != "UUID=")
					and (rootdev[0:6] != "LABEL=")):
				ok = False
				self.msgs.append(["fatal", "(root=auto) - / entry in /etc/fstab not recognized ({dev}).".format(dev=rootdev)])
			else:
				params.append("{arg}={dev}".format(arg=self.rootarg, dev=rootdev))
				if len(rootflags):
					params.append("{arg}flags={flags}".format(arg=self.rootarg, flags=rootflags))
			return ok, rootdev
		else:
			# nothing to do - but we'll generate a warning if there is no root
			# or real_root specified in params, and return the root dev.
			for param in params:
				if param[0:5] == "root=":
					return ok, param[5:]
				elif param[0:10] == "real_root=":
					return ok, param[10:]
			# if we got here, we didn't find a root or real_root
			self.msgs.append(["warn", "(root=auto) - cannot find a root= or real_root= setting in params."])
			return ok, None
	
	def ZapParam(self, params, param):
		pos = 0
		while pos < len(params):
			if params[pos][0:len(param)] == param:
				del params[pos]
				continue
			pos += 1
	
	def GetParam(self, params, param):
		pos = 0
		while pos < len(params):
			if params[pos][0:len(param)] == param:
				return params[pos][len(param):]
			pos += 1
		return None
	
	def calculate_filesystem_for_section(self, params):
		ok = True
		if "rootfstype=auto" in params:
			params.remove("rootfstype=auto")
			for item in params:
				if item.startswith("root=") or item.startswith("real_root="):
					myroot = item.split("root=")[1]
					fstype = self.fstabinfo.getFilesystemOfDevice(myroot)
					if fstype == "":
						ok = False
						self.msgs.append(["fatal", "(rootfstype=auto) - cannot find a valid / entry in /etc/fstab."])
						return [ok, self.msgs, None]
					params.append("rootfstype={fs}".format(fs=fstype))
					break
		else:
			for param in params:
				if param[0:11] == "rootfstype=":
					return ok, param[11:]
		return ok, None
	
	def GetMountPoint(self, scanpath):
		"""Searches through scanpath for a matching mountpoint in /etc/fstab"""
		mountpoint = scanpath
		
		# Avoids problems
		if os.path.isabs(mountpoint) == False:
			return None
		
		while True:
			if mountpoint == "/":
				break
			elif self.fstabinfo.hasEntry(mountpoint):
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
		
		if os.path.normpath(scanpath) == "/boot":
			# /boot mounting is handled via another process, so skip:
			return
		
		# we record things to a self.mounted list, which is used later to track when we personally mounted
		# something, so we can unmount it. If it's already mounted, we leave it mounted:
		mountpoint = self.GetMountPoint(scanpath)
		if mountpoint:
			if mountpoint in self.mounted:
				# already mounted, return
				return
			elif os.path.ismount(mountpoint):
				# mounted, but not in our list yet, so add, but don't unmount later:
				self.mounted[mountpoint] = False
				return
			else:
				# not mounted, and mountable, so we should mount it.
				cmdobj = Popen(["mount", mountpoint], bufsize=-1, stdout=PIPE, stderr=STDOUT, shell=False)
				output = cmdobj.communicate()
				if cmdobj.poll() != 0:
					self.msgs.append(["fatal", "Error mounting {mp}, Output was :\n{out}".format(mp=mountpoint, out=output[0].decode())])
					return
				else:
					self.mounted[mountpoint] = True
					return
		else:
			# No mountpoint, just return
			return
	
	def UnmountIfNecessary(self) -> None:
		for mountpoint, we_mounted in iter(self.mounted.items()):
			if we_mounted is False:
				continue
			else:
				cmdobj = Popen(["umount", mountpoint], bufsize=-1, stdout=PIPE, stderr=STDOUT, shell=False)
				output = cmdobj.communicate()
				if cmdobj.poll() != 0:
					self.msgs.append(["warn", "Error unmounting {mp}, Output was :\n{out}".format(mp=mountpoint, out=output[0].decode())])
	
	def _GenerateLinuxSection(self, l, sect, sfunc) -> bool:
		"""Generates section for Linux systems"""
		ok = True

		
		# Process a section, such as "genkernel" section.
		
		findlist, skiplist = self.config.flagItemList("{s}/kernel".format(s=sect))
		
		# findlist == special patterns to match (i.e. kernel[-v])
		# skiplist == patterns to skip.
		
		findmatch = []
		skipmatch = []
		
		scanpaths = self.config.item(sect, "scan").split()
		
		for scanpath in scanpaths:
			self.MountIfNecessary(scanpath)
			if len(skiplist):
				# find kernels to skip...
				matches = self.GetMatchingKernels(scanpath, skiplist)
				skipmatch += matches
			if len(findlist):
				# find kernels to match (skipping any kernels we should skip...)
				matches = self.GetMatchingKernels(scanpath, findlist, skipmatch)
				findmatch += matches
		
		# Generate individual boot entry using extension-supplied function
		
		found_multi = False
		
		# logic for finding a kernel to boot, based on default setting:
		# sort by modification time:
		findmatch = sorted(findmatch, key=lambda x: x[2], reverse=True)
		
		if self._default_mode == "autopick: mtime":
			# pick newest kernel by mtime, which happens to be top-of-list
			self._defpos = 0
			for kname, kext, mtime in findmatch:
				self._defnames.append(kname)
				ok = sfunc(l, sect, kname, kext)
				self._pos += 1

		else:
			def_mtime = None
			for kname, kext, mtime in findmatch:
				if (self._default == sect) or (self._default == kname) or (self._default == os.path.basename(kname)):
					# default match
					if self._defpos is not None:
						found_multi = True
						if mtime > def_mtime:
							# this kernel is newer, use it instead
							self._defpos = self._pos
							def_mtime = mtime
					else:
						self._defpos = self._pos
						def_mtime = os.stat(kname)[8]
				self._defnames.append(kname)
				ok = sfunc(l, sect, kname, kext)
				if not ok:
					break
				self._pos += 1
			
			if found_multi:
				self.msgs.append(["warn", "multiple matches found for default \"{name}\" - most recent used.".format(name=self._default)])

		return ok
	
	def _GenerateOtherSection(self, l, sect, ofunc) -> bool:
		"""Generate section for non-Linux systems"""
		
		ok = ofunc(l, sect)
		self._defnames.append(sect)
		if self._default == sect:
			if self._defpos is not None:
				self.msgs.append(["warn", "multiple matches found for default boot entry \"{name}\" - first match used.".format(name=self._default)])
			else:
				self._defpos = self._pos
		self._pos += 1
		return ok
	
	def GenerateSections(self, l, sfunc, ofunc=None) -> (bool, object, object):
		"""Generates sections using passed in extension-supplied functions"""
		
		ok = True
		
		try:
			timeout = int(self.config["boot/timeout"])
		except ValueError:
			ok = False
			self.msgs.append(["fatal", "Invalid value \"{t}\" for boot/timeout.".format(t=timeout)])
			return ok, None, None
		
		if timeout == 0:
			self.msgs.append(["warn", "boot/timeout value is zero - boot menu will not appear!"])
		elif timeout < 3:
			self.msgs.append(["norm", "boot/timeout value is below 3 seconds."])
		
		# Remove builtins from list of sections
		sections = self.config.getSections()
		for sect in sections[:]:
			if sect in self.config.builtins:
				sections.remove(sect)
		
		# If we have no boot entries, throw an error - force user to be
		# explicit.
		if len(sections) == 0:
			self.msgs.append(["fatal", "No boot entries are defined in /etc/boot.conf."])
			ok = False
			return ok, None, None
		
		# Warn if there are no linux entries
		has_linux = False
		for sect in sections:
			if self.config["{s}/{t}".format(s=sect, t="type")] == "linux":
				has_linux = True
				break
		if has_linux is False:
			self.msgs.append(["warn", "No Linux boot entries are defined. You may not be able to re-enter Linux."])
		
		# Generate sections
		for sect in sections:
			if self.config["{s}/type".format(s=sect)] in ["linux", "xen"]:
				ok = self._GenerateLinuxSection(l, sect, sfunc)
			elif ofunc:
				ok = self._GenerateOtherSection(l, sect, ofunc)
		
		if self._pos == 0:
			# this means we processed no kernels -- so we have nothing to boot!
			ok = False
			self.msgs.append(["fatal", "No matching kernels or boot entries found in /etc/boot.conf."])
			self._defpos = None
			return ok, self._defpos, None
		elif self._defpos is None:
			# this means we didn't pick a default kernel to boot!
			self.msgs.append(["warn", "Had difficulty finding a default kernel -- using first one. (report this error.)"])
			# If we didn't find a specified default, use the first one
			self._defpos = 0
		else:
			self.msgs.append(["note", "Default kernel selected via: %s." % self._default_mode])
		if self._default_mode == "autopick: mtime" and self.config.item("boot", "autopick") == "last":
				self.msgs.append(["warn", "Falling back to last modification time booting due to lack of last-booted info."])
		if self.is_intel:
			if not self.intel_cpio:
				self.msgs.append(["warn", "Intel system detected - please emerge sys-firmware/intel-microcode and sys-apps/iucode_tool and run boot-update again; boot-update will then patch your system with the latest Intel CPU and chipset microcode patches at boot-time, protecting you against important vulnerabilities and errata."])
			else:
				self.msgs.append(["note", "Intel microcode will be loaded at boot-time."])
		
		return ok, self._defpos, self._defnames[self._defpos]
	
	def RelativePathTo(self, imagepath, mountpath):
		# we expect /boot to be mounted if it is available when this is run
		if os.path.ismount("/boot"):
			return "/" + os.path.relpath(imagepath, mountpath)
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

# vim: ts=4 sw=4 noet
