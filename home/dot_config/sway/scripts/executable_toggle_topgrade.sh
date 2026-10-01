#!/usr/bin/env sh

set -eu

# Clicking the custom/updates module in Waybar runs this script.

app_id=foot_topgrade

. "$(dirname -- "$0")/lib_sway_lock.sh"
acquire_sway_lock "toggle_topgrade" || exit 0

if swaymsg -t get_marks 2>/dev/null | grep -qF '"topgrade_term"'; then
	# The show, resize, and move below run as one swaymsg command for a
	# single Sway render. The existence test must stay out of that command.
	# If the script tested with that command, `scratchpad show` would hide
	# a visible terminal, the trailing `move position center` would fail on
	# the now-hidden window, and swaymsg would report failure. The script
	# would read that failure as a missing terminal and spawn a duplicate.
	swaymsg "[con_mark=topgrade_term] scratchpad show, resize set width 75 ppt height 70 ppt, move position center" >/dev/null 2>&1 || true
	release_sway_lock "toggle_topgrade"
	exit 0
fi

swaymsg exec "foot --app-id=$app_id -e sh -c 'topgrade; pkill -RTMIN+8 waybar 2>/dev/null || true'"
release_sway_lock "toggle_topgrade"
