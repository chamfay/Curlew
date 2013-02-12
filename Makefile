APPNAME := curlew
APPVER := $(shell cat VERSION)
DESTDIR = /
DATADIR = $(DESTDIR)/usr/share
DOCDIR = $(DATADIR)/doc/$(APPNAME)-$(APPVER)
SOURCES = $(wildcard *.desktop.in)
TARGETS = ${SOURCES:.in=}
DEPS=ffmpeg fdisk
ECHO := echo
NAKE := make
PYTHON := python2
INSTALL := install
INTLTOOL_MERGE := intltool-merge
RM := $(shell which rm | egrep '/' | sed  's/\s//g')
GTK_UPDATE_ICON_CACHE := $(shell which gtk-update-icon-cache)
UPDATE_DESKTOP_DATABASE := $(shell which update-desktop-database)

	
all: $(TARGETS) icons
	
pos:
	@$(MAKE) -C po all
	
icons:
	@for i in 96 72 64 48 36 32 24 22 16; do \
		convert -background none $(APPNAME).svg -resize $${i}x$${i} $(APPNAME)-$${i}.png; \
	done
	make -C Curlew/icons/Default/ all
	
check_deps: 
	@for d in $(DEPS); do\
		s=$(which $${d} 2> /dev/null);\
		[ -z $${s} ] && (echo "---- $${d} messing!";\
	done
	
install: locale
	@$(ECHO) "*** Installing..."
	@$(PYTHON) setup.py install -O2 --root $(DESTDIR)
	@$(ECHO) "Copying: $(APPNAME).desktop -> $(DATADIR)/applications/"
	@$(INSTALL) -d $(DATADIR)/applications/
	@$(INSTALL) -m 0644 $(APPNAME).desktop $(DATADIR)/applications/
	@$(INSTALL) -d $(DOCDIR)
	@for i in ChangeLog VERSION README LICENSE-ar LICENSE-en; do\
		$(ECHO) "Copying: $${i} -> $(DOCDIR)";\
		$(INSTALL) -m 0644 -D $${i} $(DOCDIR)/$${i}; \
	done
	@$(INSTALL) -d $(DATADIR)/icons/hicolor/scalable/apps;
	@$(INSTALL) -m 0644 -D $(APPNAME).svg $(DATADIR)/icons/hicolor/scalable/apps
	@for i in 96 72 64 48 36 32 24 22 16; do \
		$(INSTALL) -d $(DATADIR)/icons/hicolor/$${i}x$${i}/apps; \
		$(INSTALL) -m 0644 -D $(APPNAME)-$${i}.png $(DATADIR)/icons/hicolor/$${i}x$${i}/apps/$(APPNAME).png; \
	done
	@$(RM) -rf build
	@$(DESTDIR)/$(UPDATE_DESKTOP_DATABASE) --quiet $(DATADIR)/applications  &> /dev/null || :
	@$(DESTDIR)/$(GTK_UPDATE_ICON_CACHE) --quiet $(DATADIR)/icons/hicolor &> /dev/null || :
	
uninstall: 
	@$(ECHO) "*** Uninstalling..."
	@$(ECHO) "- Removing: $(DATADIR)/applications/$(APPNAME).desktop"
	@$(RM) -f $(DATADIR)/applications/$(APPNAME).desktop
	@$(ECHO) "- Removing: $(DOCDIR)"
	@$(RM) -rf $(DOCDIR)
	@$(ECHO) "- Removing: $(DESTDIR)/usr/share/locale/*/LC_MESSAGES/$(APPNAME).mo"
	@$(RM) -f $(DESTDIR)/usr/share/locale/*/LC_MESSAGES/$(APPNAME).mo
	@$(ECHO) "- Removing: $(DESTDIR)/usr/bin/$(APPNAME)"
	@$(RM) -f $(DESTDIR)/usr/bin/$(APPNAME)
	@$(ECHO) "- Removing: $(DESTDIR)/usr/lib/python*/site-packages/Curlew"
	@$(RM) -rf $(DESTDIR)/usr/lib/python*/site-packages/Curlew
	@$(ECHO) "- Removing: $(DESTDIR)/usr/lib/python*/site-packages/$(APPNAME)*"
	@$(RM) -rf $(DESTDIR)/usr/lib/python*/site-packages/$(APPNAME)*
	
	@$(RM) -f $(DATADIR)/icons/hicolor/scalable/apps/$(APPNAME).svg
	@$(RM) -f $(DATADIR)/icons/hicolor/*/apps/$(APPNAME).png;
	@$(DESTDIR)/$(UPDATE_DESKTOP_DATABASE) --quiet $(DATADIR)/applications  &> /dev/null || :
	@$(DESTDIR)/$(GTK_UPDATE_ICON_CACHE) --quiet $(DATADIR)/icons/hicolor &> /dev/null || :
	
%.desktop: %.desktop.in pos
	@$(INTLTOOL_MERGE) -d po $< $@

clean:
	@$(ECHO) "*** Cleaning..."
	@$(MAKE) -C po clean
	@$(MAKE) -C Curlew/icons/Default/ clean
	@$(ECHO) "- Removing: $(TARGETS)"
	@$(RM) -f $(TARGETS)
	@$(ECHO) "- Removing: locale build"
	@$(RM) -rf locale build
	@$(ECHO) "- Removing: *.pyc"
	@$(RM) -f *.pyc
	@$(ECHO) "- Removing: */*.pyc"
	@$(RM) -f */*.pyc
	@$(ECHO) "- Removing: $(APPNAME)-*.png"
	@$(RM) -f $(APPNAME)-*.png
