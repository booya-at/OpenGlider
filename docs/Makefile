# Makefile for Sphinx documentation (OpenGlider)
# Run from docs/ directory: make html
# Requires: pip install sphinx (in your venv or environment)

SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SOURCEDIR     = source
BUILDDIR      = build
PACKAGEDIR    = ../openglider

.PHONY: help clean apidoc html dirhtml singlehtml pickle json htmlhelp epub latex latexpdf

help:
	@echo "Targets: html, apidoc, clean, latex, latexpdf, ..."
	@echo "  make apidoc   - regenerate API .rst from openglider package"
	@echo "  make html     - build HTML (runs apidoc first)"
	@echo "Requires Sphinx: pip install sphinx"

clean:
	rm -rf $(BUILDDIR)

apidoc:
	sphinx-apidoc -o $(SOURCEDIR)/api $(PACKAGEDIR) -f --separate -M

html:
	$(SPHINXBUILD) -b html $(SPHINXOPTS) $(SOURCEDIR) $(BUILDDIR)/html
	@echo "HTML built in $(BUILDDIR)/html"

dirhtml:
	$(SPHINXBUILD) -b dirhtml $(SPHINXOPTS) $(SOURCEDIR) $(BUILDDIR)/dirhtml

singlehtml:
	$(SPHINXBUILD) -b singlehtml $(SPHINXOPTS) $(SOURCEDIR) $(BUILDDIR)/singlehtml

pickle:
	$(SPHINXBUILD) -b pickle $(SPHINXOPTS) $(SOURCEDIR) $(BUILDDIR)/pickle

json:
	$(SPHINXBUILD) -b json $(SPHINXOPTS) $(SOURCEDIR) $(BUILDDIR)/json

htmlhelp:
	$(SPHINXBUILD) -b htmlhelp $(SPHINXOPTS) $(SOURCEDIR) $(BUILDDIR)/htmlhelp

epub:
	$(SPHINXBUILD) -b epub $(SPHINXOPTS) $(SOURCEDIR) $(BUILDDIR)/epub

latex:
	$(SPHINXBUILD) -b latex $(SPHINXOPTS) $(SOURCEDIR) $(BUILDDIR)/latex

latexpdf:
	$(SPHINXBUILD) -b latex $(SPHINXOPTS) $(SOURCEDIR) $(BUILDDIR)/latex
	$(MAKE) -C $(BUILDDIR)/latex all-pdf
