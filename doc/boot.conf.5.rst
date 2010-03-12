=========
boot.conf
=========

---------------------------------------------
Funtoo global boot loader configuration file
---------------------------------------------

:Author: Daniel Robbins <drobbins@funtoo.org>
:Version: ##VERSION## 
:Manual section: 5
:Manual group: Funtoo Linux Core System

SYNOPSIS
--------

  */etc/boot.conf*

DESCRIPTION
-----------

The data in */etc/boot.conf* is used by *boot-update(8)* to generate specific
configuration files for various boot loaders as necessary.

The benefit of */etc/boot.conf* is that it provides a single location to
store all boot-related information. It also provides a single, consistent file
format and feature set for configuring all boot loaders.

*boot-update(8)* utilizes */etc/boot.conf* to provide a consistent process for
updating boot loader configuration, regardless of the actual boot loader used.

Here is a sample */etc/boot.conf* configuration file:

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
*/etc/boot.conf*'s wildcard support, a single boot entry section in the
configuration file may generate multiple actual boot entries for the boot
loader, depending on how many matches are found. Wildcard support will be
explained later in this document.

Default Section
~~~~~~~~~~~~~~~

In addition, there is a special section named *default* which is used to
specify default settings for the boot entry sections. *boot-update* has several
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
*/etc/boot.conf* to generate *multiple* boot entries for your boot loader if
wildcards are used or multiple kernels are listed -- one boot entry will be
generated for each matching kernel found. 

So, for example, the following
*/etc/boot.conf* could generate two boot entries named "Funtoo Linux -
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

The */etc/boot.conf* entry above will look for all kernels matching *bzImage*
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
the setting from the *default* section. A boot entry setting can also
*extend* a default setting by using the *+=* operator as the first parameter.

If not specified, the default *params* setting of *root=auto rootfstype=auto*
is used -- these are special parameters that will be explained in the following
section.

When *+=* is used as the first argument for *params*, the default setting can
be *extended* with additional parameters.  For example, the *params* setting
for *"Funtoo Linux uvesafb"* above is *root=auto rootfstype=auto
video=uvesafb:1024x768-8,mtrr:2,ypan*.

Special Parameters
~~~~~~~~~~~~~~~~~~

**+=**

  When *+=* is specified at the beginning of the first *params* definition in a
  section, then the params after the *+=* will be added to the default
  parameters defined in *default/params* (type *boot-update --showdefaults* to
  see default settings.)  In addition, multiple *params* lines can appear in a
  section, as long as successive *params* lines begin with *+=*. This allows
  the *params* value to be defined over multiple lines.

**root=auto**

  When *root=auto* is evaluated, the framework will look at */etc/fstab* to
  determine the root filesystem device. Then *root=auto* will changed to
  reflect this, so the actual parameter passed to the kernel will be something
  like *root=/dev/sda3* .
  
**rootfstype=auto**

  In a similar fashion to *root=auto*, *rootfstype=auto* will be
  replaced with something like *rootfstype=ext4*, with the filesystem type
  determined by the setting in */etc/fstab*.

**real_root=auto** 

  This special parameter is useful when using *genkernel* initrds that expect a
  *real_root* parameter. Any *root=* options already specified (including
  *root=auto*) will be removed from *params*, and *real_root* will be set to
  the root filesystem based on */etc/fstab*, so you'll end up with a setting
  such as *real_root=/dev/sda3*.

Alternate OS Loading
--------------------

Boot entries can be created for alternate operating systems using the following
approach::
        
        "Windows 7" {
                type win7
                params root=/dev/sda6
        }


The *type* variable should be set to one of the operating system names that 
*boot-update* recognizes, which are:

- linux (default)
- dos
- msdos
- Windows 2000
- win2000
- Windows XP
- winxp
- Windows Vista
- vista
- Windows 7
- win7

For non-Linux operating systems, the *params* variable is used to specify the
root partition for chain loading. For consistency with Linux boot entries, the
syntax used is *root=device*.

*boot* Section
----------------

*boot :: generate*
~~~~~~~~~~~~~~~~~~~~

Specifies the boot loader that *boot-update* should generate a configuration
files for. This setting should be a single string, set to one of *grub*,
*grub-legacy* or *lilo*. Note that *lilo* support is currently *alpha*
quality. Defaults to *grub*.

*boot :: timeout*
~~~~~~~~~~~~~~~~~~~

Specifies the boot loader timeout, in seconds. Defaults to *5*.

