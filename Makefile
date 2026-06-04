PREFIX ?= /usr/local
DESTDIR ?=
PYTHON3 ?= python3

.PHONY: all install uninstall clean deb rpm pkg

all:
	@echo "MailSpoof Installer"
	@echo "  make install      Install to $(DESTDIR)$(PREFIX)"
	@echo "  make uninstall    Remove from $(DESTDIR)$(PREFIX)"
	@echo "  make deb          Build Debian package"
	@echo "  make rpm          Build RPM package (Fedora/RHEL)"
	@echo "  make pkg          Build Arch package (PKGBUILD)"

install:
	install -dm755 $(DESTDIR)/usr/share/mailspoof
	cp -r lib templates mailspoof requirements.txt $(DESTDIR)/usr/share/mailspoof/
	install -dm755 $(DESTDIR)/usr/bin
	install -m755 scripts/mailspoof-wrapper.sh $(DESTDIR)/usr/bin/mailspoof

uninstall:
	rm -rf $(DESTDIR)/usr/share/mailspoof
	rm -f $(DESTDIR)/usr/bin/mailspoof

clean:
	find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete 2>/dev/null || true
	rm -rf build dist *.egg-info

deb:
	bash scripts/build-deb.sh

rpm:
	rpmbuild -ba mailspoof.spec --define "_sourcedir $(PWD)"

pkg:
	makepkg -si
