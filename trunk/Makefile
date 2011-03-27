# Makefile for VideoTester
#

DIST     = dist
DOC      = doc
MAKEFILE = tools/sphinx/
BUILDDIR = tools/sphinx/_build/doc

.PHONY: help clean sdist

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  sdist      to make source distribution"

clean:
	-rm -rf $(DIST)
	-rm -f MANIFEST

sdist:
	-svn remove $(DOC) --force
	-rm -rf $(DIST)
	-make -C $(MAKEFILE) html
	-cp -rf $(BUILDDIR) .
	-svn add $(DOC)
	-make -C $(MAKEFILE) clean
	-python setup.py sdist
	@echo
	@echo "Build finished."