#!/bin/bash

VERSION=`cat VERSION`

sdist() {
	install -d dist
	rm -f dist/coreboot-$VERSION*
	cd doc
	cat boot-update.8.rst | sed -e "s/##VERSION##/$VERSION/g" | rst2man.py > boot-update.8
	cat boot.conf.5.rst | sed -e "s/##VERSION##/$VERSION/g" | rst2man.py > boot.conf.5
	git add boot-upate.8 boot.conf.5
	cd ..
	git commit -a -m "$VERSION distribution release"
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
