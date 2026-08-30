# Write Python bytecode caches outside the working tree so chezmoi never
# sees __pycache__ in managed files.
export PYTHONPYCACHEPREFIX := $(HOME)/.cache/dotfiles/pycache

# Palette tooling.
# pyyaml is the only dependency, pulled in on demand so no project venv is
# required.
PALETTE_PY := uv run --with pyyaml python3

# Quality gate runner for session_manager_lib.
# Pulls in ruff and mypy on demand so no project venv is required.
CHECK_PY := uv run --with ruff --with mypy python3

# Unique prefix for generated zip files
ZIP_PREFIX := dotfiles_$(shell date +%Y%m%d_%H%M%S)

# Output zip paths
ZIP_FILE_DEFAULT := /tmp/$(ZIP_PREFIX).zip
ZIP_FILE_COLORS  := /tmp/$(ZIP_PREFIX)_colors.zip
ZIP_FILE_SESSION := /tmp/$(ZIP_PREFIX)_session.zip

# Standard exclusions shared across pack commands
EXCLUDES := ".git/*" ".git" "*.chezmoidata.yaml" \
            "**/*__pycache__*" "**/git/*"

# Session includes shared across pack-session targets
SESSION_INCLUDES := \
	"**/executable_session_manager" \
	"**/executable_power_control.sh" \
	"**/executable_session_restore_prompt.sh" \
	"**/session_manager_lib/*.py" \
	"**/autocmds.lua" "**/options.lua" "**/persistence.lua" "**/dashboard.lua"

SESSION_EXCLUDES := "**/*__pycache__*"

.DEFAULT_GOAL := help

# --- Formatting & linting by filetype ---
# Formatters are invoked directly when available on PATH (they come from the
# nvim mason bin dir), except ruff which is pulled in on demand like CHECK_PY.
RUFF     := $(CHECK_PY) -m ruff
PRETTIER := prettier
SHFMT    := shfmt
STYLUA   := stylua

PY_FILES := scripts/*.py \
            home/dot_local/bin/executable_calibre-drive-sync \
            home/dot_local/bin/executable_flint-wallpaper \
            home/dot_local/bin/tests/test_calibre_drive_sync.py \
            home/dot_config/sway/scripts/executable_rotate_wallpaper.py.tmpl \
            $(shell find home/dot_config/sway/scripts/session_manager_lib -name '*.py') \
            home/dot_config/waybar/scripts/tests/fake_playerctl.py \
            home/dot_config/waybar/scripts/tests/test_mpris.py

SH_FILES := $(shell find home/dot_config/sway/scripts home/dot_config/waybar/scripts home/.chezmoiscripts home/dot_local/bin \
	-not -path '*__pycache__*' \
	\( -name '*.sh' -o -name '*.sh.tmpl' -o -name 'executable_chezmoi-drift-check' \
	   -o -name 'executable_wlsunset-location' \) | sort -u)
# Python executables (executable_mpris.py, executable_session_manager,
# executable_calibre-drive-sync, executable_flint-wallpaper,
# executable_rotate_wallpaper.py.tmpl) are intentionally excluded from
# SH_FILES; they are covered by PY_FILES / check-mpris / check-calibre.

BASH_FILES := home/dot_bashrc home/dot_bash_profile home/dot_bash_aliases.tmpl

MD_FILES := README.md docs/*.md style-guide.md

JSON_FILES := home/dot_config/nvim/lazyvim.json \
              home/dot_config/nvim/dot_neoconf.json

JSONC_FILES := home/dot_config/fastfetch/config.jsonc.tmpl \
               home/dot_config/waybar/config.jsonc.tmpl

YAML_FILES := palettes/*/*.yaml \
              home/.chezmoidata/packages.yaml \
              home/dot_config/lazygit/config.yml.tmpl

LUA_FILES := $(shell find home/dot_config/nvim -name '*.lua')

.PHONY: help dark light check check-session check-mpris check-calibre lint format \
        lint-py lint-sh lint-md lint-json lint-yaml lint-lua \
        format-py format-sh format-md format-json format-yaml format-lua \
        pack pack-no-scripts pack-colors \
        pack-session pack-session-one pack-session-two

help:
	@echo "Available commands:"
	@echo "  dark              - Build dark palette data"
	@echo "  light             - Build light palette data"
	@echo "  check             - Lint, type check, and test all modules"
	@echo "  format            - Format files by filetype (ruff, shfmt, prettier, stylua)"
	@echo "  lint              - Lint files by filetype without modifying them"
	@echo "  pack              - Create a zip of the dotfiles"
	@echo "  pack-no-scripts   - Create a zip of the dotfiles (excluding scripts/)"
	@echo "  pack-colors       - Create a zip of color-related config files only"
	@echo "  pack-session      - Create a zip of session-related files"
	@echo "  pack-session-one  - Session files excluding nested lib dirs"
	@echo "  pack-session-two  - Only nested session_manager_lib files"

# --- Quality gates ---
check: check-session check-mpris check-calibre
	@echo "all checks passed"

