#!/usr/bin/python2

import os, sys

sys.path.append("python/modules")

import funtoo.boot.config
import funtoo.boot.extensions

c=funtoo.boot.config.BootConfigFile(fn="etc/boot.conf")

generate=c["boot/generate"]

if generate=="":
	print "boot/generate does not specify a valid boot loader to generate a config for."
	sys.exit(1)

if generate not in funtoo.boot.extensions.__all__:
	print "extension for boot loader %s (specified in boot/generate) not found."
	sys.exit(1)

# dynamically import the proper extension
extname="funtoo.boot.extensions.%s" % generate
__import__(extname)
extmodule=sys.modules[extname]

ext=extmodule.getExtension(c)

if not ext.isAvailable():
	print "extension %s does not have the required dependencies to run" % generate
	sys.exit(1)

for line in ext.generateConfigFile():
	print line
