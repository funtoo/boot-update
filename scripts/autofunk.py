#!/usr/bin/python2
# -*- coding: ascii -*-
import commands
import fnmatch

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
revdeps={}

for line in a[1].split("\n"):
	ls = line.split()
	if len(ls) < 3:
		continue
	key = ls[0].replace("_","-")
	if len(ls)==4:
		mydeps = ls[3].replace("_","-").split(",")
		if "[permanent]" in mydeps:
			mydeps.remove("[permanent]")
		deps[key] = [int(ls[2]), mydeps]

		# reverse deps - to get easy list of things that
		# depend on me.

		for dep in mydeps:
			if not revdeps.has_key(dep):
				revdeps[dep]=[]
			revdeps[dep].append(key)

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
		assert (False)
	elif num !=0 and deplist != []:
		# need to figure this out.
		if len(deplist) < num:
			# some additional dep beyond what is in our deplist
			return True
		elif len(deplist) > num:
			# should not happen
			assert (False)
		elif len(deplist) == num:
			childdeps = map(has_deps,deplist)
			if True in childdeps:
				return True
			else:
				return False

result_list=[]

for key in deps.keys():
	if has_deps(key):
		if key in modcat["fs"]  or key in modcat["driver"]:
			if key not in modcat["sound"]:
				result_list.append(key)

fs=[]
a=commands.getstatusoutput("cat /etc/fstab | grep -v ^#")
for line in a[1].split("\n"):
	split = line.split()
	if len(split) > 2:
		fs.append(split[2])
#eliminate duplicates
fs=set(fs)
for key in fs:
	if key in modcat["fs"]:
		result_list.append(key)

# result_list contains the modules we want to load_mappings, but now we want to get
# list of our result_list, plus *all the modules* needed by our result_list.
# this is recursive:

master_list=[]

def print_mod_and_revdeps(key):
	# print the module name plus any dependent modules (recursive)
	master_list.append(key)
	if revdeps.has_key(key):
		for dep in revdeps[key]:
			print_mod_and_revdeps(dep)

for mod in result_list:
	print_mod_and_revdeps(mod)

# remove duplicates:

master_list=set(master_list)

print "TODO: need to add USB auto-load_mappings or rely on initrd for that (for keyboard)"
out=""
for mod in master_list:
	out+="%s," % mod
print out[:-1]
