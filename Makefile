PREFIX ?= /usr/local
BINDIR ?= $(PREFIX)/bin
DESTDIR ?=

.PHONY: install uninstall

install:
	install -Dm755 gitlarp "$(DESTDIR)$(BINDIR)/gitlarp"

uninstall:
	rm -f -- "$(DESTDIR)$(BINDIR)/gitlarp"
