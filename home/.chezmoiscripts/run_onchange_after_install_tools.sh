#!/usr/bin/env sh
set -eu

# The tools live in their own repositories. Pin the revisions so an apply is
# reproducible and a version bump is an explicit edit here.
SESSION_MANAGER_REV=0a8dc7d16775ab538ce84ed341e6f6ffd29d4ba8
CLIPBOARD_PICKER_REV=e015c5e470de24e6b66e6881397b9bfd9ba2344e

if ! command -v uv >/dev/null 2>&1; then
	echo "install_tools: uv not found, skipping"
	exit 0
fi

uv tool install --force \
	"git+https://github.com/athaurian/session-manager@$SESSION_MANAGER_REV"
uv tool install --force \
	"git+https://github.com/athaurian/clipboard-picker@$CLIPBOARD_PICKER_REV"
