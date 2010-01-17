class ConfigFile:
	def __init__(self,fname):
		fn=open(fname,"r")
		ln=0
		self.obj={}
		self.builtins=["boot", "display", "default", "altboot", "color" ]
		section=None
		for line in fn.readlines():
			ln += 1
			ls=line.split()
			if len(ls) == 0:
				continue
			if section == None:
				if ls[-1] == "{":
					section = deburr(" ".join(ls[:-1]))
					self.obj[section] = {}
					continue
				else:
					# bogus data outside of section
					raise 
			else:
				if ls[-1] == "{":
					# invalid nested section
					raise
				elif ls[0] == "}":
					section = None
					continue
				# valid data in section
				self.obj[section][ls[0]]=ls[1:]
		fn.close()

	def literals(self):
		# returns all literals, which are non-builtin blocks like "Funtoo Linux" { foo bar }
		keyl=[]
		for keyw in self.obj.keys():
			if keyw not in self.builtins:
				keyl.append(keyw)
		return keyl

	def has_item_split(self,cat,name):
		return len(self.item(cat,name)) != 0

	def has_item(self,key):
		return len(self.item(key)) != 0

	def item_split(self,cat,name):
		return self.itemlist(cat,name).join(" ")

	def item(self,key):
		return self.itemlist(key).join(" ")

	def itemlist_split(self,cat,name):
		if cat in self.literals():
			# this means we are dealing with a literal section like "Funtoo Linux", and we
			# should inherit default settings from the default section
			if not self.obj[cat].has_key(name):
				# case 1 -- value not defined in literal section, use default:
				if self.obj["default"].has_key(name):
					return self.obj["default"][name]
			elif (len(self.obj[cat][name]) >= 2) and (self.obj[cat][name][0] == "+="):
				# case 2: foo += bar -- append from default if it exists
				if self.obj["default"].has_key(name):
					return self.obj["default"][name] + self.obj[cat][name][1:]
	
		# case 3: otherwise, no default value, no append ("+="), just return our defined value

		if self.obj.has_key(cat):
			# not a literal - no special treatment
			if self.obj[cat].has_key(name):
				return self.obj[cat][name]
		return ""

	def itemlist(self,key):
		cat, name = key.split("/")
		return self.itemlist_split(cat,name)
