#!/usr/bin/python2.6

import sys
import commands
import fnmatch
import string

modlist = []
buckets = { "driver" : "kernel/drivers/*", "fs" : "kernel/fs/*", "sound" : "kernel/sound/*" }
modcat = {}

for cat in buckets.keys():
	modcat[cat] = []

a=commands.getstatusoutput("find /lib/modules/`uname -r` -iname *.ko")
for line in a[1].split("\n"):
	ls = line.split("/")
	subpath = "/".join(ls[4:])
	shortname = ls[-1][:-3].replace("_","-")
	modlist.append(ls)
	for modtype in buckets.keys():
		if fnmatch.fnmatch(subpath,buckets[modtype]):
			modcat[modtype].append(shortname)

a=commands.getstatusoutput("lsmod | sed 1d")

deps={}

for line in a[1].split("\n"):
	ls = line.split()
	key = ls[0].replace("_","-")
	if len(ls)==4:
		mydeps = ls[3].replace("_","-").split(",")
		deps[key] = [int(ls[2]), mydeps]
	else:
		deps[key] = [int(ls[2]), []]

def has_deps(key):
	num, deplist = deps[key]
	if num != 0 and deplist == []:
		return True
	elif num == 0 and deplist == []:
		return False
	elif num == 0 and deplist != []:
		#shouldn't happen
		raise
	elif num !=0 and deplist != []:
		# need to figure this out.
		if len(deplist) < num:
			# some additional dep beyond what is in our deplist
			return True
		elif len(deplist) > num:
			# should not happen
			raise
		elif len(deplist) == num:
			childdeps = map(has_deps,deplist)
			if True in childdeps:
				return True
			else:
				return False

for key in deps.keys():
	if has_deps(key):
		if key in modcat["fs"]  or key in modcat["driver"]:
			if key not in modcat["sound"]:
				print key

