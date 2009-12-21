==========================
Funtoo Core Boot Framework
==========================

:keywords: boot, grub, funtoo, gentoo
:description: 

        This page contains information about the Funtoo Core Boot Framework software.

:author: Daniel Robbins
:contact: drobbins@funtoo.org
:copyright: funtoo
:language: English

Introduction
============

The Funtoo Core Boot Framework is currently in development, but will soon be
used in conjunction with GRUB 1.9x and other boot loaders to become the
recommended, official way to boot Funtoo Linux systems, and configure Funtoo
Linux systems for booting.

.. _Funtoo Core Boot Framework: http://www.funtoo.org/archive/grub/grub-1.97-funtoo.tar.bz2

These Funtoo Core Boot Framework can be found in the `Funtoo Core Boot
Framework`_ source tarball. 

License
=======

The Funtoo Core Boot Framework consists of independently-developed source code
that is released under its own distinct licensing terms.

The Funtoo Core Boot Framework is distributed under the following terms:

**Copyright 2009-2010 Funtoo Technologies, LLC.**

**This program is free software; you can redistribute and/or modify it under
the terms of the GNU General Public License version 3 as published by the
Free Software Foundation. Alternatively you may (at your option) use any
other license that has been publicly approved for use with this program by
Funtoo Technologies, LLC. (or its successors, if any.)**

At this time (December 2009), no other licenses other than the default license
(GNU GPL version 3) have been approved by Funtoo Technologies, LLC for use with
this program.

What's included?
================

The Funtoo Core Boot Framework contains the following pieces of software:

- ``/etc/boot.conf`` is the configuration meta-file for all boot loaders
- ``boot-update`` manages the process of mounting and unmounting ``/boot`` and calling ``boot-mkconfig``
- ``boot-mkconfig`` uses the Funtoo Core Boot Framework template system to generate boot loader config file(s)
- ``/usr/share/boot/plugins`` contains various Python-based plugins for different boot loaders
- ``/usr/share/boot/templates`` contains templates for generating config files for various boot loaders.

In Funtoo Linux, the following additional changes have been made:

- GRUB's ``grub-mkconfig``  has been deprecated in favor of Funtoo's ``boot-mkconfig``.
- GRUB's ``grub-update``  has been deprecated in favor of Funtoo's ``boot-update``.
- GRUB's ``/etc/grub.d`` has been deprecated in favor of Funtoo's ``/usr/share/boot/templates/grub``.
- GRUB's ``/etc/default/grub`` has been deprecated in favor of Funtoo's ``/etc/boot.conf``.

``/etc/boot.conf``
==================

In Funtoo Linux, ``/etc/boot.conf`` is intended to serve as the master
configuration meta-file for all boot loaders. The data in ``/etc/boot.conf`` is
used by the Funtoo Core Boot Framework to generate specific configuration files
for various boot loaders as necessary.

The benefit of ``/etc/boot.conf`` is that it provides a single location to
store all boot-related information. It also provides a single, consistent file
format and feature set for configuring all boot loaders.

Thanks to ``boot-update``, there is also a consistent process for updating boot
loader information, regardless of the actual boot loader used.

Here is a sample ``/etc/boot.conf`` configuration file::

        boot {
                generate grub
                timeout 10
                default bzImage
        }

        display {
                gfxmode 1024x768
        }

        color {	
                normal cyan/blue
                highlight blue/cyan
        }

        default {
                scan /boot
                kernel bzImage[-v] kernel[-v] vmlinuz[-v] vmlinux[-v]
                initrd initramfs[-v]

                # root=auto will cause the parameter for the root= option to be grabbed
                # from your /etc/fstab. rootfstype= works in much the same way.

                params root=auto rootfstype=auto
        }

        "Funtoo Linux" {
                kernel bzImage
        }

        "Funtoo Linux uvesafb" { 

                # To enable uvesafb, you will need to emerge uvesafb, add
                # /usr/share/v86d/initramfs to your CONFIG_INITRAMFS_SOURCE for your
                # kernel, and then recompile your kernel, and copy your new kernel to
                # /boot/bzImage-uvesafb (or change the name below.)

                params += video=uvesafb:1024x768-8,mtrr:2,ypan

                # (note: ",mtrr:2" is supported by most video cards and signficantly
                # improves terminal scrolling performance)

                kernel bzImage-uvesafb
        }