check-session:
	$(CHECK_PY) -m ruff check --no-cache home/dot_config/sway/scripts/session_manager_lib
	$(CHECK_PY) -m ruff format --check --no-cache home/dot_config/sway/scripts/session_manager_lib
	$(CHECK_PY) -m mypy --cache-dir=/dev/null home/dot_config/sway/scripts/session_manager_lib
	PYTHONPATH=home/dot_config/sway/scripts $(CHECK_PY) -m unittest discover -s home/dot_config/sway/scripts/session_manager_lib/tests

check-mpris:
	$(CHECK_PY) -m ruff check --no-cache home/dot_config/waybar/scripts/tests/fake_playerctl.py home/dot_config/waybar/scripts/tests/test_mpris.py
	$(CHECK_PY) -m ruff format --check --no-cache home/dot_config/waybar/scripts/tests/fake_playerctl.py home/dot_config/waybar/scripts/tests/test_mpris.py
	python3 home/dot_config/waybar/scripts/tests/test_mpris.py

check-calibre:
	$(CHECK_PY) -m ruff check --no-cache home/dot_local/bin/tests/test_calibre_drive_sync.py
	$(CHECK_PY) -m ruff format --check --no-cache home/dot_local/bin/tests/test_calibre_drive_sync.py
	python3 home/dot_local/bin/tests/test_calibre_drive_sync.py

# --- Formatting & linting by filetype ---
format: format-py format-sh format-md format-json format-yaml format-lua

format-py:
	$(RUFF) format --no-cache $(PY_FILES)

format-sh:
	$(SHFMT) -w $(SH_FILES)
	$(SHFMT) -ln bash -w $(BASH_FILES)

format-md:
	$(PRETTIER) --write $(MD_FILES)

format-json:
	$(PRETTIER) --write $(JSON_FILES)
	$(PRETTIER) --parser jsonc --write $(JSONC_FILES)

format-yaml:
	$(PRETTIER) --parser yaml --write $(YAML_FILES)

format-lua:
	$(STYLUA) $(LUA_FILES)

lint: lint-py lint-sh lint-md lint-json lint-yaml lint-lua
	@echo "lint passed"

lint-py:
	$(RUFF) check --no-cache $(PY_FILES)
	$(RUFF) format --check --no-cache $(PY_FILES)

lint-sh:
	$(SHFMT) -d $(SH_FILES)
	$(SHFMT) -ln bash -d $(BASH_FILES)
	sh -n $(SH_FILES)
	bash -n $(BASH_FILES)

lint-md:
	$(PRETTIER) --check $(MD_FILES)

lint-json:
	$(PRETTIER) --check $(JSON_FILES)
	$(PRETTIER) --parser jsonc --check $(JSONC_FILES)

lint-yaml:
	$(PRETTIER) --parser yaml --check $(YAML_FILES)

lint-lua:
	$(STYLUA) --check $(LUA_FILES)

# --- Theme generation ---
dark light:
	$(PALETTE_PY) scripts/build_palette_data.py --theme $@

# --- Packaging helpers ---
define zip-clean
	rm -f $(1)
endef

define zip-create
	zip -r9 $(1) .
endef

# --- Packaging ---
pack:
	$(call zip-clean,$(ZIP_FILE_DEFAULT))
	$(call zip-create,$(ZIP_FILE_DEFAULT)) -x $(EXCLUDES)

pack-no-scripts:
	$(call zip-clean,$(ZIP_FILE_DEFAULT))
	$(call zip-create,$(ZIP_FILE_DEFAULT)) -x $(EXCLUDES) "scripts/*" "scripts"

pack-colors:
	$(call zip-clean,$(ZIP_FILE_COLORS))
	$(call zip-create,$(ZIP_FILE_COLORS)) \
		-i "*.tmpl" "scripts/*" "palettes/*" "palettes/*/*" \
		   "home/dot_local/bin/executable_flint-wallpaper" \
		   "home/dot_config/zellij/config.kdl" \
		   "home/dot_config/sway/scripts/executable_rotate_wallpaper.py.tmpl" \
		   "docs/palette-system.md" "docs/theming.md" \
		-x $(EXCLUDES) "**/systemd/*" \
		   "**/dot_bash_aliases.tmpl" \
		   "**/run_onchange_before_onboarding.sh.tmpl"

pack-session:
	$(call zip-clean,$(ZIP_FILE_SESSION))
	$(call zip-create,$(ZIP_FILE_SESSION)) \
		-i $(SESSION_INCLUDES) \
		-x $(SESSION_EXCLUDES)

pack-session-one:
	$(call zip-clean,$(ZIP_FILE_SESSION))
	$(call zip-create,$(ZIP_FILE_SESSION)) \
		-i $(SESSION_INCLUDES) \
		-x "**/session_manager_lib/*/*" $(SESSION_EXCLUDES)

pack-session-two:
	$(call zip-clean,$(ZIP_FILE_SESSION))
	$(call zip-create,$(ZIP_FILE_SESSION)) \
		-i "**/session_manager_lib/*/*" \
		-x $(SESSION_EXCLUDES)
