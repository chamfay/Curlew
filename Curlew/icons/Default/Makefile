SOURCES = $(wildcard *.svg)
TARGETS = ${SOURCES:.svg=}

MKDIR := mkdir
ECHO := echo
RM := $(shell which rm | egrep '/' | sed  's/\s*//g')
LN := $(shell which ln | egrep '/' | sed  's/\s*//g')
	
all: $(SOURCES) icons
	
icons:
	@$(ECHO) "*** Making Smail icons..."
	@$(MKDIR) -p ../Smail
	@for i in $(TARGETS); do \
		convert -background none $${i}.svg -resize 48x48 $${i}.png;\
		$(LN) -sf ../Default/$${i}.png ../Smail/$${i}.png;\
	done
	
clean:
	@$(ECHO) "*** Cleaning icons..."
	@$(RM) -f ../*/*.png
	@$(RM) -rf ../Smail
	
