#!/usr/bin/python2

# STATE OF THE CODE: 
#
# The template code is not fully implemented, and parts that need implementation are marked below.
# The Exceptions need to be implemented, search for all "raise" to see where.
# Right now, templates are defined using "[ ]" and config items are defined using "{ }", and the code will treat them as two separate namespaces.
# dump() will not currently include templates in its output. So the template stuff is very preliminary.
# There are incomplete changes to the template stuff when I realized that we should throw an exception for duplicate config items, and a template like this
# would cause problems:
# template {
#		I am a dog.
#		I love you.
# }
#
# That is why I am moving to [ ] for templates, so the parser knows that it is handling a template, which means it can throw or warnings for dup config items,
# but not throw exceptions or warnings when a template has matching first words.
#
# The latest implementation of self.item() is pretty nice, but needs testing.
# self.haskey has been renamed to hasItem() for consistency.
# deburr (helper function) has moved to self.deburr() (helper method)
#
# Right now, the section handling code is in flux. I have started adding some code to use self.sections to record an ordered list of sections in the file.
# This allows self.dump() to dump the contents of the file with the sections in the expected order. Without this, sections are dumped in random order which
# is not ideal.
# But we have another issue right now which is that self.dump() will provide the contents of the file but all comments will be stripped. This may or may not
# be ideal, but clearly there should be a way to dump/write the file with all original comments intact. So this part of the code is incomplete, but the code
# is good enough for simply reading in the config data.

import os

