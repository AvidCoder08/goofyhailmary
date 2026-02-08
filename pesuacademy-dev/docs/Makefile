# Makefile for Sphinx documentation

# Path to your package source code
PACKAGE_DIR = ../pesuacademy
# Path to your docs source directory
DOCS_SRC = ./

.PHONY: help clean html apidoc

help:
	@echo "Usage:"
	@echo "  make apidoc    # Generate rst files from package source"
	@echo "  make html      # Build HTML docs"
	@echo "  make clean     # Remove generated files"

# Generate .rst files from your package source code
apidoc:
	sphinx-apidoc -f -o $(DOCS_SRC) $(PACKAGE_DIR)

# Build the HTML documentation, regenerates rst first
html: apidoc
	sphinx-build -b html $(DOCS_SRC) $(DOCS_SRC)/_build/html

# Clean generated files
clean:
	rm -rf $(DOCS_SRC)/_build
	rm -f $(DOCS_SRC)/pesuacademy.*.rst
	rm -f $(DOCS_SRC)/modules.rst
