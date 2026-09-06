#!/usr/bin/env sh
set -eu

# This script is invoked by screenshot.sh (or wayfreeze on its behalf).
# It expects SCREENSHOT_MODE, SCREENSHOT_TMP, SCREENSHOT_GEOMETRY, and
# SCREENSHOT_FROZEN to be exported in the environment.

unfreeze() {
	if [ "${SCREENSHOT_FROZEN:-0}" = "1" ]; then
		# Use || true so set -e doesn't abort if wayfreeze is already dead
		pkill -x wayfreeze 2>/dev/null || true
	fi
	return 0
}

if [ "$SCREENSHOT_MODE" = "region" ]; then
	geometry="$(slurp)"
	if [ -z "$geometry" ]; then
		unfreeze
		rm -f "$SCREENSHOT_TMP"
		exit 0
	fi
	grim -g "$geometry" "$SCREENSHOT_TMP"
elif [ "$SCREENSHOT_MODE" = "focused" ]; then
	if [ -z "$SCREENSHOT_GEOMETRY" ]; then
		unfreeze
		rm -f "$SCREENSHOT_TMP"
		exit 1
	fi
	grim -g "$SCREENSHOT_GEOMETRY" "$SCREENSHOT_TMP"
else
	grim "$SCREENSHOT_TMP"
fi

# Unfreeze the screen before opening satty so the UI is responsive
unfreeze

if [ -s "$SCREENSHOT_TMP" ]; then
	if command -v satty >/dev/null 2>&1; then
		save_dir="$HOME/Pictures/Screenshots"
		mkdir -p "$save_dir"
		save_filename="$save_dir/screenshot-$(date '+%Y%m%d-%H%M%S').png"

		# Satty handles its own notifications for saving/copying.
		# || true ensures cleanup runs regardless of how satty exits.
		satty --filename "$SCREENSHOT_TMP" \
			--copy-command wl-copy \
			--output-filename "$save_filename" \
			--early-exit || true

	elif command -v wl-copy >/dev/null 2>&1; then
		wl-copy <"$SCREENSHOT_TMP" && notify-send -a screenshot -u low -t 1500 "󰄄 screenshot" "copied to clipboard" 2>/dev/null || true
	fi
fi

rm -f "$SCREENSHOT_TMP"
