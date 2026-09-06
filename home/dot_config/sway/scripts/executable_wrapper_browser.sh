#!/usr/bin/env sh
set -eu

# Launch preferred browser. Respects $BROWSER, falls back to known binaries.

# Honour $BROWSER if set (may contain arguments)
if [ -n "${BROWSER:-}" ]; then
	# shellcheck disable=SC2086 # $BROWSER may contain args
	exec $BROWSER "$@"
fi

# Fallback chain: preferred first, then common alternatives
for browser in helium-browser firefox chromium google-chrome; do
	if command -v "$browser" >/dev/null 2>&1; then
		exec "$browser" "$@"
	fi
done

echo "error: no browser found" >&2
exit 1
