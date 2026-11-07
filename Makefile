PRETTIER := npx --yes prettier@3.9.9
RUFF := uv run --with ruff ruff
MYPY := uv run --with mypy mypy
SHELLCHECK := uv run --with shellcheck-py shellcheck
SHFMT := uv run --with shfmt-py shfmt
STYLUA := stylua

MD_FILES := $(wildcard meta/*.md) $(wildcard docs/*.md) $(wildcard AGENTS.md) README.md
MPRIS_FILES := home/dot_config/waybar/scripts/executable_mpris.py \
	home/dot_config/waybar/scripts/tests/fake_playerctl.py \
	home/dot_config/waybar/scripts/tests/test_mpris.py \
	home/dot_config/polybar/scripts/executable_mpris.py \
	home/dot_config/polybar/scripts/tests/test_mpris.py
SW_FILES := home/dot_local/bin/executable_sw \
	home/dot_local/bin/tests/test_sw.py
SHELL_FILES := $(shell find home meta .github -type f -name '*.sh' | sort) refs/fetch-refs.sh
SHELL_TMPL_FILES := $(shell find home -type f -name '*.sh.tmpl' | sort)

.PHONY: help format lint format-md lint-md palette light dark check-mpris check-sw check-refs check-config check-shell site social

.DEFAULT_GOAL := help

help:
	@echo "Available commands:"
	@echo "  format            - Format project docs with prettier"
	@echo "  lint              - Check docs formatting without modifying them"
	@echo "  palette           - Write both LUTs + the active mode's data, run checks"
	@echo "  light             - Switch to light: record mode, regenerate, apply"
	@echo "  dark              - Switch to dark: record mode, regenerate, apply"
	@echo "  check-mpris       - Ruff + mypy + tests for the waybar and polybar MPRIS modules"
	@echo "  check-sw          - Ruff + mypy + tests for the sw wallpaper utility"
	@echo "  check-shell       - Shellcheck + shfmt over the repository shell scripts"
	@echo "  check-refs        - Probe every pinned refs/ URL for bitrot (network)"
	@echo "  check-config      - Validate the applied configs with each program's checker"
	@echo "  site              - Build the docs site into site/"
	@echo "  social            - Rebuild the Open Graph banner from the editor and empty captures"

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
	chezmoi apply --force

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

# The libs are sourced through $(dirname -- "$0"). Give shellcheck the two
# directories that hold them. The templates hold no shell syntax, so they
# are rendered before the parse.
check-shell:
	$(SHELLCHECK) -x -P home/dot_config/sway/scripts -P home/dot_config/i3/scripts $(SHELL_FILES)
	$(SHFMT) -d $(SHELL_FILES)
	for f in $(SHELL_TMPL_FILES); do chezmoi execute-template -f "$$f" | sh -n - || { echo "check-shell: FAILED $$f"; exit 1; }; done

check-refs:
	sh refs/fetch-refs.sh --check

check-config:
	sh meta/check-config.sh

site:
	uv run --with zensical==0.0.73 zensical build --strict

social:
	magick \
		\( meta/captures/editor-light.png -crop 960x1008+0+36 +repage -resize 600x630^ -extent 600x630 \) \
		\( meta/captures/empty-dark.png -crop 960x1008+960+0 +repage -resize 600x630^ -extent 600x630 \) \
		+append +repage docs/images/og.png