class ConfigFile:
	def __init__(self,fname=None,existing=True):
		
		# we use self.sections as the master list of sections, with their contents in self.obj. It is up to this class
		# to keep self.sections and self.obj in sync. self.sections is used so that the ordering of the sections can be
		# preserved when we dump the data.

		self.sections=[]
		self.obj={}
		self.templates={}
		self.parent=None
		self.defaults=""
		self.existing=existing
		self.fname=fname
		# orderedSections gives us an in-order list of all sections and templates in the config file, allowing us to
		# write the sections out (ie. dump() it) in an order that the user is expecting.
		self.orderedSections=[]

		if self.existing and self.fileExists():
			fn=open(self.fname,"r")
			self.read(fn.readlines())
			fn.close()
	
	def deburr(self,str):
		# Helper method - remove " " from around a string
		if str[0] != '"':
			return str
		elif str[0] == '"' and str[-1] == '"':
			return str[1:-1]
		else:
			# failed deburr - FIXME with real exception
			print "UNEXPECTED DEBURR", str
			raise

	def fileExists(self):
		if not self.fname:
			return False
		if not os.path.exists(self.fname):
			return False
		return True

	def setParent(self,parent):

		# The "parent" is currently a static setting that you would override in __init__() in
		# the subclass. It specifies a ConfigFile object that is the logical "parent" of the
		# current config file. The way this works in variable resolution is as follows. If
		# we are looking for variable "foo/bar" in the current config file, and it is not defined,
		# we will first call self.inherit() to see if a default value should be inherited from
		# another section in *this* ConfigFile object (see self.inherit, below.) If self.inherit()
		# returns None, or it returns a category name that has not been defined in this ConfigFile
		# object (like let's say it returns "oni" but there is no "oni/bar" defined), then we
		# take a look at self.parent to determine if there is a logical parent to this ConfigFile
		# object. If so, and the requested original variable exists in that ConfigFile object,
		# then we return the value from the parent ConfigFile object.

		# Note that ConfigFile objects can be chained using the self.parent setting.
		# Also note that self.dump() will only dump the contents of the current ConfigFile object,
		# and will not accumulate any data that is stored in any parents.

		self.parent=parent

	def dump(self):
		lines=[]

		# FIXME: we need a way to exclude any default settings that were provided, if they are the same.
		
		for section in self.obj.keys():
			lines.append("%s {\n" % section)
			for line in self.obj[section].keys():
				lines.append("	%s %s\n" % (line, " ".join(self.obj[section][line])))
			lines.append("}\n")
			lines.append("\n")
		return lines

	def write(self):
		base=os.path.dirname(self.fname)
		if not os.path.exists(base):
			os.makedirs(base)
		newf=open("%s.new" % self.fname,"w")
		for line in self.dump():
			newf.write(line)
		newf.close()
		if os.path.exists(self.fname):
			os.unlink(self.fname)
		os.rename("%s.new" % self.fname, self.fname)

	def readFromLines(self,lines):
		self.read(lines.split("\n"))

	def read(self,lines):
		section=None
		template=False
		ln=0
		for line in lines:
			ln += 1
			ls=line.split()
			if len(ls) == 0:
				continue
			if section == None:
				if ls[-1] == "{":
					section = self.deburr(" ".join(ls[:-1]))
					self.orderedSections.append(section)
					self.obj[section] = {}
					template=False
					continue
				elif ls[-1] == "[":
					section = self.deburr(" ".join(ls[:-1]))
					self.orderedSections.append(section)
					self.templates[section] = []		
					template=True
					continue
				else:
					print "UNEXPECTED", ls
					# bogus data outside of section - Throw real exception here
					raise 
			else:
				if ls[-1] == "{":
					# invalid nested section
					raise
				elif ls[-1] == "[":
					# invalid nested template
					raise
				elif ls[0] in [ "}", "]" ]:
					section = None
					continue
				# valid data in section
				if not template:
					# skip the line if there was a "#" first.
					if ls[0] == "#":
						continue
					# remove any comments that appear on the line
					myline=" ".join(ls[1:])
					compos=myline.find("#")
					if compos != -1:
						myline=myline[0:compos]
					myline=myline.split()
					self.obj[section][ls[0]]=myline
				else:
					if len(line) > 0 and line[0] == "	":
						# remove initial tab in template
						self.templates[section].append(line[1:])
					else:
						self.templates[section].append(line)

	# IMPLEMENT THIS:

	def hasTemplate(self,template):
		# TODO: Implement me
		pass

	def hasLocalTemplate(self,template):
		# TODO: Implement me
		pass

	def hasItem(self,item):
		return self.item(item,name=None,bool=True)

	def condSubItem(self,item,str):
		return self.subItem(item,str,cond=True)

	def flagItemList(self,item):
		# This method parses a variable line containing "foo bar -oni" into two sub-lists ([foo, bar], [oni])
		list=self.item(item)
		grab=[]
		skip=[]
		# put "foo" entries in grab, whereas "-bar" go in skip:
		for item in list:
			if item[0]=="-":
				skip.append(item[1:])
			else:
				grab.append(item)
		return ( grab, skip )	

	def getSections(self):
		# might want to add ability to see only local sections, vs. parent sections too.
		return self.obj.keys()

	def subItem(self,item,str,cond=False):

		# give this function "foo/bar" and "blah %s blah" and it will return "blah <value of foo/bar> blah"
		# if cond=True, then we will zap the line (return "") if str points to a null ("") value
		
		if cond and not self.item(item,name=None):
			return ""
		else:
			return str % " ".join(self.item(item,name=None))

	def hasLocalItem(self,item):

		return self.item(item,name=None,bool=True,parents=False)

	def __setitem__(self,key,value):

		# Need to throw exception if value already exists in parents?

		keysplit=key.split("/")
		cat="/".join(keysplit[:-1])
		name=keysplit[-1]

		if not self.obj.has_key(cat):
			self.obj[cat]={}
			self.orderedSections.append(cat)
		self.obj[cat][name]=value.split(" ")

	def __getitem__(self,item):
		return " ".join(self.item(item,name=None))

	def inherit(self,cat):

		# Override this in the subclass.
		#
		# This allows customized inheritance behavior - given current
		# category of cat, what category does it inherit from? Return a
		# string name of category to inherit from, or None for no
		# inheritance. For example, /etc/boot.conf's "Foobar Linux"
		# sectio would inherit from the "default" section. Whereas some
		# other config file's "graphics" section may inherit from
		# "default/graphics".

		return None

	def template(self,section):
		# TODO: IMPLEMENT ME WITH INHERITANCE JUST LIKE self.item()
		return self.templates[section]

	def item(self,cat,name=None,bool=False,parents=True,defaults=True):

		# This is the master function for returning the value of a
		# ConfigFile item, and also to get a boolean value of whether a
		# ConfigFile item exists. It has a number of parameters which
		# control its behavior, defined below:

		# If bool=True, we return a True/False value depending on whether the object exists.
		# If bool=False, we return the actual config file value. False is the default.

		# If parents=True, we look at parents. It is true by default.
		# If parents=False, we ignore any parents for both boolean and actual value calculations.

		# If defaults=True, we look at any default sections in the file that are defined via self.inherit() when retrieving values. Default.
		# If defaults=False, we ignore any default sections defined via self.inherit(). 

		# if name==None, then cat/name are autogenerated from the value in cat, which is expected to be "foo/bar"
		if name==None:
			keysplit=cat.split("/")
			cat="/".join(keysplit[:-1])
			name=keysplit[-1]

		defcat=None
		if defaults:
			defcat=self.inherit(cat)

		# this means we are dealing with a literal section like "Funtoo Linux", and we
		# should inherit default settings from the default section
		
		if self.obj.has_key(cat) and self.obj[cat].has_key(name):
			if bool:
				return True
			elif self.obj.has_key(defcat) and self.obj[defcat].has_key(name):
				# case 2: foo += bar -- append from default if it exists
				if (len(self.obj[cat][name]) >= 2) and (self.obj[cat][name][0] == "+="):
					# real value appends to default value
					return self.obj[defcat][name] + self.obj[cat][name][1:]
				else:
					# real value replaces default value - return a COPY
					return self.obj[cat][name][:]
			else:
				# only real value defined - return a COPY
				return self.obj[cat][name][:]
		elif defcat and self.obj.has_key(defcat) and self.obj[defcat].has_key(name):
			if bool:
				return True
			else:
				# only default value defined - return a COPY so we can make changes without messing up later queries
				return self.obj[defcat][name][:]
		else:
			# no value defined
			if parents and self.parent:
				return self.parent.item(cat,name,bool=bool)
			elif bool:
				return False
			else:
				return ""

