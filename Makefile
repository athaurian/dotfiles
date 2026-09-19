# Docs formatting (prettier), palette checks, and waybar MPRIS gates (ruff, mypy).
PRETTIER := prettier
RUFF := ruff
MYPY := mypy

MD_FILES := $(wildcard meta/*.md) AGENTS.md
MPRIS_FILES := home/dot_config/waybar/scripts/executable_mpris.py \
	home/dot_config/waybar/scripts/tests/fake_playerctl.py \
	home/dot_config/waybar/scripts/tests/test_mpris.py

.DEFAULT_GOAL := help

.PHONY: help format lint format-md lint-md palette check-mpris

help:
	@echo "Available commands:"
	@echo "  format            - Format project docs with prettier"
	@echo "  lint              - Check docs formatting without modifying them"
	@echo "  palette           - Derive tints, write the LUT, run checks + contrast"
	@echo "  check-mpris       - Ruff + mypy + tests for the waybar MPRIS module"

format: format-md

lint: lint-md
	@echo "lint passed"

format-md:
	$(PRETTIER) --write $(MD_FILES)

lint-md:
	$(PRETTIER) --check $(MD_FILES)

palette:
	python3 meta/palette.py

check-mpris:
	$(RUFF) check $(MPRIS_FILES)
	$(RUFF) format --check $(MPRIS_FILES)
	$(MYPY) home/dot_config/waybar/scripts/executable_mpris.py
	python3 -u home/dot_config/waybar/scripts/tests/test_mpris.py
