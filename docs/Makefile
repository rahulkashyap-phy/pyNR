# Sphinx Makefile.
#   make -C docs all        PDF lecture notes (LaTeX) + HTML site that serves the PDF  (recommended)
#   make -C docs html       HTML only (links the PDF if one was built before)
#   make -C docs latexpdf   PDF only -> _build/latex/pyNR-lecture-notes.pdf
SPHINXBUILD ?= sphinx-build
SOURCEDIR    = .
BUILDDIR     = _build
PDF          = $(BUILDDIR)/latex/pyNR-lecture-notes.pdf

.PHONY: help all html latexpdf pdf clean
help:
	@echo "targets: all (PDF + HTML), html, latexpdf, clean"
all: pdf html
html:
	@$(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS)
latexpdf:
	@PYNR_DOCS_LATEX=1 $(SPHINXBUILD) -M latexpdf "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS)
# build the PDF and stage it for the HTML site (copied to the site root by html_extra_path)
pdf: latexpdf
	@mkdir -p _generated/pdf && cp "$(PDF)" _generated/pdf/ && echo "PDF staged for the HTML site: _generated/pdf/"
clean:
	rm -rf "$(BUILDDIR)" _generated
