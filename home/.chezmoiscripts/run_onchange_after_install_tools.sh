#!/usr/bin/env sh
set -eu

# The tools live in their own repositories. Pin the revisions so an apply is
# reproducible and a version bump is an explicit edit here.
SESSION_MANAGER_REV=33f3d175ba2c6257c61df0661ee192fcf28d6eea
CLIPBOARD_PICKER_REV=e015c5e470de24e6b66e6881397b9bfd9ba2344e

if ! command -v uv >/dev/null 2>&1; then
	echo "install_tools: uv not found, skipping"
	exit 0
fi

uv tool install --force \
	"git+https://github.com/athaurian/session-manager@$SESSION_MANAGER_REV"
uv tool install --force \
	"git+https://github.com/athaurian/clipboard-picker@$CLIPBOARD_PICKER_REV"
