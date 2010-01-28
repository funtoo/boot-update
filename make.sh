#!/bin/bash

VERSION=`cat VERSION`

sdist() {
	install -d dist
	rm -f dist/coreboot-$VERSION*
	git archive --format=tar --prefix=coreboot-${VERSION}/ HEAD > dist/coreboot-${VERSION}.tar
	bzip2 dist/coreboot-$VERSION.tar
}

webupdate() {
	cp dist/coreboot-$VERSION.tar.bz2 /root/git/website/archive/coreboot
	cd /root/git/website && git add archive/coreboot/* && git commit -a -m "new coreboot"
	./install.sh
}

if [ "$1" = "sdist" ]
then
	sdist
elif [ "$1" = "webupdate" ]
then
	webupdate
elif [ "$1" = "all" ]
then
	sdist
	webupdate
fi
