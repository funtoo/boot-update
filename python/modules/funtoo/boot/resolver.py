import os, glob

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

	def FindInitrds(self,sect,kernel,kext):
		found=[]
		base_path=os.path.dirname(kernel)
		for initrd in sect:
			initrd=os.path.normpath(base_path+"/"+initrd.replace("[-v]",kext))
			if os.path.exists(initrd):
				found.append(initrd)
		return found

	def GenerateSections(self,l,sfunc):
		c=self.config
		bootsections=[]

		ok=True
		allmsgs=[]
	
		default = c["boot/default"]
		pos = 0
		defpos = None
		defnames = [] 

		for sect in c.getSections():
			if sect not in c.builtins:
				bootsections.append(sect)

		for sect in bootsections:	
			# Process boot entry section (which can generate multiple boot entries if multiple kernel matches are found)
			findlist, skiplist = c.flagItemList("%s/%s" % ( sect, "kernel" ))
			findmatch=[]

			for scanpath in c.item(sect,"scan"):
				skipmatch = self.GetMatchingKernels(scanpath, skiplist)
				findmatch += self.GetMatchingKernels(scanpath, findlist, skipmatch)

			# Generate individual boot entry using extension-supplied function

			for kname, kext in findmatch:
				if default == os.path.basename(kname):
					# default match
					if defpos != None:
						allmsgs.append(["warn","multiple matches found for default boot entry \"%s\" - first match used." % default])
					defpos = pos

				defnames.append(kname)
				ok, msgs = sfunc(l,sect,kname,kext)
				allmsgs += msgs
				if not ok:
					return [ ok, allmsgs, defpos, defnames[defpos] ]
				pos += 1
			
		if pos == 0:
			ok = False
			allmsgs.append(["fatal","No matching kernels or boot entries found in /etc/boot.conf."])

		if defpos == None:
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
