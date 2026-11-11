#!/usr/bin/env sh
set -eu

# The tool lives in its own repository. Pin the revision so an apply is
# reproducible and a version bump is an explicit edit here.
CLIPBOARD_PICKER_REV=0753ad71c8a48974c21c1abd4a4093ee46ee1f85

if ! command -v uv >/dev/null 2>&1; then
	echo "install_tools: uv not found" >&2
	exit 1
fi

uv tool install --force \
	"git+https://github.com/athaurian/clipboard-picker@$CLIPBOARD_PICKER_REV"
