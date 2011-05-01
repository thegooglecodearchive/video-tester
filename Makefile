# Makefile for VideoTester
#

DIST     = dist
DOC      = doc
MAKEFILE = tools/sphinx/
BUILDDIR = tools/sphinx/_build/doc

.PHONY: help clean doc sdist

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  sdist      to make source distribution"

clean:
	-rm -rf $(DIST)
	-rm -f MANIFEST

doc:
	-svn remove $(DOC) --force
	-make -C $(MAKEFILE) html
	-cp -rf $(BUILDDIR)/* $(DOC)
	-svn add $(DOC)
	-make -C $(MAKEFILE) clean
	@echo
	@echo "Doc rebuilt."

sdist:
	-cp VT.conf doc
	-cp README doc/README.txt
	-cp COPYING doc/COPYING.txt
	-cp -rf test doc
	-python setup.py sdist
	-rm doc/VT.conf doc/README.txt doc/COPYING.txt
	-rm -rf doc/test
	@echo
	@echo "Build finished."