Sections are specified by an alphanumeric name, followed by a space and a ``{``.
A section ends when a single ``}`` appears on a line.

There are special "builtin" sections that are expected to be found by the
framework and used for configuation settings, such as ``boot``, ``display`` and
``color``. In addition, other sections can be created -- these sections are
treated as boot loader menu definitions.  For example, the sections ``"Funtoo
Linux"`` and ``"Funtoo Linux uvesafb"`` -- or sections with any other
non-builtin names -- are understood by the framework to contain information for
generating boot loader menu items rather than boot loader configuration
settings. These sections will be referred to as "menu" sections.

There is a special section named ``default`` which is used to specify default
settings for the menu sections. Some users may simply use the settings defined
in ``default`` and not require any menu sections to be defined, because ``default``
will be processed to generate boot menus if no menu sections are found.

Default menu settings
---------------------

If a setting is defined in the ``default`` section but not in a specific menu
section, then the specific menu section inherits the setting from the
``default`` section. A specific menu setting can also *extend* a default
setting by using the ``+=`` operator. When ``+=`` is used, the specific menu
setting will consist of the default setting plus the additional parameters
specified after the ``+=``. For example, the ``params`` setting for ``"Funtoo
Linux uvesafb"`` above is ``root=auto rootfstype=auto
video=uvesafb:1024x768-8,mtrr:2,ypan``.

Menu Sections
-------------

There are four critical parameters that are used in menu sections --
``kernel``, ``initrd``, ``params`` and ``scan``. ``scan`` specifies a path
where the framework should look for kernels and initrds, and should generally
be set to ``/boot`` on Gentoo Linux and Funtoo Linux installations. ``kernel``
specifies one or more kernels, using exact names or wildcards, and a menu item
*will be generated for each menu item found*. ``initrd`` specifies one or more
initrds or initramfs images using exact names or wildcards. All matching
initrds will be added to each generated menu entry, since Linux supports
multiple initramfs images. Finally, ``params`` specifies kernel parameters used
to boot the kernel.

Special Parameters
------------------

There are two special parameters that can be specified in the ``params``
setting, ``root=auto`` and ``rootfstype=auto``. When ``root=auto`` is
encountered, the framework will look at ``/etc/fstab`` to determine the root
device node, such as ``root=/dev/sda3``, and this parameter will replace the
original ``root=auto`` parameter when generating menu entries. In a similar
fashion, ``rootfstype=auto`` will be replaced with something like
``rootfstype=ext4``, with the filesystem type determined by the setting in
``/etc/fstab``.

Using Funtoo GRUB
=================

Unlike legacy GRUB, the new GRUB 1.9x auto-generates your GRUB boot menu for
you, which is stored in ``/boot/grub/grub.cfg``. For this to work, simply copy
your kernel to ``/boot``, along with any initrd/initramfs image, and then run
``grub-update`` to have GRUB auto-generate a boot menu for you. ``grub-update``
will generate output that will show you what your GRUB boot menu will look like
at boot-time and will also handle mounting ``/boot``, if required:

.. figure:: grub-update.png 
   :alt: grub-update shows how GRUB boot menu will appear

By default, ``grub-update`` will find kernels named ``bzImage``, ``kernel`` and
``vmlinux`` with an optional version extension that begins with a hyphen, such
as ``bzImage-2.6.31-gentoo``. If a version extension is found, ``grub-update``
will use this extension to find an optional matching initramfs image named
``initramfs-<extension>`` in the same directory as the kernel.  If a kernel
with no extension is found, then ``grub-update`` will look for an initramfs
image named ``initramfs`` in the same directory as the kernel.

These defaults, as well as many other options, can be changed as detailed
below.

Funtoo GRUB Default Settings 
============================

The Funtoo GRUB default settings are located in ``/etc/conf.d/grub``, and have
been *extensively* overhauled from upstream GRUB. This means that the most
common configuration settings have *different names and functions* from
upstream GRUB, and have been redesigned to be more powerful and easier to use.
Here are the defaults as they appear in ``/etc/conf.d/grub`` in Funtoo Linux::

        GRUB_TIMEOUT=10
        GRUB_FEATURES="altboot osprobe"
        GRUB_DEFAULT="/boot/bzImage"
        GRUB_KERNEL_PARAMS=""

        GRUB_LABEL="[OS] - [KF] [ALT]"
        GRUB_LABEL_OS="Funtoo Linux"

        GRUB_SCAN_DIR="/boot"
        GRUB_SCAN_KERNELS="bzImage[-v] kernel[-v] vmlinux[-v]"
        GRUB_SCAN_INITRD="initramfs[-v]"

        GRUB_ALTBOOT_PARAMS="init=/bin/bash"

