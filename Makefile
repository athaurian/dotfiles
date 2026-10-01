PRETTIER := prettier
RUFF := uv run --with ruff ruff
MYPY := uv run --with mypy mypy

MD_FILES := $(wildcard meta/*.md) $(wildcard docs/*.md) AGENTS.md FEATURES.md README.md
MPRIS_FILES := home/dot_config/waybar/scripts/executable_mpris.py \
	home/dot_config/waybar/scripts/tests/fake_playerctl.py \
	home/dot_config/waybar/scripts/tests/test_mpris.py \
	home/dot_config/polybar/scripts/executable_mpris.py \
	home/dot_config/polybar/scripts/tests/test_mpris.py
SW_FILES := home/dot_local/bin/executable_sw \
	home/dot_local/bin/tests/test_sw.py

.DEFAULT_GOAL := help

.PHONY: help format lint format-md lint-md palette light dark check-mpris check-sw check-refs check-config site

help:
	@echo "Available commands:"
	@echo "  format            - Format project docs with prettier"
	@echo "  lint              - Check docs formatting without modifying them"
	@echo "  palette           - Derive tints, write both LUTs + the active mode's data, run checks"
	@echo "  light             - Switch to light: record mode, regenerate, apply"
	@echo "  dark              - Switch to dark: record mode, regenerate, apply"
	@echo "  check-mpris       - Ruff + mypy + tests for the waybar and polybar MPRIS modules"
	@echo "  check-sw          - Ruff + mypy + tests for the sw wallpaper utility"
	@echo "  check-refs        - Probe every pinned refs/ URL for bitrot (network)"
	@echo "  check-config      - Validate the applied configs with each program's checker"
	@echo "  site              - Build the MkDocs site into site/"

format: format-md

lint: lint-md
	@echo "lint passed"

format-md:
	$(PRETTIER) --write $(MD_FILES)

lint-md:
	$(PRETTIER) --check $(MD_FILES)

MODE :=

palette:
	uv run python3 meta/palette.py $(MODE:%=MODE=%)

light dark:
	printf '%s\n' '$@' > $(HOME)/.local/state/palette-mode
	uv run python3 meta/palette.py MODE=$@
	chezmoi apply

check-mpris:
	$(RUFF) check $(MPRIS_FILES)
	$(RUFF) format --check $(MPRIS_FILES)
	$(MYPY) home/dot_config/waybar/scripts/executable_mpris.py
	$(MYPY) home/dot_config/polybar/scripts/executable_mpris.py
	uv run python3 -u home/dot_config/waybar/scripts/tests/test_mpris.py
	uv run python3 -u home/dot_config/polybar/scripts/tests/test_mpris.py

check-sw:
	$(RUFF) check $(SW_FILES)
	$(RUFF) format --check $(SW_FILES)
	$(MYPY) home/dot_local/bin/executable_sw
	uv run python3 -u home/dot_local/bin/tests/test_sw.py

check-refs:
	sh refs/fetch-refs.sh --check

check-config:
	sh meta/check-config.sh

site:
	uv run --with mkdocs-material==9.7.7 mkdocs build --strict
