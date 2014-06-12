aur: PKGBUILD
	mkaurball -f

pkg: PKGBUILD
	makepkg -f

PKGBUILD: PKGBUILD.in
	cp -f PKGBUILD.in PKGBUILD
	sed -i -e '/^md5sums=/d' PKGBUILD
	makepkg -g >> PKGBUILD

clean:
	rm -f PKGBUILD MANIFEST *.tar.gz *.tar.xz *.pyc *.pyo
	rm -rf build pkg src dist

.PHONY: aur pkg clean
