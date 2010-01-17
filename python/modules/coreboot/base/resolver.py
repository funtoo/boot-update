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

	def ParseAddSubtractLine(self,sect,var):
		# This method parses a variable line containing "foo bar -oni" into two sub-lists ([foo, bar], [oni])
		list=self.config.item(sect,var)
		grab=[]
		skip=[]
		# put "foo" entries in grab, whereas "-bar" go in skip:
		for item in list:
			if item[0]=="-":
				skip.append(item[1:])
			else:
				grab.append(item)
		return ( grab, skip )	

	def FindKernelsInSection(self,sect):
		kgrab, kskip = self.ParseAddSubtractLine(sect,"kernel")
		found=[]
		for scanpath in self.config.item(sect,"scan"):
			# get a list of kernels to skip, and to use. getScanMatches() will discount anything found previously in skip_matches
			skip_matches=self.GetMatchingKernels(scanpath,kskip)
			found += self.GetMatchingKernels(scanpath,kgrab,skip_matches)
		return found	

	def FindKernels(self):
		sections = self.config.literals()
		found = []
		if len(sections) == 0:
			# if no literal sections are defined (ie "Funtoo Linux",) just use the "default" section to add kernels
			process = [ "default" ]
		for sect in sections:
			found.append([sect, self.FindKernelsInSection(sect)])
		return found

	def FindInitrds(self,sect,kernel,kext):
		found=[]
		base_path=os.path.dirname(kernel)
		for initrd in self.config.item(sect,"initrd"):
			initrd=os.path.normpath(base_path+"/"+initrd.replace("[-v]",kext))
			if os.path.exists(initrd):
				found.append(initrd)
		return found

	def RelativePathTo(self,imagepath,mountpath):
		# we expect /boot to be mounted if it is available when this is run
		if os.path.ismount("/boot"):
			return "/"+os.path.relpath(imagepath,mountpath)
		else:
			return os.path.normpath(imagepath)
