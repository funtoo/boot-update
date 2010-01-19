#!/usr/bin/env python

from distutils.core import setup

setup(name='coreboot',
	version='1.0',
	description='Funtoo Core Boot Framework',
	author='Daniel Robbins',
	author_email='drobbins@funtoo.org',
	url='http://www.funtoo.org/en/funtoo/core/boot',
	package_dir = { '':'python/modules' },
	packages=[ 
		'funtoo',
		'funtoo.core',
		'funtoo.boot',
		'funtoo.boot.extensions'
	]
)

