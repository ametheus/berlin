#
#   Copyright (C) 2011  Thijs van Dijk
#
#   This file is part of berlin.
#
#   Berlin is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   Berlin is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   file "COPYING" for details.
#

DESTDIR=

VERSION=0.5a1
PVERSION=$(VERSION)-0ubuntu1
DIST=lucid


all: bin/rules.py
	@true

install:
	mkdir -p $(DESTDIR)/usr/share/berlin/bin/berlin
	mkdir -p $(DESTDIR)/etc/berlin/apache/filtered
	mkdir -p $(DESTDIR)/usr/sbin
	
	install -m 0755 bin/*.py           $(DESTDIR)/usr/share/berlin/bin/
	install -m 0755 bin/berlin/*.py    $(DESTDIR)/usr/share/berlin/bin/berlin/
	
	install -m 0755 helper-scripts/recreate-firewall.sh   $(DESTDIR)/usr/sbin/recreate-firewall
	install -m 0755 helper-scripts/restore-firewall.sh    $(DESTDIR)/usr/sbin/restore-firewall
	
	install -m 0644 config/*             $(DESTDIR)/etc/berlin/
	install -m 0644 apache/filtered/*    $(DESTDIR)/etc/berlin/apache/filtered/
	install -m 0644 apache/*.*           $(DESTDIR)/etc/berlin/apache/
	
	chmod +x $(DESTDIR)/etc/berlin/apache/blocked.py
	
	
	mkdir -p $(DESTDIR)/etc/apache2/sites-available
	ln -s ../../berlin/apache/adblock.conf   $(DESTDIR)/etc/apache2/sites-available/000-adblock
	


clean:
	find . -name "*.pyc" -exec rm {} \; -print


deb-clean:
	rm -rf  debian/changelog  debian/compat  debian/copyright  debian/docs  debian/source

debian: ../berlin_$(VERSION).orig.tar.gz  ../berlin_$(PVERSION).debian.tar.gz
	debuild
#		../berlin_$(PVERSION).dsc

debian-test: ../berlin_$(PVERSION).dsc  ../berlin_$(PVERSION)_source.changes \
		../berlin_$(VERSION).orig.tar.gz  ../berlin_$(PVERSION).debian.tar.gz
	sudo pbuilder build $<
	lintian -Ivi $<

../berlin_$(VERSION).orig.tar.gz: clean deb-clean
	tar --transform 's,^,berlin-$(VERSION)/,S' -pczf ../berlin_$(VERSION).orig.tar.gz  \
		apache  bin  config  debian  helper-scripts  COPYING  Makefile  README

../berlin_$(PVERSION).debian.tar.gz: \
		debian/changelog  debian/compat  debian/control  debian/copyright  debian/docs  \
		debian/postinst   debian/postrm  debian/preinst  debian/prerm      debian/rules  \
		debian/source/format  debian/watch
	tar -pczf ../berlin_$(PVERSION).debian.tar.gz  $^
	

debian/changelog:
	@echo "Generating changelog..."
	@echo "berlin (${PVERSION}) ${DIST}; urgency=low"              > debian/changelog
	@echo ""                                                      >> debian/changelog
	@echo "  * New upstream version"                              >> debian/changelog
	@echo ""                                                      >> debian/changelog
	@echo " -- ${DEBFULLNAME} <${DEBEMAIL}>  $(shell date -R)"    >> debian/changelog
debian/compat:
	echo 7 > debian/compat
debian/copyright:
	@echo "Generating example copyright file..."
	@echo "This work was packaged for Debian by:"                  > debian/copyright
	@echo ""                                                      >> debian/copyright
	@echo "    ${DEBFULLNAME} <${DEBEMAIL}> on $(shell date -R)"  >> debian/copyright
	@cat debian/copyright.part                                    >> debian/copyright
	@echo "    Copyright (C) $(shell date +%Y) ${DEBFULLNAME} <${DEBEMAIL}>"  >> debian/copyright
	@echo ""                                                      >> debian/copyright
	@echo "and is licensed under the GPL version 3, see above."   >> debian/copyright
debian/docs:
	echo README > debian/docs
debian/source/format:
	mkdir -p debian/source
	echo "3.0 (quilt)" > debian/source/format


../berlin_$(PVERSION).dsc:  ../berlin_$(VERSION).orig.tar.gz  ../berlin_$(PVERSION).debian.tar.gz  debian/control
	@echo "Generating .dsc file..."
	@echo "Format: 3.0 (quilt)"                                    > $@
	@echo "Source: berlin"                                        >> $@
	@echo "Binary: berlin"                                        >> $@
	@grep "Architecture:"       debian/control                    >> $@
	@echo "Version: $(PVERSION)"                                  >> $@
	@grep "Maintainer:"         debian/control                    >> $@
	@grep "Homepage:"           debian/control                    >> $@
	@grep "Standards-Version:"  debian/control                    >> $@
	@grep "Build-Depends:"      debian/control                    >> $@
	
	@$(eval s_org=$(shell stat ../berlin_$(VERSION).orig.tar.gz    | grep Size | cut -d ' ' -f4))
	@$(eval s_dbn=$(shell stat ../berlin_$(PVERSION).debian.tar.gz | grep Size | cut -d ' ' -f4))
	
	@echo "Checksums-Sha1:"                                       >> $@
	@echo " $(shell sha1sum ../berlin_$(VERSION).orig.tar.gz      | grep -oP '^[0-9a-f]+') $(s_org) berlin_$(VERSION).orig.tar.gz"    >> $@
	@echo " $(shell sha1sum ../berlin_$(PVERSION).debian.tar.gz   | grep -oP '^[0-9a-f]+') $(s_dbn) berlin_$(PVERSION).debian.tar.gz" >> $@
	@echo "Checksums-Sha256:"                                     >> $@
	@echo " $(shell sha256sum ../berlin_$(VERSION).orig.tar.gz    | grep -oP '^[0-9a-f]+') $(s_org) berlin_$(VERSION).orig.tar.gz"    >> $@
	@echo " $(shell sha256sum ../berlin_$(PVERSION).debian.tar.gz | grep -oP '^[0-9a-f]+') $(s_dbn) berlin_$(PVERSION).debian.tar.gz" >> $@
	@echo "Files:"                                                >> $@
	@echo " $(shell md5sum ../berlin_$(VERSION).orig.tar.gz       | grep -oP '^[0-9a-f]+') $(s_org) berlin_$(VERSION).orig.tar.gz"    >> $@
	@echo " $(shell md5sum ../berlin_$(PVERSION).debian.tar.gz    | grep -oP '^[0-9a-f]+') $(s_dbn) berlin_$(PVERSION).debian.tar.gz" >> $@
	@echo ""                                                      >> $@
	
	gpg --clearsign $@
	mv $@.asc $@

../berlin_$(PVERSION)_source.changes:  ../berlin_$(VERSION).orig.tar.gz \
		../berlin_$(PVERSION).debian.tar.gz  ../berlin_$(PVERSION).dsc
	
	@echo "Generating .changes file..."
	
	@echo "Format: 1.8"                                            > $@
	@echo "Date: $(shell date -R)"                                >> $@
	@echo "Source: berlin"                                        >> $@
	@echo "Binary: berlin"                                        >> $@
	@echo "Architecture: source"                                  >> $@
	@echo "Version: $(PVERSION)"                                  >> $@
	@echo "Distribution: $(DIST)"                                 >> $@
	@echo "Urgency: low"                                          >> $@
	@grep "Maintainer:"         debian/control                    >> $@
	@echo "Changed-By: ${DEBFULLNAME} <${DEBEMAIL}>"              >> $@
	
	@echo "Description:"                                          >> $@
	@echo " berlin    - $(shell grep Description debian/control | cut -d: -f2)"  >> $@
	
	@echo "Changes:"                                              >> $@
	@echo -n " "                                                  >> $@
	@head -1 debian/changelog                                     >> $@
	@echo " ."                                                    >> $@
	@grep -P "^  \*" debian/changelog | sed 's/\*/ \*/'           >> $@
	
	
	@$(eval s_dsc=$(shell stat ../berlin_$(PVERSION).dsc           | grep Size | cut -d ' ' -f4))
	@$(eval s_org=$(shell stat ../berlin_$(VERSION).orig.tar.gz    | grep Size | cut -d ' ' -f4))
	@$(eval s_dbn=$(shell stat ../berlin_$(PVERSION).debian.tar.gz | grep Size | cut -d ' ' -f4))
	
	@$(eval SECT=$(shell grep Section debian/control | cut -d: -f2 | tr -d \ ))
	@$(eval priority=$(shell grep Priority debian/control | cut -d: -f2 | tr -d \ ))
	
	@echo "Checksums-Sha1:"                                       >> $@
	@echo " $(shell sha1sum ../berlin_$(PVERSION).dsc             | grep -oP '^[0-9a-f]+') $(s_dsc) berlin_$(PVERSION).dsc"           >> $@
	@echo " $(shell sha1sum ../berlin_$(VERSION).orig.tar.gz      | grep -oP '^[0-9a-f]+') $(s_org) berlin_$(VERSION).orig.tar.gz"    >> $@
	@echo " $(shell sha1sum ../berlin_$(PVERSION).debian.tar.gz   | grep -oP '^[0-9a-f]+') $(s_dbn) berlin_$(PVERSION).debian.tar.gz" >> $@
	@echo "Checksums-Sha256:"                                     >> $@
	@echo " $(shell sha256sum ../berlin_$(PVERSION).dsc           | grep -oP '^[0-9a-f]+') $(s_dsc) berlin_$(PVERSION).dsc"           >> $@
	@echo " $(shell sha256sum ../berlin_$(VERSION).orig.tar.gz    | grep -oP '^[0-9a-f]+') $(s_org) berlin_$(VERSION).orig.tar.gz"    >> $@
	@echo " $(shell sha256sum ../berlin_$(PVERSION).debian.tar.gz | grep -oP '^[0-9a-f]+') $(s_dbn) berlin_$(PVERSION).debian.tar.gz" >> $@
	@echo "Files:"                                                >> $@
	@echo " $(shell md5sum ../berlin_$(PVERSION).dsc              | grep -oP '^[0-9a-f]+') $(s_dsc) $(SECT) $(priority) berlin_$(PVERSION).dsc"           >> $@
	@echo " $(shell md5sum ../berlin_$(VERSION).orig.tar.gz       | grep -oP '^[0-9a-f]+') $(s_org) $(SECT) $(priority) berlin_$(VERSION).orig.tar.gz"    >> $@
	@echo " $(shell md5sum ../berlin_$(PVERSION).debian.tar.gz    | grep -oP '^[0-9a-f]+') $(s_dbn) $(SECT) $(priority) berlin_$(PVERSION).debian.tar.gz" >> $@
	
	@echo ""                                                      >> $@
	
	gpg --clearsign $@
	mv $@.asc $@
