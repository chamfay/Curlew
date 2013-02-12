APPNAME := curlew
POFILES := $(wildcard *.po)
MOFILES := $(patsubst %.po,%.mo,$(POFILES))
CRE_POTFILESin := for i in $(shell cat POTFILES.am ); do echo ../$${i} | sed 's/\s/\n/g; s/\.\.\///g' ; done > POTFILES.in

CAT := cat
ECHO := echo
MKDIR := mkdir
MSGFMT := msgfmt
INTLTOOL_UPDATE := intltool-update
RM := $(shell which rm | egrep '/' | sed  's/\s*//g')
MV := $(shell which mv | egrep '/' | sed  's/\s*//g')

all: $(APPNAME).pot $(MOFILES)

$(APPNAME).pot: 
	@$(CRE_POTFILESin)
	@$(ECHO) "*** Building $(APPNAME).pot: $(SOURCES)"
	@$(CAT) POTFILES.in
	@$(INTLTOOL_UPDATE) -g $(APPNAME) -p
	
%.mo: %.po
	@$(ECHO) "- Merging translations into $*.mo"
	@$(MSGFMT) $*.po -o $*.mo
	@$(MKDIR) -p ../locale/$*/LC_MESSAGES/ || :
	@$(ECHO) "- Moving: $*.mo -> ../locale/$*/LC_MESSAGES/$(APPNAME).mo"
	@$(MV) $*.mo ../locale/$*/LC_MESSAGES/$(APPNAME).mo
	@$(RM) -f *.tmp

%.po: $(APPNAME).pot
	@$(ECHO) "- Updating: $*.po"
	@$(INTLTOOL_UPDATE) -g $(APPNAME) -d $*

clean:
	@$(ECHO) "*** Cleaning pos..."
	@$(ECHO) "- Removing: $(APPNAME).pot"
	@$(RM) -f $(APPNAME).pot
	@$(ECHO) "- Removing: *.tmp"
	@$(RM) -f *.tmp
	@$(ECHO) "- Removing: *.mo"
	@$(RM) -f *.mo
	@$(ECHO) "- Removing: POTFILES.in"
	@$(RM) -f POTFILES.in
