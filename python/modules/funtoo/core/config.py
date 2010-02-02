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

import os, sys

class ConfigFile:
	def __init__(self,fname=None,existing=True):
		
		# we use self.sections as the master list of sections, with their contents in self.obj. It is up to this class
		# to keep self.sections and self.obj in sync. self.sections is used so that the ordering of the sections can be
		# preserved when we dump the data.

		self.orderedObjects = []
		self.templates = {}
		self.sectionData = {}
		self.sectionDataOrder = {}

		self.parent=None
		self.defaults=""
		
		self.existing=existing
		self.fname=fname

		if self.existing and self.fileExists():
			fn=open(self.fname,"r")
			self.read(fn.readlines())
			fn.close()
	
	def deburr(self,str, delim):
		str = str.strip().rstrip(delim).rstrip()
		if len(str) > 2 and str[0] == '"' and str[-1] == '"':
			return str[1:-1]
		else:
			return str

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
		for obj, name in self.orderedObjects:
			if obj == "section":
				lines.append("section %s {\n" % name )
				for var in self.sectionDataOrder[name]:
					lines.append("	%s %s\n" % ( var, self.sectionData[name][var]) )
				lines.append("}\n")
			elif obj == "template":
				for line in self.templates(name):
					lines.append(line)
			elif obj == "comment":
				lines.append(name)
		return lines

	def printDump(self):
		for line in self.dump():
			sys.stdout.write(line)

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

	"""
	self.orderedObjects =

	[ "section", "foo" ] 
	
	], [ "template", "bar" ] [ "comment", "# foasdflsdf asdl " ]

	self.templates = {}
	self.sectionData = { "foo" : { "bar": "alaksdf", "basl", "asdlkfds", }}
	self.sectionDataOrder = { "foo", [ "bar", "basl" ] }	



	"""


	def read(self,lines):
		ln=0
		while ln < len(lines):	
			if lines[ln].lstrip()[:1] == "#" or lines[ln].lstrip() == "":
				# comment or whitespace (which is treated as a comment)
				self.orderedObjects.append([ "comment", lines[ln] ])
				ln += 1
				continue
			elif lines[ln].rstrip()[-1:] == "{":
				# section start
				section = self.deburr(lines[ln], "{")
				if self.sectionData.has_key(section):
					# duplicate section - bad
					raise

				# Initialize internal section data store
				self.sectionData[section] = {}
				self.sectionDataOrder[section] = []
				
				ln += 1
				while ln < len(lines) and lines[ln].strip() != "}":
					# strip comments from variable line - these comments don't get preserved on dump()
					line = lines[ln][0:lines[ln].find("#")]
					ls = line.split()
					if len(ls) == 0:
						# empty line, skip
						ln += 1
						continue
					
					# at least we have a variable name
					
					varname = ls[0]
					vardata = " ".join(ls[1:])

					if varname == "{":
						# this is illegal
						raise

					if vardata == "":
						# a variable but no data
						raise

					# record our variable data
					self.sectionDataOrder[section].append(varname)
					self.sectionData[section][varname] = vardata

					ln += 1

				self.orderedObjects.append(["section", section])
				ln += 1

			elif lines[ln].rstrip()[-1:] == "[":
				template = self.deburr(lines[ln], "[")
				
				if self.templates.has_key(template):
					# bad - duplicate template
					raise
				
				ln += 1
				tdata = []
				while ln < len(lines) and lines[ln].strip() != "]":
					tdata.append(lines[ln])
					ln += 1
				
				self.templates[template] = tdata
				self.orderedObjects.append(["template", template ])
				ln += 1
			else:
				# no clue what this is
				raise 
		print "DEBUG: DUMP", self.printDump()
	
	# IMPLEMENT THIS:

	def hasTemplate(self,template):
		if self.parent:
			return self.parent.hasTemplate(template) or self.templates.has_key(template)
		else:
			return self.templates.has_key(template)

	def hasLocalTemplate(self,template):
		return self.templates.has_key(template)

	def hasItem(self,item):
		return self.item(item,varname=None,bool=True)

	def condSubItem(self,item,str):
		return self.subItem(item,str,cond=True)

	def flagItemList(self,item):
		# This method parses a variable line containing "foo bar -oni" into two sub-lists ([foo, bar], [oni])
		list=self.item(item).split()
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
		return self.sectionData.keys()

	def subItem(self,item,str,cond=False):

		# give this function "foo/bar" and "blah %s blah" and it will return "blah <value of foo/bar> blah"
		# if cond=True, then we will zap the line (return "") if str points to a null ("") value
		
		if cond and not self.item(item,varname=None):
			return ""
		else:
			return str % self.item(item,varname=None)

	def hasLocalItem(self,item):

		return self.item(item,varname=None,bool=True,parents=False)

	def __setitem__(self,key,value):

		# Need to throw exception if value already exists in parents?

		keysplit=key.split("/")
		section="/".join(keysplit[:-1])
		varname=keysplit[-1]

		if not self.sectionData.has_key(section):
			# initialize internal data store
			self.sectionData[section] = {}
			self.sectionDataOrder[section] = []
			# add to our ordered objects list so we output this section at the end when we dump()
			self.orderedObjects.append(["section", section])
		
		self.sectionData[section][varname] = value

	def __getitem__(self,item):
		return self.item(item,varname=None)

	def inherit(self,section):

		# Override this in the subclass.
		#
		# This allows customized inheritance behavior - given current
		# section of "section", what section does it inherit from? Return a
		# string name of section to inherit from, or None for no
		# inheritance. For example, /etc/boot.conf's "Foobar Linux"
		# section would inherit from the "default" section. Whereas some
		# other config file's "graphics" section may inherit from
		# "default/graphics".

		return None

	def template(self,section):
		# TODO: IMPLEMENT ME WITH INHERITANCE JUST LIKE self.item()
		return self.templates[section]

	def item(self,section,varname=None,bool=False,parents=True,defaults=True):

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
		if varname==None:
			keysplit=section.split("/")
			section="/".join(keysplit[:-1])
			varname=keysplit[-1]

		defsection=None
		if defaults:
			defsection=self.inherit(section)

		if self.sectionData.has_key(section) and self.sectionData[section].has_key(varname):
			if bool:
				return True
			elif self.sectionData.has_key(defsection) and self.sectionData[defsection].has_key(varname):
				# case 2: foo += bar -- append from default if it exists
				if (len(self.sectionData[section][varname].split()) >= 2) and (self.sectionData[section][varname].split()[0] == "+="):
					# real value appends to default value
					return self.sectionData[defsection][varname] + " " + self.sectionData[section][varname]
				else:
					# real value replaces default value
					return self.sectionData[section][varname]
			else:
				# only real value defined - return a COPY
				return self.sectionData[section][varname]
		elif defsection and self.sectionData.has_key(defsection) and self.sectionData[defsection].has_key(varname):
			if bool:
				return True
			else:
				# only default value defined
				return self.sectionData[defsection][varname]
		else:
			# no value defined
			if parents and self.parent:
				return self.parent.item(section,varname,bool=bool)
			elif bool:
				return False
			else:
				return ""

