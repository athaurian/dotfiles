#!/usr/bin/env sh
set -eu

# Toggle the dropdown foot terminal (app_id foot_drop) in and out of the
# scratchpad. Bound to $mod+grave. Serialized via lib_sway_lock.sh.

app_id=foot_drop

. "$(dirname -- "$0")/lib_sway_lock.sh"
acquire_sway_lock "toggle_drop_term" || exit 0

if swaymsg -t get_marks 2>/dev/null | grep -qF '"drop_term"'; then
	# Hide and show take separate paths: any geometry after a hide
	# re-shows the window (`move position center` pulls it back out),
	# so a single show+geometry chain can never hide.
	if swaymsg -t get_tree 2>/dev/null | jq -e '.. | select((.marks // []) | index("drop_term")) | select(.visible == true)' >/dev/null; then
		swaymsg "[con_mark=drop_term] scratchpad show" >/dev/null 2>&1 || true
	else
		swaymsg "[con_mark=drop_term] scratchpad show, resize set width 75 ppt height 70 ppt, move position center" >/dev/null 2>&1 || true
	fi
	release_sway_lock "toggle_drop_term"
	exit 0
fi

swaymsg exec "foot --app-id=$app_id"

# Hold the lock until the marked window maps, so a second keypress sees
# the mark instead of spawning its own terminal.
i=0
while [ "$i" -lt 40 ]; do
	if swaymsg -t get_marks 2>/dev/null | grep -qF '"drop_term"'; then
		break
	fi
	sleep 0.05
	i=$((i + 1))
done
# Fresh spawns map already centered via their for_window rule; re-apply
# geometry as fallback for output changes or missed placement.
if swaymsg -t get_marks 2>/dev/null | grep -qF '"drop_term"'; then
	swaymsg "[con_mark=drop_term] resize set width 75 ppt height 70 ppt, move position center" >/dev/null 2>&1 || true
fi
release_sway_lock "toggle_drop_term"
