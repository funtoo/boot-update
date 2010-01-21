clean:
	rm -f MANIFEST
	rm -f dist/*.tar.bz2
sdist:
	rm -rf stage
	install -d stage
	rsync -a ./ stage/ --exclude=.git
	cat stage/sbin/boot-update | sed -e "s/##VERSION##/`cat VERSION`/g" > stage/sbin/boot-update.new
	cat stage/sbin/boot-update.new > stage/sbin/boot-update
	rm stage/sbin/boot-update.new
	rm -rf coreboot-`cat VERSION`
	mv stage coreboot-`cat VERSION`
	tar cjvf coreboot-`cat VERSION`.tar.bz2 coreboot-`cat VERSION`
	install -d dist
	mv -f coreboot-`cat VERSION`.tar.bz2 dist/
