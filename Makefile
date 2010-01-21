clean:
	rm -f MANIFEST
	rm -f dist/*.tar.bz2
sdist:
	git archive --format=tar --prefix=coreboot-1.1/ HEAD > dist/coreboot-1.1.tar
	bzip2 dist/coreboot-1.1.tar
