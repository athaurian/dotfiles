#!/usr/bin/env sh
set -eu

# Launch the preferred browser.

# Honour $BROWSER if set (may contain arguments)
if [ -n "${BROWSER:-}" ]; then
	# shellcheck disable=SC2086 # $BROWSER may contain args
	exec $BROWSER "$@"
fi

for browser in helium-browser firefox chromium google-chrome; do
	if command -v "$browser" >/dev/null 2>&1; then
		exec "$browser" "$@"
	fi
done

echo "error: no browser found" >&2
exit 1
