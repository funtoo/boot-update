#!/bin/sh
#
#http://serverfault.com/questions/13991/howdo-i-tell-which-kernel-modules-are-required
#
for i in `find /sys/ -name modalias -exec cat {} \;`; do
	/sbin/modprobe --config /dev/null --show-depends $i ;
done | rev | cut -f 1 -d '/' | rev | sort -u
