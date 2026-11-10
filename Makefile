PRETTIER := npx --yes prettier@3.9.9
RUFF := uv run --with ruff ruff
MYPY := uv run --with mypy mypy
SHELLCHECK := uv run --with shellcheck-py shellcheck
SHFMT := uv run --with shfmt-py shfmt
STYLUA := stylua

MD_FILES := $(wildcard meta/*.md) $(wildcard docs/*.md) $(wildcard AGENTS.md) README.md
MPRIS_FILES := home/dot_local/bin/executable_mpris \
	home/dot_local/bin/tests/fake_playerctl.py \
	home/dot_local/bin/tests/test_mpris.py
SW_FILES := home/dot_local/bin/executable_sw \
	home/dot_local/bin/tests/test_sw.py
CALIBRE_FILES := home/dot_local/bin/executable_calibre-drive-sync \
	home/dot_local/bin/tests/test_calibre_drive_sync.py
WLSUNSET_FILES := home/dot_local/bin/executable_wlsunset-location \
	home/dot_local/bin/tests/test_wlsunset_location.py
LAUNCHER_WAYLAND_SRC := home/.local/share/launcher-dim/launcher_dim_wayland.c
LAUNCHER_X11_SRC := home/.local/share/launcher-dim/launcher_dim_x11.c
LAUNCHER_XML := home/.local/share/launcher-dim/wlr-layer-shell-unstable-v1.xml
WAYLAND_CFLAGS = $(shell pkg-config --cflags wayland-client)
WAYLAND_LIBS = $(shell pkg-config --libs wayland-client)
WAYLAND_PROTOCOLS = $(shell pkg-config --variable=pkgdatadir wayland-protocols)
X11_CFLAGS = $(shell pkg-config --cflags x11 xext)
X11_LIBS = $(shell pkg-config --libs x11 xext)
SHELL_FILES := $(shell find home meta .github -type f -name '*.sh' | sort) refs/fetch-refs.sh
SHELL_TMPL_FILES := $(shell find home -type f -name '*.sh.tmpl' | sort)
LUA_FILES := $(sort $(shell find home/dot_config/nvim -type f -name '*.lua'))
META_FILES := $(sort $(wildcard meta/*.py))
META_SHOTS_FILES := $(sort $(wildcard meta/shots/*.py))
META_LUA_FILES := $(sort $(shell find meta -type f -name '*.lua'))
META_MYPY := uv run --with mypy --with numpy --with pillow --with types-Pillow mypy
PROBE_FILES := meta/probe.lua meta/probe_pills.lua meta/probe_backdrop.lua

.PHONY: help format lint format-md lint-md palette light dark check-mpris check-sw check-refs check-config check-shell check-nvim check-probe check-calibre check-wlsunset check-launcher check-meta check-fonts shots site social

.DEFAULT_GOAL := help

help:
	@echo "Available commands:"
	@echo "  format            - Format project docs with prettier"
	@echo "  lint              - Check docs formatting without modifying them"
	@echo "  palette           - Write both LUTs + the active mode's data, run checks"
	@echo "  light             - Switch to light: record mode, regenerate, apply"
	@echo "  dark              - Switch to dark: record mode, regenerate, apply"
	@echo "  check-mpris       - Ruff + mypy + tests for the shared MPRIS poller"
	@echo "  check-sw          - Ruff + mypy + tests for the sw wallpaper utility"
	@echo "  check-calibre     - Ruff + mypy + tests for the calibre sync scripts"
	@echo "  check-wlsunset    - Ruff + mypy + tests for the wlsunset location script"
	@echo "  check-launcher    - Compile-check the launcher dim helper"
	@echo "  check-meta        - Ruff + stylua + mypy for the repository tooling in meta/"
	@echo "  check-fonts       - Check that the docs site uses the shared theme fonts"
	@echo "  shots             - Rebuild the automatic screenshot captures"
	@echo "  check-shell       - Shellcheck + shfmt over the repository shell scripts"
	@echo "  check-nvim        - Stylua over the Neovim Lua sources"
	@echo "  check-probe       - Assert the deployed Neovim highlights against the palette"
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
	uv run python3 -u meta/palette.py $(MODE:%=MODE=%)

light dark:
	printf '%s\n' '$@' > $(HOME)/.local/state/palette-mode
	uv run python3 -u meta/palette.py MODE=$@
	chezmoi apply --force

check-mpris:
	$(RUFF) check $(MPRIS_FILES)
	$(RUFF) format --check $(MPRIS_FILES)
	$(MYPY) home/dot_local/bin/executable_mpris
	uv run python3 -u home/dot_local/bin/tests/test_mpris.py

check-sw:
	$(RUFF) check $(SW_FILES)
	$(RUFF) format --check $(SW_FILES)
	$(MYPY) home/dot_local/bin/executable_sw
	uv run python3 -u home/dot_local/bin/tests/test_sw.py

check-calibre:
	$(RUFF) check $(CALIBRE_FILES)
	$(RUFF) format --check $(CALIBRE_FILES)
	$(MYPY) home/dot_local/bin/executable_calibre-drive-sync
	uv run python3 -u home/dot_local/bin/tests/test_calibre_drive_sync.py

check-wlsunset:
	$(RUFF) check $(WLSUNSET_FILES)
	$(RUFF) format --check $(WLSUNSET_FILES)
	$(MYPY) home/dot_local/bin/executable_wlsunset-location
	uv run python3 -u home/dot_local/bin/tests/test_wlsunset_location.py

# The layer-shell protocol references xdg-popup. The generated code thus needs
# the stable xdg-shell protocol from wayland-protocols.
check-launcher:
	@set -e; build=$$(mktemp -d); trap 'rm -rf "$$build"' EXIT HUP INT TERM; \
	wayland-scanner client-header $(LAUNCHER_XML) "$$build/wlr-layer-shell-unstable-v1-client-protocol.h"; \
	wayland-scanner private-code $(LAUNCHER_XML) "$$build/wlr-layer-shell-unstable-v1-protocol.c"; \
	wayland-scanner client-header $(WAYLAND_PROTOCOLS)/stable/xdg-shell/xdg-shell.xml "$$build/xdg-shell-client-protocol.h"; \
	wayland-scanner private-code $(WAYLAND_PROTOCOLS)/stable/xdg-shell/xdg-shell.xml "$$build/xdg-shell-protocol.c"; \
	$(CC) -O2 -Wall -Wextra -Werror -I "$$build" -o "$$build/launcher_dim_wayland" \
		$(LAUNCHER_WAYLAND_SRC) \
		"$$build/wlr-layer-shell-unstable-v1-protocol.c" \
		"$$build/xdg-shell-protocol.c" \
		$(WAYLAND_CFLAGS) $(WAYLAND_LIBS); \
	$(CC) -O2 -Wall -Wextra -Werror -o "$$build/launcher_dim_x11" \
		$(LAUNCHER_X11_SRC) $(X11_CFLAGS) $(X11_LIBS)

check-fonts:
	uv run python3 -u meta/check_fonts.py

check-meta:
	$(RUFF) check $(META_FILES) $(META_SHOTS_FILES)
	$(RUFF) format --check $(META_FILES) $(META_SHOTS_FILES)
	$(STYLUA) --check $(META_LUA_FILES)
	$(META_MYPY) $(META_FILES)
	MYPYPATH=meta/shots $(META_MYPY) $(META_SHOTS_FILES)

shots:
	meta/shots/redo-all.sh

# The scripts source the shared libs by full path. Give shellcheck the
# directories that hold them. The templates hold no shell syntax, so they
# are rendered into a scratch tree that shellcheck can follow.
check-shell:
	@set -e; lint=$$(mktemp -d); trap 'rm -rf "$$lint"' EXIT HUP INT TERM; \
	for f in $(SHELL_TMPL_FILES); do \
		out="$$lint/$${f%.tmpl}"; \
		mkdir -p "$$(dirname "$$out")"; \
		chezmoi --source "$(CURDIR)" execute-template -f "$$f" > "$$out"; \
		sh -n "$$out" || { echo "check-shell: FAILED $$f"; exit 1; }; \
	done; \
	$(SHELLCHECK) -x -P home/dot_local/lib -P home/dot_config/sway/scripts \
		-P home/dot_config/i3/scripts \
		-P "$$lint/home/dot_local/lib" \
		-P "$$lint/home/dot_config/sway/scripts" \
		-P "$$lint/home/dot_config/i3/scripts" $(SHELL_FILES); \
	$(SHFMT) -d $(SHELL_FILES)

check-nvim:
	$(STYLUA) --check $(LUA_FILES)

check-probe:
	nvim --headless -c "luafile meta/probe.lua"
	nvim --headless -c "luafile meta/probe_pills.lua"
	nvim --headless -c "luafile meta/probe_backdrop.lua"

check-refs:
	refs/fetch-refs.sh --check

check-config:
	sh meta/check-config.sh

site:
	uv run --with zensical==0.1.0 zensical build --strict

social:
	meta/shots/social.py
