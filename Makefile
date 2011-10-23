
DESTDIR=


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
	@true




