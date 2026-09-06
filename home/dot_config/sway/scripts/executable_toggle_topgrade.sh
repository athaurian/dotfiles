#!/usr/bin/env sh

set -eu

# Toggle the topgrade terminal into and out of the scratchpad. It uses foot
# with app_id foot_topgrade.
# Uses the shared lib_sway_lock.sh mkdir-based locking.
# The Waybar custom/updates module runs this script on click.

app_id=foot_topgrade

. "$(dirname -- "$0")/lib_sway_lock.sh"
acquire_sway_lock "toggle_topgrade" || exit 0

if swaymsg "[con_mark=topgrade_term] scratchpad show" >/dev/null 2>&1; then
	# Sway's `move position center` only works on the visible workspace,
	# so centering must happen after `scratchpad show` (the for_window
	# rule can only size and hide the window while it is still on the
	# scratchpad). Re-apply geometry here so resize + center actually
	# take effect. The `|| true` keeps `set -e` from aborting if the
	# mark disappeared between the two swaymsg calls (for example, window closed).
	swaymsg "[con_mark=topgrade_term] resize set width 75 ppt height 70 ppt, move position center" >/dev/null 2>&1 || true
	release_sway_lock "toggle_topgrade"
	exit 0
fi

swaymsg exec "foot --app-id=$app_id -e sh -c 'topgrade; pkill -RTMIN+8 waybar 2>/dev/null || true'"
release_sway_lock "toggle_topgrade"
