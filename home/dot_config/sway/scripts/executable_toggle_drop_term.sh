#!/usr/bin/env sh
set -eu

app_id=foot_drop

. "$(dirname -- "$0")/lib_sway_lock.sh"
acquire_sway_lock "toggle_drop_term" || exit 0

if swaymsg -t get_marks 2>/dev/null | grep -qF '"drop_term"'; then
	if swaymsg -t get_tree 2>/dev/null | jq -e '.. | select((.marks // []) | index("drop_term")) | select(.visible == true)' >/dev/null; then
		swaymsg "[con_mark=drop_term] scratchpad show" >/dev/null 2>&1 || true
	else
		swaymsg "[con_mark=drop_term] scratchpad show, resize set width 75 ppt height 70 ppt, move position center" >/dev/null 2>&1 || true
	fi
	release_sway_lock "toggle_drop_term"
	exit 0
fi

swaymsg exec "foot --app-id=$app_id"

i=0
while [ "$i" -lt 40 ]; do
	if swaymsg -t get_marks 2>/dev/null | grep -qF '"drop_term"'; then
		break
	fi
	sleep 0.05
	i=$((i + 1))
done
if swaymsg -t get_marks 2>/dev/null | grep -qF '"drop_term"'; then
	swaymsg "[con_mark=drop_term] resize set width 75 ppt height 70 ppt, move position center" >/dev/null 2>&1 || true
fi
release_sway_lock "toggle_drop_term"
