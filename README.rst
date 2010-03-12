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

The Funtoo Core Boot Framework provides a unified mechanism for configuring the
GRUB 1.9x (sys-boot/grub) and GRUB 0.97 (sys-boot/grub-legacy) boot loaders. It
is the recommended, official way to configure Funtoo Linux systems for booting.

Current Versions
================

- sys-apps/coreboot-1.4.1 (~funtoo)
- sys-apps/coreboot-1.4 (funtoo)

Man Pages
=========

Consult the following man pages for detailed, up-to-date information on configuration
file settings and command-line arguments:

.. _boot-update(8): boot-update.8.rst
.. _boot.conf(5): boot.conf.5.rst

- `boot-update(8)`_
- `boot.conf(5)`_

GRUB 1.97+ Quick Start
======================

If using sys-boot/grub-1.97+, perform the following steps:

- Partition disk using GPT/GUID (recommended) or MBR partitions.
- Install kernel/initrd to /boot
- ``emerge sys-apps/coreboot``
- ``grub-install --no-floppy /dev/sda``

Ensure that ``/etc/fstab`` is updated, and edit ``/etc/boot.conf`` to reflect
your installation. Then run::

        boot-update

This will auto-generate the complex ``/boot/grub/grub.cfg`` required for booting.

GRUB 0.97 (grub-legacy) Quick Start
===================================

If using sys-boot/grub-legacy-0.97, perform the following steps:

- Partition disk using MBR partitions (GPT not supported)
- Install kernel/initrd to /boot
- ``emerge sys-apps/coreboot``
- ``emerge sys-boot/grub-legacy`` (0.97-r11 or greater)
- ``grub-install-legacy /dev/sda``

Ensure that ``/etc/fstab`` is correct, and edit ``/etc/boot.conf`` to reflect
your installation. Ensure a ``generate grub-legacy`` setting in the ``boot``
section. Then run::

        boot-update

This will auto-generate the ``/boot/grub-legacy/grub.conf`` required for booting.
Note that grub-legacy-0.97-r11 and later stores ``grub.conf`` in the ``/boot/grub-legacy``
directory.

.. include:: ./LICENSE

