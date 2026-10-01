#!/usr/bin/env sh
set -eu

if [ -n "${BROWSER:-}" ]; then
	exec $BROWSER "$@"
fi

for browser in helium-browser firefox chromium google-chrome; do
	if command -v "$browser" >/dev/null 2>&1; then
		exec "$browser" "$@"
	fi
done

echo "error: no browser found" >&2
exit 1
