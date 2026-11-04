#!/usr/bin/env sh
set -eu

# The tools live in their own repositories. Pin the revisions so an apply is
# reproducible and a version bump is an explicit edit here.
SESSION_MANAGER_REV=1e1deb3
CLIPBOARD_PICKER_REV=0753ad71c8a48974c21c1abd4a4093ee46ee1f85

if ! command -v uv >/dev/null 2>&1; then
	echo "install_tools: uv not found, skipping"
	exit 0
fi

uv tool install --force \
	"git+https://github.com/athaurian/session-manager@$SESSION_MANAGER_REV"
uv tool install --force \
	"git+https://github.com/athaurian/clipboard-picker@$CLIPBOARD_PICKER_REV"
