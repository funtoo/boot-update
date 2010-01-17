#!/usr/bin/python

BLUE="[34;01m"
CYAN="[36;01m"
CYANN="[36m"
GREEN="[32;01m"
RED="[31;01m"
PURP="[35;01m"
OFF="[0m"

qprint() {
    $quietopt || echo "$*" >&2
}

mesg() {
    qprint " ${GREEN}*${OFF} $*"
}

error() {
    echo " ${RED}* Error${OFF}: $*" >&2
    exit 1
}

warn() {
    echo " ${RED}* Warning${OFF}: $*" >&2
}

die() {
    [ -n "$1" ] && error "$*"
    qprint
    exit 1
}

versinfo() {
    qprint
    qprint " Copyright ${CYANN}2009-2010${OFF} Funtoo Technologies, LLC."
    qprint
    qprint """ This program is free software; you can redistribute and/or modify it under
 the terms of the GNU General Public License version 3 as published by the
 Free Software Foundation. Alternatively you may (at your option) use any
 other license that has been publicly approved for use with this program by
 Funtoo Technologies, LLC. (or its successors, if any.)"""
    qprint
}

has_fstab_entry() {
	[ -n "$(cat /etc/fstab | grep "^.*[[:space:]]$1[[:space:]]")" ]
}

is_mounted() {
	[ -n "$(cat /proc/mounts | grep "^.*[[:space:]]$1[[:space:]]")" ]
}


