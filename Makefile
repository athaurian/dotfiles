# Docs formatting (prettier) and palette checks.
PRETTIER := prettier

MD_FILES := $(wildcard meta/*.md) AGENTS.md

.DEFAULT_GOAL := help

.PHONY: help format lint format-md lint-md palette

help:
	@echo "Available commands:"
	@echo "  format            - Format project docs with prettier"
	@echo "  lint              - Check docs formatting without modifying them"
	@echo "  palette           - Derive tints, write the LUT, run checks + contrast"

format: format-md

lint: lint-md
	@echo "lint passed"

format-md:
	$(PRETTIER) --write $(MD_FILES)

lint-md:
	$(PRETTIER) --check $(MD_FILES)

palette:
	python3 meta/palette.py
