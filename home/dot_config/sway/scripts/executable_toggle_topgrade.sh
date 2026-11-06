#!/usr/bin/env sh

set -eu

# Sway compares for_window titles as substrings. A kitty title that contains
# topgrade_term also takes the mark, so the class needs to match a name that
# only this script uses.
name=topgrade_term

. "$(dirname -- "$0")/lib_sway_lock.sh"
acquire_sway_lock "toggle_topgrade" || exit 0

if swaymsg -t get_marks 2>/dev/null | grep -qF '"topgrade_term"'; then
	# Keep the mark test separate from the combined command. Otherwise hiding
	# a visible terminal fails the command and the script spawns a duplicate.
	swaymsg "[con_mark=topgrade_term] scratchpad show, resize set width 75 ppt height 70 ppt, move position center" >/dev/null 2>&1 || true
	release_sway_lock "toggle_topgrade"
	exit 0
fi

swaymsg exec "kitty --class=$name --title=$name -e sh -c 'topgrade; pkill -RTMIN+8 waybar 2>/dev/null || true'"
release_sway_lock "toggle_topgrade"
