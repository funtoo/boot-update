#!/bin/bash

VERSION=`cat VERSION`

prep() {
	install -d dist
	rm -f dist/boot-update-$VERSION*
	cd doc
	cat boot-update.8.rst | sed -e "s/##VERSION##/$VERSION/g" | rst2man.py > boot-update.8
	cat boot.conf.5.rst | sed -e "s/##VERSION##/$VERSION/g" | rst2man.py > boot.conf.5
	cd ..
	sed -i -e '/^version=/s/^.*$/version="'$VERSION'"/g' sbin/boot-update 
}

commit() {
	cd doc
	git add boot-update.8 boot.conf.5
	cd ..
	git commit -a -m "$VERSION distribution release"
	git tag "$VERSION"
	git push
	git archive --format=tar --prefix=boot-update-${VERSION}/ HEAD > dist/boot-update-${VERSION}.tar
	bzip2 dist/boot-update-$VERSION.tar
}

web() {
	install -d /root/git/website/archive/boot-update
	cp dist/boot-update-$VERSION.tar.bz2 /root/git/website/archive/boot-update
	cd /root/git/website && git add archive/boot-update/* && git commit -a -m "new boot-update $VERSION"
}

if [ "$1" = "prep" ]
then
	prep
elif [ "$1" = "commit" ]
then
	commit
elif [ "$1" = "web" ]
then
	web
elif [ "$1" = "all" ]
then
	prep
	commit
	web
fi