GRUB_TIMEOUT
------------

``GRUB_TIMEOUT`` sets the boot timeout, in seconds.

GRUB_FEATURES
-------------

``GRUB_FEATURES`` defines what GRUB features are enabled. ``altboot`` enables
the "alternate boot" option functionality (see ``GRUB_ALTBOOT_PARAMS``, below.)
``osprobe`` tells GRUB to also probe for other operating systems when
constructing the GRUB boot menu. ``uuid`` (disabled by default) tells GRUB to
pass a ``root=UUID=<UUID>`` boot parameter to the kernel when an associated
initrd/initramfs is found. This parameter is used by ``Debian`` and ``Ubuntu``
initramfs images.

GRUB_DEFAULT
------------

``GRUB_DEFAULT`` specifies the path to the kernel in ``/boot`` that GRUB will
attempt to boot by default. Upstream GRUB uses an identically-named setting
that specifies an integer, rather than a path to a kernel. I chose to support
only a path to a kernel as it's more intuitive.

GRUB_KERNEL_PARAMS
------------------

``GRUB_KERNEL_PARAMS`` is used to specify any additional parameters that you
would like to pass to the kernel at boot.

GRUB_LABEL
----------

``GRUB_LABEL`` specifies a template for how GRUB text menu entries should be
displayed. The ``[OS]`` string is replaced with the value of the ``GRUB_LABEL_OS`` setting.
``[KF]`` is replaced with the full path to the kernel, and ``[KV]`` is replaced
with any extension found after the kernel name (such as ``2.4.30-gentoo``,) if any.
The ``[ALT]`` string is replaced with "alternate boot" parameters when generating
the alternate menu entry. For the primary menu entry, ``[ALT]`` is replaced with
an empty string.

GRUB_LABEL_OS
-------------

``GRUB_LABEL_OS`` specifies the name of the currently-runing operating system when
generating the GRUB boot menu.

GRUB_SCAN_DIR
-------------

``GRUB_SCAN_DIR`` specifies a space-separated list of directories to search for
kernels and initramfs images. Currently, only ``/boot`` or subdirectories of
``/boot`` are supported by the Funtoo GRUB extensions.

GRUB_SCAN_KERNELS
-----------------

``GRUB_SCAN_KERNELS`` specifies a space-separated list of patterns to use when
GRUB scans for kernels to include in the boot menu. The pattern ``bzImage[-v]``
will match both ``bzImage`` and ``bzImage-*``. In the latter case, the portion
of the kernel name matching ``[-v]`` will be used to find a matching
initrd/initramfs image.

GRUB_SCAN_INITRD
----------------

``GRUB_SCAN_INITRD`` defines a single pattern that will be used to find a
matching initrd/initramfs image in the same directory as each found kernel.
The ``[-v]`` pattern will be replaced with the ``[-v]`` pattern found
in the kernel name.

GRUB_ALTBOOT_PARAMS
-------------------

If ``altboot`` is specified in ``GRUB_FEATURES``, then GRUB will attempt to
generate an "alternate boot" menu for each found kernel. This alternate boot
menu item will be identical to the primary boot option, except that this boot
option will contain the kernel boot parameters defined in
``GRUB_ALTBOOT_PARAMS``.  This is generally used to allow easy booting into
single-user mode or into a rescue shell from the GRUB boot menu.

Upstream GRUB Settings
----------------------

The following settings are available and are used in the same way as in 
upstream GRUB:

- ``GRUB_TIMEOUT``
- ``GRUB_HIDDEN_TIMEOUT``
- ``GRUB_HIDDEN_TIMEOUT_QUIET``
- ``GRUB_TERMINAL_INPUT``
- ``GRUB_TERMINAL_OUTPUT``
- ``GRUB_SERIAL_COMMAND``
- ``GRUB_GFXMODE``

