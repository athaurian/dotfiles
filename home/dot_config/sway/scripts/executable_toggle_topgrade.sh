#!/usr/bin/env sh

set -eu

# Toggle the topgrade terminal into and out of the scratchpad. It uses foot
# with app_id foot_topgrade.
# Uses the shared lib_sway_lock.sh mkdir-based locking.
# The Waybar custom/updates module runs this script on click.

app_id=foot_topgrade

. "$(dirname -- "$0")/lib_sway_lock.sh"
acquire_sway_lock "toggle_topgrade" || exit 0

if swaymsg -t get_marks 2>/dev/null | grep -qF '"topgrade_term"'; then
	# Existence is tested via get_marks (no state change, no render).
	# Show + geometry then runs as one transaction so Sway renders
	# once. NOTE: do NOT fold the test into the transaction
	# (`if swaymsg "... scratchpad show, resize ..., move ..."`): when
	# hiding, the trailing `move position center` fails on the hidden
	# scratchpad window and poisons the exit status, so every hide
	# would fall through and spawn a duplicate terminal.
	swaymsg "[con_mark=topgrade_term] scratchpad show, resize set width 75 ppt height 70 ppt, move position center" >/dev/null 2>&1 || true
	release_sway_lock "toggle_topgrade"
	exit 0
fi

swaymsg exec "foot --app-id=$app_id -e sh -c 'topgrade; pkill -RTMIN+8 waybar 2>/dev/null || true'"
release_sway_lock "toggle_topgrade"
