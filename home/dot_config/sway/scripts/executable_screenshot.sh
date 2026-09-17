#!/usr/bin/env sh
set -eu

# Annotate via satty, wl-copy fallback.
# Usage: screenshot.sh <full|focused|region>
# Needs: grim, slurp (region), satty or wl-copy, jq (focused), wayfreeze (optional).

mode="${1:-}"
case "$mode" in
full | region | focused) ;;
*)
	echo "Usage: screenshot.sh {full|focused|region}" >&2
	exit 1
	;;
esac

tmp=$(mktemp "${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/screenshot.XXXXXX")

geometry=""
if [ "$mode" = "focused" ]; then
	geometry=$(swaymsg -t get_tree | jq -r '
[.. | select(.focused? == true)]
| first
| .rect?
| select(. != null)
| "\(.x),\(.y) \(.width)x\(.height)"
  ')
	if [ -z "$geometry" ]; then
		rm -f "$tmp"
		exit 1
	fi
fi

export SCREENSHOT_MODE="$mode"
export SCREENSHOT_TMP="$tmp"
export SCREENSHOT_GEOMETRY="$geometry"

script_dir="$(cd "$(dirname "$0")" && pwd)"
capture_script="$script_dir/helper_capture.sh"

if [ ! -x "$capture_script" ]; then
	echo "Error: $capture_script not found or not executable" >&2
	rm -f "$tmp"
	exit 1
fi

if command -v wayfreeze >/dev/null 2>&1; then
	export SCREENSHOT_FROZEN=1
	wayfreeze --after-freeze-cmd "$capture_script"
else
	export SCREENSHOT_FROZEN=0
	"$capture_script"
fi
