#!/usr/bin/python2.6

import commands

a=commands.getstatusoutput("lsmod | sed 1d")

deps={}

for line in a[1].split("\n"):
	ls = line.split()
	if len(ls)==4:
		deps[ls[0]] = [int(ls[2]), ls[3].split(",")]
	else:
		deps[ls[0]] = [int(ls[2]), []]

def is_driver(key):
	a = commands.getstatusoutput("find /lib/modules/*/kernel/drivers -iname %s.ko" % key)
	if a[1] == "":
		return False
	else:
		return True

def is_fs(key):
	a = commands.getstatusoutput("find /lib/modules/*/kernel/fs -iname %s.ko" % key)
	if a[1] == "":
		return False
	else:
		return True

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
		if is_fs(key) or is_driver(key):
			print key