*boot :: default*
~~~~~~~~~~~~~~~~~~~

Use this setting to specify the boot entry to boot by default. There are two
ways to use this setting.

The first way is to specify the filename of the kernel to boot by default. This
setting should contain no path information, just the kernel image name.  This
is the default mechanism, due to the setting of *bzImage*.

Alternatively, you can also specify the literal name of the boot entry you want
to boot. This is handy if you want to boot a non-Linux operating system by
default. If you had the following boot entry::

        "My Windows 7" {
                type win7
                params root=/dev/sda6
        }

...then, you could boot this entry by default with the following boot section::

        boot {
                generate grub
                default My Windows 7
        }

This is also a handy mechanism if you want to boot the most recently created
kernel by default. To do this, specify the name of the boot entry rather than
the kernel image name::

        boot {
                default "Funtoo Linux"
        }

If multiple "Funtoo Linux" boot entries are created, the one that has the most
recently created kernel (by file mtime) will be booted by default.

Note that double-quotes are optional both in section names and in the
*boot/default* value.

*default* and Boot Entry Sections
---------------------------------

*default :: type* 
~~~~~~~~~~~~~~~~~~~

Specifies the boot entry type; defaults to *linux*. Currently, DOS/Windows boot
entries are also supported. Set to one of: *linux*, *dos*, *msdos*, *Windows
2000*, *win2000*, *Windows XP*, *winxp*, *Windows Vista*, *vista*, *Windows 7*,
*win7*. Here's how to specify a Windows 7 boot entry::

        "My Windows 7" {
                type win7
                params root=/dev/sda6
        }

*default :: scan*
~~~~~~~~~~~~~~~~~~~

This setting specifies one or more directories to scan for kernels and 
initrds. Defaults to */boot*.

*default :: kernel*
~~~~~~~~~~~~~~~~~~~~~

This setting specifies kernel image name, names or patterns, to find kernels to
generate boot menu entries for. The path specified in the *scan* setting is
searched. Glob patterns are supported. The special pattern `[-v]` is used to
match a kernel base name (such as *bzImage*) plus all kernels with an
optional version suffix beginning with a *-*, such as *bzImage-2.6.24*. In
addition, arbitrary globs can be specified, such as *bzImage[-2.6.*].* If
more than one kernel image matches a pattern, or more than one kernel image is
specified, then more than one boot entry will be created using the settings
in this section.

*default :: initrd*
~~~~~~~~~~~~~~~~~~~~~

This setting specifies initrd/initramfs image(s) to load with the menu entry.
If multiple initrds or initramfs images are specified, then *all* specified
images will be loaded for the boot entry. Linux supports multiple initramfs
images being specified at boot time. Glob patterns are supported. The special
pattern *[-v]* is used to find initrd/initramfs images that match the
*[-v]* pattern of the current kernel.  For example, if the current menu
entry's kernel image has a *[-v]* pattern of *-2.6.24*, then
*initramfs[-v]* will match *initramfs-2.6.24*. If the current menu entry
had a *[-v]* pattern, but it was blank (in the case of *bzImage[-v]*
finding a kernel named *bzImage*,) then *initramfs[-v]* will match
*initramfs*, if it exists.

*default :: params*
~~~~~~~~~~~~~~~~~~~~~

This setting specifies the parameters passed to the kernel. This option
appearing in the *default* section can be extended in specific menu sections
by using the *+=* operator. The special parameters *root=auto*,
*rootfstype=auto* and *real_root=auto* are supported, which will be
replaced with similar settings with the *auto* string replaced with the
respective setting from */etc/fstab*. Defaults to *root=auto
rootfstype=auto*.

*display* Section
-------------------

*display :: gfxmode*
~~~~~~~~~~~~~~~~~~~~~~

Specifies the video mode to be used by the boot loader's menus. This value is
also inherited and used as the video mode for the kernel when a graphical boot
(*uvesafb*, *vesafb-tng*) is used. This option is only supported for
*grub*.

*color* Section
-----------------

Currently, the color options are only supported for *grub*.

*color :: normal*
~~~~~~~~~~~~~~~~~~~

Specifies the regular display colors in *fg/bg* format. Defaults to *cyan/blue*.

*color :: highlight*
~~~~~~~~~~~~~~~~~~~~~~

Specifies the menu highlight colors in *fg/bg* format. Defaults to *blue/cyan*.


.. include:: ./LICENSE

SEE ALSO
--------

boot-update(8), genkernel(8)


