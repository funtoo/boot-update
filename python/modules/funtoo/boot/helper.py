# -*- coding: ascii -*-

def fstabHasEntry(fs):
	fn=open("/etc/fstab","r")
	for line in fn.readlines():
		line = line[0:line.find("#")]
		split=line.split()
		if (len(split) != 6):
			continue
		if split[1] == fs:
			return True
	return False

def fstabGetFilesystemOfDevice(dev):
	fn=open("/etc/fstab","r")
	for line in fn.readlines():
		line = line[0:line.find("#")]
		split=line.split()
		if (len(split) != 6):
			continue
		if split[0] == dev:
			return split[2]
	return ""

def fstabGetDeviceOfFilesystem(fs):
	fn=open("/etc/fstab","r")
	for line in fn.readlines():
		line = line[0:line.find("#")]
		split=line.split()
		if (len(split) != 6):
			continue
		if split[1] == fs:
			return split[0]
	return ""


def fstabGetRootDevice():
	fn=open("/etc/fstab","r")
	for line in fn.readlines():
		line = line[0:line.find("#")]
		split=line.split()
		if (len(split) != 6):
			continue
		if split[1] == "/":
			return split[0]
	return ""


