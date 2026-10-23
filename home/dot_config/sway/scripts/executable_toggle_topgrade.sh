#!/usr/bin/env sh

set -eu

# Clicking the custom/updates module in Waybar runs this script.

# Every kitty window shares one app_id, so the sway rule matches on title.
title=topgrade_term

. "$(dirname -- "$0")/lib_sway_lock.sh"
acquire_sway_lock "toggle_topgrade" || exit 0

if swaymsg -t get_marks 2>/dev/null | grep -qF '"topgrade_term"'; then
	# Keep the mark test separate from the combined command. Otherwise hiding
	# a visible terminal fails the command and the script spawns a duplicate.
	swaymsg "[con_mark=topgrade_term] scratchpad show, resize set width 75 ppt height 70 ppt, move position center" >/dev/null 2>&1 || true
	release_sway_lock "toggle_topgrade"
	exit 0
fi

swaymsg exec "kitty --title=$title -e sh -c 'topgrade; pkill -RTMIN+8 waybar 2>/dev/null || true'"
release_sway_lock "toggle_topgrade"
