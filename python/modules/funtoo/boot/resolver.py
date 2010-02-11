import os, glob
from helper import *

class Resolver:
	def __init__(self,config):
		self.config=config

	def GetMatchingKernels(self, scanpath, globlist, skip=[]):
		# find kernels in scanpath that match globs in globlist, and return them
		found=[]
		for pattern in globlist:
			base_glob = os.path.normpath(scanpath+"/"+pattern.replace("[-v]",""))
			wild_glob = os.path.normpath(scanpath+"/"+pattern.replace("[-v]","-*"))	
			for match in glob.glob(base_glob):
				if match not in skip and match not in found:
					# append the matching kernel, and "" representing that no [-v] extension was used
					found.append([match,""])
			if base_glob != wild_glob:
				for match in glob.glob(wild_glob):
					if match not in skip and match not in found:
						# append the matching kernel, and the literal [-v] extension that was found on this kernel
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
		if sect == "default" and self.config["default/name"] != "":
			osname = self.config["default/name"]
		else:
			osname = sect
		return "%s - %s" % ( osname, kname )

	def DoRootAuto(self,params,ok,allmsgs):
		if "root=auto" in params:
			params.remove("root=auto")
			rootdev = fstabGetRootDevice()
			if (rootdev[0:5] != "/dev/") and (rootdev[0:5] != "UUID=") and (rootdev[0:6] != "LABEL="):
				ok = False
				allmsgs.append(["fatal","(root=auto) - / entry in /etc/fstab not recognized (%s)." % rootdev])
				return [ ok, allmsgs, None ]
			params.append("root=%s" % rootdev )
			return [ ok, allmsgs, rootdev ]	
		else:
			for param in params:
				if param[0:5] == "root=":
					return [ ok, allmsgs, param[5:] ]
		allmsgs.append(["warn","(root=auto) - cannot find a root= setting in params."])
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

	def GenerateSections(self,l,sfunc,ofunc=None):
		c=self.config

		ok=True
		allmsgs=[]
	
		default = c["boot/default"]

		pos = 0
		defpos = None
		defnames = [] 

		linuxsections = []
		othersections = []

		for sect in c.getSections():
			if sect not in c.builtins:
				if c["%s/%s" % (sect, "type")] == "linux":
					linuxsections.append(sect)
				else:
					othersections.append(sect)
		
		# if we have no linux boot entries, use the "default" section as the only linux boot entry to look for kernels
		if len(linuxsections) == 0:
			linuxsections.append("default")

		for sect in linuxsections:	
			# Process boot entry section (which can generate multiple boot entries if multiple kernel matches are found)
			findlist, skiplist = c.flagItemList("%s/%s" % ( sect, "kernel" ))
			findmatch=[]

			for scanpath in c.item(sect,"scan").split():
				skipmatch = self.GetMatchingKernels(scanpath, skiplist)
				findmatch += self.GetMatchingKernels(scanpath, findlist, skipmatch)

			# Generate individual boot entry using extension-supplied function

			for kname, kext in findmatch:
				if (default == sect) or (default == os.path.basename(kname)):
					# default match
					if defpos != None:
						allmsgs.append(["warn","multiple matches found for default boot entry \"%s\" - first match used." % default])
					else:
						defpos = pos
				defnames.append(kname)
				ok, msgs = sfunc(l,sect,kname,kext)
				allmsgs += msgs
				if not ok:
					break
				pos += 1

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
