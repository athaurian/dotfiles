#!/usr/bin/env sh
set -eu

# Every kitty window shares one app_id, so the sway rule matches on title.
title=drop_term

. "$(dirname -- "$0")/lib_sway_lock.sh"
acquire_sway_lock "toggle_drop_term" || exit 0

has_mark() {
	swaymsg -t get_marks 2>/dev/null | grep -qF '"drop_term"'
}

if has_mark; then
	swaymsg "[con_mark=drop_term] scratchpad show, resize set width 75 ppt height 70 ppt, move position center" >/dev/null 2>&1 || true
	release_sway_lock "toggle_drop_term"
	exit 0
fi

swaymsg exec "kitty --title=$title"

i=0
while [ "$i" -lt 40 ]; do
	if has_mark; then
		break
	fi
	sleep 0.05
	i=$((i + 1))
done
release_sway_lock "toggle_drop_term"
