=========
boot.conf
=========

---------------------------------------------
Funtoo global boot loader configuration file
---------------------------------------------

:Author: Daniel Robbins <drobbins@funtoo.org>
:Version: 1.4
:Manual section: 5
:Manual group: Funtoo Linux Core System

SYNOPSIS
--------

  */etc/boot.conf*

DESCRIPTION
-----------

In Funtoo Linux, ``/etc/boot.conf`` is intended to serve as the master
configuration meta-file for all boot loaders. The data in ``/etc/boot.conf`` is
used by the Funtoo Core Boot Framework to generate specific configuration files
for various boot loaders as necessary.

The benefit of ``/etc/boot.conf`` is that it provides a single location to
store all boot-related information. It also provides a single, consistent file
format and feature set for configuring all boot loaders.

Thanks to *boot-update(8)*, there is also a consistent process for updating
boot loader information, regardless of the actual boot loader used.

Here is a sample ``/etc/boot.conf`` configuration file:

.. include:: ../etc/boot.conf.example
   :literal:

Sections
~~~~~~~~

Sections are specified by an alphanumeric name, followed by a space and a *{*.
A section ends when a single *}* appears on a line.

There are special *built-in* sections that are expected to be found by the
framework and used for configuation settings, such as *boot*, *display* and
*color*. 

In addition, other sections can be created. Any sections with non-builtin names
are recognized as boot entry definitions. For example, the sections *"Funtoo
Linux"* and *"Funtoo Linux genkernel"* define boot entries. Due to
``/etc/boot.conf``'s wildcard support, a single boot entry section in the
configuration file may generate multiple actual boot entries for the boot
loader, depending on how many matches are found. Wildcard support will be
explained later in this document.

Default Section
~~~~~~~~~~~~~~~

In additiona, thereis a special section named *default* which is used to
specify default settings for the boot sections. *boot-update* has several
reasonable default built-in settings that can be overridden. For example, if
you leave out the *boot/timeout* setting, the boot menu timeout will default to
5 seconds. To see all built-in settings, type *boot-update --showdefaults*.

Linux Boot Entries
~~~~~~~~~~~~~~~~~~

There are four critical parameters that are used in boot entry and *default*
sections -- *type*, *kernel*, *initrd* and *params*. *type* defaults
to "linux" and informs *boot-update* that we are specifying a Linux boot
entry.  It can be set to other values to tell *boot-update* that we are
specifying a Microsoft Windows 7 boot entry, for example.

Linux Kernel Wildcards
~~~~~~~~~~~~~~~~~~~~~~

The *kernel* variable specifies one or more kernels, using exact kernel file
names or wildcards. Again, note that it is possible for one boot entry in
``/etc/boot.conf`` to generate *multiple* boot entries for your boot loader if
wildcards are used or multiple kernels are listed -- one boot entry will be
generated for each matching kernel found. 

So, for example, the following
``/etc/boot.conf`` could generate two boot entries named "Funtoo Linux -
bzImage" and "Funtoo Linux - bzImage-new"::

        "Funtoo Linux" {
                kernel bzImage bzImage-new
        }

The *[-v]* wildcard can be used at the end of a kernel image name to match the
base name, or any combination of the base name, plus a hypen and any additional
text::

        "Funtoo Linux" {
                kernel bzImage[-v]
        }

Above, *bzImage[-v]* will match *bzImage* as well as *bzImage-**.

In addition, *boot.conf* now supports the inclusion of arbitrary glob wildcards
within brackets, which work similarly to *[-v]*, above::

        "Funtoo Linux" {
                kernel bzImage[-2.6*]
        }

The above wildcard will match "bzImage", "bzImage-2.6.18", and "bzImage-2.6.24".

initrd/initramfs
~~~~~~~~~~~~~~~~

The *initrd* variable specifies one or more initrds or initramfs images.  Since Linux
supports multiple initramfs images, you can specify more than one initrd.
Multiple initrd or initramfs images won't result in extra boot entries like
with the *kernel* option; instead, both images will be loaded in succession at
boot time.

*initrd* also allows the use of the *[-v]* wildcard to allow you to create
matching pairs of kernels and initrds. Here's how it works -- assume you have
the following boot entry::

        "Funtoo Linux" {
                kernel bzImage[-v]
                initrd initramfs[-v]
        }

The ``/etc/boot.conf`` entry above will look for all kernels matching *bzImage*
and *bzImage-** and generate a boot entry for each one. For the boot entry for
*bzImage*, the *initramfs[-v]* wildcard will pull in the initramfs *initramfs*
if it exists -- otherwise the initramfs will be silently excluded. For the boot
entry for *bzImage-2.6.24*, the initramfs *initramfs-2.6.24* will be used if it
exists.

If you are using the enhanced glob wildcard functionality in your *kernel*
option (such as *bzImage[-2.6*]*, above), then remember that you should still
use *[-v]* in your *initrd* option. *[-v]* is the only pattern that is supported
for initrds.

Parameters
~~~~~~~~~~

The *params* variable specifies kernel parameters used to boot the kernel. Typical
kernel parameters, such as *init=/bin/bash*, *root=/dev/sda3* or others can
be specified as necessary. 

If a setting is not defined in the boot entry section but *is* defined
in the *defaults* section, then the boot entry section inherits
the setting from the *default* section. A specific menu setting can also
*extend* a default setting by using the *+=* operator as the first parameter.

The default *params*, if not specified, the default setting of *root=auto
rootfstype=auto* is used -- these are special parameters that will be explained
in the following section.

When *+=* is used as the first argument for *params*, the default setting can
be *extended* with additional parameters.  For example, the *params* setting
for *"Funtoo Linux uvesafb"* above is *root=auto rootfstype=auto
video=uvesafb:1024x768-8,mtrr:2,ypan*.

Special Parameters
~~~~~~~~~~~~~~~~~~

**root=auto**

  When *root=auto* is evaluated, the framework will look at ``/etc/fstab`` to
  determine the root filesystem device. Then *root=auto* will changed to
  reflect this, so the actual parameter passed to the kernel will be something
  like *root=/dev/sda3* 
  
**rootfstype=auto**

  In a similar fashion to *root=auto*, *rootfstype=auto* will be
  replaced with something like *rootfstype=ext4*, with the filesystem type
  determined by the setting in ``/etc/fstab``.

**real_root=auto** 

  This special parameter is useful when using *genkernel* initrds. Any *root=*
  options already specified (including *root=auto*) will be removed from
  *params*, and *real_root* will be set to the root filesystem based on
  ``/etc/fstab``, so you'll end up with a setting such as *root=/dev/sda3*.

.. include:: ../LICENSE

SEE ALSO
--------

boot-update(8), genkernel(8)


