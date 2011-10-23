
DESTDIR=

VERSION=0.4a1
PVERSION=$(VERSION)-0ubuntu1
RELEASE=lucid


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
	
	
	ln -s $(DESTDIR)/etc/berlin/apache/adblock.conf   $(DESTDIR)/etc/apache2/sites-available/000-adblock
	


clean:
	find . -name "*.pyc" -exec rm {} \; -print
	rm -rf  debian/changelog  debian/compat  debian/copyright  debian/docs  debian/source



debian: ../berlin_$(VERSION).orig.tar  ../berlin_$(PVERSION).debian.tar.gz  ../berlin_$(PVERSION).dsc
	@true

../berlin_$(VERSION).orig.tar: clean
	tar -cf ../berlin_$(VERSION).orig.tar  \
		apache  bin  config  debian  helper-scripts  COPYING  Makefile  README

../berlin_$(PVERSION).debian.tar.gz: \
		debian/changelog  debian/compat  debian/control  debian/copyright  debian/docs  \
		debian/postinst   debian/postrm  debian/preinst  debian/prerm      debian/rules  \
		debian/source/format
	tar -pczf ../berlin_$(PVERSION).debian.tar.gz  $^
	

debian/changelog:
	@echo "Generating changelog..."
	@echo "berlin (${PVERSION}) ${RELEASE}; urgency=low"           > debian/changelog
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


../berlin_$(PVERSION).dsc:  ../berlin_$(VERSION).orig.tar  ../berlin_$(PVERSION).debian.tar.gz
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
	@echo "Checksums-Sha1:"                                       >> $@
	@echo " $(shell sha1sum ../berlin_$(VERSION).orig.tar         | grep -oP '^[0-9a-f]+') $(shell stat ../berlin_$(VERSION).orig.tar       | grep Size | cut -d ' ' -f4) berlin_$(VERSION).orig.tar"       >> $@
	@echo " $(shell sha1sum ../berlin_$(PVERSION).debian.tar.gz   | grep -oP '^[0-9a-f]+') $(shell stat ../berlin_$(PVERSION).debian.tar.gz | grep Size | cut -d ' ' -f4) berlin_$(PVERSION).debian.tar.gz" >> $@
	@echo "Checksums-Sha256:"                                     >> $@
	@echo " $(shell sha256sum ../berlin_$(VERSION).orig.tar       | grep -oP '^[0-9a-f]+') $(shell stat ../berlin_$(VERSION).orig.tar       | grep Size | cut -d ' ' -f4) berlin_$(VERSION).orig.tar"       >> $@
	@echo " $(shell sha256sum ../berlin_$(PVERSION).debian.tar.gz | grep -oP '^[0-9a-f]+') $(shell stat ../berlin_$(PVERSION).debian.tar.gz | grep Size | cut -d ' ' -f4) berlin_$(PVERSION).debian.tar.gz" >> $@
	@echo "Files:"                                                >> $@
	@echo " $(shell md5sum ../berlin_$(VERSION).orig.tar          | grep -oP '^[0-9a-f]+') $(shell stat ../berlin_$(VERSION).orig.tar       | grep Size | cut -d ' ' -f4) berlin_$(VERSION).orig.tar"       >> $@
	@echo " $(shell md5sum ../berlin_$(PVERSION).debian.tar.gz    | grep -oP '^[0-9a-f]+') $(shell stat ../berlin_$(PVERSION).debian.tar.gz | grep Size | cut -d ' ' -f4) berlin_$(PVERSION).debian.tar.gz" >> $@
	@echo ""                                                      >> $@
	
	gpg --clearsign $@
	mv $@.asc $@


