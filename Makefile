clean:
	rm -f MANIFEST

sdist:
	git archive --format=tar --prefix=coreboot-1.0/ HEAD > dist/coreboot-1.0.tar
	bzip2 dist/coreboot-1.0.tar
