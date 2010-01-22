sdist:
	install -d dist
	rm -f dist/coreboot-`cat VERSION`*
	git archive --format=tar --prefix=coreboot-`cat VERRSION`/ HEAD > dist/coreboot-`cat VERSION`.tar
	bzip2 dist/coreboot-`cat VERSION`.tar
webupdate:
	cp dist/coreboot-`cat VERSION`.tar.bz2 /root/git/website/archive/coreboot
	cd /root/git/website
	git add archive/coreboot/*
	git commit -a -m "new coreboot"
	git push origin master
	./install.sh
all:	sdist webupdate
