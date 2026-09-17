#!/usr/bin/env sh
set -eu

# Invoked by screenshot.sh/wayfreeze. Expects SCREENSHOT_MODE/TMP/GEOMETRY/FROZEN in env.

unfreeze() {
	if [ "${SCREENSHOT_FROZEN:-0}" = "1" ]; then
		# || true: wayfreeze may already be dead under set -e.
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

# Unfreeze before satty so the UI stays responsive.
unfreeze

if [ -s "$SCREENSHOT_TMP" ]; then
	if command -v satty >/dev/null 2>&1; then
		save_dir="$HOME/Pictures/Screenshots"
		mkdir -p "$save_dir"
		save_filename="$save_dir/screenshot-$(date '+%Y%m%d-%H%M%S').png"

		# || true keeps cleanup running however satty exits.
		satty --filename "$SCREENSHOT_TMP" \
			--copy-command wl-copy \
			--output-filename "$save_filename" \
			--early-exit || true

	elif command -v wl-copy >/dev/null 2>&1; then
		wl-copy <"$SCREENSHOT_TMP" && notify-send -a screenshot -u low -t 1500 "󰄄 screenshot" "copied to clipboard" 2>/dev/null || true
	fi
fi

rm -f "$SCREENSHOT_TMP"
