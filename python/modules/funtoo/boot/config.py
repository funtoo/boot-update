# -*- coding: ascii -*-
from ..core import config

class DefaultBootConfigFile(config.ConfigFile):

    def inherit(self,section):
        if section not in self.builtins:
            return "default"
        return None

    def __init__(self,fn=None,existing=False):
        self.builtins = [ "default" ]
        config.ConfigFile.__init__(self,fn,existing)
        self.readFromLines("""
boot {
    path /boot
    generate grub
    timeout 5
    default bzImage
}

color { 
    normal cyan/blue
    highlight blue/cyan
}

default {
    type linux
    scan /boot
    kernel bzImage[-v] kernel[-v] vmlinuz[-v] vmlinux[-v]
    params root=auto rootfstype=auto
}""")


class BootConfigFile(config.ConfigFile):

    def inherit(self,section):
        if section not in self.builtins:
            return "default"
        return None

    def __init__(self,fn="/etc/boot.conf",existing=True):
        # builtins is our list of all those sections that we recognize as having config values and
        # not boot entries.
        self.builtins = [ "boot", "display", "default", "altboot", "color" ]
        config.ConfigFile.__init__(self,fn,existing)
        self.parent=DefaultBootConfigFile()

    def validate(self):
        invalid=[]
        validmap={ 
                "boot" : [ "path", "generate", "timeout", "default" ],
                "display" : [ "gfxmode", "background", "font" ],
                "color" : [ "normal", "highlight" ],
                "default" : [ "scan", "kernel", "initrd", "params", "type" ]
        }
        for section in self.sectionData.keys():
            if section not in validmap.keys():
                cmpto="default"
            else:
                cmpto=section
            for itemkey in self.sectionData[section].keys():
                if itemkey not in validmap[cmpto]:
                    invalid.append("%s/%s" % ( section, itemkey ))
        return invalid          
