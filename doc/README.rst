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

.. role:: change

**Funtoo Core Networking has been enabled in Funtoo stable (funtoo) and unstable (~funtoo) builds -- see** :change:`2009.2` **and emerge sys-apps/coreboot to use it.**

The Funtoo Core Boot Framework is currently in development (and masked in
Funtoo Portage,) but will soon be used in conjunction with GRUB 1.9x and other
boot loaders to become the recommended, official way to boot Funtoo Linux
systems, and configure Funtoo Linux systems for booting.

coreboot License
=================

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
- ``boot-update`` manages the process of mounting and unmounting ``/boot`` and generating boot-loader-specific configuration files 

In Funtoo Linux, the following additional changes have been made:

- GRUB's ``grub-mkconfig``  has been deprecated in favor of Funtoo's ``boot-update``.
- GRUB's ``grub-update``  has been deprecated in favor of Funtoo's ``boot-update``.
- GRUB's ``/etc/grub.d`` has been deprecated in favor of Funtoo Core Boot extensions stored in ``/usr/lib/python2.x/site-packages/funtoo/boot/extensions``.
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
settings for the menu sections.

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

There are four critical parameters that are used in menu and ``default`` sections --
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
device node. Then ``root=auto`` will changed to reflect this, so the actual
parameter passed to the kernel will be something like ``root=/dev/sda3`` In a
similar fashion, ``rootfstype=auto`` will be replaced with something like
``rootfstype=ext4``, with the filesystem type determined by the setting in
``/etc/fstab``.

Configuration Parameters by Section
===================================

``boot`` Section
----------------

``boot :: generate`` (R)
~~~~~~~~~~~~~~~~~~~~~~~~

Specifies the boot loader that coreboot should generate a configuration files
for, as well as the one that it should attempt to update, if necessary. This
setting should be a single string, set to one of ``grub``, ``grub-legacy``
or ``lilo``.

``boot :: timeout`` (O)
~~~~~~~~~~~~~~~~~~~~~~~

Specifies the boot loader timeout, in seconds.

``boot :: default`` (O)
~~~~~~~~~~~~~~~~~~~~~~~

Specifies the filename of the kernel to boot by default. This setting should
contain no path information, just the kernel image name. This kernel will be
used as the default boot option when there is no user input.

``display`` Section
-------------------

``display :: gfxmode`` (O)
~~~~~~~~~~~~~~~~~~~~~~~~~~

Specifies the video mode to be used by the boot loader's menus. This value is
also inherited and used as the video mode for the kernel when a graphical boot
(``uvesafb``, ``vesafb-tng``) is used. This option is only supported for
``grub``.

``color`` Section
-----------------

Currently, the color options are only supported for ``grub``.

``color :: normal`` (O)
~~~~~~~~~~~~~~~~~~~~~~~

Specifies the regular display colors in ``fg/bg`` format.

``color :: highlight`` (O)
~~~~~~~~~~~~~~~~~~~~~~~~~~

Specifies the menu highlight colors in ``fg/bg`` format.

``default`` and Specific Menu Sections
--------------------------------------

``default :: scan`` (R)
~~~~~~~~~~~~~~~~~~~~~~~

This setting specifies one or more directories to scan for kernels and 
initrds. Typically, this is set to ``/boot``.

``default :: kernels`` (R)
~~~~~~~~~~~~~~~~~~~~~~~~~~

This setting specifies kernel image name, names or patterns, to find kernels to
generate boot menu entries for. The path specified in the ``scan`` setting is
searched. Glob patterns are supported. The special pattern `[-v]` is used to
match an optional version suffix beginning with a ``-``, such as
``bzImage-2.6.24``. If more than one kernel image matches a pattern, or more
than one kernel image is specified, then more than one boot entry will be
created.

``default :: initrd`` (O)
~~~~~~~~~~~~~~~~~~~~~~~~~

This setting specifies initrd/initramfs image(s) to load with the menu entry.
If multiple initrds or initramfs images are specified, then *all* specified
images will be loaded for the boot entry. Linux supports multiple initramfs
images being specified at boot time. Glob patterns are supported. The special
pattern ``[-v]`` is used to find initrd/initramfs images that match the
``[-v]`` pattern of the current kernel.  For example, if the current menu
entry's kernel image had a ``[-v]`` pattern of ``-2.6.24``, then
``initramfs[-v]`` will match ``initramfs-2.6.24``. If the current menu entry
had a ``[-v]`` pattern, but it was blank (in the case of ``bzImage[-v]``
finding a kernel named ``bzImage``,) then ``initramfs[-v]`` will match
``initramfs``, if it exists.

``default :: params`` (O)
~~~~~~~~~~~~~~~~~~~~~~~~~

This setting specifies the parameters passed to the kernel. This option
appearing in the ``default`` section can be extended in specific menu 
sections by using the ``+=`` operator. The special parameters ``root=auto``
and ``rootfstype=auto`` are supported, which will be replaced with similar
settings with the ``auto`` string replaced with the respective setting from
``/etc/fstab``.

